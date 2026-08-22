# Límites, costes y escalabilidad

Documento explícito de lo que el sistema **sí** garantiza, lo que **no**, y qué haría
falta para llevarlo a producción. Publicarlo es parte del diseño: un sistema cuyos
límites no están escritos no es operable.

---

## 1. Presupuesto de tokens

### Coste por tipo de consulta (medido 2026-08-22)

| Tipo de consulta | Tokens | Latencia | % del golden set |
|---|---|---|---|
| **Petición de contacto** | **0** | ~0 ms | 6 % |
| **Fuera de dominio** (abstención) | **0** | 236–494 ms | 16 % |
| Pregunta simple | ~550–700 | 1–2 s | 50 % |
| Pregunta con seguimiento | ~900 | 1–2 s | — |
| Consulta de agregación | ~1.200 | 2–3 s | 16 % |
| **Media global** | **~660** | 1,2 s (p50) | |

**Una de cada cuatro consultas no llega al modelo.** No es un efecto secundario: es la
compuerta de evidencia, el mismo mecanismo que impide alucinar (ADR-003).

### Palancas aplicadas y su efecto

| Palanca | Efecto medido |
|---|---|
| Abstención previa a la invocación | 0 tokens en el 22 % de las consultas |
| `thinkingLevel: minimal` | **−77 %** de tokens de razonamiento |
| Recuperación top-6 en vez del corpus completo | ~500 tokens de entrada frente a ~1.860 |
| Memoria de **un** intercambio, no la transcripción | Coste **constante** por turno |
| Embeddings precalculados en build | Cero llamadas de indexación en runtime |
| Caché LRU de embeddings de consulta | Las preguntas sugeridas cuestan cero a partir de la segunda |
| Detección de idioma determinista | Evita una llamada por petición |
| Recorte del turno previo a 260 caracteres | Acota el contexto de seguimiento |
| Eliminación del pie de fuentes del contexto | No se reenvían enlaces al modelo |

### Lo que deliberadamente NO se hace

**No se envía la transcripción completa.** Es lo habitual y hace que el coste crezca de
forma cuadrática: en el turno veinte el prompt contiene los diecinueve anteriores. Aquí
el coste por turno **no crece con la longitud de la conversación**.

**No se reescribe la consulta con el LLM.** Resolvería mejor las referencias, pero
añadiría una llamada por turno. Se resuelve concatenando la pregunta previa **solo para
la búsqueda**, lo que no cuesta un token de generación.

---

## 2. Límites del nivel gratuito

Restricción real y la principal limitación operativa actual.

| Recurso | Límite | Mitigación implementada |
|---|---|---|
| Peticiones de **embedding** por día y modelo | Cuota diaria gratuita | **Índice multi-modelo**: cada modelo tiene cuota propia (ADR-011) |
| Peticiones por minuto | Se alcanza con ráfagas | Limitador a 3 llamadas simultáneas con cola de 6 s |
| Peticiones de **generación** | Cuota separada | Cadena de respaldo entre dos modelos |
| Latencia | Variable, con picos | Timeout de 12 s, presupuesto total de 25 s, respaldo rápido |
| Uso de datos | El nivel gratuito puede usarlos para mejora del producto | Solo se envían hechos públicos del CV; sin PII (ADR-006) |

**Degradación conocida:** con el modelo de embedding de respaldo, la compuerta separa
peor (3 de 5 abstenciones en lugar de 5 de 5). Las preguntas que se filtran **se
responden correctamente igual**; el coste es en tokens, no en veracidad. El golden set
reporta explícitamente cuántos casos corrieron en modo degradado.

---

## 3. Escalabilidad

### Lo que ya escala

- **Servicio sin estado.** No persiste conversaciones: toda la memoria llega en la
  petición. Se escala horizontalmente sin sincronizar nada. Configurado de 1 a 3 réplicas.
- **Estado de solo lectura en memoria.** Corpus e índice viajan en la imagen; el arranque
  no depende de ningún servicio externo.
- **Coste por turno constante**, no proporcional a la longitud de la conversación.

### Dónde deja de escalar

| Dimensión | Límite actual | A partir de ahí |
|---|---|---|
| Tamaño del corpus | Búsqueda exhaustiva O(n); razonable hasta ~10.000 hechos | Índice aproximado (HNSW) y **entonces sí** una base vectorial |
| Peticiones concurrentes | Probado con concurrencia 10 y 30 peticiones | Cuota de pago y varias réplicas; el limitador se dimensiona por réplica |
| Volumen diario | Cuota gratuita de embeddings | Tier de pago; el diseño no cambia |
| Multi-perfil | Un solo corpus | El corpus está desacoplado: bastaría enrutar por inquilino |

Nota sobre el limitador de concurrencia: es **por proceso**. Con varias réplicas el
límite efectivo se multiplica. Con cuota de pago habría que centralizarlo o sustituirlo
por *rate limiting* en la puerta de entrada.

---

## 4. Lo que no se ha probado

- **Carga sostenida.** Probado hasta concurrencia 10 y 30 peticiones, no durante horas.
- **Operación prolongada.** El servicio no se ha observado durante días.
- **Recuperación ante caída de la región de Azure.** Una sola región, sin replicación.
- **Golden set de 32 casos.** Suficiente para detectar regresiones, no para afirmar
  robustez estadística. El umbral se calibró con 15–18 preguntas por modelo.
- **La verificación de citas comprueba que el identificador existe**, no que el hecho
  respalde semánticamente la afirmación. La verificación de implicación (NLI) queda
  pendiente.

---

## 5. Requisitos para producción bancaria

Distancia explícita entre este prototipo y un despliegue real.

| Área | Ahora | Producción |
|---|---|---|
| **Proveedor de LLM** | Nivel gratuito; los datos pueden usarse para mejora del producto | Tier con **aislamiento contractual de datos**. Bloqueante |
| **Autenticación** | Token estático | OAuth 2.0 / Entra ID con tokens de vida corta |
| **Rate limiting** | Limitador interno por proceso | API Management en la puerta de entrada |
| **Registro de imágenes** | GHCR público | Registro privado interno, con escaneo de vulnerabilidades |
| **Observabilidad** | Logs estructurados y `metadata` por respuesta | Trazas distribuidas, métricas y alertas centralizadas |
| **Disponibilidad** | Una región, 1–3 réplicas | Multi-región con conmutación |
| **Datos** | Corpus público sin PII | Clasificación formal y política de retención |
| **Evaluación** | Golden set en ejecución manual | Evaluación continua en CI, con umbral que bloquea el despliegue |

---

## 6. Cómo verificar todo esto

```bash
pytest -q                                   # 89 tests, sin red ni credenciales
python eval/run_eval.py                     # golden set: 32 casos
python eval/consistencia.py                 # 26 formulaciones de 5 intenciones
AGENT_URL=... python scripts/robustez.py            # 28 entradas hostiles
AGENT_URL=... python scripts/robustez.py --carga    # ráfaga concurrente
python scripts/calibrar.py <modelo>         # recalibrar el umbral de abstención
```

Cada cifra de este documento procede de una de esas ejecuciones.
