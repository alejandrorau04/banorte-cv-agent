# Arquitectura

Modelo C4: se recorre el sistema en tres niveles de zoom, de fuera hacia dentro.
Los diagramas están escritos en Mermaid dentro del propio Markdown — viven en git, se
revisan en el diff y no pueden desactualizarse respecto a la documentación.

---

## Nivel 1 — Contexto

Quién usa el sistema y con qué sistemas externos habla.

```mermaid
flowchart TB
    R["Persona<br/>Reclutador o evaluador"]
    P["Plataforma Reto IA Banorte<br/><i>cliente Open Responses</i>"]
    S["<b>Agente de CV</b><br/>Responde sobre la trayectoria<br/>profesional con grounding estricto"]
    G["Google AI Studio<br/><i>generación y embeddings</i>"]

    R -->|"conversa"| P
    P -->|"POST /v1/responses<br/>HTTPS + Bearer"| S
    S -->|"HTTPS"| G

    style S fill:#ddf4ff,stroke:#0969da,stroke-width:2px
    style G fill:#fff8c5,stroke:#9a6700
```

**Frontera del sistema:** solo el bloque azul es nuestro. La interfaz conversacional la
pone la plataforma del reto; el modelo lo pone Google. Nuestra responsabilidad es el
servicio intermedio y la veracidad de lo que responde.

---

## Nivel 2 — Contenedores

Unidades desplegables y cómo se comunican.

```mermaid
flowchart TB
    P["Plataforma del reto"]

    subgraph AZ["Azure Container Apps · centralus"]
      API["<b>cv-agent</b><br/>Python 3.12 · FastAPI · uvicorn<br/>1 réplica mínima, 3 máxima<br/>0.5 vCPU · 1 GiB"]
    end

    subgraph IM["Imagen de contenedor"]
      C[("corpus.yaml<br/>61 hechos es/en")]
      IX[("corpus.index.json<br/>122 vectores · 768 dim")]
    end

    GH["GitHub Actions<br/><i>tests + build</i>"]
    GHCR[("GHCR<br/>imagen pública")]
    G["Google AI Studio"]

    P -->|"HTTPS · Bearer"| API
    API -.->|"lee al arrancar"| C
    API -.->|"lee al arrancar"| IX
    API -->|"HTTPS"| G
    GH -->|"push"| GHCR
    GHCR -->|"pull"| AZ

    style API fill:#ddf4ff,stroke:#0969da,stroke-width:2px
    style AZ fill:#f6f8fa,stroke:#57606a
```

Decisiones visibles en este nivel:

- **Corpus e índice viajan dentro de la imagen.** El contenedor arranca sin llamar a
  ningún servicio externo: elimina dependencias en el arranque en frío (ADR-004).
- **Sin base de datos.** El estado es de solo lectura y cabe en memoria (ADR-004).
- **La imagen se construye en GitHub Actions**, no en Azure: ACR Tasks está bloqueado
  en suscripciones nuevas (ADR-007).
- **Réplica mínima 1** para evitar arranque en frío durante la evaluación, dado que el
  timeout del cliente no está documentado.

---

## Nivel 3 — Componentes

Interior del servicio. **Las dependencias apuntan hacia adentro**: el núcleo no conoce
ni HTTP ni el proveedor de LLM.

```mermaid
flowchart TB
    subgraph T["Transporte · app/api/"]
      M["main.py<br/>rutas, auth, errores tipados"]
      OR["openresponses.py<br/>traducción del contrato<br/>31 campos obligatorios"]
      SSE["sse.py<br/>24 tipos de evento<br/>sequence_number"]
    end

    subgraph N["Núcleo · app/core/"]
      AG["agent.py<br/>recuperar → decidir<br/>→ generar → verificar"]
      RE["retrieval.py<br/>híbrido: coseno + IDF<br/>detección de idioma"]
      CO["corpus.py<br/>carga, valida, deriva<br/>línea de tiempo"]
      PR["prompts.py<br/>reglas de grounding"]
    end

    subgraph A["Adaptadores · app/adapters/"]
      B["base.py<br/><i>puertos: LLM, Embedder</i>"]
      GE["gemini.py<br/>respaldo entre modelos<br/>presupuesto de tiempo"]
    end

    M --> OR
    M --> SSE
    M --> AG
    AG --> RE
    AG --> PR
    RE --> CO
    AG -->|"depende de la<br/>interfaz, no de Gemini"| B
    GE -.->|"implementa"| B

    style N fill:#ddf4ff,stroke:#0969da,stroke-width:2px
    style A fill:#fff8c5,stroke:#9a6700
    style T fill:#f6f8fa,stroke:#57606a
```

| Capa | Responsabilidad | Desconoce |
|---|---|---|
| **Transporte** | Contrato Open Responses, autenticación, SSE, errores | Qué es un CV; qué modelo se usa |
| **Núcleo** | Recuperación, grounding, abstención, verificación de citas | HTTP, proveedores, formatos de transporte |
| **Adaptadores** | Implementan los puertos `LLM` y `Embedder` | Lógica de negocio |

**Por qué importa esta separación**, en términos concretos y verificables:

- El núcleo se prueba **sin levantar servidor y sin red**: 122 tests en 0,3 s.
- Migrar a Azure OpenAI es implementar dos métodos y cambiar una variable de entorno.
  No se toca una línea del núcleo.
- Cambiar el transporte (WebSocket, gRPC, una cola) no afecta a la lógica del agente.

---

## Flujo de una petición

```mermaid
sequenceDiagram
    participant P as Plataforma
    participant M as main.py
    participant A as agent.py
    participant R as retrieval.py
    participant G as Gemini

    P->>M: POST /v1/responses
    M->>M: verificar Bearer
    M->>A: answer(pregunta)
    A->>A: detectar idioma (0 tokens)

    alt pide datos de contacto
        A-->>M: política de privacidad · 0 tokens
    else
        A->>R: buscar(pregunta, idioma)
        R->>G: embedding de la consulta
        G-->>R: vector 768d
        R->>R: coseno + IDF sobre 122 vectores
        R-->>A: top-6 con similitud cruda

        alt similitud máxima < 0.62
            A-->>M: abstención · 0 tokens
        else
            A->>G: generar (solo hechos recuperados)
            G-->>A: texto con citas
            A->>A: verificar citas contra lo recuperado
            A-->>M: respuesta + citas verificadas
        end
    end

    M->>M: construir los 31 campos
    M-->>P: 200 · ResponseResource
```

Las dos ramas cortas —contacto y abstención— **no llegan al modelo**: cuestan cero
tokens y responden en menos de medio segundo. Cubren el 25 % del golden set.

---

## Flujo de streaming

```mermaid
sequenceDiagram
    participant P as Plataforma
    participant M as main.py
    participant A as agent.py
    participant S as sse.py

    P->>M: POST /v1/responses {"stream": true}
    M->>A: answer(pregunta)
    Note over A: se genera y VERIFICA<br/>la respuesta completa
    A-->>M: respuesta con citas verificadas
    M->>S: stream_answer(respuesta)
    S-->>P: response.created (seq 0)
    S-->>P: response.in_progress (seq 1)
    S-->>P: response.output_item.added (seq 2)
    S-->>P: response.content_part.added (seq 3)
    loop por cada fragmento
        S-->>P: response.output_text.delta
    end
    S-->>P: response.output_text.done
    S-->>P: response.content_part.done
    S-->>P: response.output_item.done
    S-->>P: response.completed
    S-->>P: [DONE]
```

**Se emite texto ya verificado, no los tokens crudos del modelo.** La verificación de
citas necesita el texto completo; retransmitir en directo significaría emitir contenido
sin verificar, y una cita inventada llegaría al usuario antes de poder eliminarla.
Grounding estricto y streaming crudo son incompatibles: se elige la veracidad, y se
asume el coste de que el primer carácter tarde más.

---

## Despliegue

```mermaid
flowchart LR
    D["git push a main"] --> T["Actions: 122 tests<br/>+ conformidad OpenAPI<br/>+ ausencia de PII"]
    T -->|"verde"| B["docker build"]
    B --> G[("GHCR<br/>tag = SHA del commit")]
    G --> A["az containerapp update"]
    A --> R["nueva revisión<br/>tráfico 100 %"]

    style T fill:#dafbe1,stroke:#1a7f37
```

La imagen se referencia por **SHA del commit**, no por `latest`: cada revisión desplegada
es trazable hasta el código exacto que la originó, y una reversión es reactivar la
revisión anterior.

---

## Referencias

| Documento | Contenido |
|---|---|
| [ADR-001](adr/ADR-001-contrato-open-responses.md) | Contrato Open Responses y su asimetría |
| [ADR-003](adr/ADR-003-estrategia-anti-alucinacion.md) | Los cuatro controles anti-alucinación |
| [ADR-004](adr/ADR-004-recuperacion-sin-base-vectorial.md) | Por qué no hay base vectorial |
| [ADR-008](adr/ADR-008-consultas-de-agregacion.md) | Consultas de agregación con metadatos |
| [RAG.md](RAG.md) | El pipeline de recuperación en detalle |
| [RUNBOOK.md](RUNBOOK.md) | Operación y diagnóstico |
| [MODELO-AMENAZAS.md](MODELO-AMENAZAS.md) | STRIDE |
