# Presentación

Aplicación React + TypeScript que presenta el proyecto: arquitectura, pipeline RAG,
decisiones técnicas, evidencia de pruebas, infraestructura y seguridad.

Se publica en **GitHub Pages**, deliberadamente separada del agente: la presentación y
el servicio tienen criticidad distinta y **no deben compartir dominio de fallo**. Un
problema aquí no puede afectar al endpoint en Azure, y no consume recursos de la
suscripción.

## Decisiones

- **Vite + React + TypeScript**, sin framework de UI ni librería de componentes: el
  sistema de diseño son ~250 líneas de CSS con tokens propios. Menos dependencias que
  auditar y control total del resultado.
- **Sin llamadas al agente en vivo.** Hacerlo exigiría incluir el token de autenticación
  en código público. Se muestran interacciones **reales capturadas**, etiquetadas como
  tales, con sus métricas verdaderas.
- **Navegación por teclado** (← →) además del scroll: al exponer se necesitan pasos
  discretos donde detenerse, no depender del desplazamiento.
- **Accesible:** enlace de salto, jerarquía de encabezados, `aria-current` en el índice,
  `<title>` descriptivo en cada diagrama SVG, foco visible y respeto por
  `prefers-reduced-motion`.
- **Tema claro y oscuro** mediante `prefers-color-scheme`.
- **Diagramas en SVG inline**: se adaptan al tema, escalan sin perder nitidez y no añaden
  dependencias.

## Desarrollo

```bash
cd web
npm install
npm run dev
npm run build      # comprueba tipos y compila a dist/
```
