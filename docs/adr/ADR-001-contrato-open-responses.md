# ADR-001 — Adopción de la especificación Open Responses `2026-04-24`

- **Estado:** Aceptado
- **Fecha:** 2026-08-22

## Contexto

El enunciado del reto exige registrar «un endpoint público de tu agente compatible con
Open Responses», sin precisar versión, campos obligatorios ni semántica de streaming.

Se consultó al agente Guía oficial del reto (2026-08-22). Su respuesta textual fue que
«la información disponible del reto no especifica esos detalles de compatibilidad», y
recomendó confirmarlo en la documentación técnica o el canal oficial. Es decir: el canal
de soporte del reto no dispone del contrato.

Ante una ambigüedad bloqueante se optó por investigación primaria en lugar de suposición.

## Hallazgo

«Open Responses» no es una referencia informal a la API de OpenAI: es una **especificación
abierta, gobernada y versionada** (https://www.openresponses.org), licencia Apache-2.0,
iniciada por OpenAI y respaldada por NVIDIA, AWS, Red Hat, Databricks, Hugging Face,
Vercel, vLLM, Ollama, OpenRouter, LM Studio y Llama Stack.

Incluye OpenAPI normativo y **suite oficial de tests de aceptación** (17 tests: 10 vía
navegador, 7 vía CLI para WebSocket).

## Decisión

1. Adoptar la versión **`2026-04-24`**, anclada en `docs/contract/openapi.json`.
   Se versiona en el repositorio para que la conformidad sea reproducible y auditable.
2. Los modelos de datos se **derivan del esquema**, no se escriben a mano.
3. La conformidad se **demuestra ejecutando la suite oficial**, no se afirma.
4. Alcance priorizado por el plazo de entrega: `POST /responses` no-streaming primero,
   luego SSE. Quedan fuera WebSocket, `/responses/compact` y tool calling.

## Consecuencias

### El contrato es asimétrico y esto condiciona la implementación

- **Request — `CreateResponseBody`: `required: []`.** Ningún campo es obligatorio, ni
  siquiera `model` o `input`. El servidor **debe** aplicar valores por defecto en lugar de
  rechazar. Una validación estricta por intuición rechazaría peticiones legítimas del
  cliente de la plataforma y el agente aparecería como no funcional.
- **Respuesta — `ResponseResource`: 31 campos obligatorios.** La implementación intuitiva
  (`{id, status, output}`) **no es conforme**. Deben emitirse los 31, con `object` fijo
  en `"response"` y valores explícitos (incluido `null`) para los anulables.

Se aplica la Ley de Postel tal como la especificación la impone: liberal en la entrada,
conservador en la salida.

### Streaming

El esquema define **24 tipos de evento SSE**. La documentación narrativa del sitio solo
describe un subconjunto; la fuente de verdad es el OpenAPI.

## Supuestos y su verificación

Se documentaron como supuestos no confirmables y se mitigaron por diseño. El formulario
de alta de agentes de la plataforma (**Parley**) confirmó posteriormente dos de ellos.

| # | Supuesto | Mitigación aplicada | Estado |
|---|---|---|---|
| 1 | La plataforma consume la versión `2026-04-24` | Emitir los 31 campos obligatorios: un cliente anclado a una versión previa ignora los campos desconocidos sin romperse | Sin confirmar; mitigado |
| 2 | Autenticación por `Authorization: Bearer <token>` | Aceptar además `x-api-key`, `api-key` y token sin prefijo | **Confirmado.** El formulario indica: «Se envía como `Authorization: Bearer …` y se almacena cifrada» |
| 3 | El valor de `model` puede llegar ausente o arbitrario | Valor por defecto y eco del recibido | **Confirmado.** El campo *Modelo* está marcado como opcional |
| 4 | El multi-turno llega como historial completo en `input` | Tomar el último mensaje de usuario del array; soportar también `previous_response_id` | **Confirmado.** El selector *Estado de la conversación* ofrece «Reproducir transcripción (sin estado)» —opción por defecto y la usada— frente a «previous_response_id (el agente guarda el estado)» |

Consecuencia de la confirmación del supuesto 4: **el servicio es deliberadamente sin
estado.** No persiste conversaciones, de modo que escala horizontalmente sin
sincronización. La alternativa habría exigido almacenamiento, gestión del ciclo de vida
de esos datos y, en un contexto bancario, una política de retención.

### Nota sobre `instructions`

El formulario permite enviar instrucciones de sistema en cada petición. El servidor las
honra **subordinadas** a las reglas de grounding: se añaden después de ellas, acotadas en
longitud y con la indicación expresa de que las reglas absolutas prevalecen. Verificado
contra producción: una instrucción de tono se aplica; una que pide afirmar experiencia
inexistente se ignora.

### Capacidades no declaradas

Los interruptores de *entrada de imágenes* y *entrada de archivos* se dejan desactivados
porque **no están implementados**. Declarar una capacidad ausente produciría un fallo
silencioso ante el evaluador y contradiría el principio que sostiene todo el diseño: no
afirmar lo que no se puede respaldar.

## Fuentes

- https://www.openresponses.org/specification
- https://github.com/openresponses/openresponses (Apache-2.0)
- `docs/contract/openapi.json` — OpenAPI 3.1.0, `info.version = 2026-04-24`
