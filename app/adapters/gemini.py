"""Adaptador de Google Gemini (AI Studio).

Dos comportamientos no negociables, ambos medidos el 2026-08-22:
  * `thinkingLevel: minimal` — elimina los tokens de razonamiento (-77% consumo).
  * Cadena de respaldo entre modelos — el nivel gratuito devuelve 503 con
    frecuencia; un modelo único sería un punto de fallo.
"""
from __future__ import annotations
import asyncio
import time

import httpx
from typing import Sequence

from app import config
from app.adapters.base import Completion, ProviderError

_RETRYABLE = {429, 500, 502, 503, 504}


class GeminiLLM:
    def __init__(self, client: httpx.AsyncClient, models: Sequence[str] | None = None):
        self._c = client
        self._models = tuple(models or config.GEN_MODELS)

    async def complete(self, system: str, user: str) -> Completion:
        deadline = time.monotonic() + config.LLM_BUDGET_S
        body = {
            "systemInstruction": {"parts": [{"text": system}]},
            "contents": [{"role": "user", "parts": [{"text": user}]}],
            "generationConfig": {
                "temperature": config.TEMPERATURE,
                "maxOutputTokens": config.MAX_OUTPUT_TOKENS,
                "thinkingConfig": {"thinkingLevel": config.THINKING_LEVEL},
            },
        }
        last: Exception | None = None
        for model in self._models:
            for attempt in range(3):
                if time.monotonic() >= deadline:
                    raise last or ProviderError("presupuesto de tiempo agotado")
                try:
                    r = await self._c.post(
                        f"{config.GEMINI_BASE}/{model}:generateContent",
                        params={"key": config.GEMINI_API_KEY},
                        json=body, timeout=config.LLM_TIMEOUT_S,
                    )
                    if r.status_code in _RETRYABLE:
                        last = ProviderError(f"{model}: HTTP {r.status_code}", status=r.status_code)
                        await asyncio.sleep(0.4 * (2 ** attempt))
                        continue
                    if r.status_code != 200:
                        last = ProviderError(
                            f"{model}: HTTP {r.status_code} {r.text[:160]}", status=r.status_code)
                        break  # error no reintentable: pasar al siguiente modelo
                    return _parse(r.json(), model)
                except httpx.HTTPError as e:
                    last = ProviderError(f"{model}: {type(e).__name__}")
                    await asyncio.sleep(0.4 * (2 ** attempt))
        raise last or ProviderError("sin modelos disponibles")


def _parse(data: dict, model: str) -> Completion:
    cands = data.get("candidates") or []
    parts = (cands[0].get("content", {}).get("parts") or []) if cands else []
    text = "".join(p.get("text", "") for p in parts).strip()
    if not text:
        raise ProviderError(f"{model}: respuesta vacía")
    u = data.get("usageMetadata") or {}
    return Completion(text=text, model=model, usage={
        "input_tokens": u.get("promptTokenCount", 0),
        "output_tokens": u.get("candidatesTokenCount", 0),
        "reasoning_tokens": u.get("thoughtsTokenCount", 0),
        "total_tokens": u.get("totalTokenCount", 0),
    })


class GeminiEmbedder:
    def __init__(self, client: httpx.AsyncClient, model: str | None = None):
        self._c = client
        self._model = model or config.EMBED_MODEL

    async def embed(self, texts: Sequence[str], *, is_query: bool = False) -> list[list[float]]:
        # Los modelos de embedding distinguen consulta de documento; usar el
        # task_type correcto mejora de forma apreciable la recuperación.
        task = "RETRIEVAL_QUERY" if is_query else "RETRIEVAL_DOCUMENT"
        out: list[list[float]] = []
        for t in texts:
            for attempt in range(3):
                r = await self._c.post(
                    f"{config.GEMINI_BASE}/{self._model}:embedContent",
                    params={"key": config.GEMINI_API_KEY},
                    json={"model": f"models/{self._model}",
                          "content": {"parts": [{"text": t}]},
                          "taskType": task,
                          "outputDimensionality": config.EMBED_DIM},
                    timeout=config.LLM_TIMEOUT_S,
                )
                if r.status_code == 200:
                    out.append(r.json()["embedding"]["values"])
                    break
                if r.status_code in _RETRYABLE and attempt < 2:
                    await asyncio.sleep(0.5 * (2 ** attempt))
                    continue
                raise ProviderError(f"embed: HTTP {r.status_code} {r.text[:160]}",
                                    status=r.status_code)
        return out
