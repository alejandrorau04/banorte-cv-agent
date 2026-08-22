"""Tipos internos del núcleo. Deliberadamente independientes de Open Responses:
el núcleo no debe conocer su transporte (ver ADR-001)."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Literal

Lang = Literal["es", "en"]


@dataclass(frozen=True)
class Fact:
    id: str
    type: str
    text_es: str
    text_en: str
    tags: tuple[str, ...] = ()
    org: str | None = None
    title: str | None = None
    title_en: str | None = None
    start: str | None = None
    end: str | None = None
    line_start: int = 0
    line_end: int = 0

    def text(self, lang: Lang) -> str:
        return self.text_es if lang == "es" else self.text_en

    def label(self, lang: Lang) -> str:
        """Etiqueta legible para mostrar la fuente a una persona.

        Un identificador como `exp.globalconnect.role` es trazabilidad para una
        maquina; una persona necesita «Experiencia · GlobalConnect (may 2025 –
        actual)». Se construye desde los metadatos que ya existen.
        """
        seccion = _SECCION[self.type][0 if lang == "es" else 1]
        partes = [seccion]
        if self.org:
            partes.append(self.org.split("·")[0].strip())
        rango = _rango(self.start, self.end, lang)
        etiqueta = " · ".join(partes)
        return f"{etiqueta} ({rango})" if rango else etiqueta


_SECCION = {
    "profile": ("Perfil", "Profile"),
    "experience": ("Experiencia", "Experience"),
    "skills": ("Competencias", "Skills"),
    "education": ("Formación", "Education"),
    "achievement": ("Logros", "Achievements"),
    "timeline": ("Trayectoria", "Timeline"),
    "other": ("CV", "CV"),
}

_MES_CORTO = {
    "01": ("ene", "Jan"), "02": ("feb", "Feb"), "03": ("mar", "Mar"),
    "04": ("abr", "Apr"), "05": ("may", "May"), "06": ("jun", "Jun"),
    "07": ("jul", "Jul"), "08": ("ago", "Aug"), "09": ("sep", "Sep"),
    "10": ("oct", "Oct"), "11": ("nov", "Nov"), "12": ("dic", "Dec"),
}


def _mes(v: str, i: int) -> str:
    y, m = v.split("-")
    return f"{_MES_CORTO[m][i]} {y}"


def _rango(start: str | None, end: str | None, lang: Lang) -> str:
    if not start:
        return ""
    i = 0 if lang == "es" else 1
    hasta = _mes(end, i) if end else ("actual" if lang == "es" else "present")
    return f"{_mes(start, i)} – {hasta}"


@dataclass(frozen=True)
class Retrieved:
    fact: Fact
    score: float          # puntuacion combinada, para ORDENAR
    semantic: float = 0.0  # coseno crudo, para DECIDIR si hay evidencia


@dataclass
class Answer:
    text: str
    lang: Lang
    citations: list[str] = field(default_factory=list)
    retrieved: list[Retrieved] = field(default_factory=list)
    abstained: bool = False
    reason: str = ""
    model: str | None = None
    usage: dict[str, int] = field(default_factory=dict)
    latency_ms: int = 0
