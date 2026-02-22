import "@testing-library/jest-dom/vitest"
import { cleanup } from "@testing-library/react"
import { afterAll, afterEach, beforeAll } from "vitest"
import { server } from "@/tests/mocks/server"

process.env.NEXT_PUBLIC_BACKEND_IP = "api.test.local"
process.env.NEXT_PUBLIC_BACKEND_PROTOCOL = "https"

beforeAll(() => {
  server.listen({ onUnhandledRequest: "error" })
})

afterEach(() => {
  server.resetHandlers()
  cleanup()
})

afterAll(() => {
  server.close()
})
