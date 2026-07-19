import { API_BASE } from "@/lib/api-base";

/** Build an API path; always same-origin in the browser (`/api/v1/...`). */
export function apiUrl(path: string): string {
  const p = path.startsWith("/") ? path : `/${path}`;
  const base =
    typeof window !== "undefined" ? "" : API_BASE.replace(/\/$/, "");
  return `${base}${p}`;
}

/** XHR fallback when window.fetch is broken (extensions) or throws. */
function xhrFetch(url: string, init?: RequestInit): Promise<Response> {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    const method = (init?.method || "GET").toUpperCase();
    xhr.open(method, url, true);
    const headers = init?.headers;
    if (headers) {
      const h =
        headers instanceof Headers
          ? headers
          : new Headers(headers as HeadersInit);
      h.forEach((value, key) => xhr.setRequestHeader(key, value));
    }
    xhr.onload = () => {
      resolve(
        new Response(xhr.responseText, {
          status: xhr.status,
          statusText: xhr.statusText,
          headers: { "Content-Type": xhr.getResponseHeader("Content-Type") || "application/json" },
        }),
      );
    };
    xhr.onerror = () => reject(new TypeError("Failed to fetch"));
    xhr.ontimeout = () => reject(new TypeError("Failed to fetch"));
    xhr.timeout = 120_000;
    xhr.send((init?.body as Document | XMLHttpRequestBodyInit | null | undefined) ?? null);
  });
}

export async function apiFetch(
  path: string,
  init?: RequestInit,
): Promise<Response> {
  const url = apiUrl(path);
  try {
    return await fetch(url, init);
  } catch {
    if (typeof window === "undefined") throw new TypeError("Failed to fetch");
    return xhrFetch(url, init);
  }
}

/** Turn FastAPI `detail` (string | object | array) into a readable message. */
export function formatApiDetail(detail: unknown, fallback: string): string {
  if (typeof detail === "string" && detail.trim()) return detail;
  if (Array.isArray(detail)) {
    const parts = detail.map((item) => {
      if (typeof item === "string") return item;
      if (item && typeof item === "object" && "msg" in item) {
        const loc = Array.isArray((item as { loc?: unknown }).loc)
          ? (item as { loc: unknown[] }).loc.join(".")
          : "";
        const msg = String((item as { msg: unknown }).msg);
        return loc ? `${loc}: ${msg}` : msg;
      }
      return JSON.stringify(item);
    });
    if (parts.length) return parts.join("; ");
  }
  if (detail && typeof detail === "object") {
    try {
      return JSON.stringify(detail);
    } catch {
      /* ignore */
    }
  }
  return fallback;
}
