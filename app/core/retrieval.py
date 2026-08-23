"""Recuperación híbrida: similitud semántica + solapamiento léxico.

Por qué híbrida: los embeddings resuelven bien la paráfrasis pero degradan con
nombres propios de baja frecuencia (`Vinte`, `Quickbase`, `Rocketbot`), donde
el término literal es la señal más fuerte. Ver ADR-004.

Por qué en proceso y no en base vectorial: 46 hechos x 2 idiomas = 92 vectores.
Una base vectorial externa añadiría infraestructura, latencia de red y un punto
de fallo sin ganancia medible. La interfaz permite sustituirla si el corpus crece.
"""
from __future__ import annotations
import json
import math
import re
import unicodedata
from pathlib import Path

from app import config
from app.adapters.base import Embedder
from app.core.models import Fact, Lang, Retrieved

_WORD = re.compile(r"[a-z0-9#+.]+")
_STOP = {
    "de","la","el","los","las","un","una","y","o","en","con","para","por","del","al","que",
    "su","sus","es","fue","ha","se","cual","cuales","como","cuanto","donde","cuando","quien",
    "the","a","an","and","or","in","with","for","of","to","is","was","has","he","his","what",
    "which","how","where","when","who","did","does","do","on","at","by","from",
}


def _norm(text: str) -> list[str]:
    t = unicodedata.normalize("NFKD", text.lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    return [w for w in _WORD.findall(t) if w not in _STOP and len(w) > 1]


def _cosine(a: list[float], b: list[float]) -> float:
    num = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return num / (na * nb) if na and nb else 0.0


def _raw_tokens(text: str) -> set[str]:
    """Tokeniza SIN eliminar stopwords.

    La deteccion de idioma se apoya precisamente en interrogativos y auxiliares
    (`what`, `where`, `does`, `que`, `cual`), que son stopwords para la
    recuperacion. Filtrarlos antes de detectar vaciaba la senal: 10 de los 21
    marcadores ingleses estaban en `_STOP` y el detector devolvia siempre `es`.
    """
    t = unicodedata.normalize("NFKD", text.lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    return set(_WORD.findall(t))


def detect_lang(text: str) -> Lang:
    """Deteccion por marcadores de alta frecuencia. Determinista y sin coste:
    delegarla al LLM anadiria una llamada por peticion (ver ADR-005)."""
    toks = _raw_tokens(text)
    es = len(toks & {
        "que", "cual", "cuales", "como", "donde", "cuando", "quien", "quienes",
        "cuanto", "cuantos", "su", "sus", "tiene", "tienes", "es", "fue", "ha",
        "experiencia", "trabajo", "trabaja", "habla", "dime", "cuentame",
        "anos", "estudios", "estudio", "sabe", "conoce", "hizo", "proyectos",
        "empresa", "empresas", "puesto", "actualmente", "del", "los", "las",
        "una", "por", "para", "con", "sobre", "cuentanos", "dame",
    })
    en = len(toks & {
        "what", "which", "how", "where", "when", "who", "whose", "does", "did",
        "do", "is", "are", "was", "were", "has", "have", "his", "him", "he",
        "tell", "experience", "work", "worked", "skills", "years", "about",
        "company", "companies", "role", "currently", "projects", "know",
        "the", "of", "for", "with", "me", "you", "your", "and",
        "current", "employer", "job", "now", "study", "studied", "hold", "held",
        "certifications", "education", "background", "career", "first", "last",
        "previous", "companies", "position", "positions", "tell", "give",
    })
    return "en" if en > es else "es"


class HybridRetriever:
    """Índice en memoria. Los vectores se precalculan en build (scripts/build_index.py)."""

    def __init__(self, facts: list[Fact], embedder=None,
                 by_model: dict[str, dict[str, list[float]]] | None = None):
        self.facts = {f.id: f for f in facts}
        self._embedder = embedder
        # Un conjunto de vectores por modelo: los espacios no son comparables.
        self._by_model = by_model or {}
        self._tokens: dict[tuple[str, Lang], set[str]] = {}
        self._df: dict[Lang, dict[str, int]] = {"es": {}, "en": {}}
        for f in facts:
            for lang in ("es", "en"):
                toks = set(_norm(f.text(lang) + " " + " ".join(f.tags) + " " + (f.org or "")))
                self._tokens[(f.id, lang)] = toks
                for t in toks:
                    self._df[lang][t] = self._df[lang].get(t, 0) + 1

    @classmethod
    def from_index(cls, facts: list[Fact], path: Path | None = None,
                   embedder=None) -> "HybridRetriever":
        p = path or config.INDEX_PATH
        by_model: dict[str, dict[str, list[float]]] = {}
        if p.exists():
            d = json.loads(p.read_text())
            by_model = d.get("by_model") or (
                {config.EMBED_MODEL: d["vectors"]} if "vectors" in d else {})
        return cls(facts, embedder=embedder, by_model=by_model)

    @property
    def has_vectors(self) -> bool:
        return any(self._by_model.values())

    @property
    def indexed_models(self) -> list[str]:
        """Modelos cuyo indice cubre el corpus COMPLETO.

        Un indice parcial es peor que ninguno: los hechos sin vector nunca se
        recuperan y el fallo es silencioso -- el agente responde «no tengo esa
        informacion» sobre algo que si esta en el corpus. Ocurrio al anadir
        hechos nuevos con la cuota diaria de un modelo agotada.
        """
        necesarias = {f"{fid}::{lang}" for fid in self.facts for lang in ("es", "en")}
        return [m for m, v in self._by_model.items()
                if v and necesarias.issubset(v.keys())]

    @property
    def partial_models(self) -> dict[str, int]:
        """Modelos con indice incompleto, y cuantos vectores les faltan."""
        necesarias = {f"{fid}::{lang}" for fid in self.facts for lang in ("es", "en")}
        return {m: len(necesarias - set(v.keys()))
                for m, v in self._by_model.items()
                if v and not necesarias.issubset(v.keys())}

    def _lexical(self, query: str, lang: Lang) -> dict[str, float]:
        """Solapamiento ponderado por IDF. Premia términos raros (nombres propios)."""
        q = _norm(query)
        if not q:
            return {}
        n = len(self.facts)
        scores: dict[str, float] = {}
        for fid in self.facts:
            toks = self._tokens[(fid, lang)]
            s = 0.0
            for t in set(q):
                if t in toks:
                    df = self._df[lang].get(t, 1)
                    s += math.log(1 + n / df)
            if s:
                scores[fid] = s
        if scores:
            top = max(scores.values())
            scores = {k: v / top for k, v in scores.items()}
        return scores

    def with_timeline(self, retrieved: list[Retrieved]) -> list[Retrieved]:
        """Antepone la linea de tiempo derivada y los hechos de puesto.

        Garantiza que una pregunta de agregacion vea TODOS los empleos, no solo
        los mas parecidos a la consulta.

        Los hechos anadidos se marcan `inyectado=True` y con similitud 0: NO son
        evidencia, porque su similitud no se midio contra la consulta. Fingir un
        1.0 anulaba la compuerta de abstencion -- cualquier pregunta que
        pareciese de agregacion, incluida una fuera de dominio o un intento de
        inyeccion, saltaba el control anti-alucinacion por completo.
        """
        derivados = [self.facts[i] for i in ("derived.timeline", "derived.duraciones")
                     if i in self.facts]
        if not derivados:
            return retrieved
        ya = {r.fact.id for r in retrieved}
        extra = [Retrieved(fact=d, score=1.0, semantic=0.0, inyectado=True)
                 for d in derivados if d.id not in ya]
        ids_derivados = {d.id for d in derivados}
        for f in self.facts.values():
            if f.title and f.id not in ya and f.id not in ids_derivados:
                extra.append(Retrieved(fact=f, score=0.99, semantic=0.0, inyectado=True))
        return extra + retrieved

    async def search(self, query: str, lang: Lang,
                     k: int | None = None) -> tuple[list[Retrieved], str | None]:
        """Devuelve los hechos recuperados y QUE modelo de embedding se uso.

        El modelo importa aguas arriba: el umbral de abstencion se calibra por
        modelo, porque la escala del coseno no es comparable entre ellos.
        """
        k = k or config.TOP_K
        lex = self._lexical(query, lang)
        sem: dict[str, float] = {}
        modelo: str | None = None

        if self.has_vectors and self._embedder:
            modelo, qv = await self._embedder.embed_query(query)
            vectores = self._by_model.get(modelo) or {}
            for fid in self.facts:
                v = vectores.get(f"{fid}::{lang}")
                if v:
                    sem[fid] = max(0.0, _cosine(qv, v))
        # `sem` se conserva SIN normalizar: el coseno crudo es la unica senal con
        # significado absoluto y es la que alimenta la compuerta de evidencia.
        # Normalizarlo por el maximo haria que el mejor resultado valiese ~1.0
        # aunque fuese pesimo, y la compuerta nunca se activaria (ADR-003).

        # Sin vectores el sistema degrada a léxico puro en lugar de caer.
        w_sem = 0.65 if sem else 0.0
        w_lex = 1.0 - w_sem
        combined = {
            fid: w_sem * sem.get(fid, 0.0) + w_lex * lex.get(fid, 0.0)
            for fid in set(sem) | set(lex)
        }
        ranked = sorted(combined.items(), key=lambda kv: kv[1], reverse=True)[:k]
        return ([Retrieved(fact=self.facts[fid], score=round(s, 4),
                           semantic=round(sem.get(fid, 0.0), 4))
                 for fid, s in ranked if s > 0], modelo)
