import { useEffect, useRef, useState } from "react";

/** Reproducción de interacciones REALES capturadas contra el endpoint desplegado.
 *
 *  No se llama al agente en vivo desde aquí a propósito: hacerlo exigiría incluir
 *  el token de autenticación en código público, lo que lo filtraría. Sería
 *  contradecir la propia argumentación de seguridad de esta presentación.
 *  Las respuestas son literales; las métricas, las medidas. */

export type Intercambio = {
  pregunta: string;
  respuesta: string;
  fuentes?: string[];
  tokens: number;
  ms: number;
  nota?: string;
};

export function Conversacion({ intercambios, titulo }: {
  intercambios: Intercambio[]; titulo: string;
}) {
  const [visibles, setVisibles] = useState(0);
  const [escribiendo, setEscribiendo] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const reducido = typeof window !== "undefined"
    && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  useEffect(() => {
    if (visibles >= intercambios.length) return;
    const nodo = ref.current;
    if (!nodo) return;
    const obs = new IntersectionObserver(([e]) => {
      if (!e.isIntersecting) return;
      if (reducido) { setVisibles(intercambios.length); return; }
      setEscribiendo(true);
      const t = setTimeout(() => { setEscribiendo(false); setVisibles((v) => v + 1); }, 650);
      return () => clearTimeout(t);
    }, { threshold: 0.35 });
    obs.observe(nodo);
    return () => obs.disconnect();
  }, [visibles, intercambios.length, reducido]);

  useEffect(() => {
    if (visibles === 0 || visibles >= intercambios.length || reducido) return;
    const t = setTimeout(() => {
      setEscribiendo(true);
      setTimeout(() => { setEscribiendo(false); setVisibles((v) => v + 1); }, 550);
    }, 1400);
    return () => clearTimeout(t);
  }, [visibles, intercambios.length, reducido]);

  return (
    <div className="charla" ref={ref}>
      <div className="charla__barra">
        <span className="charla__titulo">{titulo}</span>
        <span className="charla__sello">respuestas reales capturadas</span>
      </div>

      <div className="charla__cuerpo">
        {intercambios.slice(0, Math.max(visibles, 1)).map((it, i) => (
          <div key={i} className="turno">
            <p className="turno__usuario">{it.pregunta}</p>
            <div className="turno__agente">
              <p>{it.respuesta}</p>
              {it.fuentes && (
                <p className="turno__fuentes">
                  Fuentes: {it.fuentes.map((f, j) => (
                    <span key={j}>{j > 0 && " · "}<span className="turno__fuente">{f}</span></span>
                  ))}
                </p>
              )}
              <p className="turno__meta">
                <span className={it.tokens === 0 ? "turno__cero" : ""}>
                  {it.tokens} tokens
                </span>
                <span aria-hidden="true"> · </span>
                <span>{it.ms} ms</span>
                {it.nota && <><span aria-hidden="true"> · </span><em>{it.nota}</em></>}
              </p>
            </div>
          </div>
        ))}
        {escribiendo && (
          <p className="charla__escribiendo" aria-live="polite">
            <span /><span /><span />
          </p>
        )}
      </div>

      {visibles < intercambios.length && (
        <button className="charla__saltar" onClick={() => setVisibles(intercambios.length)}>
          Mostrar la conversación completa
        </button>
      )}
    </div>
  );
}
