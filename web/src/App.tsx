import { useEffect, useState, type ReactNode } from "react";
import { Capas, Entrega, FlujoRAG } from "./Diagramas";

const REPO = "https://github.com/alejandrorau04/banorte-cv-agent";

/* Sin lenguaje promocional: cada línea es un hecho, una medida o una decisión
   documentada. Las cifras proceden de ejecuciones reales del repositorio. */

function Avance() {
  const [p, setP] = useState(0);
  useEffect(() => {
    const calc = () => {
      const alto = document.documentElement.scrollHeight - window.innerHeight;
      setP(alto > 0 ? Math.min(Math.max(window.scrollY / alto, 0), 1) : 0);
    };
    calc();
    window.addEventListener("scroll", calc, { passive: true });
    window.addEventListener("resize", calc);
    return () => { window.removeEventListener("scroll", calc); window.removeEventListener("resize", calc); };
  }, []);
  return (
    <div className="avance" aria-hidden="true">
      <div className="avance__b" style={{ transform: `scaleX(${p})` }} />
    </div>
  );
}

const Sec = ({ n, t, children }: { n: string; t: string; children: ReactNode }) => (
  <section className="sec" aria-labelledby={`s${n}`}>
    <div className="sec__ref">
      <span className="sec__n">§ {n}</span>
      <h2 className="sec__t" id={`s${n}`} tabIndex={-1}>{t}</h2>
    </div>
    <div className="sec__cuerpo">{children}</div>
  </section>
);

const N = ({ v, u, k, tono }: { v: string; u?: string; k: string; tono?: "r" | "v" }) => (
  <div className={`n${tono ? ` n--${tono}` : ""}`}>
    <span className="n__v">{v}{u && <small>{u}</small>}</span>
    <span className="n__k">{k}</span>
  </div>
);

const Paso = ({ k, children }: { k: string; children: ReactNode }) => (
  <div className="ej__paso"><div className="ej__k">{k}</div><div className="ej__v">{children}</div></div>
);

const Verif = ({ href, t, d, m }: { href: string; t: string; d: string; m: string }) => (
  <a href={href} target="_blank" rel="noreferrer">
    <span><b>{t}</b><em>{d}</em></span>
    <span>{m}</span>
  </a>
);

/** Logotipo institucional.
 *
 *  Se carga desde `web/public/banorte.svg` (o `.png`). Si el archivo no existe,
 *  el bloque se oculta por completo: la presentacion nunca muestra una imagen
 *  rota ni un hueco vacio. Uso nominativo -- referencia al reto, no marca de la
 *  pagina -- con la autoria del documento indicada al pie.
 */
function Logotipo() {
  const [estado, setEstado] = useState<"svg" | "png" | "ninguno">("svg");
  if (estado === "ninguno") return null;
  const src = `${import.meta.env.BASE_URL}banorte.${estado}`;
  return (
    <div className="cab__marca">
      <img
        src={src}
        alt="Banorte"
        onError={() => setEstado(estado === "svg" ? "png" : "ninguno")}
      />
    </div>
  );
}

const Marca = ({ k, v }: { k: string; v: string }) => (
  <div className="marca"><span className="marca__k">{k}</span><span className="marca__v">{v}</span></div>
);

const REFS = ["s01","s02","s03","s04","s05","s06","s07","s08","s09","s10","s11","s12"];

/** Avance por secciones con las flechas. Presentar exige pasos discretos donde
 *  detenerse; el scroll continuo compite con quien habla. */
function useTeclado() {
  useEffect(() => {
    const visible = () => {
      const y = window.scrollY + window.innerHeight * 0.25;
      let actual = 0;
      REFS.forEach((id, i) => {
        const n = document.getElementById(id);
        if (n && n.getBoundingClientRect().top + window.scrollY <= y) actual = i;
      });
      return actual;
    };
    const onKey = (e: KeyboardEvent) => {
      if (e.metaKey || e.ctrlKey || e.altKey) return;
      const dentro = (e.target as HTMLElement)?.closest("input, textarea, select, [contenteditable]");
      if (dentro) return;
      const paso = e.key === "ArrowRight" || e.key === "PageDown" ? 1
                 : e.key === "ArrowLeft" || e.key === "PageUp" ? -1 : 0;
      if (!paso) return;
      e.preventDefault();
      const destino = REFS[Math.min(Math.max(visible() + paso, 0), REFS.length - 1)];
      document.getElementById(destino)?.scrollIntoView({ behavior: "smooth", block: "start" });
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);
}

export default function App() {
  useTeclado();
  return (
    <>
      <a className="saltar" href="#s01">Saltar al contenido</a>
      <Avance />
      <div className="doc">

        <header className="cab">
          <p className="cab__id">Reto IA Banorte · Documento técnico</p>
          <div className="cab__fila">
            <div>
              <h1>Agente de CV<br />Alejandro Rau Lázaro</h1>
              <p className="cab__sub">
                Servicio conversacional bilingüe con recuperación aumentada sobre corpus
                verificado. Compatible con la especificación abierta Open&nbsp;Responses y
                desplegado en Azure Container Apps.
              </p>
            </div>
            <Logotipo />
          </div>
        </header>

        <nav className="verbos" aria-label="Contenido por área">
          <a href="#s04"><span>Diseñar</span> Pipeline RAG · controles · 12 decisiones</a>
          <a href="#s03"><span>Integrar</span> Contrato Open Responses · capas · adaptadores</a>
          <a href="#s07"><span>Desplegar</span> Azure · contenedor · CI/CD</a>
          <a href="#s08"><span>Operar</span> Seguridad · coste · límites</a>
        </nav>

        <div className="ficha">
          <div className="ficha__c"><span className="ficha__k">Versión</span><span className="ficha__v mono">1.1.0</span></div>
          <div className="ficha__c"><span className="ficha__k">Contrato</span><span className="ficha__v mono">Open Responses 2026-04-24</span></div>
          <div className="ficha__c"><span className="ficha__k">Runtime</span><span className="ficha__v mono">Python 3.12 · FastAPI</span></div>
          <div className="ficha__c"><span className="ficha__k">Modelo</span><span className="ficha__v mono">gemini-3.1-flash-lite</span></div>
          <div className="ficha__c"><span className="ficha__k">Nube</span><span className="ficha__v mono">Azure Container Apps</span></div>
          <div className="ficha__c"><span className="ficha__k">Código</span><span className="ficha__v"><a href={REPO}>GitHub ↗</a></span></div>
        </div>

        <Sec n="01" t="Fiabilidad de las respuestas">
          <p className="dice">
            El conjunto de evaluación tiene 32 casos, de los cuales <strong>12 comprueban
            lo que el agente NO debe responder</strong>: preguntas fuera de dominio,
            vacíos del CV, peticiones de datos personales e intentos de inyección.
          </p>
          <div className="serie">
            <N v="0" k="Afirmaciones sin respaldo verificable en los 36 casos evaluados" tono="r" />
            <N v="5/5" k="Intentos de inyección de prompt resistidos" tono="r" />
            <N v="5/5" k="Preguntas fuera de dominio rechazadas sin invocar al modelo" tono="v" />
            <N v="2/2" k="Peticiones de datos personales bloqueadas por política" tono="v" />
            <N v="26/26" k="Respuestas consistentes ante formulaciones distintas" />
            <N v="28/28" k="Entradas malformadas sin error de servidor" />
          </div>
          <p className="dice" style={{ marginTop: "calc(var(--u) * 4)" }}>
            Toda cita emitida se contrasta contra los hechos recuperados antes de
            responder. Una cita a un identificador inexistente se elimina del texto:
            <strong> el respaldo de cada afirmación es comprobable, no declarado</strong>.
          </p>
        </Sec>

        <Sec n="02" t="Trazabilidad: anatomía de una consulta">
          <p className="dice">
            Un caso completo, con los valores exactos de una ejecución contra el endpoint
            desplegado. Es la forma más directa de ver qué hace el sistema.
          </p>
          <div className="ej">
            <Paso k="Pregunta">
              <p className="ej__preg">¿Dónde trabaja actualmente?</p>
            </Paso>
            <Paso k="Recuperación">
              <div className="ej__hechos">
                <div className="ej__h ej__h--top">
                  <span className="ej__sim">0.6929</span>
                  <span className="ej__id">exp.globalconnect.role</span>
                </div>
                <div className="ej__h"><span className="ej__sim">0.6826</span><span className="ej__id">profile.headline</span></div>
                <div className="ej__h"><span className="ej__sim">0.6628</span><span className="ej__id">exp.alcazar.role</span></div>
                <div className="ej__h"><span className="ej__sim">0.6619</span><span className="ej__id">exp.wesco.role</span></div>
                <div className="ej__h"><span className="ej__sim">0.6546</span><span className="ej__id">exp.guval.role</span></div>
              </div>
              <p className="ej__meta">
                similitud máxima 0.6929 ≥ umbral 0.62 → hay evidencia suficiente, se invoca al modelo
              </p>
            </Paso>
            <Paso k="Respuesta">
              <p className="ej__resp">
                Actualmente, Alejandro trabaja como Desarrollador Full Stack y Móvil en
                GlobalConnect, en Cancún, Quintana Roo. Ocupa este puesto desde mayo de 2025.
              </p>
              <span className="ej__cita">
                Fuentes:{" "}
                <a href={`${REPO}/blob/main/data/corpus.yaml#L38-L49`} target="_blank" rel="noreferrer">
                  Experiencia · GlobalConnect (may 2025 – actual)
                </a>
              </span>
              <p className="ej__meta">557 tokens · 1 218 ms · cita verificada contra los hechos recuperados</p>
            </Paso>
            <Paso k="Contraste">
              <p className="ej__preg">¿Cuál es la capital de Francia?</p>
              <p className="ej__meta" style={{ marginTop: "4px" }}>
                similitud máxima 0.523 &lt; umbral 0.62 → sin evidencia
              </p>
              <p className="ej__resp" style={{ marginTop: "calc(var(--u) * 1.5)" }}>
                No encuentro información en el CV de Alejandro Rau para responder eso. Puedo
                hablarte de su experiencia profesional, las empresas donde ha trabajado, sus
                habilidades técnicas, su formación y sus proyectos destacados.
              </p>
              <p className="ej__meta">0 tokens · 494 ms · no se invocó al modelo</p>
            </Paso>
          </div>
          <p className="dice" style={{ marginTop: "calc(var(--u) * 3)" }}>
            La diferencia entre ambos casos es un solo número: <strong>0.6929 frente a
            0.523</strong>. Por encima del umbral se responde citando la fuente; por debajo
            se reconoce el límite sin gastar nada.
          </p>
        </Sec>

        <Sec n="03" t="Comparativa frente al enfoque estándar">
          <p className="dice">
            Frente al enfoque directo —el que produce una implementación sin estas
            decisiones—, medido sobre el mismo conjunto de preguntas.
          </p>
          <div className="scroll-x">
            <table className="datos">
              <thead><tr><th>Aspecto</th><th>Enfoque directo</th><th>Implementado</th></tr></thead>
              <tbody>
                <tr><td>Contexto enviado por consulta</td><td className="m">~1.860 tokens (corpus completo)</td><td className="v">~500 tokens (top-6)</td></tr>
                <tr><td>Consultas que llegan al modelo</td><td className="m">100 %</td><td className="v">78 %</td></tr>
                <tr><td>Tokens en una petición trivial</td><td className="m">247 (razonamiento incluido)</td><td className="v">56</td></tr>
                <tr><td>Coste de una pregunta fuera de dominio</td><td className="m">~550 tokens</td><td className="v">0 tokens · &lt;500 ms</td></tr>
                <tr><td>Coste por turno en conversación larga</td><td className="m">crece con cada turno</td><td className="v">constante</td></tr>
                <tr><td>Latencia p95 tras corregir la cadena de respaldo</td><td className="m">31,9 s</td><td className="v">2,09 s</td></tr>
                <tr><td>Peticiones correctas con concurrencia 10</td><td className="m">25 / 30</td><td className="v">30 / 30</td></tr>
              </tbody>
            </table>
          </div>
          <div className="serie" style={{ marginTop: "calc(var(--u) * 4)" }}>
            <N v="0.97" u="s" k="Latencia mediana" />
            <N v="777" k="Tokens de media por consulta" />
            <N v="126" k="Tests automatizados, sin red ni credenciales" />
            <N v="62" k="Hechos en el corpus, bilingües y versionados" />
          </div>
        </Sec>

        <Sec n="04" t="Arquitectura del servicio">
          <p className="dice">
            Tres capas con las dependencias apuntando hacia el núcleo. El núcleo
            <strong> no conoce HTTP ni el proveedor de modelo</strong>: por eso los tests
            se ejecutan sin red y cambiar de LLM o de nube no altera la lógica.
          </p>
          <Capas />
          <div className="marcas" style={{ marginTop: "calc(var(--u) * 3)" }}>
            <Marca k="Backend" v="Python 3.12 · FastAPI · uvicorn · httpx" />
            <Marca k="Dependencias" v="6, ninguna con compilación nativa" />
            <Marca k="Recuperación" v="Coseno + IDF en proceso, 768 dimensiones" />
            <Marca k="Datos" v="61 hechos en YAML versionado, sin base de datos" />
            <Marca k="Frontend" v="React · TypeScript · Vite (este documento)" />
            <Marca k="Entrega" v="Docker · GHCR · GitHub Actions · Azure" />
          </div>
        </Sec>

        <Sec n="05" t="Recuperación aumentada (RAG)">
          <p className="dice">
            El CV no se indexa como documento troceado: se transforma en hechos atómicos
            con identificador estable, metadatos y texto paralelo en español e inglés.
            Cada respuesta cita los hechos que la respaldan.
          </p>
          <FlujoRAG />
          <div className="scroll-x" style={{ marginTop: "calc(var(--u) * 3)" }}>
            <table className="datos">
              <thead><tr><th>Componente</th><th>Implementación</th><th>Medida</th></tr></thead>
              <tbody>
                <tr><td>Recuperación</td><td>Coseno 0.65 + léxico IDF 0.35</td><td className="m">top-6</td></tr>
                <tr><td>Embeddings</td><td>gemini-embedding-001, con segundo modelo indexado</td><td className="m">768 dim</td></tr>
                <tr><td>Umbral de abstención</td><td>Calibrado: dominio mín. 0.6633 · fuera máx. 0.5899</td><td className="m">0.62</td></tr>
                <tr><td>Almacén vectorial</td><td>En proceso. 122 vectores no justifican un servicio externo</td><td className="m">—</td></tr>
                <tr><td>Consultas de agregación</td><td>Resueltas con metadatos: el orden lo calcula el código</td><td className="m">sorted()</td></tr>
                <tr><td>Memoria conversacional</td><td>Un intercambio, recortado. No se reenvía la transcripción</td><td className="m">constante</td></tr>
              </tbody>
            </table>
          </div>
        </Sec>

        <Sec n="06" t="Control de alucinaciones">
          <p className="dice">
            Cuatro controles que no dependen del modelo: son código que se ejecuta antes
            y después de invocarlo.
          </p>
          <ol className="reglas">
            <li><span className="k">01</span><span><b>Grounding cerrado</b>
              <span className="t">El prompt contiene únicamente hechos recuperados del corpus.</span></span></li>
            <li><span className="k">02</span><span><b>Compuerta de evidencia</b>
              <span className="t">Si la similitud no supera el umbral, se responde sin invocar al modelo.</span></span></li>
            <li><span className="k">03</span><span><b>Verificación de citas</b>
              <span className="t">Las citas a identificadores no recuperados se eliminan del texto.</span></span></li>
            <li><span className="k">04</span><span><b>Política determinista</b>
              <span className="t">Los datos de contacto no están en el corpus; no pueden revelarse.</span></span></li>
          </ol>
        </Sec>

        <Sec n="07" t="Eficiencia: consumo de tokens y latencia">
          <p className="dice">
            La abstención previa a la invocación elimina simultáneamente el riesgo de
            invención y el coste. <strong>Ambos efectos proceden del mismo mecanismo.</strong>
          </p>
          <div className="scroll-x">
            <table className="datos">
              <thead><tr><th>Palanca</th><th>Efecto medido</th></tr></thead>
              <tbody>
                <tr><td>Abstención previa a la invocación</td><td className="v">0 tokens · 22 % de las consultas</td></tr>
                <tr><td>thinkingLevel: minimal</td><td className="v">−77 % de tokens de razonamiento</td></tr>
                <tr><td>Recuperación top-6 frente al corpus completo</td><td className="m">~500 frente a ~1.860 tokens</td></tr>
                <tr><td>Memoria de un intercambio</td><td className="v">coste constante por turno</td></tr>
                <tr><td>Embeddings precalculados en construcción</td><td className="v">0 llamadas en ejecución</td></tr>
                <tr><td>Caché de consultas repetidas</td><td className="v">0 tokens en repeticiones</td></tr>
                <tr><td>Detección de idioma determinista</td><td className="v">evita una llamada por petición</td></tr>
              </tbody>
            </table>
          </div>
          <div className="marcas" style={{ marginTop: "calc(var(--u) * 3)" }}>
            <Marca k="Primario" v="gemini-3.1-flash-lite · mediana 1.12 s" />
            <Marca k="Respaldo" v="gemini-3.5-flash-lite · mediana 1.01 s" />
            <Marca k="Descartado" v="gemini-3.6-flash · mediana 15.46 s" />
            <Marca k="Cambio de proveedor" v="Implementar dos interfaces y una variable de entorno" />
          </div>
        </Sec>

        <Sec n="08" t="Integración y entrega continua (CI/CD)">
          <p className="dice">
            Azure restringe la construcción de imágenes en suscripciones nuevas. La
            construcción se trasladó a GitHub Actions, conservando Azure como destino.
          </p>
          <Entrega />
          <div className="scroll-x" style={{ marginTop: "calc(var(--u) * 2)" }}>
            <table className="datos">
              <thead><tr><th>Etapa</th><th>Contenido</th></tr></thead>
              <tbody>
                <tr><td>Calidad</td><td>122 tests · conformidad contra el OpenAPI oficial · corpus sin datos personales · cobertura del índice</td></tr>
                <tr><td>Imagen</td><td>Publicada en GHCR, etiquetada con el SHA del commit</td></tr>
                <tr><td>Despliegue</td><td>Service principal acotado al grupo de recursos</td></tr>
                <tr><td>Verificación</td><td>Comprueba el estado real del contenedor, no solo el código HTTP</td></tr>
              </tbody>
            </table>
          </div>
        </Sec>

        <Sec n="09" t="Seguridad y cumplimiento">
          <p className="dice">
            Modelo de amenazas STRIDE documentado, con los riesgos aceptados explícitos y
            la distancia hasta un despliegue productivo.
          </p>
          <div className="scroll-x">
            <table className="datos">
              <thead><tr><th>Control</th><th>Implementación</th></tr></thead>
              <tbody>
                <tr><td>Autenticación</td><td>Token requerido en cada petición · 401 tipado</td></tr>
                <tr><td>Secretos</td><td>Gestionados por la plataforma; ausentes de la imagen y del repositorio</td></tr>
                <tr><td>Privilegio de despliegue</td><td>Acotado al grupo de recursos, no a la suscripción</td></tr>
                <tr><td>Contenedor</td><td>Usuario sin privilegios, imagen mínima</td></tr>
                <tr><td>Inyección de prompt</td><td>Verificada con casos adversariales en el conjunto de evaluación</td></tr>
                <tr><td>Datos personales</td><td>Ausentes del corpus; comprobado en cada construcción</td></tr>
                <tr><td>Registro de actividad</td><td>Sin contenido de conversaciones</td></tr>
                <tr><td>Entradas malformadas</td><td>28 casos hostiles sin ningún error de servidor</td></tr>
              </tbody>
            </table>
          </div>
          <div className="marcas" style={{ marginTop: "calc(var(--u) * 3)" }}>
            <Marca k="Pendiente para producción" v="Proveedor con aislamiento contractual de datos" />
            <Marca k="Pendiente" v="OAuth 2.0 / Entra ID" />
            <Marca k="Pendiente" v="Rate limiting en la puerta de entrada" />
            <Marca k="Pendiente" v="Registro de imágenes privado" />
          </div>
        </Sec>

        <Sec n="10" t="Aseguramiento de calidad: defectos corregidos">
          <div className="serie">
            <N v="11" k="Defectos localizados en el propio sistema y corregidos" tono="r" />
            <N v="3" k="Veces que la cadena de respaldo falló pareciendo correcta en el código" />
            <N v="2" k="Veces que el equivocado resultó ser el propio evaluador" />
            <N v="11" k="Pruebas de regresión añadidas, una por defecto" tono="v" />
          </div>
          <p className="dice" style={{ marginTop: "calc(var(--u) * 4)" }}>
            Ninguno se detectó leyendo el código: todos surgieron de medir. Detección de
            idioma anulada por sus propias palabras vacías, compuerta inoperante por
            normalizar el coseno, modelo de respaldo más lento que su propio tiempo
            límite, índice parcial sin error visible.
          </p>
          <p className="dice">
            En dos ocasiones el fallo estaba en el conjunto de evaluación, no en el
            agente: prohibía la palabra «Harvard» en lugar de prohibir afirmarla, y daba
            por correcta una fecha equivocada. <strong>Un evaluador mal diseñado lleva a
            corregir un sistema que funciona.</strong>
          </p>
        </Sec>

        <Sec n="11" t="Evidencia y verificación independiente">
          <p className="dice">
            Cada afirmación de este documento tiene su origen en el repositorio. Estos son
            los enlaces directos.
          </p>
          <div className="verif">
            <Verif href={`${REPO}/blob/main/data/corpus.yaml`}
              t="El corpus completo" d="Los 61 hechos con sus identificadores, metadatos y texto bilingüe" m="corpus.yaml" />
            <Verif href={`${REPO}/tree/main/docs/adr`}
              t="Las 12 decisiones técnicas" d="Cada una con su contexto, la decisión y las alternativas descartadas" m="docs/adr/" />
            <Verif href={`${REPO}/blob/main/eval/golden_set.yaml`}
              t="El conjunto de evaluación" d="Los 32 casos, incluidos los adversariales y los de abstención" m="eval/golden_set.yaml" />
            <Verif href={`${REPO}/blob/main/eval/results.json`}
              t="Resultados de la última ejecución" d="Respuesta, citas, tokens y latencia de cada caso" m="eval/results.json" />
            <Verif href={`${REPO}/blob/main/app/core/agent.py`}
              t="El núcleo del agente" d="Compuerta de evidencia, verificación de citas y memoria conversacional" m="app/core/agent.py" />
            <Verif href={`${REPO}/blob/main/docs/contract/openapi.json`}
              t="El contrato anclado" d="Especificación Open Responses 2026-04-24 usada para verificar en CI" m="docs/contract/" />
            <Verif href={`${REPO}/blob/main/docs/MODELO-AMENAZAS.md`}
              t="Modelo de amenazas" d="STRIDE, con los riesgos aceptados explícitos" m="MODELO-AMENAZAS.md" />
            <Verif href={`${REPO}/blob/main/docs/LIMITES-Y-COSTES.md`}
              t="Límites y costes" d="Presupuesto de tokens, escalabilidad y distancia hasta producción" m="LIMITES-Y-COSTES.md" />
            <Verif href={`${REPO}/actions`}
              t="Ejecuciones del pipeline" d="Historial completo de calidad, construcción y despliegue" m="GitHub Actions" />
          </div>
        </Sec>

        <Sec n="12" t="Límites conocidos y riesgos aceptados">
          <div className="scroll-x">
            <table className="datos">
              <thead><tr><th>Aspecto</th><th>Estado</th></tr></thead>
              <tbody>
                <tr><td>Carga sostenida</td><td className="m">No probada por encima de concurrencia 10</td></tr>
                <tr><td>Verificación semántica de citas</td><td className="m">Comprueba existencia, no implicación</td></tr>
                <tr><td>Calibración del umbral</td><td className="m">15–18 preguntas por modelo</td></tr>
                <tr><td>Disponibilidad</td><td className="m">Una región, sin replicación</td></tr>
                <tr><td>Escala del corpus</td><td className="m">Búsqueda exhaustiva, razonable hasta ~10.000 hechos</td></tr>
              </tbody>
            </table>
          </div>
        </Sec>

        <section className="final">
          <p className="final__t">
            El mismo criterio que impide al agente afirmar lo que no puede respaldar
            se aplicó a este documento: <em>cada cifra procede de una ejecución real
            y enlaza a su origen</em>.
          </p>
          <div className="final__d">
            <div><b>Servicio</b><span>Azure Container Apps · v1.1.0</span></div>
            <div><b>Contrato</b><span>Open Responses 2026-04-24</span></div>
            <div><b>Evidencia</b><span>122 tests · 32 casos · 12 ADRs</span></div>
            <div><b>Código</b><span><a href={REPO}>github.com ↗</a></span></div>
          </div>
        </section>

        <footer className="pie">
          <span>Alejandro Rau Lázaro · Agosto 2026</span>
          <span>Reto IA Banorte · entregable de candidato</span>
          <span><a href={REPO}>github.com/alejandrorau04/banorte-cv-agent ↗</a></span>
        </footer>

      </div>
    </>
  );
}
