"""Conformidad del streaming SSE. Sin red."""
import json
import re

import pytest

from app.api.sse import SSEStream, chunk_text, stream_answer
from app.core.models import Answer


def test_sequence_number_es_monotonico():
    s = SSEStream()
    seqs = [json.loads(s.event("t", {}).split("data: ")[1])["sequence_number"] for _ in range(5)]
    assert seqs == [0, 1, 2, 3, 4]


def test_campo_event_coincide_con_type_del_payload():
    raw = SSEStream().event("response.created", {"response": {}})
    ev = re.search(r"^event: (.+)$", raw, re.M).group(1)
    assert ev == json.loads(re.search(r"^data: (.+)$", raw, re.M).group(1))["type"]


def test_chunk_text_no_parte_palabras():
    text = "Alejandro trabaja como desarrollador full stack en GlobalConnect"
    assert "".join(chunk_text(text)).split() == text.split()


@pytest.mark.asyncio
async def test_secuencia_completa_de_eventos_y_terminador():
    a = Answer(text="Hola mundo desde el agente", lang="es")
    chunks = [c async for c in stream_answer({}, a, chunk_text(a.text))]
    assert chunks[-1] == "data: [DONE]\n\n"

    types, seqs = [], []
    for c in chunks[:-1]:
        d = json.loads(re.search(r"^data: (.+)$", c, re.M).group(1))
        types.append(d["type"])
        seqs.append(d["sequence_number"])

    assert seqs == list(range(len(seqs)))
    assert types[0] == "response.created"
    assert types[-1] == "response.completed"
    for t in ("response.in_progress", "response.output_item.added",
              "response.content_part.added", "response.output_text.delta",
              "response.output_text.done", "response.output_item.done"):
        assert t in types
