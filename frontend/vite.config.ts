import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// 개발 중 /api → FastAPI(:8000) 프록시
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});
