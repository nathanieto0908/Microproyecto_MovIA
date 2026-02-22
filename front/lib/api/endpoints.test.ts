import { http, HttpResponse } from "msw"
import { DUMMY_MOVIE_CATALOG } from "@/tests/fixtures/movie-catalog"
import { server } from "@/tests/mocks/server"
import {
  getHealth,
  getModelInfo,
  getMovies,
  getRecommendations,
  searchMovies,
} from "@/lib/api/endpoints"
import { describe, expect, it } from "vitest"

describe("API endpoints", () => {
  it("obtiene peliculas paginadas desde /movies", async () => {
    const page = await getMovies({ page: 1, pageSize: 4 })

    expect(page.items).toHaveLength(4)
    expect(page.total).toBe(DUMMY_MOVIE_CATALOG.length)
    expect(page.items[0].title).toBe("Inception")
  })

  it("busca peliculas por texto", async () => {
    const results = await searchMovies("matrix")
    expect(results).toHaveLength(1)
    expect(results[0].title).toBe("The Matrix")
  })

  it("obtiene recomendaciones y normaliza matchPercent desde probability", async () => {
    const selectedIds = [27205, 603, 496243, 550, 335984]
    const recommendations = await getRecommendations(selectedIds, DUMMY_MOVIE_CATALOG)

    expect(recommendations).toHaveLength(3)
    expect(recommendations[0].movie.title).toBe("Dune")
    expect(recommendations[0].matchPercent).toBeGreaterThan(80)
  })

  it("hace fallback de pelicula cuando /recommend solo devuelve movie_id", async () => {
    server.use(
      http.post("https://api.test.local/recommend", async () => {
        return HttpResponse.json({
          recommendations: [{ movie_id: 999, probability: 0.42 }],
        })
      }),
    )

    const recommendations = await getRecommendations(
      [27205, 603, 496243, 550, 335984],
      DUMMY_MOVIE_CATALOG,
    )

    expect(recommendations).toHaveLength(1)
    expect(recommendations[0].movie.title).toBe("Pelicula 999")
    expect(recommendations[0].matchPercent).toBe(42)
  })

  it("consulta /health y /model/info", async () => {
    const health = await getHealth()
    const modelInfo = await getModelInfo()

    expect(health.status).toBe("ok")
    expect(modelInfo.version).toBe("v1.0.0")
  })
})
