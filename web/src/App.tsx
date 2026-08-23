import type { ReactNode } from "react";
import { Capas, Entrega, FlujoRAG } from "./Diagramas";

const REPO = "https://github.com/alejandrorau04/banorte-cv-agent";

/* Sin lenguaje promocional: cada línea es un hecho, una medida o una decisión
   documentada. Las cifras proceden de ejecuciones reales del repositorio. */

const Sec = ({ n, t, children }: { n: string; t: string; children: ReactNode }) => (
  <section className="sec" aria-labelledby={`s${n}`}>
    <div className="sec__ref">
      <span className="sec__n">§ {n}</span>
      <h2 className="sec__t" id={`s${n}`}>{t}</h2>
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

const Marca = ({ k, v }: { k: string; v: string }) => (
  <div className="marca"><span className="marca__k">{k}</span><span className="marca__v">{v}</span></div>
);

export default function App() {
  return (
    <>
      <a className="saltar" href="#s01">Saltar al contenido</a>
      <div className="doc">

        <header className="cab">
          <p className="cab__id">Reto IA Banorte · Documento técnico</p>
          <div className="cab__fila">
            <div>
              <h1>Agente de CV<br />Alejandro Rau Lázaro</h1>
              <p className="cab__sub">
                Servicio conversacional bilingüe compatible con la especificación abierta
                Open&nbsp;Responses, desplegado en Azure Container Apps.
              </p>
            </div>
            <div className="cab__marca">
              {/* Coloca aquí el logotipo oficial: web/public/banorte.svg */}
              <span className="cab__hueco">logotipo<br />banorte.svg</span>
            </div>
          </div>
        </header>

        <div className="ficha">
          <div className="ficha__c"><span className="ficha__k">Versión</span><span className="ficha__v mono">1.1.0</span></div>
          <div className="ficha__c"><span className="ficha__k">Contrato</span><span className="ficha__v mono">Open Responses 2026-04-24</span></div>
          <div className="ficha__c"><span className="ficha__k">Runtime</span><span className="ficha__v mono">Python 3.12 · FastAPI</span></div>
          <div className="ficha__c"><span className="ficha__k">Modelo</span><span className="ficha__v mono">gemini-3.1-flash-lite</span></div>
          <div className="ficha__c"><span className="ficha__k">Nube</span><span className="ficha__v mono">Azure Container Apps</span></div>
          <div className="ficha__c"><span className="ficha__k">Código</span><span className="ficha__v"><a href={REPO}>GitHub ↗</a></span></div>
        </div>

        <Sec n="01" t="Resultados medidos">
          <div className="serie">
            <N v="32/32" k="Golden set. 12 de los casos evalúan lo que el agente no debe responder" tono="r" />
            <N v="102" k="Tests automatizados, sin red ni credenciales" />
            <N v="25" u="%" k="Consultas resueltas sin invocar al modelo" tono="v" />
            <N v="1.2" u="s" k="Latencia mediana" />
            <N v="660" k="Tokens de media por consulta" />
            <N v="61" k="Hechos en el corpus, bilingües y versionados" />
          </div>
        </Sec>

        <Sec n="02" t="Arquitectura">
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

        <Sec n="03" t="Pipeline RAG">
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

        <Sec n="04" t="Control de alucinaciones">
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

        <Sec n="05" t="Consumo y latencia">
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

        <Sec n="06" t="Entrega continua">
          <p className="dice">
            Azure restringe la construcción de imágenes en suscripciones nuevas. La
            construcción se trasladó a GitHub Actions, conservando Azure como destino.
          </p>
          <Entrega />
          <div className="scroll-x" style={{ marginTop: "calc(var(--u) * 2)" }}>
            <table className="datos">
              <thead><tr><th>Etapa</th><th>Contenido</th></tr></thead>
              <tbody>
                <tr><td>Calidad</td><td>102 tests · conformidad contra el OpenAPI oficial · corpus sin datos personales · cobertura del índice</td></tr>
                <tr><td>Imagen</td><td>Publicada en GHCR, etiquetada con el SHA del commit</td></tr>
                <tr><td>Despliegue</td><td>Service principal acotado al grupo de recursos</td></tr>
                <tr><td>Verificación</td><td>Comprueba el estado real del contenedor, no solo el código HTTP</td></tr>
              </tbody>
            </table>
          </div>
        </Sec>

        <Sec n="07" t="Seguridad">
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

        <Sec n="08" t="Verificación">
          <div className="serie">
            <N v="32/32" k="Conjunto de evaluación" tono="r" />
            <N v="26/26" k="Consistencia ante formulaciones distintas" />
            <N v="28/28" k="Entradas hostiles sin error de servidor" />
            <N v="30/30" k="Peticiones correctas con concurrencia 10" />
            <N v="11" k="Defectos localizados en el propio sistema y corregidos" tono="r" />
          </div>
          <p className="dice" style={{ marginTop: "calc(var(--u) * 4)" }}>
            Ninguno de los once defectos se detectó leyendo el código: todos surgieron de
            medir. Detección de idioma anulada por sus propias palabras vacías, compuerta
            inoperante por normalizar el coseno, respaldo inalcanzable por presupuesto de
            tiempo, índice parcial sin error visible. Cada uno tiene su prueba de regresión.
          </p>
        </Sec>

        <Sec n="09" t="Límites">
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

        <footer className="pie">
          <span>Alejandro Rau Lázaro · Agosto 2026</span>
          <span>Reto IA Banorte · entregable de candidato</span>
          <span><a href={REPO}>github.com/alejandrorau04/banorte-cv-agent ↗</a></span>
        </footer>

      </div>
    </>
  );
}
