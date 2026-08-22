"""Consistencia ante distintas formas de preguntar lo mismo.

Recomendado explicitamente por el agente Guia del reto (2026-08-22):
«pruebas de consistencia ante distintas formas de preguntar».

Que se mide: varias formulaciones de una MISMA intencion deben producir
respuestas equivalentes en el hecho central. No se compara el texto (el modelo
redacta distinto cada vez), sino:

  1. que se recupere y cite el mismo hecho clave,
  2. que aparezcan los datos esenciales (empresa, fecha, dato concreto),
  3. que ninguna variante se abstenga si las demas responden.

Una variante que falla revela fragilidad de la recuperacion frente a erratas,
mayusculas, registro coloquial o mezcla de idiomas.
"""
from __future__ import annotations
import asyncio, json, sys, unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx
from app.adapters.base import ProviderError
from app.adapters.gemini import GeminiEmbedder, GeminiLLM
from app.core.agent import CVAgent
from app.core.corpus import load_facts
from app.core.retrieval import HybridRetriever

def _idioma_esperado(q: str) -> str:
    """Idioma en que DEBE responderse, anotado explicitamente por formulacion."""
    return "en" if q in _EN else "es"


# Formulaciones en ingles: la respuesta debe venir en ingles.
_EN = {"Where does he work now?", "current employer?", "What is his AI experience?",
       "What certifications does he hold?", "What was his first job?",
       "Where did he study?"}

# (intencion, [formulaciones], hecho que debe citarse, terminos esperados)
GRUPOS = [
    ("empleo actual",
     ["¿Dónde trabaja actualmente Alejandro?",
      "donde travaja aorita??",
      "EN QUE EMPRESA ESTA AHORA",
      "cual es su chamba actual",
      "Where does he work now?",
      "current employer?",
      "dime su trabajo actual porfa"],
     "exp.globalconnect.role", ["globalconnect"]),

    ("experiencia en IA",
     ["¿Qué experiencia tiene con inteligencia artificial?",
      "q sabe de ia",
      "hábleme de su experiencia en IA",
      "What is his AI experience?",
      "ha trabajado con IA?",
      "cuentame sobre inteligencia artificial en su carrera"],
     None, ["retell", "twilio", "openai", "conversacional", "conversational", "agentes", "agents"]),

    ("certificaciones",
     ["¿Qué certificaciones tiene?",
      "certificaciones?",
      "esta certificado en algo",
      "What certifications does he hold?",
      "tiene algun certificado"],
     "education.certifications", ["ccna", "scrum"]),

    ("primer empleo",
     ["¿Cuál fue su primer empleo?",
      "donde empezo a trabajar",
      "What was his first job?",
      "su primer trabajo cual fue"],
     None, ["summa", "2015"]),

    ("formación",
     ["¿Dónde estudió?",
      "que estudio",
      "Where did he study?",
      "cual es su carrera universitaria"],
     "education.degree", ["cuautitlán", "cuautitlan", "sistemas"]),
]


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s.lower())
    return "".join(c for c in s if not unicodedata.combining(c))


async def main() -> int:
    facts = load_facts()
    fallos, total = [], 0

    async with httpx.AsyncClient() as c:
        agent = CVAgent(HybridRetriever.from_index(facts, embedder=GeminiEmbedder(c)),
                        GeminiLLM(c))
        for intencion, variantes, cita, terminos in GRUPOS:
            print(f"\n=== {intencion} ({len(variantes)} formulaciones) ===")
            for q in variantes:
                total += 1
                try:
                    a = await agent.answer(q)
                except ProviderError as e:
                    fallos.append((intencion, q, f"error proveedor: {e}"))
                    print(f"  ERROR  {q[:52]:54} {e}")
                    continue

                problemas = []
                if a.abstained:
                    problemas.append("se abstuvo")
                if cita and cita not in a.citations:
                    problemas.append(f"no cita {cita}")
                txt = _norm(a.text)
                if terminos and not any(_norm(t) in txt for t in terminos):
                    problemas.append(f"no menciona ninguno de {terminos}")
                esperado = _idioma_esperado(q)
                if a.lang != esperado:
                    problemas.append(f"idioma {a.lang}, esperado {esperado}")

                if problemas:
                    fallos.append((intencion, q, "; ".join(problemas)))
                print(f"  {'FALLO' if problemas else '  ok '} [{a.lang}] {q[:50]:52}"
                      + ("  <- " + "; ".join(problemas) if problemas else ""))

    print("\n" + "=" * 74)
    print(f"  formulaciones probadas : {total}")
    print(f"  consistentes           : {total - len(fallos)}/{total} "
          f"({100*(total-len(fallos))/total:.1f}%)")
    if fallos:
        print("  INCONSISTENCIAS:")
        for i, q, p in fallos:
            print(f"    - [{i}] {q}  ->  {p}")
    Path(__file__).parent.joinpath("consistencia.json").write_text(json.dumps(
        {"total": total, "fallos": [{"intencion": i, "q": q, "problema": p}
                                    for i, q, p in fallos]}, ensure_ascii=False, indent=2))
    return 1 if fallos else 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
