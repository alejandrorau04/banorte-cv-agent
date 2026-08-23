"""Carga y validación del corpus. Falla al arrancar, nunca en producción."""
from __future__ import annotations
import re
import yaml
from app.config import CORPUS_PATH
from app.core.models import SECCIONES, Fact

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

        # `type` alimenta la etiqueta legible de la fuente. Un valor no previsto
        # cargaba sin error y reventaba al responder, como HTTP 500 y solo para
        # las preguntas que citaran ese hecho. Se valida aqui: falla al arrancar.
        tipo = it.get("type", "other")
        if tipo not in SECCIONES:
            raise CorpusError(
                f"{fid}: tipo '{tipo}' desconocido. Validos: {sorted(SECCIONES)}")

        facts.append(Fact(
            id=fid, type=tipo,
            text_es=es.strip(), text_en=en.strip(),
            tags=tuple(it.get("tags") or []),
            org=it.get("org"), title=it.get("title"),
            title_en=it.get("title_en") or it.get("title"),
            start=it.get("start"), end=it.get("end"),
            line_start=lineas.get(fid, (0, 0))[0],
            line_end=lineas.get(fid, (0, 0))[1],
        ))
    facts.append(_timeline(facts))
    facts.append(_duraciones(facts))
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


def _meses(inicio: str, fin: str | None) -> int | None:
    """Meses entre dos fechas `AAAA-MM`. `None` si el puesto sigue en curso."""
    if not fin:
        return None
    ai, mi = (int(x) for x in inicio.split("-"))
    af, mf = (int(x) for x in fin.split("-"))
    return (af - ai) * 12 + (mf - mi)


def _en_palabras(m: int) -> str:
    a, r = divmod(m, 12)
    if a and r:
        return f"{a} año{'s' if a > 1 else ''} y {r} mes{'es' if r > 1 else ''}"
    if a:
        return f"{a} año{'s' if a > 1 else ''}"
    return f"{r} mes{'es' if r > 1 else ''}"


def _en_palabras_en(m: int) -> str:
    a, r = divmod(m, 12)
    if a and r:
        return f"{a} year{'s' if a > 1 else ''} and {r} month{'s' if r > 1 else ''}"
    if a:
        return f"{a} year{'s' if a > 1 else ''}"
    return f"{r} month{'s' if r > 1 else ''}"


def _duraciones(facts: list[Fact]) -> Fact:
    """Duracion de cada puesto, CALCULADA de los metadatos.

    Motivo: el modelo hacia esta aritmetica mentalmente y se equivocaba. Ante
    «¿en que puesto estuvo mas tiempo?» respondia WESCO (33 meses) cuando la
    respuesta es SUMMA Woodbridge (42). Restar fechas es trabajo de codigo.

    Solo se calculan duraciones CERRADAS. La del puesto en curso crece cada mes:
    incluirla haria que el texto -- y por tanto su vector -- quedase obsoleto a
    diario. Se expresa como «en curso desde», que es exacto y estable.
    """
    roles = sorted((f for f in facts if f.title and f.start),
                   key=lambda f: f.start or "")
    cerrados = [(f, _meses(f.start, f.end)) for f in roles if f.end]
    curso = [f for f in roles if not f.end]

    es = "; ".join(f"{f.org}: {_en_palabras(m)}" for f, m in cerrados)
    en = "; ".join(f"{f.org}: {_en_palabras_en(m)}" for f, m in cerrados)
    if curso:
        es += "".join(f"; {f.org}: en curso desde {_fecha(f.start, 0)}" for f in curso)
        en += "".join(f"; {f.org}: ongoing since {_fecha(f.start, 1)}" for f in curso)

    largo = max(cerrados, key=lambda x: x[1])
    corto = min(cerrados, key=lambda x: x[1])

    return Fact(
        id="derived.duraciones",
        type="timeline",
        text_es=(
            f"Duración de cada puesto de Alejandro Rau Lázaro, calculada a partir de las "
            f"fechas del CV: {es}. El puesto más largo fue {largo[0].org} con "
            f"{_en_palabras(largo[1])}; el más corto, {corto[0].org} con "
            f"{_en_palabras(corto[1])}. Su trayectoria profesional comenzó en "
            f"{_fecha(roles[0].start, 0)}, con más de 10 años de experiencia acumulada."),
        text_en=(
            f"Duration of each of Alejandro Rau Lázaro's roles, computed from the CV dates: "
            f"{en}. The longest role was {largo[0].org} at {_en_palabras_en(largo[1])}; "
            f"the shortest, {corto[0].org} at {_en_palabras_en(corto[1])}. His professional "
            f"career began in {_fecha(roles[0].start, 1)}, with over 10 years of "
            f"accumulated experience."),
        tags=("duracion", "duraciones", "cuanto", "tiempo", "meses", "anos", "años",
              "mas-tiempo", "menos-tiempo", "permanencia", "antiguedad", "how-long",
              "duration", "longest", "shortest", "tenure", "years", "time"),
    )


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
