import { Capas, Entrega, FlujoRAG } from "./Diagramas";

const REPO = "https://github.com/alejandrorau04/banorte-cv-agent";

const Cifra = ({ v, u, k, tono }: { v: string; u?: string; k: string; tono?: "on" | "verde" }) => (
  <div className={`cifra${tono ? ` cifra--${tono}` : ""}`}>
    <span className="cifra__v">{v}{u && <small>{u}</small>}</span>
    <span className="cifra__k">{k}</span>
  </div>
);

const Rotulo = ({ n, t, nota }: { n: string; t: string; nota?: string }) => (
  <header className="rotulo">
    <span className="rotulo__n">{n}</span>
    <h2 className="rotulo__t">{t}</h2>
    {nota && <p className="rotulo__nota">{nota}</p>}
  </header>
);

const Panel = ({ t, children, vivo }: { t: string; children: React.ReactNode; vivo?: boolean }) => (
  <div className={`panel${vivo ? " panel--vivo" : ""}`}>
    <h3>{t}</h3>
    <p className="panel__t">{children}</p>
  </div>
);

export default function App() {
  return (
    <>
      <a className="saltar" href="#arq">Saltar al contenido</a>
      <div className="hoja">

        <header className="portada">
          <p className="portada__sello">Reto IA Banorte · Agosto 2026</p>
          <h1>Agente de CV<br /><span>que no inventa nada.</span></h1>
          <p className="portada__linea">
            Servicio conversacional bilingüe conforme a Open&nbsp;Responses, desplegado en Azure.
            Todo el diseño gira alrededor de un requisito: ninguna afirmación sin respaldo verificable.
          </p>
          <div className="portada__pie">
            <span><strong>Alejandro Rau Lázaro</strong> · Full Stack · IA</span>
            <span>Python · FastAPI · RAG · Azure · React</span>
            <span><a href={REPO}>Código ↗</a></span>
          </div>
        </header>

        <section className="bloque">
          <div className="cifras">
            <Cifra v="32/32" k="Golden set. 12 casos miden lo que NO debe responder" tono="on" />
            <Cifra v="102" k="Tests, sin red ni credenciales" />
            <Cifra v="25" u="%" k="Consultas que no invocan al modelo" tono="verde" />
            <Cifra v="1.2" u="s" k="Latencia mediana" />
            <Cifra v="660" k="Tokens de media por consulta" />
          </div>
        </section>

        <section className="bloque" id="arq">
          <Rotulo n="01" t="Arquitectura"
            nota="El núcleo no conoce HTTP ni el proveedor. Los tests corren sin red; migrar de LLM o de nube no toca la lógica." />
          <div className="malla malla--ancho">
            <Capas />
            <div className="malla" style={{ gap: "var(--u)" }}>
              <Panel t="Backend">Python · FastAPI · uvicorn · httpx · 6 dependencias, ninguna con compilación nativa</Panel>
              <Panel t="IA">Gemini 3.1 Flash Lite tras un puerto · embeddings 768 dim · índice multi-modelo</Panel>
              <Panel t="Infraestructura">Docker · Azure Container Apps · GHCR · GitHub Actions</Panel>
              <Panel t="Datos">61 hechos bilingües en YAML versionado · sin base de datos</Panel>
            </div>
          </div>
        </section>

        <section className="bloque">
          <Rotulo n="02" t="Pipeline RAG"
            nota="El CV no se trocea como documento: son 61 hechos atómicos con identificador estable y metadatos." />
          <FlujoRAG />
          <div className="malla malla--3" style={{ marginTop: "calc(var(--u) * 3)" }}>
            <Panel t="Recuperación híbrida" vivo>
              Coseno 0.65 + léxico IDF 0.35. Los embeddings resuelven la paráfrasis;
              el léxico rescata nombres propios raros donde el término literal manda.
            </Panel>
            <Panel t="Umbral medido, no elegido" vivo>
              En dominio mín. 0.6633 · fuera máx. 0.5899 · separación +0.073.
              Umbral 0.62, por debajo del punto medio a propósito.
            </Panel>
            <Panel t="Sin base vectorial" vivo>
              122 vectores no justifican Qdrant ni pgvector. Detrás de una interfaz:
              sustituirla es implementar una clase.
            </Panel>
          </div>
        </section>

        <section className="bloque">
          <Rotulo n="03" t="Cuatro controles anti-alucinación"
            nota="Ninguno confía en el modelo: son código que se ejecuta antes y después de invocarlo." />
          <ol className="numerado">
            <li><span className="k">01</span><span className="v">
              <b>Grounding cerrado</b>El prompt contiene solo hechos recuperados del corpus versionado.
            </span></li>
            <li><span className="k">02</span><span className="v">
              <b>Compuerta de evidencia</b>Sin similitud suficiente no se invoca al modelo. Un modelo que no se invoca no puede alucinar.
            </span></li>
            <li><span className="k">03</span><span className="v">
              <b>Verificación de citas</b>Las citas inventadas se eliminan del texto antes de responder.
            </span></li>
            <li><span className="k">04</span><span className="v">
              <b>Política determinista</b>Los datos de contacto no existen en el corpus: no puede revelarlos.
            </span></li>
          </ol>
          <p className="cita" style={{ marginTop: "calc(var(--u) * 4)" }}>
            El control de alucinaciones y el ahorro de tokens son el mismo mecanismo.
          </p>
        </section>

        <section className="bloque">
          <Rotulo n="04" t="Coste y latencia"
            nota="Una de cada cuatro consultas cuesta cero. El coste por turno no crece con la conversación." />
          <div className="malla malla--ancho">
            <div className="scroll-x">
              <table>
                <thead><tr><th>Palanca</th><th>Efecto medido</th></tr></thead>
                <tbody>
                  <tr><td><strong>Abstención previa a la invocación</strong></td><td className="g">0 tokens · 22 % de consultas</td></tr>
                  <tr><td><strong>thinkingLevel: minimal</strong></td><td className="g">−77 % tokens de razonamiento</td></tr>
                  <tr><td><strong>Top-6 en vez del corpus completo</strong></td><td className="n">~500 vs ~1.860 tokens</td></tr>
                  <tr><td><strong>Memoria de un intercambio</strong></td><td className="g">coste constante por turno</td></tr>
                  <tr><td><strong>Embeddings precalculados en build</strong></td><td className="g">0 llamadas en runtime</td></tr>
                  <tr><td><strong>Caché de consultas repetidas</strong></td><td className="g">0 tokens en repeticiones</td></tr>
                  <tr><td><strong>Detección de idioma determinista</strong></td><td className="g">evita 1 llamada/petición</td></tr>
                </tbody>
              </table>
            </div>
            <div className="malla" style={{ gap: "var(--u)" }}>
              <Panel t="Modelos elegidos midiendo">
                flash-lite 1.12 s · respaldo 1.01 s · descartado 15.46 s.
                Un respaldo más lento que el timeout no es un respaldo.
              </Panel>
              <Panel t="Cambiar de LLM">
                El núcleo depende de dos interfaces, <span className="mono">LLM</span> y{" "}
                <span className="mono">Embedder</span>. Migrar a Azure OpenAI: implementar
                dos métodos y cambiar una variable de entorno.
              </Panel>
            </div>
          </div>
        </section>

        <section className="bloque">
          <Rotulo n="05" t="Entrega continua"
            nota="Azure bloquea la construcción de imágenes en suscripciones nuevas. La restricción produjo CI/CD real." />
          <Entrega />
          <div className="malla malla--3" style={{ marginTop: "calc(var(--u) * 3)" }}>
            <Panel t="Verificación real">
              No basta un HTTP 200: se comprueba que el contenedor no esté degradado —
              índice cargado, hechos suficientes, modelos disponibles.
            </Panel>
            <Panel t="Trazabilidad">
              Imagen etiquetada por SHA del commit. Revertir es reactivar la revisión anterior.
            </Panel>
            <Panel t="Puerta de calidad">
              102 tests · conformidad contra el OpenAPI oficial · corpus sin PII ·
              cobertura del índice. Sin verde, no hay imagen.
            </Panel>
          </div>
        </section>

        <section className="bloque">
          <Rotulo n="06" t="Seguridad"
            nota="Modelo STRIDE documentado, con los riesgos aceptados explícitos." />
          <div className="malla malla--ancho">
            <div className="scroll-x">
              <table>
                <thead><tr><th>Control</th><th>Implementación</th></tr></thead>
                <tbody>
                  <tr><td><strong>Autenticación</strong></td><td>Token en cada petición · 401 tipado</td></tr>
                  <tr><td><strong>Secretos</strong></td><td>Gestionados por la plataforma · nunca en imagen ni repositorio</td></tr>
                  <tr><td><strong>Mínimo privilegio</strong></td><td>Service principal acotado al grupo de recursos</td></tr>
                  <tr><td><strong>Contenedor</strong></td><td>Usuario sin privilegios · imagen slim</td></tr>
                  <tr><td><strong>Inyección de prompt</strong></td><td>Probada con casos adversariales</td></tr>
                  <tr><td><strong>Datos personales</strong></td><td>Ausentes del corpus · verificado en cada build</td></tr>
                  <tr><td><strong>Logs</strong></td><td>Sin contenido de conversaciones</td></tr>
                </tbody>
              </table>
            </div>
            <div className="malla" style={{ gap: "var(--u)" }}>
              <Panel t="Para producción bancaria">
                Proveedor con aislamiento contractual de datos —bloqueante—, OAuth 2.0,
                rate limiting en la entrada, registro privado, multi-región.
              </Panel>
              <Panel t="Robustez verificada">
                28 entradas hostiles sin ningún 5xx · 30/30 peticiones correctas con
                concurrencia 10.
              </Panel>
            </div>
          </div>
        </section>

        <section className="bloque">
          <Rotulo n="07" t="Evidencia"
            nota="«Respuesta correcta» está definido en código, no es una impresión." />
          <div className="cifras">
            <Cifra v="32/32" k="Golden set" tono="on" />
            <Cifra v="26/26" k="Consistencia ante formulaciones distintas" />
            <Cifra v="28/28" k="Entradas hostiles sin 5xx" />
            <Cifra v="30/30" k="Carga con concurrencia 10" />
            <Cifra v="11" k="Defectos hallados en el propio sistema" tono="on" />
          </div>
          <div className="malla malla--2" style={{ marginTop: "calc(var(--u) * 3)" }}>
            <Panel t="Ninguno salió de leer el código">
              Detección de idioma anulada por sus propias stopwords · compuerta
              inoperante por normalizar el coseno · respaldo inalcanzable · índice
              parcial fallando en silencio. Todos salieron de medir.
            </Panel>
            <Panel t="Dos veces el equivocado era el evaluador">
              El golden set prohibía la palabra «Harvard» en lugar de prohibir afirmarla.
              Un evaluador mal diseñado lleva a arreglar un sistema que funciona.
            </Panel>
          </div>
        </section>

        <footer className="cierre">
          <span>Alejandro Rau Lázaro · Agosto 2026</span>
          <span className="chips">
            <span className="chip chip--on">Endpoint en Azure</span>
            <span className="chip">Registrado en la plataforma</span>
            <span className="chip"><a href={REPO}>Repositorio público ↗</a></span>
          </span>
        </footer>

      </div>
    </>
  );
}
