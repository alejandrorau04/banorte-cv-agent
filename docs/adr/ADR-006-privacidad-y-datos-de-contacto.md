# ADR-006 — Exclusión de datos de contacto del corpus

- **Estado:** Aceptado
- **Fecha:** 2026-08-22

## Contexto

El CV contiene datos personales de contacto: número telefónico y correo electrónico.
La solución expone un **endpoint público en internet** y publica el corpus en un
**repositorio abierto de GitHub**.

Incluirlos implicaría: (a) un agente que entrega el teléfono del titular a cualquier
solicitante anónimo, y (b) esos datos indexados públicamente en GitHub, susceptibles
de recolección automatizada.

## Decisión

`data/corpus.yaml` **no contiene** teléfono ni correo electrónico. Ante una pregunta de
contacto, el agente responde que por privacidad no comparte datos de contacto por este
canal y remite al CV formal o al proceso de selección.

La ausencia de PII se verifica con una comprobación automática sobre el corpus, para que
no pueda reintroducirse por descuido en una edición futura.

## Justificación

- **Minimización de datos.** Solo se procesa el dato necesario para la finalidad. Un
  agente que describe una trayectoria profesional no necesita datos de contacto.
- Los datos de contacto **no aportan** a los criterios evaluados por el reto.
- El proveedor de LLM opera en nivel gratuito, donde los datos pueden emplearse para
  mejora del producto. Todo lo que entra al prompt debe asumirse como no confidencial.

## Consecuencias

- El agente **no puede** responder a «¿cuál es su teléfono?». Es intencional y se
  demuestra como decisión de diseño, no como carencia.
- Se documenta como caso de prueba explícito en el golden set: la respuesta correcta a
  una pregunta de contacto es la negativa cortés, no el dato.
- En un despliegue productivo bancario, esta decisión escalaría a clasificación formal
  de datos y a un proveedor con aislamiento contractual de la información.
