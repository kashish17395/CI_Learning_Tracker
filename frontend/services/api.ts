export class ApiError extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string,
  ) {
    super(message);
  }
}
function csrf() {
  return typeof document === "undefined"
    ? ""
    : document.cookie
        .split("; ")
        .find((c) => c.startsWith("lt_csrf="))
        ?.split("=")[1] || "";
}
let refreshTask: Promise<boolean> | null = null;
export async function refreshSession() {
  if (!refreshTask) {
    const rotate = async () => {
      // Another tab may have renewed the shared cookies while this tab waited.
      const current = await fetch("/api/v1/auth/me", {
        credentials: "include",
        cache: "no-store",
      });
      if (current.ok) return true;
      const response = await fetch("/api/v1/auth/refresh", {
        method: "POST",
        credentials: "include",
        headers: { "X-CSRF-Token": csrf() },
      });
      return response.ok;
    };
    // Web Locks serialize refresh across tabs on HTTPS and localhost.
    const rotation =
      typeof navigator !== "undefined" && navigator.locks
        ? navigator.locks.request("learning-session-refresh", rotate)
        : rotate();
    refreshTask = Promise.resolve(rotation)
      .catch(() => false)
      .finally(() => {
        refreshTask = null;
      });
  }
  return refreshTask;
}
export async function api<T>(
  path: string,
  options: RequestInit = {},
  retry = true,
  responseType: "json" | "blob" = "json",
): Promise<T> {
  const headers = new Headers(options.headers);
  if (options.body && !(options.body instanceof FormData))
    headers.set("Content-Type", "application/json");
  if (options.method && options.method !== "GET")
    headers.set("X-CSRF-Token", csrf());
  const response = await fetch("/api/v1" + path, {
    ...options,
    headers,
    credentials: "include",
    cache: "no-store",
  });
  if (
    response.status === 401 &&
    retry &&
    !path.startsWith("/auth/login") &&
    (await refreshSession())
  )
    return api(path, options, false, responseType);
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    if (
      response.status === 401 &&
      !path.startsWith("/auth/login") &&
      typeof window !== "undefined"
    )
      window.location.assign("/login");
    const details = body.error?.details
      ?.map(
        (d: { field: string; message: string }) => `${d.field}: ${d.message}`,
      )
      .join("; ");
    throw new ApiError(
      response.status,
      body.error?.code || "REQUEST_FAILED",
      details || body.error?.message || "Request failed. Please try again.",
    );
  }
  if (response.status === 204) return undefined as T;
  if (responseType === "blob") return (await response.blob()) as unknown as T;
  return response.json();
}

export async function downloadCertificate(id: string, filename: string) {
  const blob = await api<Blob>(
    `/certificates/${encodeURIComponent(id)}/download`,
    {},
    true,
    "blob",
  );
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  setTimeout(() => URL.revokeObjectURL(url), 30000);
}
export const post = <T>(path: string, value: unknown) =>
  api<T>(path, { method: "POST", body: JSON.stringify(value) });
export const patch = <T>(path: string, value: unknown) =>
  api<T>(path, { method: "PATCH", body: JSON.stringify(value) });
export function query(
  values: Record<string, string | number | boolean | null | undefined>,
) {
  const p = new URLSearchParams();
  Object.entries(values).forEach(([key, value]) => {
    if (value !== "" && value != null) p.set(key, String(value));
  });
  return p.toString() ? "?" + p.toString() : "";
}
