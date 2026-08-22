"""Regresiones de la revisión de código del 2026-08-22.

Un test por hallazgo. Ninguno de estos fallos debe poder reaparecer en silencio.
"""
import pytest

from app import config
from app.api.openresponses import build_response
from app.api.sse import chunk_text
from app.core.agent import CVAgent, _CONTACT
from app.core.retrieval import HybridRetriever, detect_lang


# --- 1: los marcadores de idioma eran stopwords y se eliminaban antes de comparar
@pytest.mark.parametrize("q", [
    "Which companies has he worked for?",
    "Where did he study?",
    "Does he speak English?",
    "What certifications does he have?",
    "Who is Alejandro?",
    "How many years of experience does he have?",
])
def test_preguntas_en_ingles_se_detectan_como_ingles(q):
    assert detect_lang(q) == "en", q


@pytest.mark.parametrize("q", [
    "¿Dónde trabaja actualmente?",
    "¿Qué certificaciones tiene?",
    "¿Cuántos años de experiencia tiene?",
    "Dame una receta de pizza",
])
def test_preguntas_en_espanol_se_detectan_como_espanol(q):
    assert detect_lang(q) == "es", q


# --- 2: sin índice de embeddings el agente se abstenía del 100 % de preguntas
@pytest.mark.asyncio
async def test_sin_indice_degrada_a_lexico_en_vez_de_abstenerse(facts, fake_llm):
    r = HybridRetriever(facts)            # sin vectores
    assert not r.has_vectors
    a = await CVAgent(r, fake_llm()).answer("¿Qué certificaciones tiene?")
    assert not a.abstained, "en modo degradado debe responder, no abstenerse de todo"


@pytest.mark.asyncio
async def test_sin_indice_no_se_aplica_compuerta_lexica_arbitraria(facts, fake_llm):
    """Se midio que la senal lexica no separa dominio de no-dominio, asi que en
    modo degradado no se filtra: la red de seguridad es el prompt. En produccion
    este modo no existe porque el arranque falla sin indice."""
    a = await CVAgent(HybridRetriever(facts), fake_llm()).answer(
        "Escribe un poema sobre gatos y pizza")
    assert not a.abstained


# --- 3: un `top_logprobs` no numérico provocaba HTTP 500
@pytest.mark.parametrize("valor", ["abc", {}, [], None, "3", 3.7, True])
def test_campos_numericos_no_validos_no_rompen_la_respuesta(valor):
    r = build_response({"top_logprobs": valor, "temperature": valor,
                        "top_p": valor}, None)
    assert isinstance(r["top_logprobs"], int)
    assert isinstance(r["temperature"], float)


# --- 4: chunk_text añadía un espacio y los deltas no reconstruían el texto
@pytest.mark.parametrize("texto", [
    "Alejandro trabaja como desarrollador full stack en GlobalConnect.",
    "corto",
    "",
    "Una  frase   con espacios    irregulares y una palabraextremadamentelargasinespacios",
    "Cita al final [exp.globalconnect.role]",
])
def test_los_deltas_reconstruyen_el_texto_exacto(texto):
    assert "".join(chunk_text(texto)) == texto


# --- 7: el patrón de contacto capturaba `number` y `contacto` sueltos
@pytest.mark.parametrize("q", [
    "What number of years did he work at Vinte?",
    "¿En qué contexto usó Docker?",
    "¿Con cuántas empresas ha trabajado?",
    "Tell me about the contact center project",
])
def test_preguntas_legitimas_no_se_confunden_con_peticion_de_contacto(q):
    assert not _CONTACT.search(q), q


@pytest.mark.parametrize("q", [
    "¿Cuál es su número de teléfono?",
    "What is his email address?",
    "Dame sus datos de contacto",
    "How can I reach him?",
    "¿Cómo lo puedo contactar?",
])
def test_peticiones_de_contacto_si_se_detectan(q):
    assert _CONTACT.search(q), q


# --- 8: el presupuesto de tiempo debe acotar el peor caso
def test_presupuesto_total_por_debajo_de_un_timeout_tipico():
    assert config.LLM_TIMEOUT_S < config.LLM_BUDGET_S
    assert config.LLM_BUDGET_S + config.EMBED_BUDGET_S <= 35.0
