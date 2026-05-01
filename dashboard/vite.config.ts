/// <reference types="vitest" />

import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  base: "./",
  plugins: [react()],
  server: {
    host: "0.0.0.0",
    port: 5173
  },
  test: {
    environment: "node",
    include: ["src/**/*.test.ts"]
  }
});
