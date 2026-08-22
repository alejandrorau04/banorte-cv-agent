"""Puertos del núcleo. El núcleo depende de estas interfaces, nunca de un
proveedor concreto. Migrar a Azure OpenAI es implementar estas dos clases
(ver ADR-004)."""
from __future__ import annotations
from typing import Protocol, Sequence
from dataclasses import dataclass


@dataclass
class Completion:
    text: str
    model: str
    usage: dict[str, int]


class ProviderError(RuntimeError):
    """Fallo del proveedor tras agotar reintentos y respaldos."""
    def __init__(self, message: str, *, status: int | None = None):
        super().__init__(message)
        self.status = status


class LLM(Protocol):
    async def complete(self, system: str, user: str) -> Completion: ...


class Embedder(Protocol):
    async def embed(self, texts: Sequence[str], *, is_query: bool = False) -> list[list[float]]: ...
