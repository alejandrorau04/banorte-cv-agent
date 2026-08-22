import type { ReactNode } from "react";

/* Piezas reutilizables. Cada una resuelve un patrón que se repite en la
   presentación; ninguna existe por decoración. */

export function Seccion({ id, etiqueta, titulo, entradilla, children }: {
  id: string; etiqueta?: string; titulo?: string; entradilla?: string; children?: ReactNode;
}) {
  return (
    <section id={id} className="seccion" aria-labelledby={titulo ? `${id}-t` : undefined}>
      <div className="seccion__interior">
        {etiqueta && <span className="etiqueta">{etiqueta}</span>}
        {titulo && <h2 id={`${id}-t`}>{titulo}</h2>}
        {entradilla && <p className="entradilla" style={{ marginTop: "1rem" }}>{entradilla}</p>}
        {children}
      </div>
    </section>
  );
}

export function Dato({ cifra, sufijo, pie, acento = false }: {
  cifra: string; sufijo?: string; pie: string; acento?: boolean;
}) {
  return (
    <div className={`dato${acento ? " dato--acento" : ""}`}>
      <span className="dato__cifra">
        {cifra}{sufijo && <small>{sufijo}</small>}
      </span>
      <span className="dato__pie">{pie}</span>
    </div>
  );
}

export function Tarjeta({ titulo, children }: { titulo: string; children: ReactNode }) {
  return (
    <div className="tarjeta">
      <h3>{titulo}</h3>
      {children}
    </div>
  );
}

export function Nota({ children }: { children: ReactNode }) {
  return <p className="nota">{children}</p>;
}

export function Pildora({ estado, children }: {
  estado: "si" | "no" | "parcial"; children: ReactNode;
}) {
  const simbolo = estado === "si" ? "✓" : estado === "parcial" ? "~" : "—";
  return (
    <span className={`pildora pildora--${estado}`}>
      <span aria-hidden="true">{simbolo}</span>
      {children}
    </span>
  );
}

export function Tabla({ cabeceras, filas, caption }: {
  cabeceras: string[]; filas: ReactNode[][]; caption?: string;
}) {
  return (
    <div className="tabla-scroll">
      <table>
        {caption && <caption className="dato__pie" style={{ textAlign: "left", paddingBottom: ".5rem" }}>{caption}</caption>}
        <thead>
          <tr>{cabeceras.map((c) => <th key={c} scope="col">{c}</th>)}</tr>
        </thead>
        <tbody>
          {filas.map((f, i) => (
            <tr key={i}>{f.map((celda, j) => <td key={j}>{celda}</td>)}</tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
