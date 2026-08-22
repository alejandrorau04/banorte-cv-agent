# ADR-011 — Índice multi-modelo: eliminar el punto único de fallo de los embeddings

- **Estado:** Aceptado
- **Fecha:** 2026-08-22

## Contexto

Durante las pruebas finales, el proveedor empezó a devolver:

```
HTTP 429  EmbedContentRequestsPerDayPerProjectPerModel-FreeTier
```

Cuota **diaria** de embeddings agotada.

La gravedad es máxima y no era evidente: **el embedding de la consulta se calcula en
TODA petición**, incluso en las que después se abstienen. Es la llamada más frecuente
del sistema, más aún que la generación. Si esa cuota se agota, la recuperación deja de
funcionar y **el agente no puede responder a nada**.

Era el punto único de fallo más grave de toda la arquitectura, y estaba oculto porque
la atención se había puesto en la resiliencia del modelo de generación.

## La trampa de la solución obvia

Añadir «un modelo de embedding de respaldo» **no funciona sin más**: cada modelo produce
vectores en un **espacio distinto**. Comparar una consulta embebida con el modelo B
contra un corpus indexado con el modelo A da resultados sin sentido. Además invalida el
umbral de abstención, calibrado para una escala concreta.

## Decisión

**Indexar el corpus con todos los modelos de la cadena, y comparar siempre contra el
conjunto de vectores del modelo que respondió.**

1. `scripts/build_index.py` genera un conjunto de vectores **por modelo**
   (`by_model`), de forma incremental y por lotes con guardado parcial.
2. `MultiEmbedder` recorre los modelos en orden y **declara cuál respondió**.
3. `HybridRetriever` selecciona el conjunto de vectores de **ese** modelo.
4. Cada modelo tiene su **propio umbral calibrado** (`MIN_SCORE_BY_MODEL`).

Medición que lo hace posible: la cuota es `PerProjectPerModel`, es decir, **cada modelo
tiene su propio límite diario**. `gemini-embedding-2` seguía disponible con
`gemini-embedding-001` agotado.

## Calibración por modelo

`scripts/calibrar.py`, mismo método empírico del ADR-003:

| Modelo | En dominio (mín.) | Fuera de dominio (máx.) | Separación | Umbral |
|---|---|---|---|---|
| `gemini-embedding-001` | 0.6633 | 0.5899 | **+0.073** | **0.62** |
| `gemini-embedding-2` | 0.5593 | 0.5620 | **−0.003** | **0.55** |

**El modelo de respaldo no separa limpiamente: hay solapamiento.** No existe umbral
perfecto. Se elige 0.55 aplicando el criterio asimétrico del ADR-003 — dejar pasar
alguna pregunta fuera de dominio cuesta menos que abstenerse ante una legítima.

## Degradación medida y reportada

Golden set ejecutado íntegramente sobre el modelo de respaldo:

| Categoría | Con modelo primario | Con respaldo |
|---|---|---|
| `answer` | 20/20 | **20/20** |
| `honest` | 5/5 | **5/5** |
| `contact` | 2/2 | **2/2** |
| `abstain` | 5/5 | **3/5** |
| **Total** | **32/32** | **30/32** |

Las dos preguntas que se filtran (`Write me a poem about cats`,
`How do I fix a car engine?`) **se responden correctamente**: el prompt las redirige. El
coste de la degradación es **tokens, no veracidad**.

El ejecutor del golden set registra el modelo de embedding de cada caso y **reporta
explícitamente cuántos corrieron en modo degradado**. Atribuir al agente una degradación
causada por la cuota sería un diagnóstico erróneo.

## Otras mitigaciones incorporadas

- **Caché de embeddings de consulta** (LRU, 512). Las preguntas sugeridas de la interfaz
  se repiten mucho: en las repeticiones la llamada desaparece.
- **Limitador de concurrencia también en los embeddings.** Antes solo cubría la
  generación, siendo el embedding la llamada más frecuente.
- **Índice incremental con hash por texto**: solo se recalcula lo que cambió. Reconstruir
  los 118 vectores en cada edición del corpus fue lo que agotó la cuota.
- **Guardado por lotes**: un 429 a mitad ya no descarta lo calculado.

## Consecuencias

- El índice ocupa el doble (dos conjuntos de 118 vectores, ~2 MB). Irrelevante.
- Cada modelo nuevo en la cadena exige **reindexar y recalibrar**. Documentado en el
  runbook y verificado por un test que exige umbral para cada modelo declarado.
- El sistema tolera el agotamiento de la cuota diaria de un modelo sin dejar de responder.

## Lección

**Los mecanismos de resiliencia se diseñaron para el modelo de generación, mientras el
componente más invocado del sistema no tenía ninguno.** El fallo no apareció revisando
el código: apareció al agotar una cuota real. Es la cuarta vez en este proyecto que un
mecanismo aparentemente correcto no resiste el contacto con la medición.
