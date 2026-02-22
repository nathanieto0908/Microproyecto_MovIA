import { getBackendBaseUrl, normalizeBackendBaseUrl } from "@/lib/api/config"
import { afterEach, describe, expect, it, vi } from "vitest"

const ORIGINAL_ENV = { ...process.env }

describe("API config", () => {
  afterEach(() => {
    vi.unstubAllEnvs()
    Object.keys(process.env).forEach((key) => {
      if (!(key in ORIGINAL_ENV)) {
        delete process.env[key]
      }
    })
    Object.entries(ORIGINAL_ENV).forEach(([key, value]) => {
      process.env[key] = value
    })
  })

  it("respeta URL completa cuando ya incluye protocolo", () => {
    expect(normalizeBackendBaseUrl("https://api.example.com/")).toBe("https://api.example.com")
  })

  it("agrega protocolo cuando solo se recibe host", () => {
    vi.stubEnv("NEXT_PUBLIC_BACKEND_PROTOCOL", "http")
    expect(normalizeBackendBaseUrl("api.example.com")).toBe("http://api.example.com")
  })

  it("usa https por defecto si no se define protocolo", () => {
    vi.stubEnv("NEXT_PUBLIC_BACKEND_PROTOCOL", "")
    expect(normalizeBackendBaseUrl("api.example.com")).toBe("https://api.example.com")
  })

  it("lanza error cuando NEXT_PUBLIC_BACKEND_IP esta vacia", () => {
    expect(() => normalizeBackendBaseUrl("   ")).toThrow(/esta vacia/i)
  })

  it("devuelve string vacio cuando falta NEXT_PUBLIC_BACKEND_IP (proxy mode)", () => {
    delete process.env.NEXT_PUBLIC_BACKEND_IP
    expect(getBackendBaseUrl()).toBe("")
  })

  it("devuelve base URL normalizada desde variable de entorno", () => {
    process.env.NEXT_PUBLIC_BACKEND_IP = "api.test.local/"
    process.env.NEXT_PUBLIC_BACKEND_PROTOCOL = "https"
    expect(getBackendBaseUrl()).toBe("https://api.test.local")
  })
})
