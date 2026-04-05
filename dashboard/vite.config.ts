import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  base: "/dashboard/",
  build: {
    outDir: "../static/dashboard",   // FastAPI serves this
    emptyOutDir: true,
  },
  server: {
    proxy: {
      "/api": { target: "http://localhost:7860", changeOrigin: true, rewrite: (p) => p.replace(/^\/api/, "") },
      "/ws":  { target: "ws://localhost:7860",   ws: true },
    },
  },
});
