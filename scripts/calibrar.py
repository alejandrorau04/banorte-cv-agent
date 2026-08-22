"""Calibra el umbral de abstencion para un modelo de embeddings.

La escala del coseno no es comparable entre modelos: cambiar de modelo invalida
el umbral. Este script lo recalcula con el mismo metodo empirico del ADR-003.

Uso:  python scripts/calibrar.py <modelo>
"""
from __future__ import annotations
import asyncio, json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx
from app import config
from app.adapters.gemini import GeminiEmbedder
from app.core.corpus import load_facts
from app.core.retrieval import _cosine, detect_lang

DENTRO = ["¿Dónde trabaja actualmente?", "What experience with AI?",
          "¿Qué hizo para Vinte?", "¿Qué certificaciones tiene?",
          "Tell me about his mobile skills", "¿Habla inglés?",
          "¿Con qué bases de datos ha trabajado?", "Who is Alejandro?",
          "¿Está disponible para CDMX?", "¿A qué se dedica Alldora?"]
FUERA = ["¿Cuál es la capital de Francia?", "What is the weather today?",
         "Dame una receta de pizza", "Write me a poem about cats",
         "¿Cuánto es 2+2?", "How do I fix a car engine?",
         "¿Quién ganó el mundial de 2022?", "Explain quantum physics"]


async def main() -> int:
    modelo = sys.argv[1] if len(sys.argv) > 1 else config.EMBED_MODEL
    idx = json.loads(config.INDEX_PATH.read_text())
    vect = (idx.get("by_model") or {}).get(modelo)
    if not vect:
        print(f"ERROR: el indice no contiene vectores de {modelo}", file=sys.stderr)
        return 1
    facts = load_facts()

    async with httpx.AsyncClient() as c:
        emb = GeminiEmbedder(c, model=modelo)

        async def mejor(q: str) -> float:
            lang = detect_lang(q)
            qv = (await emb.embed([q], is_query=True))[0]
            return max((_cosine(qv, vect[f"{f.id}::{lang}"])
                        for f in facts if f"{f.id}::{lang}" in vect), default=0.0)

        d = [await mejor(q) for q in DENTRO]
        f = [await mejor(q) for q in FUERA]

    print(f"=== {modelo} ===")
    print(f"  en dominio    n={len(d)}  min={min(d):.4f}  max={max(d):.4f}")
    print(f"  fuera dominio n={len(f)}  min={min(f):.4f}  max={max(f):.4f}")
    gap = min(d) - max(f)
    print(f"  separacion    {gap:+.4f}")
    if gap <= 0:
        print("  SOLAPAMIENTO: no existe umbral perfecto para este conjunto")
        return 1
    medio = (min(d) + max(f)) / 2
    # Igual que en ADR-003: por debajo del punto medio. Abstenerse ante una
    # pregunta legitima cuesta mas que responder una fuera de dominio.
    sugerido = round(medio - gap * 0.1, 2)
    print(f"  punto medio   {medio:.4f}")
    print(f"  UMBRAL SUGERIDO: {sugerido}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
