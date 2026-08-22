# ADR-005 — Consumo de tokens y latencia percibida

- **Estado:** Aceptado
- **Fecha:** 2026-08-22

## Contexto

En un despliegue bancario real, un agente atiende volúmenes en los que cada token es
coste recurrente. Además, la plataforma del reto no documenta su timeout, por lo que la
latencia es también un riesgo de integración.

El campo `usage` es **obligatorio** en `ResponseResource`: la especificación obliga a
contabilizar tokens. La medición de coste no es un añadido, es un requisito que se
aprovecha como observabilidad.

## Mediciones (2026-08-22, Google AI Studio, nivel gratuito)

### Tokens de razonamiento invisibles

Para el prompt trivial «Responde solo: OK»:

| Modelo | entrada | salida | **razonamiento** | total |
|---|---|---|---|---|
| `gemini-3.6-flash` | 5 | 1 | **91** | 97 |

**El 94 % del consumo era razonamiento interno invisible** para producir dos caracteres.

### Efecto de `thinkingLevel`

| Configuración | latencia | razonamiento | total |
|---|---|---|---|
| `low` | 16.29 s | 197 | 247 |
| **`minimal`** | 18.36 s | **0** | **56** |

**Reducción del 77 %** en consumo. `thinkingLevel: "none"` y `thinkingBudget: 0` son
rechazados por la API (HTTP 400): `minimal` es el mínimo admitido.

### Selección de modelo

Misma pregunta, mismos hechos, `thinkingLevel: minimal`:

| Modelo | latencia | total tokens | calidad |
|---|---|---|---|
| **`gemini-3.1-flash-lite`** | **1.44 s** | 377 | equivalente |
| `gemini-3.6-flash` | 19.72 s | 406 | equivalente, mejor formato de cita |

El modelo grande tarda **13 veces más** sin mejorar el contenido.

**Justificación arquitectónica:** con grounding estricto, la tarea del modelo no es
razonar ni recordar, sino **redactar a partir de hechos ya verificados**. Es una tarea
sencilla. **Un buen sistema de recuperación permite usar un modelo más barato**: el
grounding no solo evita alucinaciones, también reduce coste.

`gemini-2.5-flash` devolvió HTTP 404 («no longer available to new users»). Fijar un
modelo por costumbre, sin verificar, habría producido un fallo en producción.

## Decisiones

1. **`thinkingLevel: minimal`** en todas las llamadas.
2. **Modelo primario `gemini-3.1-flash-lite`**, con `gemini-3.6-flash` como respaldo.
3. **Cadena de respaldo entre modelos con reintentos exponenciales.** El nivel gratuito
   devolvió HTTP 503 por alta demanda durante las pruebas: un modelo único sería un
   punto de fallo.
4. **Abstención previa a la invocación.** Sin evidencia no hay llamada: 0 tokens.
5. **Recuperación selectiva.** Top-6 hechos (~500 tokens de entrada) frente a ~1.860 del
   corpus completo en un idioma.
6. **Embeddings precalculados en build**, no en runtime.
7. **Detección de idioma determinista**, sin llamada al modelo.
8. **`max_output_tokens = 800`** y prompt de sistema conciso.

## Resultado agregado

Conjunto de 8 preguntas (3 fuera de dominio, 1 de contacto, 4 legítimas):

| Métrica | Valor |
|---|---|
| Preguntas que no invocan al LLM | **4 / 8** |
| Tokens totales | **2.279** (antes 4.966) |
| Reducción | **−54 %** |
| Latencia de una abstención | 236–494 ms |
| Latencia típica con LLM | 1.0–3.7 s |

## Riesgo aceptado

La latencia del nivel gratuito es **variable**: se observaron respuestas de 16 s en el
mismo endpoint que normalmente responde en 1–2 s. Mitigaciones aplicadas: modelo rápido
como primario, respaldo automático y reintentos. Mitigación pendiente si se dispusiera de
tier de pago: cuota dedicada.

## Alternativa evaluada y descartada

**Meter el CV completo en contexto** (~1.860 tokens/idioma) en lugar de recuperar. Sería
defendible con un corpus tan pequeño: más simple y sin fallos de recuperación. Se descarta
porque (a) cuadruplica los tokens de entrada por petición, (b) elimina la señal de
similitud que hace posible la abstención sin invocar al modelo, que es el control
anti-alucinación más eficaz, y (c) no escala si el corpus crece.
