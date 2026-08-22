# Backlog de valor agregado

Ideas registradas durante el diseño. **No forman parte de la entrega del reto.**
Se documentan porque demuestran visión de producto y porque la arquitectura
actual ya las contempla sin necesidad de reescribirse.

## 1. Interacción por voz (bidireccional)

Preguntar por voz y recibir respuesta hablada.

- **Entrada:** Web Speech API en el navegador (coste cero) o Speech-to-Text gestionado.
- **Salida:** Text-to-Speech, con síntesis por fragmentos aprovechando el streaming SSE.
- **Encaje arquitectónico:** el núcleo del agente es agnóstico del transporte, así que
  la voz es una capa de presentación adicional, no un cambio de diseño.
- **Nota sectorial:** en banca la voz abre un frente de biometría y consentimiento;
  merece su propio modelo de amenazas.

## 2. Generador de CV conversacional

Tras responder preguntas sobre el perfil, ofrecer al usuario construir su propio CV
mediante entrevista guiada por el agente.

- Invierte el flujo: de *consultar* un corpus a *construir* uno.
- Reutiliza el mismo esquema de corpus como formato de salida.
- Exportación a PDF y a JSON estructurado.
- **Encaje arquitectónico:** encaja como `tool` del contrato Open Responses, que ya
  define `tools` y `tool_choice`. No requiere endpoint nuevo.

## 3. Otras líneas identificadas

- **Multi-perfil:** el mismo servicio sirviendo corpus de varias personas (tenancy).
- **`/responses/compact`:** compactación de historial, ya definida en la spec.
- **Panel de observabilidad:** consultas, latencia, tasa de abstención y coste por token.
- **Evaluación continua:** el golden set corriendo en CI en cada cambio del corpus.
