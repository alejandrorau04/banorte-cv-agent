/* Diagramas en SVG inline: se adaptan al tema, escalan sin perder nitidez y no
   añaden ninguna dependencia. */

export function FlujoRAG() {
  const pasos = [
    { x: 20,  t: "Pregunta",   s: "" },
    { x: 150, t: "Idioma",     s: "0 tokens" },
    { x: 280, t: "¿Contacto?", s: "0 tokens" },
    { x: 420, t: "Recuperar",  s: "coseno + IDF" },
    { x: 560, t: "¿Evidencia ≥ 0.62?", s: "" },
    { x: 720, t: "Generar",    s: "solo hechos" },
    { x: 850, t: "Verificar",  s: "citas" },
  ];
  return (
    <svg viewBox="0 0 980 200" role="img" aria-labelledby="rag-t" className="diagrama">
      <title id="rag-t">
        Flujo del pipeline: pregunta, detección de idioma, política de contacto,
        recuperación híbrida, compuerta de evidencia, generación y verificación de citas.
        Las ramas de contacto y de evidencia insuficiente devuelven la respuesta sin
        invocar al modelo, con coste cero.
      </title>
      {pasos.map((p, i) => (
        <g key={i}>
          <rect x={p.x} y={70} width={110} height={52} rx="3"
                className={i >= 5 ? "d-caja d-caja--activa" : "d-caja"} />
          <text x={p.x + 55} y={p.s ? 92 : 100} className="d-texto">{p.t}</text>
          {p.s && <text x={p.x + 55} y={108} className="d-nota">{p.s}</text>}
          {i < pasos.length - 1 && (
            <path d={`M${p.x + 110} 96 L${pasos[i + 1].x - 4} 96`} className="d-linea" markerEnd="url(#f)" />
          )}
        </g>
      ))}
      <path d="M335 70 L335 34 L900 34" className="d-linea d-linea--corta" markerEnd="url(#f)" />
      <text x={610} y={26} className="d-nota d-nota--corta">política de privacidad · 0 tokens</text>
      <path d="M615 122 L615 160 L900 160" className="d-linea d-linea--corta" markerEnd="url(#f)" />
      <text x={745} y={176} className="d-nota d-nota--corta">abstención · 0 tokens · &lt;500 ms</text>
      <rect x={900} y={70} width={62} height={52} rx="3" className="d-caja d-caja--fin" />
      <text x={931} y={100} className="d-texto">Respuesta</text>
      <defs>
        <marker id="f" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="7" markerHeight="7" orient="auto">
          <path d="M0 0 L8 4 L0 8 z" className="d-punta" />
        </marker>
      </defs>
    </svg>
  );
}

export function Capas() {
  const capas = [
    { y: 16,  t: "Transporte · app/api/",   s: "Open Responses · SSE · auth · errores tipados" },
    { y: 96,  t: "Núcleo · app/core/",      s: "recuperar → decidir → generar → verificar" },
    { y: 176, t: "Adaptadores · app/adapters/", s: "puertos LLM y Embedder" },
  ];
  return (
    <svg viewBox="0 0 620 290" role="img" aria-labelledby="capas-t" className="diagrama">
      <title id="capas-t">
        Tres capas concéntricas: transporte, núcleo y adaptadores. Las dependencias
        apuntan hacia el núcleo, que no conoce ni HTTP ni el proveedor de modelo.
      </title>
      {capas.map((c, i) => (
        <g key={i}>
          <rect x={40} y={c.y} width={540} height={64} rx="3"
                className={i === 1 ? "d-caja d-caja--activa" : "d-caja"} />
          <text x={60} y={c.y + 27} className="d-texto d-texto--izq">{c.t}</text>
          <text x={60} y={c.y + 46} className="d-nota d-nota--izq">{c.s}</text>
        </g>
      ))}
      <path d="M300 80 L300 92" className="d-linea" markerEnd="url(#f2)" />
      <path d="M300 160 L300 172" className="d-linea" markerEnd="url(#f2)" />
      <text x={310} y={268} className="d-nota d-nota--izq">las dependencias apuntan hacia adentro</text>
      <defs>
        <marker id="f2" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="7" markerHeight="7" orient="auto">
          <path d="M0 0 L8 4 L0 8 z" className="d-punta" />
        </marker>
      </defs>
    </svg>
  );
}

export function Entrega() {
  const pasos = ["git push", "Calidad", "Imagen · GHCR", "Azure", "Verificación"];
  return (
    <svg viewBox="0 0 940 96" role="img" aria-labelledby="cd-t" className="diagrama">
      <title id="cd-t">
        Cadena de entrega continua: un push dispara la puerta de calidad, la
        construcción y publicación de la imagen, el despliegue en Azure y la
        verificación del estado real del contenedor.
      </title>
      {pasos.map((p, i) => (
        <g key={i}>
          <rect x={i * 190} y={24} width={162} height={48} rx="3"
                className={i === 1 || i === 4 ? "d-caja d-caja--activa" : "d-caja"} />
          <text x={i * 190 + 81} y={53} className="d-texto">{p}</text>
          {i < pasos.length - 1 && (
            <path d={`M${i * 190 + 162} 48 L${(i + 1) * 190 - 4} 48`} className="d-linea" markerEnd="url(#f3)" />
          )}
        </g>
      ))}
      <defs>
        <marker id="f3" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="7" markerHeight="7" orient="auto">
          <path d="M0 0 L8 4 L0 8 z" className="d-punta" />
        </marker>
      </defs>
    </svg>
  );
}
