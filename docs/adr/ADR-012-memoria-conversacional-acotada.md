# ADR-012 — Memoria conversacional acotada: un intercambio, no la transcripción

- **Estado:** Aceptado
- **Fecha:** 2026-08-22

## Contexto

La plataforma reenvía la transcripción completa en cada petición (modo «Reproducir
transcripción (sin estado)», ADR-001). La primera implementación tomaba **solo el último
mensaje de usuario** e ignoraba el resto.

Eso ahorraba muchos tokens, pero rompía la conversación. Verificado contra producción:

> **U:** ¿Dónde trabaja actualmente?
> **A:** En GlobalConnect, desde mayo de 2025.
> **U:** ¿Y qué hace ahí?
> **A:** *No encuentro información en el CV para responder eso.* ← **abstención**

«Ahí» no significa nada aislado. El reto pide que el agente responda «de forma clara,
coherente y útil»: una conversación que muere al segundo turno no lo cumple.

## Las dos soluciones malas

**Enviar la transcripción completa al modelo.** Es lo que hace la mayoría, y el coste
crece de forma **cuadrática**: cada turno reenvía todos los anteriores. En una
conversación de veinte turnos el prompt es enorme y el coste se dispara. Es la fuga de
tokens más común en agentes conversacionales.

**Reescribir la pregunta con el LLM** (*query rewriting*). Resuelve las referencias, pero
añade **una llamada al modelo por turno** — exactamente lo que se busca evitar.

## Decisión

**Se conserva un solo intercambio, y se usa de dos formas distintas según su coste.**

### Para recuperar: expansión de consulta, coste cero de LLM

Si la pregunta parece depender del contexto —corta, o con marcas como «ahí», «eso»,
«y qué», «cuéntame más», «tell me more»— la consulta de **búsqueda** se forma
concatenando la pregunta anterior con la actual.

Solo afecta al texto que se embebe. **No cuesta un token de generación.**

### Para generar: turno anterior recortado, solo cuando hace falta

Cuando se detecta un seguimiento, se añade al prompt un bloque con la pregunta previa y
la respuesta previa **recortada a 260 caracteres**, con instrucción explícita de usarlo
solo para resolver referencias.

Se elimina el pie de «Fuentes» de la respuesta previa: reenviar enlaces no aporta
contexto y gasta tokens.

## Coste medido

Conversación de seis turnos con cuatro seguimientos encadenados:

| | Antes | Después |
|---|---|---|
| Seguimientos entendidos | 0 | **4 / 4** |
| Tokens por turno | ~600 | **942** |
| Crecimiento con la longitud | — | **ninguno** |

Lo importante no es el promedio sino la última fila: **el coste por turno es constante**.
Con transcripción completa, el turno veinte costaría un orden de magnitud más.

## Consecuencias

- El agente resuelve referencias a un turno de distancia, no más. «¿Y lo que dijiste al
  principio?» no funciona. Es un límite consciente: cubrir más exigiría enviar más
  contexto en cada petición.
- La detección de seguimiento es heurística. Un falso positivo añade ~150 tokens; un
  falso negativo devuelve el comportamiento anterior. Ambos son degradaciones suaves.
- El servicio sigue siendo **sin estado**: toda la memoria viene en la petición. Escala
  horizontalmente sin sincronización.
