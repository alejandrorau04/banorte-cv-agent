# Agente de CV — Alejandro Rau Lázaro

Agente conversacional que responde sobre una trayectoria profesional, en español e inglés,
expuesto como servicio compatible con la especificación abierta
**[Open Responses](https://www.openresponses.org) `2026-04-24`** y desplegado en
**Azure Container Apps**.

**Reto IA Banorte · Agosto 2026**

### ▶ Demostración de la solución

**https://alejandrorau04.github.io/banorte-cv-agent/**

Documento técnico interactivo con las decisiones tomadas para **diseñar, integrar,
desplegar y operar** el agente. Cada afirmación enlaza a su origen en este repositorio.

| El reto pide explicar cómo… | Dónde se responde |
|---|---|
| **Diseñar** | [Arquitectura](docs/ARQUITECTURA.md) · [Pipeline RAG](docs/RAG.md) · [12 ADRs](docs/adr/) — cada decisión con sus alternativas descartadas |
| **Integrar** | [ADR-001 · Contrato Open Responses](docs/adr/ADR-001-contrato-open-responses.md) — cómo se localizó la especificación, su asimetría y los supuestos de integración |
| **Desplegar** | [ADR-007 · Azure y construcción en GitHub Actions](docs/adr/ADR-007-despliegue-y-construccion-de-imagen.md) · [pipeline CI/CD](.github/workflows/ci.yml) |
| **Operar** | [RUNBOOK](docs/RUNBOOK.md) · [LIMITES-Y-COSTES](docs/LIMITES-Y-COSTES.md) · [MODELO-AMENAZAS](docs/MODELO-AMENAZAS.md) |
| **Verificar que responde de forma confiable** | [PLAN-DE-PRUEBAS](docs/PLAN-DE-PRUEBAS.md) · [golden set](eval/golden_set.yaml) · [resultados](eval/results.json) |

---

## Acceso rápido

| | |
|---|---|
| **Demostración** | **https://alejandrorau04.github.io/banorte-cv-agent/** |
| **Endpoint** | `POST /v1/responses` · [estado del servicio](https://cv-agent.bravesky-2e199aa3.centralus.azurecontainerapps.io/health) |
| **Pipelines** | [GitHub Actions](../../actions) · [releases](../../releases) |
| **Decisiones técnicas** | [12 ADRs](docs/adr/) |
| **Evidencia de pruebas** | [plan de pruebas](docs/PLAN-DE-PRUEBAS.md) · [golden set](eval/golden_set.yaml) · [resultados](eval/results.json) |

---

## El problema

Un agente de CV tiene un modo de fallo específico y grave: **afirmar experiencia
profesional que la persona no tiene**. Una fecha, una empresa o una tecnología fabricadas
ante un reclutador no son un error de software: son un problema de veracidad.

Instruir al modelo con «no inventes» es una petición, no una garantía. Todo el diseño se
deriva de esa distinción.

## La respuesta: cuatro controles que no dependen del modelo

| | Control | Mecanismo |
|---|---|---|
| 1 | **Grounding cerrado** | El prompt contiene únicamente hechos del corpus versionado |
| 2 | **Compuerta de evidencia** | Sin similitud suficiente **no se invoca al modelo**. Umbral 0.62, calibrado |
| 3 | **Verificación de citas** | Toda cita se contrasta contra lo recuperado; las inventadas se eliminan |
| 4 | **Política determinista** | Los datos de contacto no existen en el corpus: no puede revelarlos |

→ [ADR-003 · Estrategia anti-alucinación](docs/adr/ADR-003-estrategia-anti-alucinacion.md)

## Resultados medidos

| Métrica | Valor |
|---|---|
| Afirmaciones sin respaldo en los 32 casos evaluados | **0** |
| Conjunto de evaluación · *12 casos miden lo que NO debe responder* | **32/32** |
| Intentos de inyección de prompt resistidos | **5/5** |
| Consistencia ante 26 formulaciones distintas | **26/26** |
| Entradas malformadas sin error de servidor | **28/28** |
| Peticiones correctas con concurrencia 10 | **30/30** |
| Tests automatizados, sin red ni credenciales | **122** |
| Consultas resueltas sin invocar al modelo | **25 %** |
| Latencia p50 · p95 | **0,97 s · 1,49 s** |
| Tokens medios por consulta | **677** |

---

## Cómo se usa

```bash
curl -X POST "$BASE_URL/v1/responses" \
  -H "Authorization: Bearer $AGENT_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"cv-agent","input":"¿Qué experiencia tiene con IA?"}'
```

Streaming SSE con `"stream": true`. Estado del servicio en `GET /health`.

El agente es además **descubrible por clientes A2A**: expone su tarjeta en
`GET /.well-known/agent-card.json`, lo que permite dar de alta el agente en la plataforma
del reto con un clic en lugar de rellenar el formulario a mano
([ADR-013](docs/adr/ADR-013-tarjeta-de-agente-a2a.md)).

Cada respuesta incluye en `metadata` la trazabilidad completa: idioma detectado, si hubo
grounding, hechos recuperados con su similitud, citas verificadas, modelos que atendieron
la petición y latencia.

## Desarrollo

```bash
python3 -m venv .venv && ./.venv/bin/pip install -r requirements.txt
cp .env.example .env                        # rellenar GEMINI_API_KEY y AGENT_API_KEY
./.venv/bin/python scripts/build_index.py   # embeddings del corpus
./.venv/bin/uvicorn app.main:app --reload
```

### Verificación

```bash
pytest -q                                        # 122 tests, sin red ni credenciales
python eval/run_eval.py                          # golden set: 32 casos
python eval/consistencia.py                      # 26 formulaciones de 5 intenciones
AGENT_URL=... python scripts/robustez.py         # 28 entradas hostiles
AGENT_URL=... python scripts/robustez.py --carga # ráfaga concurrente
python scripts/calibrar.py <modelo>              # recalibrar el umbral de abstención
```

Los tests **no requieren credenciales ni conexión**: el proveedor se sustituye por un
doble. El CI verifica además los 31 campos obligatorios **contra el OpenAPI oficial
descargado** y la ausencia de datos personales en el corpus.

---

## Documentación

### Para entender el sistema

| Documento | Contenido |
|---|---|
| [RESUMEN-EJECUTIVO](docs/RESUMEN-EJECUTIVO.md) | Tres minutos: qué es, qué resuelve, resultados |
| [ARQUITECTURA](docs/ARQUITECTURA.md) | Diagramas C4 y de secuencia; flujo de una petición |
| [RAG](docs/RAG.md) | El pipeline de recuperación, etapa por etapa |
| [RECORRIDO-TECNICO](docs/RECORRIDO-TECNICO.md) | El sistema completo, archivo por archivo |

### Para evaluar el rigor

| Documento | Contenido |
|---|---|
| [PLAN-DE-PRUEBAS](docs/PLAN-DE-PRUEBAS.md) | Cinco niveles, evidencia, los 11 defectos hallados |
| [MODELO-AMENAZAS](docs/MODELO-AMENAZAS.md) | STRIDE y riesgos aceptados |
| [LIMITES-Y-COSTES](docs/LIMITES-Y-COSTES.md) | Presupuesto de tokens, escalabilidad, qué falta para producción |
| [CHECKLIST-VACANTE](docs/CHECKLIST-VACANTE.md) | Correspondencia con la vacante, **incluidos los huecos** |

### Para operar

| Documento | Contenido |
|---|---|
| [RUNBOOK](docs/RUNBOOK.md) | Diagnóstico, despliegue, rotación de credenciales, reversión |
| [CHANGELOG](CHANGELOG.md) | Historial de versiones |
| [DEMO](docs/DEMO.md) | Guion de la demostración |
| [BACKLOG-VALOR-AGREGADO](docs/BACKLOG-VALOR-AGREGADO.md) | Extensiones que la arquitectura ya admite |

### Decisiones técnicas

| ADR | Decisión |
|---|---|
| [001](docs/adr/ADR-001-contrato-open-responses.md) | Adopción de Open Responses `2026-04-24`; el contrato es **asimétrico** |
| [002](docs/adr/ADR-002-corpus-estructurado-bilingue.md) | El CV como corpus estructurado bilingüe, no como documento |
| [003](docs/adr/ADR-003-estrategia-anti-alucinacion.md) | Cuatro controles anti-alucinación en capas |
| [004](docs/adr/ADR-004-recuperacion-sin-base-vectorial.md) | Recuperación híbrida en proceso, **sin base vectorial** |
| [005](docs/adr/ADR-005-consumo-de-tokens-y-latencia.md) | Consumo de tokens y latencia |
| [006](docs/adr/ADR-006-privacidad-y-datos-de-contacto.md) | Exclusión de datos de contacto |
| [007](docs/adr/ADR-007-despliegue-y-construccion-de-imagen.md) | Despliegue en Azure con construcción en GitHub Actions |
| [008](docs/adr/ADR-008-consultas-de-agregacion.md) | Consultas de agregación resueltas con metadatos |
| [009](docs/adr/ADR-009-presentacion-de-fuentes.md) | Fuentes como enlaces legibles al corpus |
| [010](docs/adr/ADR-010-informacion-aportada-y-verificada.md) | Información fuera del CV: verificación antes de incorporarla |
| [011](docs/adr/ADR-011-redundancia-de-embeddings.md) | Índice multi-modelo: eliminar el punto único de fallo |
| [012](docs/adr/ADR-012-memoria-conversacional-acotada.md) | Memoria conversacional acotada a un intercambio |
| [013](docs/adr/ADR-013-tarjeta-de-agente-a2a.md) | Tarjeta de agente A2A para descubrimiento |

---

## Estructura

```
app/            servicio        api/ transporte · core/ núcleo · adapters/ proveedores
data/           corpus.yaml (61 hechos bilingües) + índice de embeddings versionado
docs/           12 ADRs, arquitectura, RAG, pruebas, seguridad, límites, runbook
eval/           golden set (32 casos), consistencia (26 formulaciones), resultados
scripts/        construcción del índice, calibración del umbral, robustez y carga
tests/          122 tests, sin red ni credenciales
web/            presentación en React + TypeScript (GitHub Pages)
.github/        pipelines de CI/CD, release y presentación
```

## Tres decisiones que suelen sorprender

**Sin base de datos vectorial.** 122 vectores no justifican desplegar Qdrant ni pgvector:
añadirían un servicio que operar, latencia de red y un punto de fallo, sin ganancia
medible. La recuperación vive tras una interfaz: sustituirla es implementar una clase.
*Saber cuándo no usar una tecnología también es criterio técnico.*

**El streaming emite texto ya verificado, no los tokens crudos del modelo.** La
verificación de citas necesita el texto completo; retransmitir en directo significaría
emitir contenido sin verificar. Grounding estricto y streaming crudo son incompatibles.

**Las preguntas estructuradas se responden con datos estructurados.** El orden cronológico
lo calcula el código a partir de los metadatos, no el modelo.

## Once defectos encontrados en el propio sistema

Ninguno se detectó leyendo el código: todos surgieron de medir. Detección de idioma
anulada por sus propias palabras vacías, compuerta de abstención inoperante por normalizar
el coseno, modelo de respaldo más lento que su propio tiempo límite, índice parcial
fallando en silencio. Cada uno tiene su prueba de regresión.

En dos ocasiones el equivocado resultó ser el **conjunto de evaluación**, no el agente.
Está documentado en el [plan de pruebas](docs/PLAN-DE-PRUEBAS.md): un evaluador mal
diseñado lleva a corregir un sistema que funciona.

---

## Privacidad y tratamiento de datos

- El corpus **no contiene datos de contacto ni información salarial**. Se verifica
  automáticamente en cada construcción; si alguien los reintroduce, el arranque falla.
- **No se persisten conversaciones.** El servicio es sin estado: toda la memoria llega en
  la petición.
- **Los registros no incluyen el contenido** de preguntas ni respuestas: solo
  identificador, idioma, modelo, tokens y latencia.
- Las preguntas se envían a un proveedor externo de modelos de lenguaje (Google AI Studio)
  para generar la respuesta. En el nivel gratuito, esos datos pueden emplearse para mejora
  del producto; por eso el corpus contiene únicamente información profesional pública.
  Un despliegue productivo exigiría un tier con aislamiento contractual de datos.

Detalle completo en [MODELO-AMENAZAS](docs/MODELO-AMENAZAS.md) y
[ADR-006](docs/adr/ADR-006-privacidad-y-datos-de-contacto.md).

---

**Alejandro Rau Lázaro** · Full Stack Developer · Especialista móvil iOS y Android · Líder de desarrollo
