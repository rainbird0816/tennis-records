import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// 개발 중 /api → FastAPI(:8000) 프록시
export default defineConfig({
  plugins: [react()],
  build: {
    rollupOptions: {
      output: {
        // recharts(차트)는 큰 의존성 — 별도 청크로 분리
        manualChunks: { recharts: ["recharts"] },
      },
    },
  },
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
