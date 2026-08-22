"""Carga y validación del corpus. Falla al arrancar, nunca en producción."""
from __future__ import annotations
import re
import yaml
from app.config import CORPUS_PATH
from app.core.models import Fact

# El corpus no debe contener datos de contacto (ADR-006). Se verifica al cargar
# para que no puedan reintroducirse por descuido en una edición futura.
_PII = re.compile(r"[\w.+-]+@[\w-]+\.\w+|\b\d{2}\s?\d{4}\s?\d{4}\b|\b77714\b")


class CorpusError(RuntimeError):
    pass


def load_facts() -> list[Fact]:
    raw = yaml.safe_load(CORPUS_PATH.read_text(encoding="utf-8"))
    items = raw.get("facts") or []
    if not items:
        raise CorpusError("corpus vacío")

    facts: list[Fact] = []
    seen: set[str] = set()
    for it in items:
        fid = it.get("id")
        if not fid:
            raise CorpusError(f"hecho sin id: {it}")
        if fid in seen:
            raise CorpusError(f"id duplicado: {fid}")
        seen.add(fid)

        es, en = it.get("es"), it.get("en")
        if not es or not en:
            raise CorpusError(f"{fid}: falta texto es o en")
        if _PII.search(es) or _PII.search(en):
            raise CorpusError(f"{fid}: contiene datos de contacto (ADR-006)")

        facts.append(Fact(
            id=fid, type=it.get("type", "other"),
            text_es=es.strip(), text_en=en.strip(),
            tags=tuple(it.get("tags") or []),
            org=it.get("org"), start=it.get("start"), end=it.get("end"),
        ))
    return facts
