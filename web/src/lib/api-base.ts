/**
 * Browser API calls must stay same-origin (`/api/v1/...` → Next rewrite).
 * Never point the browser at :8000 — some extensions break cross-origin fetch.
 */
export const API_BASE =
  typeof window !== "undefined"
    ? ""
    : (process.env.NEXT_PUBLIC_API_URL ?? "").replace(/\/$/, "");

/** Absolute FastAPI base for Next server routes and docs links. */
export const BACKEND_URL = (
  process.env.API_INTERNAL_URL ||
  "http://127.0.0.1:8000"
).replace(/\/$/, "");
