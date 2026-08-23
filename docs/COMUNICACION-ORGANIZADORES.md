# Comunicación con los organizadores del reto

Documento vivo. Recoge qué contar, cuándo y con qué evidencia.

## Principio

Se comunica **desde una posición de trabajo hecho**, nunca desde la duda. Cada punto
debe poder respaldarse con un enlace al repositorio o con una medición reproducible.
Nada que no exista en el código.

## Cronología

| Momento | Canal | Contenido |
|---|---|---|
| 2026-08-22 (mañana) | Agente Guía | 4 preguntas sobre el contrato de Open Responses. Respuesta: «la información disponible del reto no especifica esos detalles». |
| Al entregar | Correo a organizadores | Repositorio, endpoint y decisiones técnicas |

## Puntos para el correo de entrega

Ordenados por fuerza del argumento.

### 1. El contrato de Open Responses no estaba documentado; se resolvió por investigación

El agente Guía confirmó no disponer del contrato. En lugar de asumir un formato
«parecido», se localizó la especificación abierta (openresponses.org, Apache-2.0,
respaldada por OpenAI, NVIDIA, AWS, Red Hat, Hugging Face, vLLM y otros), se ancló la
versión `2026-04-24` en el repositorio y se implementó contra el esquema normativo.

**Hallazgo que se comparte como aportación:** el contrato es **asimétrico**. El request
no tiene ningún campo obligatorio (`required: []`), pero `ResponseResource` exige **31**.
La implementación intuitiva —devolver `{id, status, output}`— **no es conforme**.
Es información útil para otros participantes y para la propia organización.

### 2. Anti-alucinación con umbral calibrado, no con buenas intenciones

Cuatro controles en capas. El central: si la evidencia recuperada no supera un umbral,
**no se invoca al modelo**. Un modelo que no se invoca no puede alucinar.

Umbral **0.62**, calibrado empíricamente: en dominio mín. 0.6633, fuera de dominio
máx. 0.5899.

### 3. El control de alucinaciones y el ahorro de tokens son el mismo mecanismo

Medido: 8 de 26 consultas del golden set no llegan al modelo. `thinkingLevel: minimal`
elimina el 77 % de tokens de razonamiento. Coste medio 422 tokens/consulta.

### 4. Evaluación automatizada, no impresiones

Golden set de 26 casos, **26/26**. Doce de ellos miden que el agente sepa **lo que no
sabe**: abstenciones, honestidad ante vacíos e inyección de prompt.

Anécdota honesta que merece contarse: la primera ejecución dio 23/26, y los tres fallos
resultaron ser **errores del evaluador, no del agente** — prohibía la palabra «Harvard»
en lugar de prohibir afirmarla, y un agente no puede negar «Harvard» sin escribirla.

### 5. Decisiones de omisión, tan justificadas como las de inclusión

- **Sin base vectorial.** 122 vectores no justifican Qdrant ni pgvector. Detrás de una
  interfaz, sustituible. Saber cuándo no usar una tecnología es criterio técnico.
- **Sin datos de contacto en el corpus.** Endpoint público + repositorio abierto: el
  agente no puede revelar lo que no tiene. Verificado en CI.
- **Streaming de texto verificado, no de tokens crudos.** La verificación de citas
  necesita el texto completo; retransmitir en directo sería emitir contenido sin
  verificar. Grounding estricto y streaming crudo son incompatibles.

### 6. Una restricción real de Azure produjo una arquitectura mejor

`ACR Tasks` está bloqueado en suscripciones nuevas por política antifraude de Microsoft.
En lugar de cambiar de nube, se trasladó la construcción a GitHub Actions con publicación
en GHCR. Resultado: se conserva Azure **y** se gana un pipeline CI/CD real y demostrable.

### 7. Supuestos no confirmables, documentados con su mitigación

Cuatro detalles de integración que la organización no publica (versión de la spec que
consume el cliente, formato de autenticación, valor de `model`, forma del multi-turno).
No se asumieron: se mitigaron por diseño. Tabla completa en ADR-001.

## Ideas pendientes de valorar

- Ofrecer el hallazgo del contrato asimétrico como aportación explícita al reto.
- Mencionar el backlog de producto (voz bidireccional, generador conversacional de CV)
  como evidencia de que la arquitectura tiene recorrido.

## Reglas de redacción

- Sin adjetivos autoelogiosos. Los números y los enlaces hablan.
- Cada afirmación, con su evidencia en el repositorio.
- No mencionar nada que no esté implementado.
