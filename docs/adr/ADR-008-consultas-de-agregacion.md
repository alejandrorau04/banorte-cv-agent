# ADR-008 — Consultas de agregación resueltas con metadatos, no con recuperación

- **Estado:** Aceptado
- **Fecha:** 2026-08-22

## Contexto

Una sesión de QA adversarial contra el endpoint desplegado, simulando las preguntas de
un reclutador, reveló **dos fallos factuales**:

> **P:** «¿Cuál fue su último puesto antes de GlobalConnect?»
> **R:** «Los hechos no mencionan ningún puesto entre su salida de SUMMA en julio de 2018
> y su ingreso a GlobalConnect en mayo de 2025.»

Falso: fue Alldora Latinoamérica. **El agente afirmó una ausencia inexistente**, que es
el modo de fallo más grave posible en un agente de CV.

> **P:** «Lista todas las empresas en orden cronológico»
> **R:** orden incorrecto, y mezclaba clientes (Vinte, Grupo Salinas) con empleadores.

## Causa raíz

Ambos fallos comparten origen: **las preguntas de agregación, ordenación o secuencia
requieren el corpus completo, y la recuperación top-k entrega solo los k hechos más
similares.**

Para «¿qué puesto tuvo antes de X?», los hechos semánticamente más próximos son los de X
y los del puesto más antiguo, no necesariamente el inmediatamente anterior. El modelo
recibe un subconjunto y concluye —correctamente, dada su información— que no hay nada más.

Es una limitación estructural de RAG, no un defecto del modelo ni del prompt. Subir `k`
no la resuelve: solo desplaza el umbral donde reaparece.

## Decisión

**Las preguntas estructuradas se responden con datos estructurados; la recuperación
semántica queda para las preguntas semánticas.**

1. Al cargar el corpus se **deriva por código** un hecho `derived.timeline`: la
   trayectoria completa ordenada por el campo `start`, construida a partir de `title`,
   `org`, `start` y `end`. Incluye el total de puestos y una aclaración explícita de
   qué entidades fueron clientes y no empleadores.
2. Un patrón detecta consultas de agregación, orden o secuencia («lista», «cronológico»,
   «antes de», «anterior», «cuántas empresas», «list all», «previous job», «timeline»…).
3. Ante esas consultas se inyectan la línea de tiempo y **todos** los hechos de puesto,
   por delante del resultado de la recuperación.

## Por qué derivarla y no escribirla en el corpus

Un texto escrito a mano puede **contradecir** al resto del corpus si se edita una fecha
y se olvida actualizarlo. Al derivarse de los mismos campos, el orden es correcto por
construcción y cualquier cambio de fecha se propaga solo. **Una sola fuente de verdad.**

Además, el orden lo calcula `sorted()`, no el modelo: un LLM ordenando cronológicamente
ocho fechas es un riesgo innecesario cuando el dato ya está estructurado.

## Consecuencias

- Las consultas de agregación consumen ~1.180 tokens frente a ~566 de una consulta
  normal. Solo esas: el resto no cambia. Se acepta el coste a cambio de eliminar un
  error factual.
- El patrón puede activarse de más en alguna consulta. El efecto de un falso positivo es
  únicamente contexto extra, nunca una respuesta incorrecta: es un fallo benigno.
- Cinco casos nuevos en el golden set cubren esta clase de pregunta, incluidos dos con
  `forbid_text` que verifican que no reaparezca la afirmación de ausencia ni la mezcla
  de clientes con empleadores.

## Lección general

Un sistema RAG con recuperación por similitud **no responde bien preguntas sobre el
conjunto**: cuántos, en qué orden, cuál fue el anterior, cuál falta. Cuando los datos
tienen estructura, conviene explotarla en lugar de esperar que los embeddings la
reconstruyan. Es una limitación que conviene conocer antes de que la encuentre un
evaluador.
