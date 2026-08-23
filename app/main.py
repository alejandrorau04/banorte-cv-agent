"""Servidor Open Responses del agente de CV.

Contrato: `POST /v1/responses` (OpenAPI 2026-04-24, ver docs/contract/).
"""
from __future__ import annotations
import logging
import os
import time
import uuid
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse

from app import config
from app.adapters.base import ProviderError
from app.adapters.gemini import GeminiLLM, MultiEmbedder
from app.api.agentcard import agent_card
from app.api.openresponses import (SPEC_VERSION, build_response, error_body,
                                   extract_question, extract_turns)
from app.api.sse import chunk_text, stream_answer
from app.core.agent import CVAgent
from app.core.corpus import load_facts
from app.core.retrieval import HybridRetriever

logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL.upper(), logging.INFO),
    format='{"ts":"%(asctime)s","level":"%(levelname)s","msg":%(message)s}',
)
log = logging.getLogger("cv-agent")

STATE: dict = {}


@asynccontextmanager
async def lifespan(_: FastAPI):
    facts = load_facts()
    client = httpx.AsyncClient()
    # Solo se ofrecen los modelos que estan realmente indexados: uno sin
    # vectores produciria similitudes vacias y abstencion permanente.
    retriever = HybridRetriever.from_index(facts)
    retriever._embedder = MultiEmbedder(client, disponibles=retriever.indexed_models)
    STATE["client"] = client
    STATE["agent"] = CVAgent(retriever, GeminiLLM(client))
    STATE["facts"] = len(facts)
    parciales = retriever.partial_models
    if parciales:
        # No es fatal mientras quede un modelo completo, pero debe verse: un
        # indice parcial deja hechos invisibles sin ningun error visible.
        log.warning('"indice INCOMPLETO en %s"',
                    ", ".join(f"{m} (faltan {n})" for m, n in parciales.items()))
    if not retriever.indexed_models:
        # El indice se versiona en git y se copia en la imagen: su ausencia es un
        # error de construccion, no una condicion de ejecucion. Sin el no se puede
        # calibrar la compuerta de abstencion, de modo que fallar ruidosamente es
        # preferible a degradar en silencio la garantia anti-alucinacion.
        raise RuntimeError(
            "ningun modelo de embedding tiene el indice completo. "
            "Ejecutar scripts/build_index.py y reconstruir la imagen."
        )
    STATE["vectors"] = retriever.has_vectors
    STATE["embed_models"] = retriever.indexed_models
    STATE["embed_parciales"] = parciales
    STATE["started"] = time.time()
    log.info('"arranque: %d hechos, vectores=%s"', len(facts), retriever.has_vectors)
    yield
    await client.aclose()


app = FastAPI(title="CV Agent — Open Responses",
              version=config.VERSION, lifespan=lifespan)

# El validador oficial de conformidad se ejecuta desde el navegador y necesita CORS.
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["*"], expose_headers=["*"],
)


def _authorized(request: Request) -> bool:
    """Acepta varias formas de autenticación.

    La plataforma del reto no documenta cuál usa (ADR-001, supuesto 2), así que
    se toleran las variantes habituales en lugar de apostar por una.
    """
    if not config.AGENT_API_KEY:
        return True  # sin clave configurada, endpoint abierto (solo desarrollo)
    candidates = [
        request.headers.get("authorization", ""),
        request.headers.get("x-api-key", ""),
        request.headers.get("api-key", ""),
    ]
    for raw in candidates:
        token = raw[7:].strip() if raw.lower().startswith("bearer ") else raw.strip()
        if token and token == config.AGENT_API_KEY:
            return True
    return False


@app.exception_handler(Exception)
async def unhandled(_: Request, exc: Exception) -> JSONResponse:
    """Red de ultimo recurso.

    Un error imprevisto devolveria `Internal Server Error` en texto plano, que
    NO cumple el formato de error del contrato. Todo fallo debe salir tipado.
    """
    log.exception('"error no controlado: %s"', type(exc).__name__)
    return JSONResponse(status_code=500, content=error_body(
        "Unexpected server error.", "server_error", "internal_error"))


def _base_publica(request: Request) -> str:
    """URL publica del servicio, respetando el proxy de terminacion TLS.

    Azure Container Apps termina el TLS y reenvia en claro, de modo que
    `request.base_url` ve `http://`. Publicar esa URL en la tarjeta haria que un
    cliente intentase llamar al agente sin cifrar. Se respeta la cabecera
    `X-Forwarded-Proto` que el proxy anade.
    """
    proto = request.headers.get("x-forwarded-proto", "").split(",")[0].strip()
    host = request.headers.get("x-forwarded-host", "").split(",")[0].strip() \
        or request.headers.get("host", "").strip()
    if proto and host:
        return f"{proto}://{host}"
    return str(request.base_url).rstrip("/")


@app.get("/.well-known/agent-card.json")
async def tarjeta_agente(request: Request) -> JSONResponse:
    """Descubrimiento A2A. Sin autenticacion a proposito: una tarjeta que exige
    credenciales para ser leida no puede cumplir su funcion, y no revela nada
    que el repositorio publico no diga ya."""
    return JSONResponse(content=agent_card(_base_publica(request)),
                        media_type="application/a2a+json")


@app.get("/health")
async def health() -> dict:
    return {
        "status": "ok",
        "version": config.VERSION,
        # Revision del contenedor en ejecucion. Permite comprobar QUE codigo
        # esta sirviendo, no solo que el servicio responda.
        "revision": os.getenv("CONTAINER_APP_REVISION", "local"),
        "spec_version": SPEC_VERSION,
        "facts": STATE.get("facts", 0),
        "vectors_loaded": STATE.get("vectors", False),
        "embed_models": STATE.get("embed_models", []),
        "embed_models_incompletos": STATE.get("embed_parciales", {}),
        "uptime_s": round(time.time() - STATE.get("started", time.time()), 1),
    }


@app.post("/v1/responses")
@app.post("/responses")
async def create_response(request: Request):
    rid = uuid.uuid4().hex[:12]
    t0 = time.monotonic()

    if not _authorized(request):
        return JSONResponse(status_code=401, content=error_body(
            "Missing or invalid API key.", "invalid_request", "invalid_api_key"))

    try:
        body = await request.json()
    except Exception:
        body = {}
    if not isinstance(body, dict):
        body = {}

    try:
        turnos = extract_turns(body)
        question = extract_question(body)
    except Exception:  # noqa: BLE001
        # Defensa en profundidad: la extraccion ya es tolerante, pero una forma
        # de `input` no prevista no debe convertirse en un 500 sin contrato.
        log.warning('"%s input no interpretable"', rid)
        turnos, question = [], ""

    agent: CVAgent = STATE["agent"]

    try:
        instrucciones = body.get("instructions")
        answer = await agent.answer(
            question,
            instructions=instrucciones if isinstance(instrucciones, str) else None,
            history=turnos)
    except ProviderError as e:
        status = 429 if e.status == 429 else 503
        type_ = "too_many_requests" if status == 429 else "server_error"
        log.warning('"%s upstream: %s"', rid, e)
        return JSONResponse(status_code=status, content=error_body(
            str(e), type_, "upstream_unavailable"))
    except Exception as e:  # noqa: BLE001
        log.exception('"%s error"', rid)
        return JSONResponse(status_code=500, content=error_body(
            f"{type(e).__name__}", "server_error", "internal_error"))

    log.info(
        '"%s lang=%s abstained=%s model=%s tokens=%d ms=%d"',
        rid, answer.lang, answer.abstained, answer.model or "-",
        answer.usage.get("total_tokens", 0), int((time.monotonic() - t0) * 1000),
    )

    if body.get("stream"):
        return StreamingResponse(
            stream_answer(body, answer, chunk_text(answer.text)),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no",
                     "Connection": "keep-alive"},
        )

    return JSONResponse(content=build_response(body, answer))
