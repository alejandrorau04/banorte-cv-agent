"""Precalcula los embeddings del corpus, de forma incremental.

Se ejecuta en build, no en runtime: evita coste y latencia por peticion, y hace
que el arranque del contenedor no dependa del proveedor (ver ADR-005).

Es INCREMENTAL: cada vector se guarda junto al hash de su texto, y solo se
recalculan los hechos nuevos o modificados. Reconstruir el indice entero cada
vez desperdicia cuota -- el nivel gratuito devolvio HTTP 429 tras varias
reconstrucciones completas el 2026-08-22 -- y ralentiza el ciclo de desarrollo.

Uso:
    python scripts/build_index.py            # incremental
    python scripts/build_index.py --full     # fuerza recalculo completo
"""
from __future__ import annotations
import asyncio, hashlib, json, sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx
from app import config
from app.adapters.base import ProviderError
from app.adapters.gemini import GeminiEmbedder
from app.core.corpus import load_facts


LOTE = 20      # peticiones por lote antes de guardar
PAUSA = 8.0    # segundos entre lotes, para no agotar la cuota por minuto


def _hash(texto: str) -> str:
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()[:16]


def _guardar(por_modelo: dict, hashes: dict) -> None:
    config.INDEX_PATH.write_text(json.dumps({
        "dim": config.EMBED_DIM,
        "models": {m: len(v) for m, v in por_modelo.items()},
        "hashes": hashes,
        "by_model": por_modelo,
    }))


async def main() -> int:
    if not config.GEMINI_API_KEY:
        print("ERROR: falta GEMINI_API_KEY", file=sys.stderr)
        return 1

    completo = "--full" in sys.argv
    solo = [a for a in sys.argv[1:] if not a.startswith("--")]
    modelos = solo or list(config.EMBED_MODELS)

    previo: dict = {}
    if config.INDEX_PATH.exists() and not completo:
        previo = json.loads(config.INDEX_PATH.read_text())
        if previo.get("dim") != config.EMBED_DIM:
            print("dimension distinta: se recalcula todo")
            previo = {}

    por_modelo: dict[str, dict] = dict(previo.get("by_model") or {})
    hashes_por_modelo: dict[str, dict] = dict(previo.get("hashes") or {})
    facts = load_facts()
    fallos = 0

    for modelo in modelos:
        vectores = dict(por_modelo.get(modelo) or {})
        hashes = dict(hashes_por_modelo.get(modelo) or {})

        pendientes: list[tuple[str, str]] = []
        vigentes: set[str] = set()
        for f in facts:
            for lang in ("es", "en"):
                clave = f"{f.id}::{lang}"
                vigentes.add(clave)
                h = _hash(f.text(lang))
                if vectores.get(clave) is None or hashes.get(clave) != h:
                    pendientes.append((clave, f.text(lang)))
                hashes[clave] = h
        for obsoleta in set(vectores) - vigentes:
            vectores.pop(obsoleta, None)
            hashes.pop(obsoleta, None)

        print(f"\n[{modelo}] necesarios {len(vigentes)} | "
              f"reutilizados {len(vigentes) - len(pendientes)} | "
              f"a calcular {len(pendientes)}")

        if pendientes:
            t0 = time.time()
            # Por lotes con guardado incremental: el nivel gratuito limita las
            # peticiones por minuto, y perder 100 vectores calculados por un 429
            # en el ultimo es inaceptable. Al reejecutar, continua donde quedo.
            cortado = False
            async with httpx.AsyncClient() as c:
                emb = GeminiEmbedder(c, model=modelo)
                for i in range(0, len(pendientes), LOTE):
                    lote = pendientes[i:i + LOTE]
                    try:
                        nuevos = await emb.embed([x for _, x in lote])
                    except ProviderError as e:
                        print(f"  cortado en {i}/{len(pendientes)}: "
                              f"{str(e)[:70]}", file=sys.stderr)
                        cortado = True
                        break
                    for (clave, _), v in zip(lote, nuevos):
                        vectores[clave] = v
                    hechos_ok = min(i + LOTE, len(pendientes))
                    print(f"  {hechos_ok}/{len(pendientes)}", end="\r", flush=True)
                    # Guardado incremental tras cada lote.
                    por_modelo[modelo] = vectores
                    hashes_por_modelo[modelo] = {
                        k: v for k, v in hashes.items() if k in vectores}
                    _guardar(por_modelo, hashes_por_modelo)
                    if hechos_ok < len(pendientes):
                        await asyncio.sleep(PAUSA)
            print(f"  {len(vectores)} vectores tras {time.time() - t0:.1f}s")
            if cortado:
                fallos += 1

        por_modelo[modelo] = vectores
        hashes_por_modelo[modelo] = {k: v for k, v in hashes.items() if k in vectores}

    _guardar(por_modelo, hashes_por_modelo)
    print("\nindice guardado:")
    for m, v in por_modelo.items():
        completo_m = "completo" if len(v) == len(facts) * 2 else f"INCOMPLETO ({len(v)})"
        print(f"  {m:24} {len(v):>4} vectores  {completo_m}")
    return 1 if fallos == len(modelos) else 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
