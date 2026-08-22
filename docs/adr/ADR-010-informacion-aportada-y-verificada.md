# ADR-010 — Información que no está en el CV: verificación antes de incorporarla

- **Estado:** Aceptado
- **Fecha:** 2026-08-22

## Contexto

Al probar el agente aparecieron dos clases de pregunta frecuentes que el CV **no** puede
responder:

1. **Sobre las empresas.** «¿A qué se dedica Webmaps?», «¿tienen sitio web?». El CV
   nombra las empresas pero no las describe.
2. **Sobre la situación profesional actual.** «¿Está disponible para CDMX?», «¿qué busca
   en su próximo rol?», «¿expectativa salarial?». Es lo que un reclutador pregunta
   primero, y no aparece en ningún CV.

La segunda es especialmente relevante: la vacante es híbrida en Ciudad de México y el
titular reside en Playa del Carmen. Que el agente no resolviera esa duda lo dejaba corto
para su propósito declarado, «ayudar a otras personas a conocer tu perfil».

## La tentación y por qué se descarta

La solución aparente es dar al agente acceso a la web en tiempo de respuesta —*tool use*,
que además la vacante menciona—. Se descarta por tres motivos:

1. **Rompe el grounding.** El contenido de una web no está verificado. El agente pasaría
   a afirmar cosas que nadie comprobó: exactamente el fallo que todo el diseño previene.
2. **No es fiable.** Se intentó consultar los siete sitios: **cuatro fallaron** — dos con
   HTTP 403, uno sin contenido descriptivo y uno con error de certificado. Más de la
   mitad de las consultas fallarían o se colgarían durante una evaluación.
3. **Añade latencia** en la ruta crítica y un punto de fallo externo.

## Decisión

**La investigación ocurre en tiempo de construcción y con verificación humana; en runtime
solo se sirve lo ya verificado.**

- **Descripciones obtenidas del sitio oficial** (verificadas el 2026-08-22):
  GlobalConnect, Alldora, Guval Foods.
- **Descripciones aportadas por el titular del CV**, cuyos sitios rechazan peticiones
  automatizadas: Alcazar & Compañía, WESCO, Johnson Health Technologies, SUMMA Woodbridge.
- **Webmaps queda sin descripción**: no se pudo verificar y no se inventa. El agente
  responde honestamente que no dispone de esa información.
- **Situación profesional**: disponibilidad, objetivo, motivación por la IA y por el
  sector financiero, redactadas y **aprobadas por el titular**.

Todo entra al corpus como hechos normales: citables, enlazables y versionados.

## Dos decisiones sobre contenido sensible

**Nivel de inglés.** El CV declara «inglés intermedio (conversacional)». Se sustituye por
una formulación precisa —avanzado en lectura y escritura técnica, conversacional en
desarrollo— que **no contradice el documento original** y describe mejor la capacidad
real. Declararlo simplemente «avanzado» habría creado una contradicción con el CV
publicado en el mismo repositorio, y un riesgo evidente si la entrevista se realiza en
inglés.

**Expectativa salarial: no se incluye la cifra.** El endpoint es público y el corpus vive
en un repositorio abierto, donde el historial de git es permanente. Publicar una cifra
expone un dato de negociación a cualquiera y no puede retirarse después. El agente
responde con la política —se trata en el proceso de selección—, coherente con el
tratamiento de datos de contacto del ADR-006.

**Contenedores, Azure y Kubernetes.** El titular pidió añadir experiencia en Azure y
Kubernetes, ausentes de ambas versiones del CV, planteándolo como «podría decir que tengo
más de 4 años». Se declinó redactar esa afirmación y se acordó una formulación precisa del
alcance real: producción con Docker y CI/CD, arquitectura cloud profunda en AWS, despliegue
propio en Azure Container Apps con registro de imágenes y secretos gestionados, y
Kubernetes a nivel conceptual sin haber operado un clúster.

Razones: (a) declarar años de una tecnología que la vacante pide explícitamente, horas
antes de entregar, es un patrón detectable; (b) la afirmación genérica invita a una
repregunta técnica que, si no se sostiene, arrastra la credibilidad del resto del CV; y
(c) contradiría el principio que sostiene todo el sistema. La formulación acordada
describe con exactitud dónde está el candidato, lo cual en una entrevista técnica pesa
más que un número.

**Este proyecto como hecho del corpus.** Se añade `project.cv_agent`: el propio agente es
la experiencia más reciente en Azure, Python y RAG, y la única enteramente verificable
—el código es público—. El agente puede describir cómo está construido.

## Consecuencias

- El corpus pasa de 46 a 59 hechos.
- La procedencia de cada dato queda anotada en el propio YAML: verificado en el sitio
  oficial o aportado por el titular.
- La navegación web en runtime queda registrada en el backlog, con la medición de
  fiabilidad (3 de 7 sitios accesibles) como justificación de por qué no se implementó.
