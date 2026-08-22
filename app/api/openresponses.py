"""Traducción entre el contrato Open Responses y el núcleo del agente.

El contrato es ASIMÉTRICO (ADR-001):
  * Entrada: `CreateResponseBody.required = []`. Ningún campo es obligatorio,
    ni `model` ni `input`. Se aplican valores por defecto, nunca se rechaza.
  * Salida: `ResponseResource` exige 31 campos. Emitir solo `{id, status, output}`
    NO es conforme.
"""
from __future__ import annotations
import time
import uuid
from typing import Any

from app.core.models import Answer

SPEC_VERSION = "2026-04-24"


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex}"


# ---------------------------------------------------------------- entrada ----

def extract_question(body: dict[str, Any]) -> str:
    """Obtiene el último mensaje de usuario.

    `input` admite tres formas segun el esquema: texto plano, array de items, o
    null. Las tres deben funcionar; ninguna puede provocar un rechazo.
    """
    inp = body.get("input")
    if inp is None:
        return ""
    if isinstance(inp, str):
        return inp.strip()
    if not isinstance(inp, list):
        return str(inp).strip()

    last = ""
    for item in inp:
        if not isinstance(item, dict):
            continue
        if item.get("type") not in (None, "message"):
            continue
        if item.get("role") not in (None, "user"):
            continue
        content = item.get("content")
        if isinstance(content, str):
            last = content
        elif isinstance(content, list):
            parts: list[str] = []
            for p in content:
                if not isinstance(p, dict):
                    continue
                if p.get("type") not in ("input_text", "text", "output_text", None):
                    continue
                txt = p.get("text")
                # `text` puede llegar con cualquier forma: el contrato no valida
                # tipos. Solo se acepta texto; cualquier otra cosa se ignora en
                # lugar de propagar un TypeError.
                if isinstance(txt, str):
                    parts.append(txt)
            if any(parts):
                last = "".join(parts)
    return last.strip() if isinstance(last, str) else ""


# ----------------------------------------------------------------- salida ----

def message_item(text: str) -> dict[str, Any]:
    return {
        "id": _id("msg"),
        "type": "message",
        "status": "completed",
        "role": "assistant",
        "content": [{"type": "output_text", "text": text, "annotations": []}],
    }


def build_response(
    body: dict[str, Any],
    answer: Answer | None,
    *,
    status: str = "completed",
    output: list[dict[str, Any]] | None = None,
    error: dict[str, Any] | None = None,
    response_id: str | None = None,
    created_at: int | None = None,
) -> dict[str, Any]:
    """Construye un `ResponseResource` con los 31 campos obligatorios.

    Los anulables se emiten explícitamente como `null`: omitirlos incumple el
    esquema aunque el valor sea vacío.
    """
    now = int(time.time())
    items = output if output is not None else ([message_item(answer.text)] if answer else [])

    usage = None
    if answer and answer.usage:
        usage = {
            "input_tokens": answer.usage.get("input_tokens", 0),
            "input_tokens_details": {"cached_tokens": 0},
            "output_tokens": answer.usage.get("output_tokens", 0),
            "output_tokens_details": {
                "reasoning_tokens": answer.usage.get("reasoning_tokens", 0)
            },
            "total_tokens": answer.usage.get("total_tokens", 0),
        }
    elif answer is not None:
        # Abstención: no hubo llamada al modelo. Cero es el dato correcto y es
        # justamente la evidencia del ahorro (ADR-005).
        usage = {
            "input_tokens": 0,
            "input_tokens_details": {"cached_tokens": 0},
            "output_tokens": 0,
            "output_tokens_details": {"reasoning_tokens": 0},
            "total_tokens": 0,
        }

    # Trazabilidad: qué se recuperó y qué se citó. `metadata` es un campo
    # estándar, por lo que no rompe la conformidad (ADR-007).
    metadata: dict[str, str] = {"spec_version": SPEC_VERSION}
    if answer:
        metadata.update({
            "lang": answer.lang,
            "grounded": "false" if answer.abstained else "true",
            "abstained": str(answer.abstained).lower(),
            "citations": ",".join(answer.citations)[:480],
            "retrieved": ",".join(f"{r.fact.id}:{r.semantic}" for r in answer.retrieved[:5])[:480],
            "latency_ms": str(answer.latency_ms),
        })
        if answer.reason:
            metadata["abstain_reason"] = answer.reason[:120]

    return {
        "id": response_id or _id("resp"),
        "object": "response",
        "created_at": created_at or now,
        "completed_at": now if status in ("completed", "failed", "incomplete") else None,
        "status": status,
        "incomplete_details": None,
        "model": body.get("model") or (answer.model if answer and answer.model else "cv-agent"),
        "previous_response_id": body.get("previous_response_id"),
        "instructions": body.get("instructions"),
        "output": items,
        "error": error,
        "tools": body.get("tools") or [],
        "tool_choice": body.get("tool_choice") or "auto",
        "truncation": body.get("truncation") or "disabled",
        "parallel_tool_calls": bool(body.get("parallel_tool_calls", True)),
        "text": body.get("text") or {"format": {"type": "text"}},
        "top_p": _num(body.get("top_p"), 1.0),
        "presence_penalty": _num(body.get("presence_penalty"), 0.0),
        "frequency_penalty": _num(body.get("frequency_penalty"), 0.0),
        "top_logprobs": _int(body.get("top_logprobs"), 0),
        "temperature": _num(body.get("temperature"), 0.2),
        "reasoning": None,
        "usage": usage,
        "max_output_tokens": body.get("max_output_tokens"),
        "max_tool_calls": body.get("max_tool_calls"),
        "store": bool(body.get("store", False)),
        "background": bool(body.get("background", False)),
        "service_tier": body.get("service_tier") or "default",
        "metadata": metadata,
        "safety_identifier": body.get("safety_identifier"),
        "prompt_cache_key": body.get("prompt_cache_key"),
    }


def _num(v: Any, default: float) -> float:
    try:
        return float(v) if v is not None else default
    except (TypeError, ValueError):
        return default


def _int(v: Any, default: int) -> int:
    """El contrato no declara ningun campo obligatorio ni valida tipos, asi que
    un valor no numerico debe aplicar el default, nunca provocar un 500."""
    try:
        return int(v) if v is not None else default
    except (TypeError, ValueError):
        return default


def error_body(message: str, type_: str, code: str, param: str | None = None) -> dict[str, Any]:
    e = {"message": message, "type": type_, "code": code}
    if param:
        e["param"] = param
    return {"error": e}
