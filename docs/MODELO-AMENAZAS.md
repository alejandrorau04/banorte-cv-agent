# Modelo de amenazas

Alcance: el servicio `cv-agent` expuesto públicamente en internet. Metodología STRIDE,
adaptada a los riesgos propios de una aplicación GenAI.

## Activos

| Activo | Sensibilidad | Nota |
|---|---|---|
| `GEMINI_API_KEY` | **Alta** | Su fuga permite consumir cuota a cargo del titular |
| `AGENT_API_KEY` | **Alta** | Controla el acceso al endpoint |
| Corpus del CV | Baja | Información profesional destinada a ser pública |
| Datos de contacto | **No presentes** | Excluidos por diseño (ADR-006) |
| Historial de conversación | No persistido | El servicio es sin estado |

## Amenazas y controles

### S — Suplantación

**Un tercero llama al endpoint haciéndose pasar por la plataforma del reto.**
→ Autenticación por token en todas las peticiones. Sin token válido, HTTP 401. Se
aceptan varias cabeceras porque el formato de la plataforma no está documentado, pero
**siempre** se exige el token.
*Riesgo residual:* token estático sin rotación automática. En producción bancaria
correspondería OAuth 2.0 con tokens de vida corta.

### T — Manipulación

**Inyección de prompt: instrucciones dentro de la pregunta que alteren el comportamiento.**
→ Tres controles: instrucción explícita de ignorar órdenes embebidas; **grounding cerrado**
(el modelo solo dispone de hechos del corpus, así que no puede afirmar lo que no está);
y verificación de citas posterior. Verificado en el golden set con casos adversariales.

**Manipulación del corpus.** → Versionado en git, revisable en diff. Validación al arranque
que rechaza duplicados, hechos incompletos o PII.

### R — Repudio

→ Log estructurado por petición con identificador, modelo, tokens y latencia. La respuesta
incluye en `metadata` los hechos recuperados con su similitud y las citas emitidas: toda
afirmación es rastreable hasta un `id` versionado.

### I — Divulgación de información

**El agente revela datos personales.** → Los datos de contacto **no existen en el corpus**;
no puede revelar lo que no tiene. Adicionalmente, detección determinista de preguntas de
contacto con respuesta fija. Verificación automática de ausencia de PII en CI.

**Fuga de secretos.** → `.env` excluido del control de versiones; `.env.example` documenta
nombres, nunca valores; las claves se inyectan como secretos de Container Apps y **no
viajan en la imagen**, que es pública.

**Los datos enviados al proveedor.** → El nivel gratuito de Google AI Studio puede usar los
datos para mejorar el producto. Aceptable aquí porque **solo se envían hechos públicos del
CV y la pregunta del usuario**. En un despliegue bancario esto exigiría un tier con
aislamiento contractual de datos, y es un requisito bloqueante, no una preferencia.

### D — Denegación de servicio

**Agotamiento de cuota por abuso.** → La autenticación limita el acceso. La compuerta de
abstención impide que preguntas fuera de dominio consuman tokens: **el ataque más barato
—inundar con preguntas irrelevantes— cuesta cero al defensor**.
*Riesgo residual:* no hay limitación de tasa por cliente. En producción, rate limiting en
la puerta de entrada.

**Latencia del proveedor.** → Timeout de 12 s por llamada y presupuesto total de 25 s.
Ante un proveedor degradado se devuelve un error tipado, no un cuelgue.

### E — Elevación de privilegios

→ El contenedor corre como usuario sin privilegios (UID 10001). Sin ejecución de código
arbitrario, sin acceso a base de datos, sin herramientas con efectos secundarios: el
agente solo lee un corpus estático y llama a una API.

## Riesgos aceptados conscientemente

| Riesgo | Motivo | Mitigación en producción |
|---|---|---|
| Token estático sin rotación | Plazo de entrega | OAuth 2.0 / Entra ID |
| Sin rate limiting por cliente | Fuera del alcance del reto | API Management |
| Proveedor en nivel gratuito | Coste cero para la evaluación | Tier con aislamiento de datos |
| Imagen pública en GHCR | No contiene secretos | Registro privado interno |
