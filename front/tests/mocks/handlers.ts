import { delay, http, HttpResponse } from "msw"
import { DUMMY_MOVIE_CATALOG, DUMMY_RECOMMENDATION_IDS } from "@/tests/fixtures/movie-catalog"

const API_HOST = "https://api.test.local"

function parsePagination(url: URL) {
  const page = Number(url.searchParams.get("page") || "1")
  const pageSize = Number(url.searchParams.get("page_size") || "60")
  return {
    page: Number.isFinite(page) && page > 0 ? page : 1,
    pageSize: Number.isFinite(pageSize) && pageSize > 0 ? pageSize : 60,
  }
}

function paginate<T>(items: T[], page: number, pageSize: number) {
  const start = (page - 1) * pageSize
  const end = start + pageSize
  const paginated = items.slice(start, end)
  const total = items.length
  const totalPages = Math.max(1, Math.ceil(total / pageSize))

  return {
    items: paginated,
    page,
    page_size: pageSize,
    total,
    total_pages: totalPages,
  }
}

export const handlers = [
  // El catalogo ya es local, pero mantenemos estos endpoints por si algun
  // test legacy los necesita
  http.get(`${API_HOST}/movies`, async ({ request }) => {
    const { page, pageSize } = parsePagination(new URL(request.url))
    await delay(20)
    return HttpResponse.json(paginate(DUMMY_MOVIE_CATALOG, page, pageSize))
  }),

  http.get(`${API_HOST}/movies/search`, async ({ request }) => {
    const url = new URL(request.url)
    const query = (url.searchParams.get("q") || "").toLowerCase().trim()
    const { page, pageSize } = parsePagination(url)
    const filtered = DUMMY_MOVIE_CATALOG.filter(
      (movie) =>
        movie.title.toLowerCase().includes(query) ||
        movie.genres.some((genre) => genre.toLowerCase().includes(query)),
    )

    await delay(20)
    return HttpResponse.json(paginate(filtered, page, pageSize))
  }),

  http.post(`${API_HOST}/recommend`, async ({ request }) => {
    const body = (await request.json()) as { movie_ids?: number[] }
    const movieIds = body.movie_ids || []

    if (movieIds.length !== 5) {
      return HttpResponse.json({ message: "Se requieren exactamente 5 movie_ids." }, { status: 400 })
    }

    const recommendations = DUMMY_RECOMMENDATION_IDS.map((movieId, index) => ({
      movie: DUMMY_MOVIE_CATALOG.find((movie) => movie.id === movieId),
      probability: 0.91 - index * 0.07,
      reason: "Coincide con tus patrones de genero y calificacion.",
    }))

    await delay(50)
    return HttpResponse.json({
      recommendations,
    })
  }),

  http.get(`${API_HOST}/health`, async () => {
    return HttpResponse.json({ status: "ok" })
  }),

  http.get(`${API_HOST}/model/info`, async () => {
    return HttpResponse.json({
      version: "v1.0.0",
      metrics: { precision_at_3: 0.82 },
      trained_at: "2026-02-01",
    })
  }),
]
