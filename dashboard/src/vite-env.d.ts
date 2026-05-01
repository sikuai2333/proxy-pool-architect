/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL?: string;
  readonly VITE_API_REQUEST_TIMEOUT_MS?: string;
  readonly VITE_DASHBOARD_DATA_MODE?: "mock" | "live";
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
