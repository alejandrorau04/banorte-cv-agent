"""Precalcula los embeddings del corpus.

Se ejecuta en build, no en runtime: evita coste y latencia por petición, y hace
que el arranque del contenedor no dependa del proveedor (ver ADR-005).
"""
from __future__ import annotations
import asyncio, json, sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx
from app import config
from app.adapters.gemini import GeminiEmbedder
from app.core.corpus import load_facts


async def main() -> int:
    if not config.GEMINI_API_KEY:
        print("ERROR: falta GEMINI_API_KEY", file=sys.stderr)
        return 1
    facts = load_facts()
    keys, texts = [], []
    for f in facts:
        for lang in ("es", "en"):
            keys.append(f"{f.id}::{lang}")
            texts.append(f.text(lang))

    t0 = time.time()
    async with httpx.AsyncClient() as c:
        vectors = await GeminiEmbedder(c).embed(texts)

    config.INDEX_PATH.write_text(json.dumps({
        "model": config.EMBED_MODEL,
        "dim": len(vectors[0]),
        "count": len(vectors),
        "vectors": dict(zip(keys, vectors)),
    }))
    print(f"indice: {len(vectors)} vectores, dim={len(vectors[0])}, "
          f"{time.time()-t0:.1f}s -> {config.INDEX_PATH.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
