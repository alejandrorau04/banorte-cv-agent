# Plan de pruebas y aseguramiento de calidad

Documento legible sin ejecutar nada. Toda cifra citada procede de una ejecución real
reproducible con los comandos indicados.

## Estrategia

Cuatro niveles, cada uno con un propósito distinto y un coste distinto:

| Nivel | Qué verifica | Red | Credenciales | Duración |
|---|---|---|---|---|
| **1. Unitario / contrato** | Conformidad con el esquema, lógica del núcleo, SSE | No | No | 0,05 s |
| **2. Integración local** | Servidor real, autenticación, streaming | Local | Sí | ~30 s |
| **3. Evaluación (golden set)** | Comportamiento del agente frente al modelo real | Sí | Sí | ~60 s |
| **4. Producción** | Endpoint público desplegado | Sí | Sí | ~15 s |

El nivel 1 corre en cada `push` mediante GitHub Actions. **No requiere red ni claves**:
el proveedor se sustituye por un doble. Esto permite que el CI de un repositorio público
sea ejecutable por cualquiera, incluido un evaluador.

---

## Nivel 1 — Pruebas automatizadas (57)

```bash
pytest -q          # 57 passed
```

| Archivo | Casos | Cubre |
|---|---|---|
| `tests/test_contract.py` | 8 | Los 31 campos obligatorios, campos fuera de esquema, `object` constante, anulables explícitos, las 4 formas de `input`, multi-turno, forma del error |
| `tests/test_agent.py` | 11 | Detección de idioma, verificación de citas, citas agrupadas, política de contacto sin LLM, integridad y ausencia de PII del corpus |
| `tests/test_sse.py` | 8 | `sequence_number` monotónico, `event` == `type`, troceo sin partir palabras, secuencia completa y `[DONE]` |
| `tests/test_regresiones.py` | 30 | Un caso por hallazgo de la revisión de código (ver abajo) |

Dos verificaciones adicionales corren en CI y **fallan la construcción**:

- Los campos obligatorios se comprueban **contra el OpenAPI oficial** descargado, no
  contra una lista escrita a mano. Si la especificación cambia, el CI lo detecta.
- El corpus se valida buscando datos de contacto. Reintroducir PII rompe el build.

---

## Nivel 3 — Golden set: 26 casos, 26/26

```bash
python eval/run_eval.py     # resultados en eval/results.json
```

| Categoría | Casos | Qué mide |
|---|---|---|
| `answer` | 14 | Responde y cita hechos correctos. Incluye consulta temporal («¿dónde trabajaba en marzo de 2024?») y ambos idiomas |
| `honest` | 5 | Reconoce lo que **no** está en el CV. Incluye 2 adversariales (inyección de prompt) |
| `abstain` | 5 | Fuera de dominio: no debe invocar al modelo |
| `contact` | 2 | Aplica la política de privacidad |

**Doce de los 26 casos miden que el agente sepa lo que no sabe.** Un conjunto compuesto
solo de preguntas fáciles no probaría la propiedad que más importa aquí.

### Resultados (última ejecución)

| Métrica | Valor |
|---|---|
| Aciertos | **26 / 26 (100 %)** |
| Consultas que no invocan al LLM | 8 / 26 (30,8 %) |
| Tokens totales | 10.829 (media 416/consulta) |
| Latencia p50 / p95 | 1.144 ms / 13.613 ms |

### Recorrido feliz — ejemplo verificado

**Pregunta:** «¿Dónde trabaja actualmente Alejandro?»
**Recuperación:** `exp.globalconnect.role` (similitud 0,6929) entre los 6 primeros.
**Respuesta:** menciona GlobalConnect, Cancún y mayo de 2025, citando
`[exp.globalconnect.role]`.
**Verificación:** la cita existe entre los hechos recuperados → se conserva.
**Coste:** 557 tokens, 1,2 s.

### Casos límite verificados

| Caso | Comportamiento observado |
|---|---|
| Fuera de dominio | Abstención, **0 tokens**, 236–494 ms |
| Petición de contacto | Respuesta de privacidad, 0 tokens, ~0 ms |
| Pregunta legítima sin evidencia (Kubernetes) | «Los hechos no mencionan…» + lo adyacente que sí existe, con cita |
| Inyección de prompt | No emite la afirmación falsa; responde con hechos reales |
| Pregunta vacía | Abstención |
| `input` ausente, nulo, texto o array | Todas aceptadas, ninguna rechazada |
| Campos numéricos con valores no válidos | Se aplica el valor por defecto, sin error |

---

## Revisión de código — 2026-08-22

Revisión sistemática de las ~1.000 líneas del servicio, nivel de exigencia alto.
**Ocho hallazgos, todos corregidos, todos con test de regresión.**

| # | Hallazgo | Impacto | Corrección |
|---|---|---|---|
| 1 | `detect_lang` eliminaba stopwords **antes** de comparar, y 10 de los 21 marcadores ingleses eran stopwords | Preguntas en inglés respondidas en español. Reproducido en 3 casos del propio golden set | Tokenización sin filtrar para la detección |
| 2 | Sin índice, la compuerta abstenía el 100 % de preguntas, contradiciendo el runbook | Servicio inútil ante una imagen mal construida | El arranque **falla ruidosamente** si falta el índice |
| 3 | `top_logprobs` no numérico lanzaba `ValueError` no capturado | HTTP 500, violando la tolerancia de entrada que exige el contrato | Conversión segura con valor por defecto |
| 4 | `chunk_text` añadía un espacio: los deltas SSE no reconstruían el texto | Parpadeo o duplicación al final del stream | Invariante `"".join(chunks) == texto`, con test |
| 5 | Una respuesta vacía del modelo saltaba toda la cadena de respaldo | 503 evitable | El error se trata como reintentable |
| 6 | El embedding de la consulta no tenía presupuesto de tiempo | ~37 s fuera del presupuesto declarado | Presupuesto propio de 8 s |
| 7 | El patrón de contacto capturaba `number` y `contacto` sueltos | «What number of years…» recibía la respuesta de privacidad | Patrón restringido a expresiones explícitas |
| 8 | El timeout no se acotaba al presupuesto restante; se esperaba tras el último intento | Tiempo total hasta ~37 s frente a los 25 s declarados | Timeout acotado y sin espera final |

### Dos hallazgos derivados, encontrados al corregir

- **El umbral léxico propuesto para el hallazgo 2 no funcionaba.** Al medirlo: una
  pregunta legítima puntuaba **0,00** y una fuera de dominio **3,85**. La señal léxica
  no separa dominio de no-dominio. Se descartó el umbral y se optó por fallar al
  arrancar. *Medir antes de confiar en una intuición.*
- **La cadena de respaldo era decorativa.** Con timeout de 12 s y un respaldo
  (`gemini-3.6-flash`) cuya mediana medida es 15,5 s y su máximo 35,7 s, el respaldo
  **nunca podía completarse**. Sustituido por `gemini-3.5-flash-lite` (1,01 s). Efecto:
  p95 del golden set de 31,9 s a 13,6 s.

---

## Hallazgo del propio conjunto de evaluación

La primera ejecución del golden set dio **23/26**. Al inspeccionar las tres respuestas
«fallidas», el agente había respondido correctamente en las tres:

> «La información disponible **no indica** que Alejandro cuente con un doctorado en
> Harvard. Alejandro es Ingeniero en Sistemas Computacionales… [education.degree]»

El error estaba en el evaluador: prohibía que la palabra apareciera, en lugar de prohibir
que se **afirmara**. Un agente no puede negar «Harvard» sin escribir «Harvard». Se
corrigió el criterio para exigir una marca de negación en la misma frase.

Se documenta porque ilustra un riesgo real de la evaluación de sistemas GenAI:
**un evaluador mal diseñado produce falsos negativos que llevan a "arreglar" un sistema
que funciona.**

---

## Cronología

| Hora (2026-08-22) | Actividad |
|---|---|
| Mañana | Consulta al agente Guía del reto; investigación y anclaje del contrato |
| — | Corpus bilingüe, validación e integración de PII en CI |
| — | Núcleo: recuperación, compuerta, verificación de citas |
| — | Calibración empírica del umbral de abstención (15 preguntas) |
| — | Capa Open Responses; verificación de los 31 campos y del SSE |
| — | Suite de pruebas y CI; primera ejecución del golden set |
| — | Despliegue: fallo de ACR Tasks → build en GitHub Actions + GHCR → Azure |
| Tarde | **Revisión de código**: 8 hallazgos, corregidos con tests de regresión |
| — | Re-medición: p95 de 31,9 s a 13,6 s; golden set 26/26 |

---

## Qué no se ha probado

Honestidad sobre los límites de esta campaña:

- **Sin pruebas de carga.** No se conoce el comportamiento con concurrencia alta.
- **Sin pruebas de larga duración.** No se ha observado el servicio durante días.
- **Golden set de 26 casos**, ampliable. El umbral se calibró con 15 preguntas: es
  suficiente para separar los grupos observados, no para afirmar robustez estadística.
- **La verificación de citas comprueba que el identificador existe**, no que el hecho
  respalde semánticamente la afirmación. La verificación de implicación (NLI) queda
  como trabajo futuro.
- **Sin pruebas de accesibilidad**: no hay interfaz propia; el cliente es la plataforma
  del reto.
