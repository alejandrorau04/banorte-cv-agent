"""Comportamiento del nucleo: abstencion, citas y privacidad. Sin red."""
import pytest

from app.core.agent import CVAgent, _verify_citations
from app.core.retrieval import HybridRetriever, detect_lang


@pytest.mark.parametrize("q,lang", [
    ("¿Dónde trabaja actualmente?", "es"),
    ("¿Qué certificaciones tiene?", "es"),
    ("What experience does he have?", "en"),
    ("Tell me about his skills", "en"),
])
def test_deteccion_de_idioma(q, lang):
    assert detect_lang(q) == lang


def test_citas_inventadas_se_eliminan():
    text, cites = _verify_citations(
        "Afirmacion A [real.id]. Afirmacion B [inventado.id].", {"real.id"})
    assert "inventado.id" not in text
    assert cites == ["real.id"]


def test_citas_agrupadas_se_filtran_conservando_las_validas():
    text, cites = _verify_citations("Algo [a.b, c.d, x.y].", {"a.b", "c.d"})
    assert cites == ["a.b", "c.d"] and "x.y" not in text


@pytest.mark.asyncio
async def test_pregunta_de_contacto_no_invoca_al_llm(facts, fake_llm):
    llm = fake_llm()
    agent = CVAgent(HybridRetriever(facts), llm)
    a = await agent.answer("¿Cuál es su número de teléfono?")
    assert a.abstained and a.reason == "contact_policy"
    assert llm.calls == 0, "una pregunta de contacto no debe llegar al modelo"
    assert a.usage.get("total_tokens", 0) == 0


@pytest.mark.asyncio
async def test_pregunta_vacia_se_abstiene(facts, fake_llm):
    llm = fake_llm()
    a = await CVAgent(HybridRetriever(facts), llm).answer("   ")
    assert a.abstained and llm.calls == 0


def test_el_corpus_no_contiene_datos_de_contacto(facts):
    """ADR-006. Falla el build si alguien reintroduce PII."""
    import re
    pat = re.compile(r"[\w.+-]+@[\w-]+\.\w+|\b\d{2}\s?\d{4}\s?\d{4}\b")
    for f in facts:
        assert not pat.search(f.text_es), f.id
        assert not pat.search(f.text_en), f.id


def test_todo_hecho_tiene_ambos_idiomas(facts):
    for f in facts:
        assert f.text_es and f.text_en, f.id


def test_ids_del_corpus_son_unicos(facts):
    ids = [f.id for f in facts]
    assert len(ids) == len(set(ids))
