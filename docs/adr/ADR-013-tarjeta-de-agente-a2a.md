# ADR-013 — Tarjeta de agente A2A para descubrimiento

- **Estado:** Aceptado
- **Fecha:** 2026-08-23

## Contexto

El formulario de alta de agentes de la plataforma del reto ofrece un campo
**«Importar desde tarjeta de agente»**, con la indicación:

> «Obtiene `/.well-known/agent-card.json` (tarjeta de agente A2A) y completa el
> formulario, incluida la URL de Open Responses.»

El servicio no la exponía, de modo que ese botón fallaba y el alta debía hacerse a mano.

## A2A y Open Responses resuelven cosas distintas

No compiten, se complementan:

| | **A2A** | **Open Responses** |
|---|---|---|
| Responde a | *¿Quién eres y qué sabes hacer?* | *¿Qué contestas a esta pregunta?* |
| Cuándo se usa | Una vez, antes de integrarse | En cada conversación |
| Formato | Un JSON estático descubrible | Un endpoint conversacional |

Un cliente lee la tarjeta **antes** de enviar nada. Es descubrimiento; el otro es
conversación.

## Decisión

Servir `/.well-known/agent-card.json` conforme a la especificación A2A.

**Sin autenticación**, deliberadamente: una tarjeta que exige credenciales para ser
leída no puede cumplir su función —el cliente aún no las tiene— y no revela nada que el
repositorio público no diga ya. La ausencia de datos de contacto se verifica con un test,
igual que en el corpus.

**Superconjunto de versiones.** Los campos obligatorios difieren entre la v0.3.0 (diez
campos) y la v1.0.0 (que añade `supportedInterfaces` y otros). Como un cliente ignora los
campos que no conoce, emitir ambos conjuntos cuesta unas líneas y evita apostar por una
versión —el mismo problema que ya tuvimos con Open Responses, donde la especificación
existía pero nadie decía cuál.

**Tres habilidades declaradas** con ejemplos reales: trayectoria, competencias y
situación profesional. Los ejemplos importan: un enrutador basado en LLM decide con ellos
si este agente sirve para una consulta.

## Consecuencias

- El alta en la plataforma pasa de rellenar ocho campos a pulsar un botón.
- El agente es descubrible por cualquier cliente A2A, no solo por la plataforma del reto.
- La tarjeta declara `streaming: true`, coherente con el soporte SSE de Open Responses.
- Hay que mantenerla al día si cambian la URL, la versión o las capacidades. Un test
  verifica los campos obligatorios y la ausencia de datos personales.

## Alternativa descartada

**No servirla.** El reto no la pide y el alta manual funciona. Se descarta porque la
propia interfaz de la plataforma la ofrece: un hueco visible en el flujo que ellos
diseñaron, resoluble en unas líneas.
