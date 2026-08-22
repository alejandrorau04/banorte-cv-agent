"""Ejecuta el golden set contra el agente e imprime métricas.

Criterios por tipo de caso:
  answer  -> responde, no se abstiene, y cita al menos uno de `must_cite`
  abstain -> se abstiene por baja evidencia y NO invoca al LLM (0 tokens)
  contact -> aplica la política de privacidad, sin LLM
  honest  -> responde sin afirmar ninguno de los términos de `forbid`
"""
from __future__ import annotations
import asyncio, json, re, sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx, yaml
from app.adapters.base import ProviderError
from app.adapters.gemini import GeminiLLM, MultiEmbedder
from app.core.agent import CVAgent
from app.core.corpus import load_facts
from app.core.retrieval import HybridRetriever
from app import config

GS = Path(__file__).parent / "golden_set.yaml"

# Marcas de negacion en espanol e ingles.
_NEG = ("no ", "no,", "not ", "n't", "sin ", "ninguna", "ningun", "nada indica",
        "tampoco", "lo siento", "sorry", "cannot", "unable", "carece")


def _afirma(text: str, term: str) -> bool:
    """True si el termino aparece en una frase SIN marca de negacion."""
    term = term.lower()
    for frase in re.split(r"(?<=[.!?])\s+|\n+", text.lower()):
        if term in frase and not any(n in frase for n in _NEG):
            return True
    return False


def judge(case: dict, a) -> tuple[bool, str]:
    exp = case["expect"]
    if exp == "abstain":
        if not a.abstained:
            return False, "debia abstenerse y respondio"
        if not a.reason.startswith("low_evidence"):
            return False, f"abstuvo por motivo inesperado: {a.reason}"
        if a.usage.get("total_tokens", 0) != 0:
            return False, "consumio tokens"
        return True, ""
    if exp == "contact":
        return (a.abstained and a.reason == "contact_policy"), \
               "" if a.reason == "contact_policy" else f"motivo={a.reason}"
    if exp == "answer":
        if a.abstained:
            return False, f"se abstuvo: {a.reason}"
        want = set(case.get("must_cite") or [])
        if want and not (set(a.citations) & want):
            return False, f"citas {a.citations} no intersecan {sorted(want)}"
        # `forbid_text`: fragmentos que NO deben aparecer literalmente. Distinto
        # de `forbid` (que admite negacion): aqui la frase es incorrecta en si.
        mal = [s for s in (case.get("forbid_text") or []) if s.lower() in a.text.lower()]
        if mal:
            return False, f"contiene texto prohibido: {mal}"
        return True, ""
    if exp == "honest":
        if a.abstained:
            return True, ""  # abstenerse tambien es honesto
        # `forbid` prohibe AFIRMAR el termino, no mencionarlo: un agente no puede
        # negar "Harvard" sin escribir "Harvard". Se exige por tanto una marca de
        # negacion en la MISMA frase donde aparece el termino.
        bad = [w for w in (case.get("forbid") or []) if _afirma(a.text, w)]
        return (not bad), (f"AFIRMA termino prohibido: {bad}" if bad else "")
    return False, f"tipo desconocido: {exp}"


async def main() -> int:
    cases = yaml.safe_load(GS.read_text())["cases"]
    facts = load_facts()
    rows, t0 = [], time.time()

    async with httpx.AsyncClient() as c:
        retriever = HybridRetriever.from_index(facts)
        retriever._embedder = MultiEmbedder(c, disponibles=retriever.indexed_models)
        agent = CVAgent(retriever, GeminiLLM(c))
        for case in cases:
            try:
                a = await agent.answer(case["q"])
            except ProviderError as e:
                # Un fallo del proveedor no debe abortar la corrida: se registra
                # como error de infraestructura, distinto de un fallo del agente.
                rows.append({"q": case["q"], "expect": case["expect"], "ok": False,
                             "why": f"ERROR PROVEEDOR: {e}", "lang": "-",
                             "abstained": False, "tokens": 0, "ms": 0,
                             "citations": [], "text": ""})
                print(f"  ERROR  [{case['expect']:7}] {case['q'][:58]}  <- {e}")
                continue
            ok, why = judge(case, a)
            degradado = bool(a.embed_model and a.embed_model != config.EMBED_MODELS[0])
            rows.append({"q": case["q"], "expect": case["expect"], "ok": ok, "why": why,
                         "embed_model": a.embed_model, "degradado": degradado,
                         "lang": a.lang, "abstained": a.abstained,
                         "tokens": a.usage.get("total_tokens", 0),
                         "ms": a.latency_ms, "citations": a.citations,
                         "text": a.text})
            print(("  OK   " if ok else "  FALLO") + f" [{case['expect']:7}] {case['q'][:58]}"
                  + ("" if ok else f"  <- {why}"))

    n = len(rows)
    passed = sum(r["ok"] for r in rows)
    no_llm = sum(1 for r in rows if r["tokens"] == 0)
    tok = sum(r["tokens"] for r in rows)
    lat = sorted(r["ms"] for r in rows)

    degradados = [r for r in rows if r.get("degradado")]
    fallos_degradados = [r for r in degradados if not r["ok"]]

    print("\n" + "=" * 72)
    if degradados:
        # Transparencia: la compuerta se calibra por modelo y el respaldo separa
        # peor. Reportarlo por separado evita atribuir al agente una degradacion
        # que en realidad viene de haber agotado la cuota del modelo primario.
        modelos = sorted({r["embed_model"] for r in degradados if r["embed_model"]})
        print(f"  MODO DEGRADADO      : {len(degradados)}/{n} casos usaron "
              f"embedding de respaldo ({', '.join(modelos)})")
        if fallos_degradados:
            print(f"                        {len(fallos_degradados)} de los fallos "
                  f"ocurrieron en ese modo")
    print(f"  aciertos            : {passed}/{n}  ({100*passed/n:.1f}%)")
    print(f"  sin invocar al LLM  : {no_llm}/{n}  ({100*no_llm/n:.1f}%)")
    print(f"  tokens totales      : {tok}   (media {tok/n:.0f}/consulta)")
    print(f"  latencia p50 / p95  : {lat[n//2]} ms / {lat[int(n*0.95)]} ms")
    print(f"  duracion            : {time.time()-t0:.1f}s")

    by = {}
    for r in rows:
        d = by.setdefault(r["expect"], [0, 0])
        d[0] += r["ok"]; d[1] += 1
    print("  por categoria       : " + "  ".join(f"{k}={v[0]}/{v[1]}" for k, v in sorted(by.items())))

    out = Path(__file__).parent / "results.json"
    out.write_text(json.dumps({
        "passed": passed, "total": n, "no_llm": no_llm, "tokens": tok,
        "p50_ms": lat[n//2], "p95_ms": lat[int(n*0.95)], "rows": rows,
    }, ensure_ascii=False, indent=2))
    print(f"  detalle             : eval/{out.name}")
    return 0 if passed == n else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
