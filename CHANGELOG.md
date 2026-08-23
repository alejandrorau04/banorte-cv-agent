# Changelog

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/).
Versionado según [SemVer](https://semver.org/lang/es/).

En este proyecto el versionado cubre **el servicio y el contrato**, no el contenido del
CV: una corrección del corpus es `PATCH`; un cambio en la forma de la respuesta que un
cliente pudiera notar es `MINOR` o `MAJOR`.

---

## [No publicado]

### Corregido
- **La compuerta de evidencia se podía saltar por completo.** Los hechos inyectados por
  regla en consultas de agregación llevaban una similitud fingida de 1.0, y la compuerta
  mide el máximo: cualquier pregunta con esa forma —incluida una fuera de dominio o un
  intento de inyección— anulaba el control anti-alucinación. Ahora solo la similitud
  medida cuenta como evidencia.
- Detección de seguimiento: `it` coincidía con «IT», los demostrativos con preguntas
  autónomas y `amplia` con el adjetivo común. Reescrita y ampliada a los interrogativos
  sueltos («¿Por qué?»).
- Un tipo de hecho desconocido cargaba sin error y provocaba HTTP 500 al citarlo. Ahora
  se valida al cargar el corpus.
- `prev_user` se acota igual que `prev_answer`: un turno previo largo desbordaba el
  límite de entrada del proveedor.
- CI comparaba cardinalidades donde el servidor compara conjuntos de claves. Ahora usa el
  mismo predicado, y un índice parcial vuelve a fallar salvo excepción declarada.
- `tsc --noEmit` sin `-b` comprobaba cero archivos; sustituido por el lint.
- `cancel-in-progress` en el despliegue de la presentación podía dejarlo atascado.
- Presentación: CSS de la navegación borrado por error, enlace «Integrar» a la sección
  equivocada, indicador de avance invertido con el rebote de scroll.

### Añadido
- Navegación por teclado (← →) entre secciones de la presentación.
- `/health` expone `embed_models` y `embed_models_incompletos`.
- Variable `PERMITIR_INDICE_PARCIAL` para declarar explícitamente una degradación.

### Eliminado
- `web/src/index.css` y dos SVG sin referenciar, restos de la plantilla inicial.

## [1.1.0] — 2026-08-22

### Añadido
- **Memoria conversacional acotada** a un intercambio (ADR-012). Los seguimientos
  («¿y qué hace ahí?») se entienden sin reenviar la transcripción: el coste por turno
  es constante, no crece con la conversación.
- **Índice multi-modelo de embeddings** (ADR-011). Cada modelo tiene cuota diaria propia;
  agotar la del primario ya no deja al agente sin poder responder.
- **Fuentes como enlaces legibles** a las líneas exactas del corpus (ADR-009), en lugar
  de identificadores internos.
- **Información fuera del CV verificada** (ADR-010): siete empresas con sitio y
  descripción, y situación profesional (disponibilidad, objetivo, motivación).
- Soporte del campo `instructions` del contrato, **subordinado** a las reglas de grounding.
- `metadata.upstream_model` y `metadata.embed_model`: qué modelos atendieron la petición.
- Pipeline **CI/CD completo** con despliegue automático y verificación de salud.
- `scripts/calibrar.py`, `scripts/robustez.py`, `eval/consistencia.py`.
- Documentación: límites y costes, plan de pruebas, arquitectura C4, RAG, recorrido
  técnico, guion de demo, resumen ejecutivo.

### Cambiado
- Índice de embeddings **incremental** por hash, con guardado por lotes.
- Timeouts acotados y **presupuesto repartido entre modelos**: el respaldo ya se ejecuta.
- Modelo de respaldo `gemini-3.6-flash` (mediana 15,5 s) sustituido por
  `gemini-3.5-flash-lite` (1,01 s).
- Nivel de inglés reformulado con precisión, sin contradecir el CV.

### Corregido
- Detección de idioma anulada por eliminación de *stopwords*: las preguntas en inglés se
  respondían en español.
- Compuerta de abstención inoperante por normalizar el coseno: no filtraba nada.
- Consultas de agregación afirmaban ausencias falsas (ADR-008).
- HTTP 500 con `text` de forma inesperada; añadido manejador global de errores.
- Los deltas SSE no reconstruían exactamente el texto anunciado.
- Patrón de contacto demasiado amplio: «What number of years…» recibía la respuesta de
  privacidad.
- Arranque silencioso sin índice: ahora falla de forma explícita.

### Seguridad
- Sin datos de contacto ni expectativa salarial en el corpus público (ADR-006, ADR-010).
- Service principal de despliegue acotado al grupo de recursos, no a la suscripción.
- Contenedor con usuario sin privilegios.

## [1.0.0] — 2026-08-22

### Añadido
- Agente de CV bilingüe conforme a **Open Responses `2026-04-24`**: los 31 campos
  obligatorios de `ResponseResource` y streaming SSE (ADR-001).
- Corpus estructurado bilingüe con identificadores estables (ADR-002).
- **Cuatro controles anti-alucinación** con umbral calibrado empíricamente (ADR-003).
- Recuperación híbrida en proceso, sin base vectorial (ADR-004).
- Despliegue en Azure Container Apps con imagen construida en GitHub Actions (ADR-007).

[1.1.0]: https://github.com/alejandrorau04/banorte-cv-agent/releases/tag/v1.1.0
[1.0.0]: https://github.com/alejandrorau04/banorte-cv-agent/releases/tag/v1.0.0
