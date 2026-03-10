import { normalizeMoviesPage, normalizeRecommendations } from "@/lib/api/adapters"
import { apiRequest } from "@/lib/api/client"
import type { HealthResponse, ModelInfoResponse, RecommendRequest } from "@/lib/api/types"
import type { Movie, MoviesPage, Recommendation } from "@/lib/types"

interface MoviesQueryParams {
  page?: number
  pageSize?: number
}

export async function getMovies(params: MoviesQueryParams = {}): Promise<MoviesPage> {
  const { page = 1, pageSize = 60 } = params
  const raw = await apiRequest<unknown>("/movies", {
    method: "GET",
    query: {
      page,
      page_size: pageSize,
    },
  })

  return normalizeMoviesPage(raw)
}

export async function searchMovies(
  query: string,
  params: MoviesQueryParams = {},
): Promise<Movie[]> {
  const { page = 1, pageSize = 60 } = params
  const raw = await apiRequest<unknown>("/movies/search", {
    method: "GET",
    query: {
      q: query,
      page,
      page_size: pageSize,
    },
  })

  return normalizeMoviesPage(raw).items
}

export async function getRecommendations(
  movieIds: number[],
  knownMovies: Movie[] = [],
): Promise<Recommendation[]> {
  const payload: RecommendRequest = { movie_ids: movieIds }
  const raw = await apiRequest<unknown>("/recommend", {
    method: "POST",
    body: payload,
  })

  return normalizeRecommendations(raw, knownMovies)
}

export async function getHealth(): Promise<HealthResponse> {
  return apiRequest<HealthResponse>("/health", { method: "GET" })
}

export async function getModelInfo(): Promise<ModelInfoResponse> {
  return apiRequest<ModelInfoResponse>("/model/info", { method: "GET" })
}
