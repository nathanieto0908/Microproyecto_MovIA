import { ApiError, apiRequest } from "@/lib/api/client"
import { afterEach, describe, expect, it, vi } from "vitest"

describe("apiRequest", () => {
  afterEach(() => {
    vi.restoreAllMocks()
    vi.useRealTimers()
  })

  it("devuelve payload JSON cuando la respuesta es exitosa", async () => {
    vi.spyOn(global, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ ok: true }), {
        status: 200,
        headers: {
          "Content-Type": "application/json",
        },
      }),
    )

    const response = await apiRequest<{ ok: boolean }>("/health", { method: "GET" })
    expect(response).toEqual({ ok: true })
  })

  it("lanza ApiError con el mensaje del backend cuando la respuesta HTTP falla", async () => {
    vi.spyOn(global, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ message: "Backend caido" }), {
        status: 503,
        headers: {
          "Content-Type": "application/json",
        },
      }),
    )

    await expect(apiRequest("/movies")).rejects.toMatchObject<ApiError>({
      message: "Backend caido",
      status: 503,
    })
  })

  it("lanza timeout cuando la solicitud excede el limite", async () => {
    vi.useFakeTimers()

    vi.spyOn(global, "fetch").mockImplementation((_, init) => {
      return new Promise((_, reject) => {
        init?.signal?.addEventListener("abort", () => {
          reject(new DOMException("Aborted", "AbortError"))
        })
      })
    })

    const request = apiRequest("/movies", { timeoutMs: 5 })
    const expectation = expect(request).rejects.toMatchObject<ApiError>({
      message: "La solicitud excedio el tiempo limite.",
      status: 408,
    })

    await vi.advanceTimersByTimeAsync(10)
    await expectation
  })

  it("agrega query params y serializa body JSON", async () => {
    const fetchMock = vi.spyOn(global, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ status: "ok" }), {
        status: 200,
        headers: {
          "Content-Type": "application/json",
        },
      }),
    )

    await apiRequest<{ status: string }>("/recommend", {
      method: "POST",
      query: { source: "web", page: 1 },
      body: { movie_ids: [1, 2, 3, 4, 5] },
    })

    const [url, init] = fetchMock.mock.calls[0]
    expect(String(url)).toContain("/recommend?source=web&page=1")
    expect(init?.body).toBe(JSON.stringify({ movie_ids: [1, 2, 3, 4, 5] }))
    expect(new Headers(init?.headers).get("Content-Type")).toBe("application/json")
  })

  it("maneja respuestas no JSON", async () => {
    vi.spyOn(global, "fetch").mockResolvedValue(
      new Response("pong", {
        status: 200,
        headers: {
          "Content-Type": "text/plain",
        },
      }),
    )

    const response = await apiRequest<string>("/health")
    expect(response).toBe("pong")
  })

  it("usa mensaje HTTP por defecto cuando el backend falla sin campo message", async () => {
    vi.spyOn(global, "fetch").mockResolvedValue(
      new Response("falla", {
        status: 502,
        headers: {
          "Content-Type": "text/plain",
        },
      }),
    )

    await expect(apiRequest("/movies")).rejects.toMatchObject<ApiError>({
      message: "Error HTTP 502",
      status: 502,
    })
  })

  it("respeta abort signal externo", async () => {
    const externalController = new AbortController()
    vi.spyOn(global, "fetch").mockImplementation((_, init) => {
      return new Promise((_, reject) => {
        init?.signal?.addEventListener("abort", () => {
          reject(new DOMException("Aborted", "AbortError"))
        })
      })
    })

    const request = apiRequest("/movies", {
      signal: externalController.signal,
      timeoutMs: 1000,
    })

    externalController.abort()

    await expect(request).rejects.toMatchObject<ApiError>({
      message: "La solicitud excedio el tiempo limite.",
      status: 408,
    })
  })

  it("serializa body string sin convertirlo a JSON", async () => {
    const fetchMock = vi.spyOn(global, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ ok: true }), {
        status: 200,
        headers: {
          "Content-Type": "application/json",
        },
      }),
    )

    await apiRequest("/recommend", {
      method: "POST",
      body: "{\"movie_ids\":[1,2,3,4,5]}",
    })

    const [, init] = fetchMock.mock.calls[0]
    expect(init?.body).toBe("{\"movie_ids\":[1,2,3,4,5]}")
  })

  it("envuelve errores no-Error en ApiError generico", async () => {
    vi.spyOn(global, "fetch").mockRejectedValue("network-down")
    await expect(apiRequest("/movies")).rejects.toMatchObject<ApiError>({
      message: "Error inesperado de red.",
    })
  })
})
