import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

// Build çıktısı repo kökündeki dist/'e gider; api.py oradan servis eder.
// Geliştirmede /api istekleri Starlette sunucusuna (8000) proxy'lenir; böylece
// EventSource aynı origin'den (5173) çalışır, CORS gerekmez.
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: { "@": path.resolve(__dirname, "./src") },
  },
  build: {
    outDir: "../dist",
    emptyOutDir: true,
  },
  server: {
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});
