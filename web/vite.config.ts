import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Se publica en GitHub Pages, NO en el contenedor del agente: la presentación y
// el servicio tienen criticidad distinta y no deben compartir dominio de fallo.
// Además no consume recursos de Azure.
export default defineConfig({
  plugins: [react()],
  base: "/banorte-cv-agent/",
  build: { outDir: "dist", emptyOutDir: true, sourcemap: false },
});
