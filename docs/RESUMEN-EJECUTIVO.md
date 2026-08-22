# Resumen ejecutivo

**Agente de CV conversacional** — Reto IA Banorte, Alejandro Rau Lázaro, 22 de agosto de 2026.

---

## Qué es

Un servicio que responde preguntas sobre una trayectoria profesional, en español e
inglés, expuesto como endpoint público compatible con la especificación abierta
**Open Responses `2026-04-24`** y desplegado en **Azure Container Apps**.

## El problema real

Un agente de CV tiene un modo de fallo grave y específico: **inventar experiencia
profesional que la persona no tiene**. Una fecha, una empresa o una tecnología
fabricadas ante un reclutador no son un error de software, son un problema de veracidad.

Instruir al modelo con «no inventes» es una petición, no una garantía. Este proyecto
implementa cuatro controles que **no dependen de la buena voluntad del modelo**.

## Cómo se resuelve

| Control | Mecanismo |
|---|---|
| **Grounding cerrado** | El prompt contiene únicamente hechos del corpus versionado |
| **Compuerta de evidencia** | Sin evidencia suficiente **no se invoca al modelo**. Umbral 0.62, calibrado con datos |
| **Verificación de citas** | Toda cita se contrasta contra lo recuperado; las inventadas se eliminan |
| **Política de privacidad** | Los datos de contacto no existen en el corpus: no puede revelarlos |

## Resultados medidos

| Métrica | Valor |
|---|---|
| Golden set (32 casos, 12 de ellos sobre lo que **no** debe responder) | **32/32** |
| Consistencia ante 26 formulaciones distintas | **26/26** |
| Entradas hostiles y malformadas | **28/28 sin errores 5xx** |
| Carga, concurrencia 10 | **30/30 correctas** |
| Pruebas automatizadas | **65**, sin red ni credenciales |
| Latencia p50 / p95 | 1,2 s / 13,3 s |
| Consultas que **no** invocan al modelo | 25 % |
| Reducción de consumo de tokens | **−54 %** |

## Decisiones que definen la solución

**Sin base vectorial.** 94 vectores no justifican desplegar Qdrant ni pgvector: añadirían
infraestructura, latencia y un punto de fallo sin ganancia medible. La recuperación vive
tras una interfaz sustituible.

**Sin datos de contacto en el corpus.** El endpoint es público y el repositorio abierto:
el agente no puede revelar lo que no tiene. Verificado automáticamente en cada build.

**El coste y la veracidad son el mismo mecanismo.** Abstenerse sin invocar al modelo
elimina simultáneamente el riesgo de invención y el gasto. No son dos optimizaciones que
compiten: es una decisión con doble beneficio.

**Las preguntas estructuradas se responden con datos estructurados.** El orden
cronológico lo calcula el código a partir de los metadatos, no el modelo.

## Coste operativo

Modelo y embeddings en nivel gratuito. Consumo medio **416 tokens por consulta**, y cero
en el 25 % de los casos. La infraestructura es un único contenedor de 0,5 vCPU.

## Trazabilidad y seguridad

Cada respuesta expone qué hechos se recuperaron, con qué similitud y cuáles se citaron.
Autenticación por token, secretos gestionados por la plataforma —nunca en la imagen ni en
el repositorio—, contenedor sin privilegios y modelo de amenazas STRIDE documentado con
sus riesgos aceptados.

## Qué haría falta para producción bancaria

Explicitado porque un prototipo honesto reconoce su distancia con producción:

- Proveedor de LLM con **aislamiento contractual de datos** (el nivel gratuito puede usar
  los datos para mejora del producto). **Requisito bloqueante.**
- OAuth 2.0 / Entra ID en lugar de token estático.
- *Rate limiting* por cliente en la puerta de entrada.
- Registro de contenedores privado interno.
- Pruebas de carga sostenida y observabilidad centralizada.

## Enlaces

| Recurso | Dónde |
|---|---|
| Repositorio | `github.com/alejandrorau04/banorte-cv-agent` |
| Endpoint | Azure Container Apps, `centralus` |
| Arquitectura y diagramas C4 | [ARQUITECTURA.md](ARQUITECTURA.md) |
| Pipeline RAG en detalle | [RAG.md](RAG.md) |
| Pruebas y evidencia | [PLAN-DE-PRUEBAS.md](PLAN-DE-PRUEBAS.md) |
| Decisiones técnicas | [8 ADRs](adr/) |
