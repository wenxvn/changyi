import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, ".", "");
  const backendUrl = env.VITE_BACKEND_URL || "http://127.0.0.1:5002";
  return {
    plugins: [react()],
    server: {
      proxy: {
        "/api": backendUrl,
        "/static": backendUrl,
      },
    },
    build: {
      outDir: "dist",
      emptyOutDir: true,
    },
  };
});
