# ADR-009 — Las fuentes se muestran como enlaces legibles, no como identificadores

- **Estado:** Aceptado
- **Fecha:** 2026-08-22

## Contexto

Al probar el agente registrado en la plataforma del reto, la primera respuesta fue:

> «Actualmente, Alejandro Rau Lázaro se desempeña como Desarrollador Full Stack y Móvil
> en GlobalConnect, en Cancún, Quintana Roo **[exp.globalconnect.role]**. Ocupa este
> puesto desde mayo de 2025 **[exp.globalconnect.role]**.»

El contenido es correcto y trazable. La presentación tiene dos problemas:

1. `exp.globalconnect.role` es un **identificador interno** filtrándose a la interfaz.
   No significa nada para quien lee.
2. El modelo repite la misma cita en frases consecutivas, lo que ensucia la lectura.

El reto pide explícitamente que el agente responda «de forma **clara**, coherente y útil»
y que se entienda **de dónde viene la información**. La versión anterior cumplía lo
segundo a costa de lo primero.

## Decisión

**Separar la trazabilidad interna de su presentación.**

- Las citas `[id]` se siguen exigiendo al modelo y **se siguen verificando** contra los
  hechos recuperados. Ese mecanismo no cambia: es el cuarto control anti-alucinación.
- Antes de responder, se **eliminan del cuerpo** y se consolidan en una línea final.
- Cada fuente se muestra con una **etiqueta legible** construida desde los metadatos:
  `Experiencia · GlobalConnect (may 2025 – actual)`.
- La etiqueta **enlaza a las líneas exactas** del hecho en `data/corpus.yaml` dentro del
  repositorio público: `…/corpus.yaml#L38-L49`.
- `metadata.citations` conserva los identificadores para consumo por máquina.

Resultado:

> Actualmente, Alejandro trabaja como Desarrollador Full Stack y Móvil en GlobalConnect,
> en Cancún, Quintana Roo. Desempeña este puesto desde mayo de 2025.
>
> Fuentes: [Experiencia · GlobalConnect (may 2025 – actual)](…/corpus.yaml#L38-L49)

## Alternativas descartadas

| Alternativa | Por qué se descarta |
|---|---|
| Dejar los identificadores en el cuerpo | Filtra implementación al usuario y dificulta la lectura |
| Eliminar las citas por completo | Se pierde la evidencia visible del grounding, que es el argumento central del diseño |
| Enlazar al PDF del CV | El PDF no tiene anclas por sección; el enlace no podría señalar el dato exacto |
| Numerar las fuentes `[1] [2]` | Legible, pero obliga a bajar a un pie para saber qué es cada una; la etiqueta ya lo dice |

## Consecuencias

- El usuario puede **verificar cualquier afirmación con un clic**, sobre el dato original
  versionado en git. La trazabilidad pasa de ser una promesa a ser navegable.
- Los números de línea se calculan al cargar el corpus, no se escriben a mano: reordenar
  el YAML no rompe los enlaces. Verificado con un test que comprueba que la línea
  registrada contiene el identificador esperado.
- Varias citas de la misma sección se muestran una sola vez.
- La abstención no lleva pie de fuentes, porque no hay nada que citar.
- Si el cliente no renderiza Markdown, la variable `SOURCES_AS_LINKS=false` lista las
  etiquetas sin hipervínculo. La información sigue siendo legible en ambos casos.

## Principio general

**La trazabilidad y su presentación son problemas distintos.** Un sistema auditable
necesita identificadores estables; una persona necesita nombres y enlaces. Resolver ambos
con el mismo artefacto degrada los dos.
