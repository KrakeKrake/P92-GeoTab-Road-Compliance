import { getAppConfig } from './runtime-config';

// `??` keeps an explicitly empty value, which means "same origin" behind the
// web app's nginx. `||` would silently fall back to localhost.
export const NHVR_API_URL = (
  getAppConfig().VITE_NHVR_API_URL ?? 'http://localhost:5000'
).replace(/\/$/, '');
