/**
 * API client wrapper with cookie-based authentication.
 * All requests include credentials (HTTP-only JWT cookies).
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

export class ApiError extends Error {
  constructor(
    public status: number,
    public detail: string,
  ) {
    super(detail);
    this.name = "ApiError";
  }
}

const AUTH_PATHS = ["/auth/login", "/auth/register", "/auth/logout"];

async function handleResponse<T>(response: Response, path: string): Promise<T> {
  if (!response.ok) {
    const isAuthEndpoint = AUTH_PATHS.some((p) => path.includes(p));

    // Auto-redirect to login on 401 — but only for non-auth endpoints
    // (a 401 on /auth/login means wrong credentials, not expired session)
    if (response.status === 401 && !isAuthEndpoint && typeof window !== "undefined") {
      window.location.href = "/login";
      throw new ApiError(401, "Session expired");
    }
    const body = await response.json().catch(() => ({ detail: response.statusText }));
    // FastAPI validation errors (422) return detail as an array of objects
    let detail: string;
    if (Array.isArray(body.detail)) {
      detail = body.detail
        .map((e: { msg?: string }) => (e.msg || String(e)).replace(/^Value error, /i, ""))
        .join(". ");
    } else {
      detail = body.detail || response.statusText;
    }
    throw new ApiError(response.status, detail);
  }
  return response.json() as Promise<T>;
}

export async function apiGet<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}/api/v1${path}`, {
    method: "GET",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
  });
  return handleResponse<T>(response, path);
}

export async function apiPost<T>(path: string, body?: unknown): Promise<T> {
  const response = await fetch(`${API_BASE_URL}/api/v1${path}`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  });
  return handleResponse<T>(response, path);
}

export async function apiPut<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(`${API_BASE_URL}/api/v1${path}`, {
    method: "PUT",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return handleResponse<T>(response, path);
}

export async function apiPatch<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(`${API_BASE_URL}/api/v1${path}`, {
    method: "PATCH",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return handleResponse<T>(response, path);
}

export async function apiDelete<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}/api/v1${path}`, {
    method: "DELETE",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
  });
  return handleResponse<T>(response, path);
}

export async function apiUpload<T>(path: string, file: File): Promise<T> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE_URL}/api/v1${path}`, {
    method: "POST",
    credentials: "include",
    body: formData,
  });
  return handleResponse<T>(response, path);
}
