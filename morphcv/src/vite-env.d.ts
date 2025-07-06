/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL?: string; // Make it optional as it has a fallback
  // Add other environment variables here if needed in the future
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
