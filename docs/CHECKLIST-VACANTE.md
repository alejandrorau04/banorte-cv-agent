# Checklist: vacante ↔ solución entregada

Correspondencia entre lo que pide la vacante **Desarrollador Full Stack con enfoque en IA**
(Dirección de IA e Innovación, Banorte) y lo implementado en este repositorio.

**Se marca también lo NO cubierto.** Un checklist todo en verde no es creíble, y conocer
los huecos vale más que ocultarlos.

Leyenda: ✅ cubierto y demostrable · 🟡 parcial · ⬜ no cubierto

---

## 1. Entregables del reto

| # | Requisito | Estado | Evidencia |
|---|---|---|---|
| 1 | Agente de CV desplegado en endpoint público | ✅ | Azure Container Apps, `/health` público |
| 2 | Compatible con **Open Responses** | ✅ | Spec `2026-04-24` anclada; 31/31 campos verificados en CI |
| 3 | Registrado y funcionando en la plataforma | ✅ | Alta en Parley y conversación probada |
| 4 | Repositorio público en GitHub | ✅ | `alejandrorau04/banorte-cv-agent` |
| 5 | Conversa sobre perfil, experiencia, habilidades y proyectos | ✅ | 61 hechos; golden set 32/32 |
| 6 | Demostración con decisiones técnicas explicadas | 🟡 | Guion en `docs/DEMO.md`; presentación pendiente |
| 7 | Verificar respuesta clara, coherente y confiable | ✅ | 5 niveles de prueba, 102 tests |

---

## 2. Requisitos técnicos de la vacante

### Backend e IA

| Requisito | Estado | Evidencia |
|---|---|---|
| **Python (FastAPI)** | ✅ | Todo el servicio |
| APIs REST productivas | ✅ | `POST /v1/responses`, `/health` |
| Integración con **APIs de LLMs** | ✅ | Gemini tras interfaz sustituible |
| **Sistemas RAG** | ✅ | Recuperación híbrida, `docs/RAG.md` |
| **Embeddings** | ✅ | 768 dim, índice multi-modelo |
| **Bases vectoriales** | 🟡 | **Decisión deliberada de no usarla** (ADR-004): 122 vectores no la justifican. Interfaz preparada |
| Contratos de API claros | ✅ | OpenAPI normativo anclado |
| **Streaming de respuestas** | ✅ | SSE, 24 tipos de evento, `sequence_number` |
| **Manejo de estado conversacional** | ✅ | Memoria acotada a un intercambio (ADR-012) |
| **Trazabilidad de interacciones** | ✅ | `metadata` con hechos recuperados, similitudes y citas |
| **Control de latencia percibida** | ✅ | p50 1,2 s; presupuesto acotado a 25 s; streaming |
| **Prompt engineering** | ✅ | Reglas de grounding, precedencia sobre `instructions` |
| Tool use / agentes autónomos | 🟡 | Enrutado determinista, sin herramientas ejecutables |
| **MCP** | ⬜ | No implementado |
| GraphQL · SOAP | ⬜ | No implementados; el contrato exigido es REST |
| **Node.js / TypeScript** | ⬜ | No en este proyecto (acreditado en el CV) |

### Frontend

| Requisito | Estado | Nota |
|---|---|---|
| React / Next.js / Flutter | ⬜ | **La interfaz la aporta la plataforma del reto** |
| Experiencia conversacional fluida | ✅ | Streaming, seguimiento contextual, respuestas citadas |
| Accesibilidad WCAG | ⬜ | Sin interfaz propia que evaluar |
| Diseño responsivo | ⬜ | Ídem |

> **Hueco reconocido.** El reto no pedía frontend, pero la vacante es *full stack*. En
> este entregable la mitad frontend no está representada.

### Nube, contenedores y CI/CD

| Requisito | Estado | Evidencia |
|---|---|---|
| **Despliegue en Azure** | ✅ | Container Apps, `centralus` |
| **Docker** | ✅ | Imagen sin privilegios, healthcheck |
| **Kubernetes** | ⬜ | No usado; Container Apps cubre el caso sin operar clúster |
| **CI/CD** | ✅ | GitHub Actions: calidad → imagen → despliegue → verificación |
| Versionado y releases | ✅ | SemVer, CHANGELOG, release automatizada |
| **Testing (pytest)** | ✅ | 102 tests sin red ni credenciales |
| **Observabilidad** | 🟡 | Logs estructurados y `metadata` por respuesta; sin trazas distribuidas |
| Git | ✅ | Ramas, PR con checks, protección de rama |

---

## 3. Seguridad — sector financiero

Detalle ampliado por tratarse de banca. Fuente: `docs/MODELO-AMENAZAS.md` (STRIDE).

### Implementado

| Control | Cómo |
|---|---|
| **Autenticación del endpoint** | Token obligatorio en cada petición; `401` tipado sin él |
| **Tolerancia de formato de credencial** | `Authorization: Bearer`, `x-api-key`, `api-key` |
| **Gestión de secretos** | Secretos de Azure Container Apps por referencia; **nunca en la imagen ni en el repositorio** |
| **Secretos fuera del control de versiones** | `.env` ignorado y verificado; `.env.example` documenta nombres, no valores |
| **Mínimo privilegio en el despliegue** | Service principal acotado **solo** al grupo de recursos, no a la suscripción |
| **Contenedor sin privilegios** | Usuario UID 10001, imagen `slim`, 6 dependencias |
| **Superficie de ataque mínima** | Sin base de datos, sin ejecución de código, sin herramientas con efectos secundarios |
| **Defensa contra inyección de prompt** | Instrucción explícita + grounding cerrado + verificación de citas. Probado con casos adversariales |
| **`instructions` subordinadas** | El cliente puede influir en tono y formato, **nunca** anular las reglas |
| **Sin PII en el corpus** | Teléfono y correo excluidos; **verificado automáticamente en CI** |
| **Sin datos de negociación** | Expectativa salarial fuera del corpus público |
| **Errores tipados** | Ningún error escapa sin el formato del contrato; sin trazas internas al cliente |
| **Logs sin contenido sensible** | Se registran identificador, idioma, modelo, tokens y latencia; **no** preguntas ni respuestas |
| **Trazabilidad de cada afirmación** | Toda respuesta expone qué hechos la respaldan y con qué similitud |
| **Trazabilidad de despliegue** | Imagen por SHA del commit; reversión a revisión anterior |
| **Protección de rama** | `main` exige checks en verde; sin `force push` ni borrado |
| **Rechazo de entradas hostiles** | 28 casos malformados sin ningún 5xx |
| **Resistencia a agotamiento** | Limitador de concurrencia; abstención sin coste ante preguntas irrelevantes |

### Riesgos aceptados y documentados

| Riesgo | Por qué se acepta | Producción exigiría |
|---|---|---|
| Token estático sin rotación | Alcance del reto | OAuth 2.0 / Entra ID, tokens de vida corta |
| Sin *rate limiting* por cliente | Ídem | API Management en la entrada |
| Proveedor en nivel gratuito: los datos pueden usarse para mejora del producto | Solo se envían hechos públicos del CV | **Tier con aislamiento contractual. Bloqueante** |
| Imagen pública en GHCR | No contiene secretos | Registro privado con escaneo de vulnerabilidades |
| Una sola región | Alcance del reto | Multi-región con conmutación |

### ⬜ Pendiente y recomendable

| Elemento | Por qué importa en banca |
|---|---|
| **Aviso de privacidad del servicio** | El endpoint procesa preguntas de terceros y las envía a un proveedor externo. Debe declararse qué se procesa, qué se registra y qué no |
| Escaneo de dependencias | Cadena de suministro de software |
| Cabeceras de seguridad HTTP | Buenas prácticas de exposición pública |

---

## 4. Valor añadido sobre lo pedido

Ninguno se pidió; todos responden a un problema real detectado.

| Extra | Por qué se añadió |
|---|---|
| **Contrato localizado por investigación propia** | El agente Guía no disponía de él; se ancló la spec normativa y se halló su asimetría (31 campos obligatorios) |
| **Umbral de abstención calibrado empíricamente** | Un número medido, no elegido: 0.62 con separación de +0.073 |
| **Abstención sin invocar al modelo** | Une control de alucinaciones y ahorro: 25 % de consultas a coste cero |
| **Verificación de citas posterior** | Una cita inventada se elimina antes de responder |
| **Fuentes como enlaces al corpus** | Cada afirmación se verifica con un clic sobre el dato versionado |
| **Índice multi-modelo de embeddings** | Cerró el punto único de fallo más grave del sistema |
| **Memoria conversacional acotada** | Conversación fluida con coste **constante** por turno |
| **Consultas de agregación con metadatos** | El orden cronológico lo calcula el código, no el modelo |
| **Golden set + consistencia + robustez + carga** | 5 niveles de prueba; 12 casos miden lo que **no** debe responder |
| **12 ADRs** | Cada decisión con contexto y alternativas descartadas |
| **CI/CD con verificación post-despliegue** | No basta un 200: se comprueba que el contenedor no esté degradado |
| **SemVer, CHANGELOG y release automatizada** | La release verifica coherencia antes de publicar |
| **El agente explica cómo está construido** | El proyecto es un hecho más del corpus |
| **Documento de límites y costes** | Presupuesto de tokens, dónde escala y dónde no |

---

## 5. Resumen honesto

**Fuerte:** backend, RAG, control de alucinaciones, contrato, pruebas, CI/CD, seguridad
del servicio, documentación de decisiones.

**Ausente:** frontend propio, Kubernetes, MCP, GraphQL/SOAP, TypeScript en este proyecto.

**Deliberadamente omitido con justificación:** base vectorial, navegación web en runtime,
capacidades multimodales no implementadas.
