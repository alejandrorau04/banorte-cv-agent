"""Emisión de eventos SSE conforme a la especificación.

Requisitos normativos (OpenAPI 2026-04-24):
  * `Content-Type: text/event-stream`
  * formato `event: <tipo>` + `data: <JSON>`
  * el campo `event` DEBE coincidir con el `type` del payload
  * `sequence_number` monotónico creciente en TODOS los eventos
  * terminador literal `[DONE]`
"""
from __future__ import annotations
import json
from typing import Any, AsyncIterator

from app.api.openresponses import build_response, message_item
from app.core.models import Answer


class SSEStream:
    def __init__(self) -> None:
        self._n = 0

    def event(self, type_: str, payload: dict[str, Any]) -> str:
        payload = {"type": type_, "sequence_number": self._n, **payload}
        self._n += 1
        return f"event: {type_}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"

    @staticmethod
    def done() -> str:
        return "data: [DONE]\n\n"


async def stream_answer(body: dict[str, Any], answer: Answer,
                        chunks: list[str]) -> AsyncIterator[str]:
    """Emite la secuencia completa de eventos para una respuesta."""
    s = SSEStream()
    item = message_item("")
    item_id = item["id"]

    base = build_response(body, answer, status="in_progress", output=[])
    resp_id, created = base["id"], base["created_at"]

    yield s.event("response.created", {"response": base})
    yield s.event("response.in_progress", {"response": base})
    yield s.event("response.output_item.added", {"output_index": 0, "item": item})
    yield s.event("response.content_part.added", {
        "item_id": item_id, "output_index": 0, "content_index": 0,
        "part": {"type": "output_text", "text": "", "annotations": []}})

    for ch in chunks:
        yield s.event("response.output_text.delta", {
            "item_id": item_id, "output_index": 0, "content_index": 0,
            "delta": ch, "logprobs": []})

    full = answer.text
    yield s.event("response.output_text.done", {
        "item_id": item_id, "output_index": 0, "content_index": 0, "text": full})
    yield s.event("response.content_part.done", {
        "item_id": item_id, "output_index": 0, "content_index": 0,
        "part": {"type": "output_text", "text": full, "annotations": []}})

    done_item = {**item, "content": [{"type": "output_text", "text": full, "annotations": []}]}
    yield s.event("response.output_item.done", {"output_index": 0, "item": done_item})

    final = build_response(body, answer, status="completed", output=[done_item],
                           response_id=resp_id, created_at=created)
    yield s.event("response.completed", {"response": final})
    yield SSEStream.done()


def chunk_text(text: str, size: int = 24) -> list[str]:
    """Trocea respetando límites de palabra: evita cortar a mitad de palabra,
    que en la interfaz se percibe como un fallo de renderizado."""
    out, cur = [], ""
    for word in text.split(" "):
        cand = f"{cur} {word}" if cur else word
        if len(cand) >= size:
            out.append(cand + " ")
            cur = ""
        else:
            cur = cand
    if cur:
        out.append(cur)
    return out or [text]
