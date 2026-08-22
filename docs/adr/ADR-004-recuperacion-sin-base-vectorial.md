# ADR-004 — Recuperación híbrida en proceso, sin base vectorial externa

- **Estado:** Aceptado
- **Fecha:** 2026-08-22

## Contexto

El corpus son **46 hechos × 2 idiomas = 92 vectores**. La opción por defecto en un
proyecto RAG es desplegar una base vectorial (Qdrant, pgvector, Azure AI Search).

## Decisión

**Recuperación híbrida en memoria, dentro del propio proceso**, detrás de una interfaz
sustituible.

### Por qué sin base vectorial externa

Para 92 vectores, una base vectorial añade un servicio que desplegar y operar, latencia
de red por consulta, un punto de fallo adicional, coste y credenciales que gestionar —
**sin ninguna ganancia medible**: la búsqueda exhaustiva sobre 46 vectores en Python puro
es de microsegundos.

Introducir infraestructura que no resuelve un problema real no es sofisticación, es
deuda operativa. **Saber cuándo no usar una tecnología es parte del criterio técnico.**

La recuperación vive tras una interfaz: si el corpus creciera dos órdenes de magnitud,
sustituirla es implementar una clase. La decisión es reversible por diseño.

### Por qué híbrida y no solo semántica

Los embeddings resuelven bien la paráfrasis, pero degradan con **nombres propios de baja
frecuencia**: `Vinte`, `Quickbase`, `Rocketbot`, `Netcontent`. Ahí la coincidencia
literal es la señal más fuerte.

Se combina similitud coseno (peso 0.65) con solapamiento léxico ponderado por IDF
(peso 0.35). El IDF premia los términos raros, que es exactamente donde el vector falla.

Comprobación: «¿Qué hizo para Vinte?» recupera `exp.alldora.vinte` con puntuación
combinada 1.0.

### Dos señales separadas, con propósitos distintos

- La puntuación **combinada y normalizada** sirve para **ordenar**.
- El **coseno crudo, sin normalizar**, sirve para **decidir** si hay evidencia.

Confundirlas fue un error real durante la implementación: normalizar por el máximo hace
que el mejor resultado valga siempre ~1.0 aunque sea pésimo, y la compuerta de abstención
nunca se activa (ver ADR-003).

### Dimensionalidad reducida: 768 en lugar de 3072

`gemini-embedding-001` admite `outputDimensionality`. Reducir a 768 da un índice 4 veces
menor (3.7 MB → 950 KB), un coseno 4 veces más rápido en Python puro y una imagen de
contenedor más ligera, con pérdida de calidad marginal por tratarse de embeddings
entrenados para truncarse.

### El índice se versiona en git

Los embeddings se calculan en `scripts/build_index.py` y el resultado se commitea.
Consecuencias: construir la imagen **no requiere credenciales**, arrancar el contenedor
**no llama al proveedor**, y el arranque en frío no depende de un servicio externo.

## Consecuencias

- Cero infraestructura de datos que operar.
- El índice debe regenerarse al cambiar el corpus. Se documenta en el runbook.
- Cambiar de modelo de embeddings invalida tanto el índice como la calibración del
  umbral de abstención: la escala del coseno no es comparable entre modelos.
- La búsqueda exhaustiva es O(n). Aceptable hasta ~10.000 hechos; por encima, sustituir.
