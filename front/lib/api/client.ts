import { getBackendBaseUrl } from "@/lib/api/config"

const DEFAULT_TIMEOUT_MS = 12000

export class ApiError extends Error {
  status?: number
  details?: unknown

  constructor(message: string, status?: number, details?: unknown) {
    super(message)
    this.name = "ApiError"
    this.status = status
    this.details = details
  }
}

interface ApiRequestOptions extends Omit<RequestInit, "body"> {
  body?: BodyInit | object | null
  query?: Record<string, string | number | boolean | null | undefined>
  timeoutMs?: number
}

function buildUrl(path: string, query?: ApiRequestOptions["query"]): string {
  const normalizedPath = path.startsWith("/") ? path : `/${path}`
  const base = getBackendBaseUrl()

  if (!base) {
    if (!query) return normalizedPath
    const params = new URLSearchParams()
    Object.entries(query).forEach(([key, value]) => {
      if (value === null || value === undefined || value === "") return
      params.set(key, String(value))
    })
    const qs = params.toString()
    return qs ? `${normalizedPath}?${qs}` : normalizedPath
  }

  const url = new URL(`${base}${normalizedPath}`)

  if (!query) {
    return url.toString()
  }

  Object.entries(query).forEach(([key, value]) => {
    if (value === null || value === undefined || value === "") return
    url.searchParams.set(key, String(value))
  })

  return url.toString()
}

function parseBody(body: ApiRequestOptions["body"]): BodyInit | undefined {
  if (!body) return undefined
  if (typeof body === "string" || body instanceof FormData || body instanceof URLSearchParams) {
    return body
  }
  return JSON.stringify(body)
}

export async function apiRequest<T>(path: string, options: ApiRequestOptions = {}): Promise<T> {
  const { query, timeoutMs = DEFAULT_TIMEOUT_MS, headers, body, signal, ...rest } = options
  const url = buildUrl(path, query)

  const controller = new AbortController()
  const timeout = setTimeout(() => controller.abort(), timeoutMs)

  if (signal) {
    signal.addEventListener("abort", () => controller.abort(), { once: true })
  }

  const parsedBody = parseBody(body)
  const resolvedHeaders = new Headers(headers ?? {})
  if (parsedBody && !resolvedHeaders.has("Content-Type")) {
    resolvedHeaders.set("Content-Type", "application/json")
  }

  try {
    const response = await fetch(url, {
      ...rest,
      body: parsedBody,
      headers: resolvedHeaders,
      signal: controller.signal,
    })

    const contentType = response.headers.get("content-type") || ""
    const hasJson = contentType.includes("application/json")
    const payload = hasJson ? await response.json().catch(() => null) : await response.text()

    if (!response.ok) {
      const errorMessage =
        (payload &&
          typeof payload === "object" &&
          "message" in payload &&
          typeof payload.message === "string" &&
          payload.message) ||
        `Error HTTP ${response.status}`

      throw new ApiError(errorMessage, response.status, payload)
    }

    return payload as T
  } catch (error) {
    if (error instanceof ApiError) throw error
    if (error instanceof DOMException && error.name === "AbortError") {
      throw new ApiError("La solicitud excedio el tiempo limite.", 408)
    }
    if (error instanceof Error) {
      throw new ApiError(error.message)
    }
    throw new ApiError("Error inesperado de red.")
  } finally {
    clearTimeout(timeout)
  }
}
