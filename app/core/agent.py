"""Núcleo del agente: recuperar -> decidir -> generar -> verificar.

Estrategia anti-alucinación en cuatro controles (ADR-003):
  1. Grounding    - el prompt solo contiene hechos recuperados del corpus.
  2. Compuerta    - si la evidencia es débil se abstiene SIN invocar al LLM
                    (coste cero y latencia mínima en preguntas fuera de dominio).
  3. Verificación - toda cita [id] emitida debe existir en lo recuperado; las
                    inventadas se eliminan del texto.
  4. Trazabilidad - se registra qué se recuperó, con qué puntuación y qué se citó.
"""
from __future__ import annotations
import re
import time

from app.adapters.base import LLM, ProviderError
from app.core import prompts
from app.core.models import Answer, Lang, Retrieved
from app.core.retrieval import HybridRetriever, detect_lang
from app import config

# Acepta tanto [id] como la forma agrupada [id1, id2] que el modelo produce.
_CITE_BLOCK = re.compile(r"\[([a-z0-9_.\-]+(?:\s*,\s*[a-z0-9_.\-]+)*)\]", re.I)

# Preguntas de contacto: se atienden con respuesta fija, sin LLM (ADR-006).
# Patron deliberadamente estrecho. Una version previa capturaba `number`,
# `contact` y `contacto` sueltos, de modo que "What number of years did he work
# at Vinte?" recibia la respuesta de privacidad. La compuerta precede a la
# recuperacion, asi que un falso positivo aqui no tiene via de recuperacion.
# Preguntas de AGREGACION, ORDEN o SECUENCIA. La recuperacion top-k no puede
# responderlas: necesitan el corpus completo. Se detectan para inyectar la linea
# de tiempo derivada de los metadatos (ver ADR-008).
#
# Sin esto se midieron dos fallos reales contra produccion:
#   "cual fue su ultimo puesto antes de GlobalConnect?" -> afirmaba que no habia
#   ninguno entre 2018 y 2025, cuando la respuesta era Alldora.
#   "lista todas las empresas en orden cronologico" -> orden incorrecto y
#   mezclaba clientes con empleadores.
_AGREGADA = re.compile(
    r"\b(todas?\s+(las\s+)?(sus\s+)?empresas?|lista|listado|enumera|"
    r"cronol[oó]gic\w*|orden\w*|trayectoria|historial|carrera\s+completa|"
    r"cu[aá]nt\w+\s+(empresas?|trabajos?|puestos?|a[nñ]os)|"
    r"antes\s+de|anterior\w*|previo\w*|despu[eé]s\s+de|"
    r"primer\w*\s+(empleo|trabajo|puesto)|[uú]ltim\w*\s+(empleo|trabajo|puesto)|"
    r"resumen\s+de\s+su|"
    r"list\s+(all|every|the)|all\s+(the\s+)?(companies|jobs|roles|positions)|"
    r"chronolog\w*|timeline|work\s+history|career\s+(path|history|summary)|"
    r"how\s+many\s+(companies|jobs|roles|years)|"
    r"before\s+|previous\s+(job|role|position|employer)|after\s+(he|leaving)|"
    r"first\s+(job|role|position)|last\s+(job|role|position))\b", re.I)

_CONTACT = re.compile(
    r"\b(tel[eé]fono|celular|whatsapp|"
    r"correo\s+(electr[oó]nico|personal)?|e-?mail|"
    r"datos?\s+de\s+contacto|c[oó]mo\s+(lo\s+)?(puedo\s+)?contact|"
    r"phone\s+number|email\s+address|contact\s+(details?|info)|"
    r"reach\s+(him|out)|get\s+in\s+touch)", re.I)


class CVAgent:
    def __init__(self, retriever: HybridRetriever, llm: LLM):
        self._r = retriever
        self._llm = llm

    async def answer(self, question: str, lang: Lang | None = None) -> Answer:
        t0 = time.monotonic()
        lang = lang or detect_lang(question)

        def done(a: Answer) -> Answer:
            a.latency_ms = int((time.monotonic() - t0) * 1000)
            return a

        q = (question or "").strip()
        if not q:
            return done(Answer(text=prompts.ABSTAIN[lang], lang=lang,
                               abstained=True, reason="empty_question"))

        if _CONTACT.search(q):
            return done(Answer(text=prompts.CONTACT[lang], lang=lang,
                               abstained=True, reason="contact_policy"))

        retrieved = await self._r.search(q, lang)

        # Las preguntas de agregacion / orden se responden con la linea de tiempo
        # derivada de los metadatos, no con lo que el modelo infiera del top-k.
        if _AGREGADA.search(q):
            retrieved = self._r.with_timeline(retrieved)

        # Compuerta de evidencia: sin base suficiente no se llama al modelo.
        # La compuerta usa el coseno CRUDO maximo, no la puntuacion combinada.
        #
        # Sin indice de embeddings NO se aplica: se midio que la senal lexica no
        # separa dominio de no-dominio (una pregunta legitima puede puntuar 0.00
        # y una absurda 3.85), asi que cualquier umbral lexico seria arbitrario.
        # Ese modo degradado existe solo para pruebas unitarias: en produccion el
        # arranque falla si falta el indice (ver app/main.py). La red de seguridad
        # restante es el prompt, que redirige con elegancia.
        best = max((r.semantic for r in retrieved), default=0.0)
        floor = config.MIN_SCORE
        if self._r.has_vectors and (not retrieved or best < floor):
            return done(Answer(text=prompts.ABSTAIN[lang], lang=lang,
                               retrieved=retrieved, abstained=True,
                               reason=f"low_evidence(sim={best:.3f}<{floor})"))

        user = _build_user_prompt(q, retrieved, lang)
        try:
            c = await self._llm.complete(prompts.SYSTEM[lang], user)
        except ProviderError as e:
            raise e

        text, cites = _verify_citations(c.text, {r.fact.id for r in retrieved})
        return done(Answer(text=text, lang=lang, citations=cites, retrieved=retrieved,
                           model=c.model, usage=c.usage))


def _build_user_prompt(question: str, retrieved: list[Retrieved], lang: Lang) -> str:
    facts = "\n".join(f"[{r.fact.id}] {r.fact.text(lang)}" for r in retrieved)
    label = "PREGUNTA" if lang == "es" else "QUESTION"
    return f"HECHOS:\n{facts}\n\n{label}: {question}"


def _verify_citations(text: str, allowed: set[str]) -> tuple[str, list[str]]:
    """Elimina las citas a identificadores que no fueron recuperados.

    El modelo puede inventar un id plausible. Una cita no verificable es peor
    que ninguna: aparenta respaldo donde no lo hay.
    """
    valid: list[str] = []

    def _clean(m: re.Match[str]) -> str:
        ids = [i.strip() for i in m.group(1).split(",")]
        keep = [i for i in ids if i in allowed]
        valid.extend(keep)
        return f"[{', '.join(keep)}]" if keep else ""

    text = _CITE_BLOCK.sub(_clean, text)
    text = re.sub(r"\s+([.,;:])", r"\1", text)
    text = re.sub(r"[ \t]{2,}", " ", text).strip()
    seen, ordered = set(), []
    for c in valid:
        if c not in seen:
            seen.add(c)
            ordered.append(c)
    return text, ordered
