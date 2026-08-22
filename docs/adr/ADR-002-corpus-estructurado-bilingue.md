# ADR-002 — El CV como corpus estructurado bilingüe, no como documento

- **Estado:** Aceptado
- **Fecha:** 2026-08-22

## Contexto

El agente debe responder sobre la trayectoria profesional en español y en inglés.
El material de origen son dos PDF (español e inglés) que, al momento de esta decisión,
**no coincidían**: la versión en inglés conservaba fechas de empleo con solapamientos
que la versión en español ya había corregido.

## Decisión

1. **El CV en español es la única fuente de verdad.** El texto en inglés se deriva de él.
   Ante cualquier discrepancia, prevalece `es`.
2. El CV **no** se indexa como documento. Se transforma en `data/corpus.yaml`: una lista
   de hechos atómicos, cada uno con `id` estable, metadatos (`type`, `org`, `start`,
   `end`, `tags`) y texto paralelo en `es` y `en`.
3. La traducción se hace **en tiempo de construcción, revisada por el titular del CV**,
   nunca en tiempo de ejecución.

## Alternativas descartadas

**Trocear el PDF y traducir en runtime.** Descartada por tres motivos:

- **Alucinación.** Traducir con el LLM en cada petición equivale a reescribir hechos en
  cada respuesta. Fechas, cifras y nombres propios quedan expuestos a deriva.
- **Trazabilidad.** Una cita debe poder verificarse contra un texto que existe en el
  repositorio. Si el texto se genera en runtime, la cita no es verificable.
- **Latencia y coste.** Añade una llamada al modelo por petición sin aportar valor.

**Un corpus por idioma, independientes.** Descartada: duplica la fuente de verdad y
reintroduce exactamente el problema de divergencia que originó este ADR.

## Consecuencias

- Cada afirmación del agente es rastreable hasta un `id` versionado en git. Un cambio
  en un hecho aparece como diff revisable.
- Los `id` son **contrato interno**: renombrarlos invalida las citas y el golden set.
- Los metadatos permiten filtrado determinista (por ejemplo, consultas por rango de
  fechas) sin depender del modelo.
- Obliga a mantener `es` y `en` sincronizados. Se mitiga con validación automática que
  verifica que todo hecho tenga ambos idiomas.

## Estado del corpus

46 hechos: 3 de perfil, 28 de experiencia, 10 de habilidades, 3 de formación y 2 de logros.
Volumen total ≈ 3.700 tokens (≈ 1.860 por idioma), dato base para el análisis de
consumo de tokens del ADR-005.
