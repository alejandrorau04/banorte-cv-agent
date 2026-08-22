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
_CONTACT = re.compile(
    r"\b(tel[eé]fono|celular|whatsapp|correo|e-?mail|contacto|contactar|"
    r"phone|number|reach him|contact)\b", re.I)


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

        # Compuerta de evidencia: sin base suficiente no se llama al modelo.
        # La compuerta usa el coseno CRUDO maximo, no la puntuacion combinada.
        best = max((r.semantic for r in retrieved), default=0.0)
        if not retrieved or best < config.MIN_SCORE:
            return done(Answer(text=prompts.ABSTAIN[lang], lang=lang,
                               retrieved=retrieved, abstained=True,
                               reason=f"low_evidence(sim={best:.3f}<{config.MIN_SCORE})"))

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
