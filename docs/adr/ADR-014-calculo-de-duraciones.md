# ADR-014 — Las duraciones las calcula el código, no el modelo

- **Estado:** Aceptado
- **Fecha:** 2026-08-23

## Contexto

Auditoría del enunciado del reto contra lo entregado. El enunciado enumera qué se evalúa
sobre la integración: «cómo integras modelos, contexto, **herramientas** o fuentes de
información». Era el único elemento de esa lista sin cubrir.

Antes de implementar nada se comprobó si existía un problema real que una herramienta
resolviera. Lo había, y era un **error factual en producción**:

> **P:** ¿Cuál fue el puesto en el que más tiempo estuvo?
> **R:** WESCO Distribution de México, de octubre de 2020 a julio de 2023.

Incorrecto. Las duraciones reales, calculadas de las fechas del propio corpus:

| Puesto | Meses |
|---|---|
| **SUMMA Woodbridge** | **42** |
| WESCO | 33 |
| Johnson Health | 17 |

SUMMA fue nueve meses más largo. El modelo hizo la aritmética mentalmente y se equivocó.

Dos síntomas más de lo mismo: «¿Cuánto tiempo estuvo en WESCO?» devolvía las fechas en
lugar de la duración, y «¿Cuánto lleva en GlobalConnect?» respondía «desde mayo de 2025,
por lo tanto lleva desde ese mes» — una no-respuesta.

## Decisión

**Un hecho derivado, `derived.duraciones`, calculado al cargar el corpus a partir de los
campos `start` y `end`.** Incluye la duración de cada puesto, el más largo y el más corto.
Un patrón enruta las preguntas de duración para que ese hecho llegue siempre al prompt.

Es el mismo principio del ADR-008: **las preguntas estructuradas se responden con datos
estructurados.** Restar fechas es trabajo de código; un modelo de lenguaje haciéndolo de
memoria es un riesgo innecesario cuando el dato ya está en el corpus.

### Solo se calculan duraciones cerradas

La del puesto en curso crece cada mes. Incluirla haría que el texto —y por tanto su
vector— quedaran obsoletos a diario, y obligaría a reindexar para mantener la exactitud.
Se expresa como «en curso desde mayo de 2025», que es **exacto y estable**.

## Sobre «herramientas»

El enunciado admite integrar «modelos, contexto, herramientas **o** fuentes de
información» — es una lista de opciones, no de requisitos.

Se implementa el cálculo como **derivación determinista**, no como *tool calling* decidido
por el modelo. Con ocho puestos, dejar que el modelo decida cuándo invocar una función
añade un viaje de ida y vuelta, un punto de fallo y latencia, para resolver algo que puede
estar siempre disponible y no puede fallar.

El contrato Open Responses acepta `tools` y `tool_choice`, de modo que soportar *tool
calling* sería una extensión natural si un caso lo justificara. Hoy no lo justifica:
**la herramienta correcta es la que no hace falta invocar.**

## Consecuencias

- El corpus pasa de 61 a 62 hechos y el índice de 122 a 124 vectores.
- Cuatro casos nuevos en el golden set, uno de ellos con `forbid_text` para que la
  respuesta errónea original no pueda reaparecer.
- Cambiar una fecha del CV actualiza las duraciones solo, igual que la línea de tiempo.
- Las preguntas de duración consumen algo más de contexto, por inyectarse el hecho
  derivado. Es el mismo intercambio del ADR-008: contexto extra a cambio de exactitud.

## Lección

El error llevaba en producción desde el principio y **ninguna de las cinco capas de prueba
lo detectó**: ni el golden set, ni la consistencia, ni la robustez, ni la carga, ni la
revisión de código. Apareció al auditar el enunciado punto por punto y preguntarse si una
capacidad ausente resolvía algo real.

**Buscar el problema antes de construir la solución** es lo que convirtió una casilla por
marcar en una corrección con valor.
