/** Contenido de la presentación.
 *  Todas las cifras proceden de ejecuciones reales documentadas en el
 *  repositorio; ninguna es estimada. */

export const REPO = "https://github.com/alejandrorau04/banorte-cv-agent";

export const SECCIONES = [
  { id: "portada",       titulo: "Portada" },
  { id: "problema",      titulo: "El problema" },
  { id: "solucion",      titulo: "Cómo lo resuelvo" },
  { id: "arquitectura",  titulo: "Arquitectura" },
  { id: "decisiones",    titulo: "Criterio" },
  { id: "rag",           titulo: "El pipeline RAG" },
  { id: "modelos",       titulo: "Modelos e intercambio" },
  { id: "tokens",        titulo: "Coste y latencia" },
  { id: "pruebas",       titulo: "Cómo sé que funciona" },
  { id: "infra",         titulo: "Infraestructura y CI/CD" },
  { id: "seguridad",     titulo: "Seguridad" },
  { id: "demo",          titulo: "Pruébalo" },
  { id: "limites",       titulo: "Límites y siguiente paso" },
] as const;

export const CIFRAS = {
  goldenSet:    { cifra: "32/32", pie: "Golden set. 12 casos miden lo que NO debe responder" },
  consistencia: { cifra: "26/26", pie: "Formulaciones distintas de la misma intención" },
  robustez:     { cifra: "28/28", pie: "Entradas hostiles sin ningún error 5xx" },
  carga:        { cifra: "30/30", pie: "Peticiones correctas con concurrencia 10" },
  tests:        { cifra: "102",   pie: "Tests automatizados, sin red ni credenciales" },
  sinLLM:       { cifra: "25", sufijo: "%", pie: "De las consultas no invocan al modelo" },
  p50:          { cifra: "1.2", sufijo: "s", pie: "Latencia mediana" },
  tokens:       { cifra: "660",  pie: "Tokens de media por consulta" },
};

export const CONTROLES = [
  {
    n: "01",
    titulo: "Grounding cerrado",
    texto: "El prompt contiene únicamente hechos recuperados del corpus versionado. Sin CV completo en contexto y sin conocimiento externo autorizado.",
  },
  {
    n: "02",
    titulo: "Compuerta de evidencia",
    texto: "Si la similitud máxima no supera el umbral, se devuelve una abstención sin invocar al modelo. Un modelo que nunca se invoca no puede alucinar.",
  },
  {
    n: "03",
    titulo: "Verificación de citas",
    texto: "Toda cita emitida se contrasta contra los hechos recuperados. Las inventadas se eliminan del texto antes de responder.",
  },
  {
    n: "04",
    titulo: "Política determinista",
    texto: "Las peticiones de datos de contacto se resuelven sin recuperación y sin modelo. El corpus no contiene esos datos: no puede revelarlos.",
  },
];

export const CALIBRACION = [
  { conjunto: "Preguntas en dominio",     n: 8, min: "0.6633", max: "0.7962" },
  { conjunto: "Preguntas fuera de dominio", n: 7, min: "0.5228", max: "0.5899" },
];

export const CAPAS = [
  {
    capa: "Transporte",
    ruta: "app/api/",
    hace: "Contrato Open Responses, autenticación, streaming SSE, errores tipados",
    ignora: "Qué es un CV · qué modelo se usa",
  },
  {
    capa: "Núcleo",
    ruta: "app/core/",
    hace: "Recuperación, grounding, abstención, verificación de citas",
    ignora: "HTTP · proveedores · formatos de transporte",
  },
  {
    capa: "Adaptadores",
    ruta: "app/adapters/",
    hace: "Implementan los puertos LLM y Embedder",
    ignora: "Lógica de negocio",
  },
];

export const DECISIONES = [
  {
    titulo: "Sin base de datos vectorial",
    texto: "122 vectores no justifican desplegar Qdrant ni pgvector: añadirían un servicio que operar, latencia de red y un punto de fallo, sin ganancia medible. La recuperación vive tras una interfaz: sustituirla es implementar una clase.",
    remate: "Saber cuándo no usar una tecnología también es criterio técnico.",
  },
  {
    titulo: "Streaming de texto verificado",
    texto: "La verificación de citas necesita el texto completo. Retransmitir los tokens crudos del modelo significaría emitir contenido sin verificar, y una cita inventada llegaría al usuario antes de poder eliminarla.",
    remate: "Grounding estricto y streaming crudo son incompatibles. Elegí la veracidad.",
  },
  {
    titulo: "Datos estructurados para preguntas estructuradas",
    texto: "«¿Cuál fue su puesto anterior?» no se responde con búsqueda por similitud: requiere el corpus completo. La trayectoria cronológica se deriva por código de los metadatos.",
    remate: "El orden lo calcula sorted(), no el modelo.",
  },
  {
    titulo: "Modelo pequeño, recuperación buena",
    texto: "Con grounding estricto la tarea del modelo no es razonar ni recordar, sino redactar a partir de hechos ya verificados. Medido: 1,1 s frente a 15,5 s, con calidad equivalente.",
    remate: "Una buena recuperación permite usar un modelo más barato.",
  },
];

export const PIPELINE = [
  { paso: "Calidad",      detalle: "102 tests · conformidad con el OpenAPI oficial · corpus sin PII · cobertura del índice" },
  { paso: "Imagen",       detalle: "Docker build y publicación en GHCR, etiquetada con el SHA del commit" },
  { paso: "Despliegue",   detalle: "Azure Container Apps mediante service principal acotado al grupo de recursos" },
  { paso: "Verificación", detalle: "No basta un HTTP 200: se comprueba que el contenedor no esté degradado" },
];

export const SEGURIDAD = [
  { control: "Autenticación por token en cada petición",           detalle: "401 tipado sin credencial válida" },
  { control: "Secretos gestionados por la plataforma",             detalle: "Nunca en la imagen ni en el repositorio" },
  { control: "Mínimo privilegio en el despliegue",                 detalle: "Service principal acotado al grupo de recursos" },
  { control: "Contenedor sin privilegios",                         detalle: "UID 10001 · imagen slim · 6 dependencias" },
  { control: "Defensa contra inyección de prompt",                 detalle: "Probada con casos adversariales en el golden set" },
  { control: "Sin datos personales en el corpus",                  detalle: "Verificado automáticamente en cada build" },
  { control: "Logs sin contenido de conversaciones",               detalle: "Identificador, idioma, modelo, tokens y latencia" },
  { control: "Trazabilidad de cada afirmación",                    detalle: "Hechos recuperados, similitudes y citas por respuesta" },
];

export const LIMITES = [
  "Sin pruebas de carga sostenida: probado hasta concurrencia 10.",
  "La verificación comprueba que la cita exista, no que respalde semánticamente la afirmación.",
  "Umbral calibrado con 15–18 preguntas por modelo: suficiente para detectar regresiones, no para afirmar robustez estadística.",
  "Una sola región de Azure, sin replicación.",
];

export const PRODUCCION = [
  { area: "Proveedor de LLM", ahora: "Nivel gratuito", produccion: "Tier con aislamiento contractual de datos. Bloqueante" },
  { area: "Autenticación",     ahora: "Token estático", produccion: "OAuth 2.0 / Entra ID con tokens de vida corta" },
  { area: "Rate limiting",     ahora: "Limitador interno", produccion: "API Management en la puerta de entrada" },
  { area: "Observabilidad",    ahora: "Logs y metadata", produccion: "Trazas distribuidas y alertas centralizadas" },
];
