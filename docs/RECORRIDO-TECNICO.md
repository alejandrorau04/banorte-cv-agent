# Recorrido técnico completo

Explicación de todo el sistema, de cero, en el orden en que se construyó. Cada sección
responde **qué se hizo, por qué, y dónde está en el repositorio**.

---

# Parte 1 · El punto de partida

## 1.1 Qué pedía el reto

Literalmente cuatro entregables:

1. Un agente de CV desplegado en un **endpoint público compatible con Open Responses**.
2. Registrarlo en la plataforma del reto y probarlo.
3. Un **repositorio público** en GitHub.
4. Una **demostración** explicando las decisiones técnicas.

Y una frase que condiciona todo lo demás:

> «No existe una única arquitectura correcta: elige el enfoque que mejor demuestre tu
> capacidad para convertir una idea en un producto de IA funcional y **explica por qué
> tomaste esas decisiones**.»

**Lectura:** no evalúan el stack. Evalúan el criterio. Por eso el repositorio tiene ocho
ADRs y no un README bonito.

## 1.2 El primer problema: nadie sabía qué era «Open Responses»

Se preguntó al agente Guía oficial del reto. Respuesta textual:

> «La información disponible del reto no especifica esos detalles de compatibilidad […]
> conviene confirmarlo en la documentación técnica o canal oficial.»

Es decir: **el canal de soporte no tenía el contrato**. Ante una ambigüedad bloqueante
caben dos caminos: asumir algo «parecido», o investigar.

Se investigó. **Open Responses resultó ser una especificación abierta, gobernada y
versionada** (`openresponses.org`, licencia Apache-2.0), iniciada por OpenAI y respaldada
por NVIDIA, AWS, Red Hat, Databricks, Hugging Face, Vercel, vLLM, Ollama, OpenRouter,
LM Studio y Llama Stack. Con OpenAPI normativo y **suite oficial de tests de conformidad**.

Se descargó el esquema y se ancló en el repositorio: `docs/contract/openapi.json`,
versión `2026-04-24`, 108 esquemas.

> **Lección:** cuando falte información crítica, primero busca la fuente autoritativa.
> Asumir un formato «parecido» habría producido un agente incompatible.

## 1.3 El hallazgo que cambió la implementación

Al leer el esquema **con un script**, no en prosa, apareció esto:

```
CreateResponseBody.required   = []      ← el request no exige NINGÚN campo
ResponseResource.required     = 31      ← la respuesta exige 31
```

El contrato es **asimétrico**. Es la Ley de Postel llevada a especificación: *sé liberal
en lo que aceptas, conservador en lo que emites*.

Consecuencia práctica: la implementación intuitiva —devolver `{id, status, output}`—
**no es conforme**. Y validar estrictamente la entrada tampoco: hay que aplicar valores
por defecto, nunca rechazar.

Documentado en [`docs/adr/ADR-001-contrato-open-responses.md`](adr/ADR-001-contrato-open-responses.md).

---

# Parte 2 · El stack y por qué

## 2.1 Lenguaje: Python

**Por qué Python y no Node.js**, teniendo más experiencia en Node: la vacante pide
«Node js, Python (FastAPI, Flask)» y «JavaScript/TypeScript y Python (indispensables)».
El CV ya acredita Node de sobra; Python era la brecha. El reto es la oportunidad de
cerrarla **con código público**, no con una afirmación en una entrevista.

Versión de la imagen: **Python 3.12** (`Dockerfile`). El desarrollo local usa 3.14, y por
eso se eligieron dependencias sin compilación nativa: una librería sin *wheel* para una
versión reciente de Python es una forma tonta de perder una entrega.

## 2.2 Framework: FastAPI

- Es el que nombra la vacante.
- Asíncrono nativo, necesario para SSE y para llamadas concurrentes al proveedor.
- `StreamingResponse` de serie.
- Tipado con Pydantic.

## 2.3 Dependencias: mínimas y sin compilación nativa

`requirements.txt` completo — **seis paquetes**:

```
PyYAML==6.0.3
fastapi==0.141.1
httpx==0.28.1
pydantic==2.13.4
python-dotenv==1.2.3
uvicorn[standard]==0.52.4
```

Ausencias deliberadas:

| No se usa | Por qué |
|---|---|
| `numpy` | La similitud coseno se implementa en Python puro. Con 122 vectores el rendimiento es irrelevante y se elimina una dependencia con compilación nativa |
| `langchain` / `llamaindex` | Ocultarían exactamente las decisiones que el reto pide explicar. El pipeline RAG son ~150 líneas legibles |
| SDK de Google | `httpx` directo: menos superficie, control total de timeouts y reintentos |
| Base de datos | El estado es de solo lectura y cabe en memoria |

Cada dependencia en banca es una revisión de seguridad. Seis es defendible; treinta, no.

**Las versiones están fijadas exactamente a las probadas.** Fijar una versión no
verificada es la receta clásica del «en mi máquina funciona».

## 2.4 Proveedor de LLM: Google Gemini

La vacante menciona «OpenAI, Azure, Google Vertex AI, **etc.**» — lista ilustrativa, no
requisito. Se eligió Gemini por nivel gratuito real, tanto generación como embeddings.

Los modelos **se eligieron midiendo**, no por nombre:

| Modelo | Mediana | Máximo | Decisión |
|---|---|---|---|
| `gemini-3.1-flash-lite` | 1,12 s | 1,18 s | **Primario** |
| `gemini-3.5-flash-lite` | 1,01 s | 1,01 s | **Respaldo** |
| `gemini-3.6-flash` | 15,46 s | 35,67 s | Descartado |
| `gemini-2.5-flash` | — | — | HTTP 404, retirado para cuentas nuevas |

`gemini-2.5-flash` es el caso más elocuente: es el nombre que uno pondría por costumbre,
y **habría producido un fallo en producción**.

**Todo el proveedor vive detrás de una interfaz** (`app/adapters/base.py`). Migrar a Azure
OpenAI es implementar dos métodos.

## 2.5 Nube: Azure

El reto no exige nube concreta. Se eligió Azure porque la vacante dice «soluciones
end-to-end desplegables Azure»: es el único punto donde alinearse con el entorno real de
la Dirección de IA e Innovación de Banorte, a coste casi nulo.

---

# Parte 3 · Estructura del repositorio

```
.
├── app/                         ← el servicio
│   ├── config.py                   toda la configuración, un solo sitio
│   ├── main.py                     servidor FastAPI: rutas, auth, errores
│   ├── api/                     ← CAPA DE TRANSPORTE
│   │   ├── openresponses.py        traducción al contrato (31 campos)
│   │   └── sse.py                  eventos de streaming
│   ├── core/                    ← NÚCLEO (no conoce HTTP ni proveedores)
│   │   ├── models.py               tipos internos
│   │   ├── corpus.py               carga, valida y deriva la línea de tiempo
│   │   ├── retrieval.py            recuperación híbrida + idioma
│   │   ├── prompts.py              reglas de grounding
│   │   └── agent.py                el pipeline completo
│   └── adapters/                ← ADAPTADORES
│       ├── base.py                 puertos: LLM, Embedder
│       └── gemini.py               implementación de Google
├── data/
│   ├── corpus.yaml                 61 hechos bilingües  ← FUENTE DE VERDAD
│   └── corpus.index.json           122 vectores de 768 dim (versionado)
├── docs/
│   ├── contract/openapi.json       contrato oficial anclado
│   ├── adr/                        8 decisiones documentadas
│   └── *.md                        arquitectura, RAG, pruebas, runbook…
├── eval/
│   ├── golden_set.yaml             32 casos con comportamiento esperado
│   ├── run_eval.py                 ejecutor + criterios de corrección
│   └── consistencia.py             26 formulaciones de 5 intenciones
├── scripts/
│   ├── build_index.py              calcula los embeddings (en build)
│   └── robustez.py                 28 entradas hostiles + carga
├── tests/                          122 tests, sin red ni credenciales
├── .github/workflows/ci.yml        tests → imagen → GHCR
├── Dockerfile
├── requirements.txt
├── .env.example                    nombres de variables, nunca valores
└── .gitignore                      excluye .env
```

**La estructura no es decorativa: expresa la arquitectura.** `core/` no importa nada de
`api/`, y esa regla es lo que permite probar el agente sin levantar un servidor.

---

# Parte 4 · Configuración y secretos

## 4.1 Las dos claves

`.env.example` (se versiona, documenta nombres):

```
GEMINI_API_KEY=      # nuestra credencial HACIA Google
AGENT_API_KEY=       # la credencial que la plataforma usa para llamarnos A NOSOTROS
LOG_LEVEL=INFO
```

Son **dos claves distintas y ambas necesarias**. El endpoint es público: sin
`AGENT_API_KEY` cualquiera podría consumir la cuota de Gemini a nuestro cargo.

`AGENT_API_KEY` se generó con `secrets.token_urlsafe(24)` — aleatoriedad
criptográficamente segura, no una cadena inventada.

## 4.2 El flujo de un secreto, de principio a fin

```
.env (local, IGNORADO por git)
   └─> nunca entra al repositorio
   └─> nunca entra a la imagen Docker (.dockerignore lo excluye)
   └─> se registra como SECRETO de Azure Container Apps
       └─> se expone al contenedor por referencia: secretref:gemini-api-key
```

Se verificó explícitamente con `git check-ignore` que `.env` está excluido, y el historial
se revisó para confirmar cero apariciones de la clave.

> Durante el desarrollo la clave se pegó por error en `.env.example` —el archivo que **sí**
> se versiona—. Se detectó antes de commitear. Por eso los nombres importan: `.env` y
> `.env.example` se parecen demasiado.

## 4.3 Configuración centralizada

Todo en `app/config.py`, un único punto:

| Constante | Valor | Por qué ese valor |
|---|---|---|
| `GEN_MODELS` | dos modelos rápidos | Cadena de respaldo; ambos medidos ~1 s |
| `EMBED_DIM` | 768 | Índice 4× menor, coseno 4× más rápido |
| `THINKING_LEVEL` | `minimal` | Elimina el 77 % de tokens de razonamiento |
| `TOP_K` | 6 | Suficiente contexto sin inflar el prompt |
| `MIN_SCORE` | **0.62** | **Calibrado empíricamente**, no elegido a ojo |
| `LLM_TIMEOUT_S` | 12 | El p95 medido del nivel gratuito es alto |
| `LLM_BUDGET_S` | 25 | Cota total, por debajo de un timeout típico de 30 s |
| `MAX_CONCURRENT_LLM` | 3 | Evita los 429 bajo ráfaga |

Cada constante lleva en el código el comentario de **por qué** tiene ese valor y **qué
medición** lo respalda. Un número sin justificación es deuda técnica.

---

# Parte 5 · El código, archivo por archivo

Se recorren en orden de dependencia: de dentro hacia fuera.

## 5.1 `data/corpus.yaml` — la fuente de verdad

61 hechos atómicos. Cada uno:

```yaml
- id: exp.alldora.vinte        # ESTABLE: cambiarlo rompe citas y golden set
  type: experience
  org: "Alldora Latinoamérica"
  title: "Líder de Desarrollo – DevOps"
  title_en: "Development Lead – DevOps"
  start: "2024-06"             # metadatos para consultas deterministas
  end: "2025-05"
  tags: [ia, vinte, robot]
  es: "Diseñó y desplegó un robot digital..."
  en: "He designed and deployed an AI-powered digital robot..."
```

**Por qué hechos y no trozos de PDF:** una cita a `exp.alldora.vinte` es verificable en
git; una cita a «fragmento 7» no significa nada. Y los metadatos permiten responder
«¿dónde trabajaba en marzo de 2024?» sin depender de que el modelo lo deduzca.

**Por qué bilingüe en el corpus y no traducción en runtime:** traducir con el LLM en cada
petición reescribe hechos —fechas y cifras quedan expuestas a deriva—, añade latencia y
rompe la trazabilidad, porque la cita ya no coincide con un texto existente.

**El CV en español es la única fuente de verdad.** Los dos PDF originales tenían fechas
distintas: el inglés conservaba solapamientos que el español ya había corregido.

## 5.2 `app/core/models.py` — los tipos internos

`Fact`, `Retrieved`, `Answer`. Deliberadamente **independientes de Open Responses**: el
núcleo no debe conocer su transporte.

Detalle importante, `Retrieved` tiene **dos** puntuaciones:

```python
score: float      # combinada y normalizada  -> para ORDENAR
semantic: float   # coseno crudo             -> para DECIDIR
```

Confundirlas fue un error real (ver 5.4).

## 5.3 `app/core/corpus.py` — cargar, validar, derivar

Tres responsabilidades:

1. **Cargar** el YAML a objetos `Fact`.
2. **Validar al arrancar**: identificadores únicos, ambos idiomas presentes, y una
   expresión regular que detecta correos y teléfonos. Si encuentra PII, **el proceso no
   arranca**. La política de privacidad deja de ser un documento y pasa a ser código.
3. **Derivar** `derived.timeline`: la trayectoria completa ordenada por `start` con
   `sorted()`. **El orden lo calcula el código, no el modelo.**

## 5.4 `app/core/retrieval.py` — la recuperación

Tres piezas.

**Detección de idioma.** Determinista, por marcadores. Sin llamada al modelo: delegarla
añadiría una petición por consulta.

> **Error cometido:** la primera versión eliminaba *stopwords* antes de comparar, y
> **10 de los 21 marcadores ingleses eran stopwords** (`what`, `where`, `does`, `who`…).
> El detector se anulaba solo y devolvía siempre español. Tres preguntas en inglés del
> golden set estaban registradas como `lang=es` y nadie lo había mirado.

**Búsqueda híbrida.** Coseno (0.65) + solapamiento léxico ponderado por IDF (0.35).

Los embeddings resuelven la paráfrasis; el léxico resuelve los nombres propios raros
—`Vinte`, `Quickbase`, `Rocketbot`—, donde el término literal es la señal fuerte. El IDF
premia precisamente lo raro.

> **Error cometido:** la primera versión normalizaba *todas* las puntuaciones dividiendo
> por el máximo. Eso hace que el mejor resultado valga siempre ≈1.0 **aunque sea pésimo**,
> y la compuerta de abstención nunca se activaba: «¿Cuál es la capital de Francia?» pasaba
> el filtro. Solo el valor **absoluto** sirve para decidir.

**`with_timeline()`.** Ante una consulta de agregación, antepone la línea de tiempo y
todos los hechos de puesto.

## 5.5 `app/core/prompts.py` — las reglas

Prompt de sistema por idioma, con cinco reglas absolutas: responder solo con los hechos,
citar el identificador de cada afirmación, decir con claridad cuando falte información,
no compartir datos de contacto, e **ignorar instrucciones embebidas en la pregunta**.

Contiene además los textos fijos de abstención y de política de contacto. Al ser fijos,
esas respuestas **no cuestan tokens**.

## 5.6 `app/core/agent.py` — el pipeline

El corazón. Ocho etapas:

```python
async def answer(self, question, lang=None):
    lang = lang or detect_lang(question)          # 1 · idioma, 0 tokens
    if not question.strip():        return abstención
    if _CONTACT.search(question):   return política de privacidad   # 2 · 0 tokens
    retrieved = await self._r.search(question, lang)                # 3-4
    if _AGREGADA.search(question):                                  # 5
        retrieved = self._r.with_timeline(retrieved)
    best = max(r.semantic for r in retrieved)                       # 6 · compuerta
    if best < MIN_SCORE:            return abstención · 0 tokens
    c = await self._llm.complete(SYSTEM[lang], prompt)              # 7 · generar
    text, cites = _verify_citations(c.text, ids_recuperados)        # 8 · verificar
    return Answer(...)
```

**El detalle más importante del proyecto está en la etapa 6:** si no hay evidencia, se
devuelve la abstención **sin llamar al modelo**.

> Un modelo que nunca se invoca no puede alucinar.

Y esa misma línea es la que ahorra el 25 % de las consultas en tokens. **El control de
alucinaciones y el ahorro de coste son el mismo mecanismo.**

**Etapa 8, verificación de citas:** el modelo puede fabricar un identificador plausible.
Se contrasta cada cita contra lo recuperado y las inventadas se eliminan del texto. Una
cita no verificable es peor que ninguna: aparenta respaldo donde no lo hay.

## 5.7 `app/adapters/base.py` — los puertos

Dos `Protocol` de Python: `LLM` y `Embedder`. El núcleo depende de **estas interfaces**,
nunca de Gemini.

Esto es lo que hace real la afirmación «migrar a Azure OpenAI es trivial»: hay que
implementar dos métodos y cambiar una variable de entorno. **No es retórica: es una
propiedad verificable del código.**

## 5.8 `app/adapters/gemini.py` — la implementación

Aquí vive toda la resiliencia:

- **Cadena de respaldo** entre dos modelos.
- **Presupuesto de tiempo repartido**: cada modelo recibe su porción del tiempo restante.
- **Un timeout no se reintenta contra el mismo modelo**: si está degradado, insistir solo
  quema el presupuesto del respaldo.
- **Limitador de concurrencia** (semáforo a 3) con cola de 6 s.
- **`thinkingLevel: minimal`**: elimina el razonamiento interno invisible.
- **`taskType`** correcto en embeddings: `RETRIEVAL_QUERY` al consultar,
  `RETRIEVAL_DOCUMENT` al indexar.

> **La cadena de respaldo falló tres veces, siempre pareciendo correcta en el código:**
> primero el modelo de respaldo era más lento (15,5 s) que el timeout (12 s), así que
> nunca podía completarse; luego los reintentos del primario consumían el presupuesto
> entero y el respaldo no llegaba a intentarse. **Un mecanismo de resiliencia no existe
> hasta que se demuestra que se ejecuta.** Hoy hay un test con un cliente falso que fuerza
> el fallo del primario y verifica que el segundo responde.

## 5.9 `app/api/openresponses.py` — la traducción del contrato

Dos funciones clave:

**`extract_question(body)`** — tolerante por diseño. `input` admite texto plano, array de
items, items con `content` anidado, o `null`. Las cuatro formas funcionan, y cualquier
forma inesperada devuelve cadena vacía en lugar de lanzar.

> **Error encontrado atacando producción:** un campo `text` con forma de objeto provocaba
> `TypeError` **fuera** del bloque de captura → HTTP 500 con «Internal Server Error» en
> texto plano, que además **no cumple el formato de error del contrato**.

**`build_response(...)`** — construye los **31 campos obligatorios**, emitiendo `null`
explícito en los anulables: omitirlos incumple el esquema aunque el valor sea vacío.

Incluye `metadata` con la trazabilidad: idioma, si hubo grounding, citas, hechos
recuperados con su similitud, y latencia. `metadata` es un campo estándar, así que
añadirlo **no rompe la conformidad**.

## 5.10 `app/api/sse.py` — el streaming

Emite los eventos con los requisitos normativos: `Content-Type: text/event-stream`,
`event:` coincidiendo con el `type` del payload, **`sequence_number` monotónico en todos**
y terminador `[DONE]`.

`chunk_text()` trocea respetando límites de palabra con un invariante estricto:
`"".join(chunks) == texto`.

> **Error cometido:** la primera versión añadía un espacio al final de cada trozo, de modo
> que los deltas **no reconstruían** el texto que después anunciaba `output_text.done`.
> El test lo ocultaba porque comparaba con `.split()`.

## 5.11 `app/main.py` — el servidor

- Autenticación que acepta `Authorization: Bearer`, `x-api-key` y `api-key`, porque la
  plataforma no documenta cuál usa. **Robustez en lugar de certeza.**
- Errores tipados: 401 `invalid_request`, 429 `too_many_requests`, 503 `server_error`.
- **Manejador global de excepciones**: ningún error imprevisto puede salir sin el formato
  del contrato.
- **El arranque falla si falta el índice de embeddings.** Sin él no puede calibrarse la
  compuerta, y degradar en silencio comprometería la garantía anti-alucinación.
- Logs estructurados en JSON, sin registrar el contenido de preguntas ni respuestas.
- CORS abierto, necesario para el validador oficial de conformidad, que corre en navegador.

---

# Parte 6 · Pruebas

Cinco niveles, cada uno con propósito y coste distintos.

| Nivel | Qué verifica | Red | Resultado |
|---|---|---|---|
| Unitario y de contrato | Esquema, núcleo, SSE | No | **65/65** |
| Golden set | Comportamiento con el modelo real | Sí | **32/32** |
| Consistencia | 26 formulaciones de 5 intenciones | Sí | **26/26** |
| Robustez | 28 entradas hostiles | Sí | **28/28 sin 5xx** |
| Carga | 30 peticiones, concurrencia 10 | Sí | **30/30** |

**Los tests unitarios no requieren red ni credenciales**: el proveedor se sustituye por un
doble. Por eso el CI de un repositorio público es ejecutable por cualquiera, incluido un
evaluador.

**Qué significa «respuesta correcta»** está definido explícitamente en `judge()`:

| Categoría | Criterio |
|---|---|
| `answer` | No se abstiene, cita un hecho esperado, sin texto prohibido |
| `abstain` | Se abstiene **y** consume **0 tokens** |
| `contact` | Aplica la política de privacidad |
| `honest` | No **afirma** el término prohibido (se comprueba negación por frase) |

**12 de los 32 casos miden lo que el agente NO debe responder.** Un conjunto de preguntas
fáciles no probaría la propiedad que aquí más importa.

---

# Parte 7 · Despliegue

## 7.1 El Dockerfile

`python:3.12-slim`, seis dependencias, **usuario sin privilegios** (UID 10001),
*healthcheck*, y un solo worker —el estado es de solo lectura y se escala con réplicas,
no con procesos—.

Copia `corpus.yaml` y `corpus.index.json` a la imagen: **el contenedor arranca sin llamar
a ningún servicio externo.**

## 7.2 La restricción que mejoró la arquitectura

El plan era `az containerapp up --source .`, que construye la imagen en Azure. Falló:

```
ERROR: (TasksOperationsNotAllowed) ACR Tasks requests ... are not permitted.
```

**Azure bloquea ACR Tasks en suscripciones nuevas** por política antifraude.
Desbloquearlo requiere un ticket de soporte.

En lugar de cambiar de nube, se trasladó la construcción a **GitHub Actions** con
publicación en **GHCR**, de donde Azure descarga la imagen.

Resultado: se conserva Azure **y** se gana entrega continua real. La vacante pide
familiaridad con pipelines CI/CD; ahora es demostrable, no declarativo.

## 7.3 El pipeline

```
git push a main
  └─> 122 tests (sin red)
  └─> verificación de los 31 campos CONTRA EL OPENAPI OFICIAL descargado
  └─> verificación de ausencia de PII en el corpus
  └─> docker build
  └─> push a GHCR, etiquetado con el SHA del commit
  └─> az containerapp update  ->  nueva revisión, 100 % del tráfico
```

La imagen se referencia por **SHA**, no por `latest`: cada revisión desplegada es
trazable hasta el código exacto, y revertir es reactivar la revisión anterior.

---

# Parte 8 · Los once defectos encontrados

Ninguno salió de leer el código pensando que estaba bien. Todos salieron de **medir**.

| # | Defecto | Cómo apareció |
|---|---|---|
| 1 | Detección de idioma anulada por stopwords | Revisión de código |
| 2 | Compuerta abstenía el 100 % sin índice | Revisión de código |
| 3 | `top_logprobs` no numérico → HTTP 500 | Revisión de código |
| 4 | Los deltas SSE no reconstruían el texto | Revisión de código |
| 5 | Respuesta vacía saltaba el respaldo | Revisión de código |
| 6 | Embedding sin presupuesto de tiempo | Revisión de código |
| 7 | Patrón de contacto demasiado amplio | Revisión de código |
| 8 | Timeout sin acotar al presupuesto | Revisión de código |
| 9 | Compuerta anulada por normalizar el coseno | Prueba con preguntas fuera de dominio |
| 10 | Respaldo más lento que el timeout | Medición de latencias |
| 11 | Consultas de agregación con respuesta falsa | QA adversarial contra producción |

Y dos hallazgos sobre el propio sistema de evaluación:

- **El evaluador prohibía la palabra en vez de la afirmación.** Un agente no puede negar
  «Harvard» sin escribir «Harvard». Producía tres falsos negativos.
- **El golden set tenía una respuesta esperada incorrecta**: daba por bueno «Alcazar» para
  marzo de 2024 cuando la respuesta es Guval Foods. La línea de tiempo derivada lo destapó.

> **Un evaluador mal diseñado produce falsos negativos que llevan a «arreglar» un sistema
> que funciona.** Es un riesgo real y poco discutido en sistemas GenAI.

---

# Parte 9 · Glosario

| Término | Qué es aquí |
|---|---|
| **RAG** | Recuperar información relevante y entregársela al modelo para que responda solo con ella |
| **Embedding** | Vector numérico donde la cercanía geométrica aproxima la cercanía de significado |
| **Coseno** | Medida de similitud entre dos vectores: 1 = idénticos, 0 = sin relación |
| **IDF** | Ponderación que da más peso a los términos raros, útil para nombres propios |
| **Grounding** | Obligar al modelo a responder solo con la información suministrada |
| **Abstención** | Reconocer que no hay evidencia suficiente y no responder |
| **Alucinación** | Afirmación que el modelo genera sin respaldo en los datos |
| **SSE** | Server-Sent Events: el servidor envía eventos por HTTP conforme los produce |
| **ADR** | Architecture Decision Record: un archivo por decisión, con contexto y alternativas |
| **Golden set** | Conjunto de casos con comportamiento esperado, para detectar regresiones |
| **Puerto / adaptador** | Interfaz que aísla la lógica de una tecnología concreta |
| **STRIDE** | Metodología de modelado de amenazas de seis categorías |
| **p50 / p95** | Latencia de la mitad de las peticiones / del 95 % de ellas |
| **Cold start** | Retraso del primer arranque cuando el servicio estaba apagado |

---

# Parte 10 · Las cinco ideas que sostienen todo

1. **La ambigüedad se investiga, no se asume.** El contrato existía y era público.
2. **Un modelo que no se invoca no puede alucinar.** La abstención previa es el control
   más eficaz, y además el más barato.
3. **Saber cuándo NO usar una tecnología es criterio técnico.** 122 vectores no justifican
   una base vectorial.
4. **Las preguntas estructuradas se responden con datos estructurados.** El orden
   cronológico lo calcula `sorted()`, no el modelo.
5. **Un mecanismo de resiliencia no existe hasta que se demuestra que se ejecuta.** Falló
   tres veces pareciendo correcto.
