const FALLBACK_PROTOCOL = "https"

export function normalizeBackendBaseUrl(rawValue: string): string {
  const trimmed = rawValue.trim().replace(/\/+$/, "")
  if (!trimmed) {
    throw new Error("NEXT_PUBLIC_BACKEND_IP esta vacia")
  }

  if (/^https?:\/\//i.test(trimmed)) {
    return trimmed
  }

  const protocol = (process.env.NEXT_PUBLIC_BACKEND_PROTOCOL || FALLBACK_PROTOCOL)
    .trim()
    .replace("://", "")

  return `${protocol}://${trimmed}`
}

/**
 * Returns the backend base URL.
 * - If NEXT_PUBLIC_BACKEND_IP is set, normalizes and returns it (direct mode).
 * - If not set, returns "" (same-origin proxy mode for nginx).
 */
export function getBackendBaseUrl(): string {
  const rawValue = process.env.NEXT_PUBLIC_BACKEND_IP

  if (!rawValue || !rawValue.trim()) {
    return ""
  }

  return normalizeBackendBaseUrl(rawValue)
}
