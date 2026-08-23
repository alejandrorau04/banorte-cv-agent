/* Diagramas como protagonistas: grandes, adaptados al tema, sin dependencias. */

const punta = (id: string) => (
  <defs>
    <marker id={id} viewBox="0 0 8 8" refX="7" refY="4" markerWidth="6" markerHeight="6" orient="auto">
      <path d="M0 0 L8 4 L0 8 z" className="dg-p" />
    </marker>
  </defs>
);

export function FlujoRAG() {
  const p = [
    { x: 0,   t: "Pregunta" },
    { x: 148, t: "Idioma",     s: "determinista" },
    { x: 296, t: "Recuperar",  s: "coseno + IDF" },
    { x: 444, t: "Compuerta",  s: "sim ≥ 0.62" },
    { x: 592, t: "Generar",    s: "solo hechos" },
    { x: 740, t: "Verificar",  s: "citas" },
  ];
  return (
    <svg viewBox="0 0 900 210" role="img" aria-label="Recorrido de una pregunta: detección de idioma, recuperación híbrida, compuerta de evidencia, generación restringida a los hechos recuperados y verificación de citas. Dos caminos alternativos evitan el modelo por completo: las peticiones de datos de contacto y las preguntas sin evidencia suficiente, ambas con coste cero." className="dg">
      {p.map((n, i) => (
        <g key={i}>
          <rect x={n.x} y={74} width={128} height={54} rx="4"
                className={i >= 4 ? "dg-caja dg-caja--on" : "dg-caja"} />
          <text x={n.x + 64} y={n.s ? 95 : 101} className="dg-t">{n.t}</text>
          {n.s && <text x={n.x + 64} y={112} className="dg-s">{n.s}</text>}
          {i < p.length - 1 && (
            <path d={`M${n.x + 128} 101 L${p[i + 1].x - 5} 101`} className="dg-l" markerEnd="url(#a)" />
          )}
        </g>
      ))}
      <rect x={868} y={74} width={32} height={54} rx="4" className="dg-caja dg-caja--on" />
      <path d="M508 74 L508 30 L884 30 L884 70" className="dg-l dg-l--v" markerEnd="url(#a)" />
      <text x={696} y={20} className="dg-s dg-s--v">sin evidencia → abstención · 0 tokens · &lt;500 ms</text>
      <path d="M64 128 L64 172 L884 172 L884 132" className="dg-l dg-l--v" markerEnd="url(#a)" />
      <text x={474} y={190} className="dg-s dg-s--v">petición de contacto → política determinista · 0 tokens</text>
      {punta("a")}
    </svg>
  );
}

export function Capas() {
  const c = [
    { y: 0,   t: "Transporte",  r: "app/api/",      s: "Open Responses · SSE · auth · errores tipados" },
    { y: 78,  t: "Núcleo",      r: "app/core/",     s: "recuperar → decidir → generar → verificar" },
    { y: 156, t: "Adaptadores", r: "app/adapters/", s: "puertos LLM y Embedder" },
  ];
  return (
    <svg viewBox="0 0 560 250" role="img" aria-label="Tres capas: transporte, núcleo y adaptadores. Las dependencias apuntan hacia el núcleo, que no conoce ni HTTP ni el proveedor de modelo." className="dg">
      {c.map((n, i) => (
        <g key={i}>
          <rect x={0} y={n.y} width={470} height={62} rx="4"
                className={i === 1 ? "dg-caja dg-caja--on" : "dg-caja"} />
          <text x={18} y={n.y + 24} className="dg-t dg-t--i">{n.t}</text>
          <text x={18} y={n.y + 42} className="dg-s dg-s--i">{n.r} — {n.s}</text>
        </g>
      ))}
      <path d="M500 20 L520 20 L520 218 L500 218" className="dg-l" />
      <path d="M520 108 L482 108" className="dg-l" markerEnd="url(#b)" />
      <text x={534} y={119} className="dg-s dg-s--i" transform="rotate(-90 534 119)">
        dependencias hacia adentro
      </text>
      {punta("b")}
    </svg>
  );
}

export function Entrega() {
  const p = ["git push", "Calidad", "Imagen", "Azure", "Verificación"];
  const s = ["", "122 tests", "GHCR · SHA", "Container Apps", "estado real"];
  return (
    <svg viewBox="0 0 900 96" role="img" aria-label="Cadena de entrega continua: un push dispara la puerta de calidad, la construcción y publicación de la imagen, el despliegue en Azure y la verificación del estado real del contenedor." className="dg">
      {p.map((n, i) => (
        <g key={i}>
          <rect x={i * 182} y={20} width={156} height={56} rx="4"
                className={i === 1 || i === 4 ? "dg-caja dg-caja--on" : "dg-caja"} />
          <text x={i * 182 + 78} y={s[i] ? 41 : 48} className="dg-t">{n}</text>
          {s[i] && <text x={i * 182 + 78} y={58} className="dg-s">{s[i]}</text>}
          {i < p.length - 1 && (
            <path d={`M${i * 182 + 156} 48 L${(i + 1) * 182 - 5} 48`} className="dg-l" markerEnd="url(#c)" />
          )}
        </g>
      ))}
      {punta("c")}
    </svg>
  );
}
