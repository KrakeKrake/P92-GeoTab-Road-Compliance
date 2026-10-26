/**
 * Runtime configuration.
 *
 * Containers write /config.js from environment variables before nginx starts,
 * so the same image can be deployed to different hosts. Local `npm run dev`
 * falls back to import.meta.env (web-app/.env).
 */
export interface AppConfig {
  VITE_VALHALLA_URL?: string;
  VITE_NHVR_API_URL?: string;
  VITE_NOMINATIM_URL?: string;
  VITE_CENTER_COORDS?: string;
  VITE_DEFAULT_COSTING_MODEL?: string;
  VITE_CLIENT_ID?: string;
}

declare global {
  interface Window {
    __APP_CONFIG__?: Partial<AppConfig>;
  }
}

export function getAppConfig(): AppConfig {
  const runtime =
    typeof window !== 'undefined' ? window.__APP_CONFIG__ : undefined;

  // `??` is deliberate: an empty VITE_NHVR_API_URL means same-origin, while
  // `||` would incorrectly fall back to localhost:5000.
  return {
    VITE_VALHALLA_URL:
      runtime?.VITE_VALHALLA_URL ?? import.meta.env.VITE_VALHALLA_URL,
    VITE_NHVR_API_URL:
      runtime?.VITE_NHVR_API_URL ?? import.meta.env.VITE_NHVR_API_URL,
    VITE_NOMINATIM_URL:
      runtime?.VITE_NOMINATIM_URL ?? import.meta.env.VITE_NOMINATIM_URL,
    VITE_CENTER_COORDS:
      runtime?.VITE_CENTER_COORDS ?? import.meta.env.VITE_CENTER_COORDS,
    VITE_DEFAULT_COSTING_MODEL:
      runtime?.VITE_DEFAULT_COSTING_MODEL ??
      import.meta.env.VITE_DEFAULT_COSTING_MODEL,
    VITE_CLIENT_ID: runtime?.VITE_CLIENT_ID ?? import.meta.env.VITE_CLIENT_ID,
  };
}
