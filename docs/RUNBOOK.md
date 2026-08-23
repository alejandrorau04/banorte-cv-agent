# Runbook operativo

Servicio: **cv-agent** — endpoint Open Responses del agente de CV.

## Topología

| Componente | Dónde | Rol |
|---|---|---|
| Código | `github.com/alejandrorau04/banorte-cv-agent` | Fuente de verdad |
| Imagen | `ghcr.io/alejandrorau04/cv-agent:latest` | Construida por GitHub Actions |
| Runtime | Azure Container Apps `cv-agent` (grupo `rg-cv-agent`, `centralus`) | Endpoint HTTPS |
| Modelo | Google AI Studio — `gemini-3.1-flash-lite`, respaldo `gemini-3.6-flash` | Generación |
| Embeddings | `gemini-embedding-001` y `gemini-embedding-2`, 768 dim | Índice por modelo; en build |

## Comprobación de salud

```bash
curl -s "$BASE_URL/health"
```

Respuesta sana: `status: ok`, `facts: 61`, `vectors_loaded: true`, y **`embed_models` con
todos los modelos declarados**.

**Si ningún modelo tiene el índice completo, el contenedor no arranca.** Sin índice no puede
calibrarse la compuerta de abstención, y degradar en silencio comprometería la garantía
anti-alucinación. Se midió que la señal léxica no separa dominio de no-dominio (una pregunta
legítima puede puntuar 0.00 y una fuera de dominio 3.85), por lo que no existe umbral léxico
defendible.

**`embed_models_incompletos`** lista los modelos cuyo índice no cubre el corpus entero. Un
modelo así **no se usa**: un hecho sin vector nunca se recupera y el fallo sería silencioso.
Si aparece algo ahí, la redundancia está reducida y hay que reconstruir:

```bash
python scripts/build_index.py      # incremental: solo calcula lo que falta
```

Cada modelo tiene su propio umbral calibrado, así que perder el primario **también cambia el
umbral de abstención en uso**. Consultar `embed_models` para saber cuál está activo.

El pipeline bloquea cualquier índice parcial. Para desplegar durante una incidencia de cuota
hay que declarar la excepción de forma explícita y retirarla después:

```bash
gh variable set PERMITIR_INDICE_PARCIAL --body true    # durante la incidencia
gh variable delete PERMITIR_INDICE_PARCIAL             # al reconstruir
```

## Prueba funcional

```bash
curl -X POST "$BASE_URL/v1/responses" \
  -H "Authorization: Bearer $AGENT_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"cv-agent","input":"¿Dónde trabaja actualmente Alejandro?"}'
```

Debe mencionar GlobalConnect y citar `exp.globalconnect.role`.

## Despliegue

Automático: `git push` a `main` → tests → imagen a GHCR.
Publicación de la nueva revisión en Azure:

```bash
az containerapp update -n cv-agent -g rg-cv-agent \
  --image ghcr.io/alejandrorau04/cv-agent:latest
```

## Cambios en el corpus

El índice de embeddings **debe** regenerarse tras editar `data/corpus.yaml`:

```bash
python scripts/build_index.py && pytest -q && git commit -am "corpus: ..." && git push
```

Omitirlo deja hechos nuevos sin vector: no se recuperarán semánticamente.

## Diagnóstico

| Síntoma | Causa probable | Acción |
|---|---|---|
| HTTP 401 | Token incorrecto o ausente | Verificar `Authorization: Bearer` contra el secreto `agent-api-key` |
| HTTP 429 | Cuota del nivel gratuito agotada | Esperar la ventana de cuota; considerar tier de pago |
| HTTP 503 `upstream_unavailable` | Ambos modelos fallaron | Revisar estado de Google AI Studio; el respaldo ya se intentó |
| Latencia > 25 s | Pico del nivel gratuito | Presupuesto de tiempo lo corta; se degrada a error controlado |
| Se abstiene de más | Umbral alto, o el primario caído y en uso el umbral del respaldo | Verificar `embed_models` en `/health`; recalibrar con `scripts/calibrar.py` |
| Responde sin citas | El modelo omitió el formato | Verificar que la verificación no las eliminó por inválidas (revisar `metadata.retrieved`) |

## Logs

Estructurados en JSON. Cada petición registra: identificador, idioma, si hubo
abstención, modelo usado, tokens y latencia.

```bash
az containerapp logs show -n cv-agent -g rg-cv-agent --tail 100
```

No se registra el contenido de las preguntas ni de las respuestas.

## Rotación de credenciales

```bash
az containerapp secret set -n cv-agent -g rg-cv-agent --secrets gemini-api-key=<nuevo>
az containerapp update -n cv-agent -g rg-cv-agent   # nueva revisión
```

Revocar después la clave anterior en Google AI Studio.

## Coste

`min-replicas = 1` mantiene una réplica activa para evitar arranque en frío durante la
evaluación. Terminada la evaluación, `min-replicas = 0` reduce el coste a casi cero
aceptando arranque en frío:

```bash
az containerapp update -n cv-agent -g rg-cv-agent --min-replicas 0
```

## Reversión

```bash
az containerapp revision list -n cv-agent -g rg-cv-agent -o table
az containerapp revision activate -n cv-agent -g rg-cv-agent --revision <anterior>
```
