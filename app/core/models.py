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
    start: str | None = None
    end: str | None = None

    def text(self, lang: Lang) -> str:
        return self.text_es if lang == "es" else self.text_en


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
