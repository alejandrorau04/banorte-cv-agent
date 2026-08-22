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


def _lineas_por_id(texto: str) -> dict[str, tuple[int, int]]:
    """Localiza en que lineas del YAML vive cada hecho.

    Permite enlazar cada cita a las lineas exactas del corpus en el repositorio
    publico: la fuente deja de ser un identificador y pasa a ser un enlace que
    cualquiera puede abrir y verificar.
    """
    lineas = texto.splitlines()
    marcas: list[tuple[str, int]] = []
    for n, l in enumerate(lineas, start=1):
        s = l.strip()
        if s.startswith("- id:"):
            marcas.append((s.split("- id:", 1)[1].strip(), n))
    out: dict[str, tuple[int, int]] = {}
    for i, (fid, ini) in enumerate(marcas):
        fin = marcas[i + 1][1] - 1 if i + 1 < len(marcas) else len(lineas)
        while fin > ini and not lineas[fin - 1].strip():
            fin -= 1
        out[fid] = (ini, fin)
    return out


def load_facts() -> list[Fact]:
    crudo = CORPUS_PATH.read_text(encoding="utf-8")
    lineas = _lineas_por_id(crudo)
    raw = yaml.safe_load(crudo)
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
            org=it.get("org"), title=it.get("title"),
            title_en=it.get("title_en") or it.get("title"),
            start=it.get("start"), end=it.get("end"),
            line_start=lineas.get(fid, (0, 0))[0],
            line_end=lineas.get(fid, (0, 0))[1],
        ))
    facts.append(_timeline(facts))
    return facts


_MES = {
    "01": ("enero", "January"), "02": ("febrero", "February"),
    "03": ("marzo", "March"), "04": ("abril", "April"),
    "05": ("mayo", "May"), "06": ("junio", "June"),
    "07": ("julio", "July"), "08": ("agosto", "August"),
    "09": ("septiembre", "September"), "10": ("octubre", "October"),
    "11": ("noviembre", "November"), "12": ("diciembre", "December"),
}


def _fecha(v: str | None, i: int) -> str:
    if not v:
        return ("la actualidad", "the present")[i]
    y, m = v.split("-")
    return f"{_MES[m][i]} de {y}" if i == 0 else f"{_MES[m][i]} {y}"


def _timeline(facts: list[Fact]) -> Fact:
    """Linea de tiempo DERIVADA de los metadatos, no redactada a mano.

    Las preguntas de agregacion y ordenacion ("lista todas las empresas",
    "cual fue su puesto anterior") no pueden responderse con recuperacion
    top-k: necesitan el corpus completo. Se resuelven con los campos
    estructurados `start`, `end`, `org` y `title`, que ya existen.

    Al derivarse por codigo, el orden es correcto por construccion y no puede
    contradecir al resto del corpus: si cambia una fecha, cambia la linea de
    tiempo. Ver ADR-008.
    """
    roles = sorted((f for f in facts if f.title and f.start),
                   key=lambda f: f.start or "")
    es = "; ".join(
        f"{f.title} en {f.org} de {_fecha(f.start, 0)} a {_fecha(f.end, 0)}"
        for f in roles)
    en = "; ".join(
        f"{f.title_en} at {f.org} from {_fecha(f.start, 1)} to {_fecha(f.end, 1)}"
        for f in roles)
    return Fact(
        id="derived.timeline", type="timeline",
        text_es=("Trayectoria profesional completa de Alejandro Rau Lázaro en orden "
                 f"cronológico, del puesto más antiguo al más reciente: {es}. "
                 f"Son {len(roles)} puestos en total, sin solapamientos. "
                 "Vinte y Grupo Salinas fueron clientes de Alldora y Webmaps "
                 "respectivamente, no empleadores."),
        text_en=("Complete professional timeline of Alejandro Rau Lázaro in "
                 f"chronological order, from earliest to most recent role: {en}. "
                 f"That is {len(roles)} roles in total, with no overlaps. "
                 "Vinte and Grupo Salinas were clients of Alldora and Webmaps "
                 "respectively, not employers."),
        tags=("cronologia", "timeline", "empresas", "companies", "orden", "historial",
              "trayectoria", "anterior", "previous", "carrera", "career"),
    )
