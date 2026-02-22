import type { Movie, MoviesPage, Recommendation } from "@/lib/types"

const DEFAULT_POSTER = "/placeholder.svg"
const DEFAULT_REASON = "Recomendacion generada por el modelo con base en tus preferencias."

type UnknownRecord = Record<string, unknown>

function isRecord(value: unknown): value is UnknownRecord {
  return typeof value === "object" && value !== null
}

function asString(value: unknown): string | null {
  if (typeof value === "string") return value
  if (typeof value === "number" || typeof value === "boolean") return String(value)
  return null
}

function asNumber(value: unknown): number | null {
  if (typeof value === "number" && Number.isFinite(value)) return value
  if (typeof value === "string" && value.trim() !== "") {
    const parsed = Number(value)
    if (Number.isFinite(parsed)) return parsed
  }
  return null
}

function extractYear(value: unknown): number {
  const numeric = asNumber(value)
  if (numeric !== null) return Math.floor(numeric)

  const asText = asString(value)
  if (!asText) return 0

  const match = asText.match(/(\d{4})/)
  return match ? Number(match[1]) : 0
}

function normalizeGenres(rawGenres: unknown): string[] {
  if (typeof rawGenres === "string" && rawGenres.trim()) {
    const separator = rawGenres.includes(",") ? "," : rawGenres.includes("|") ? "|" : null
    if (separator) {
      return rawGenres.split(separator).map((g) => g.trim()).filter(Boolean)
    }
    return [rawGenres.trim()]
  }

  if (!Array.isArray(rawGenres)) return []

  return rawGenres
    .map((item) => {
      if (typeof item === "string") return item.trim()
      if (isRecord(item)) {
        const name = asString(item.name ?? item.genre)
        return name ? name.trim() : ""
      }
      return ""
    })
    .filter(Boolean)
}

function pickFirstString(record: UnknownRecord, keys: string[]): string | null {
  for (const key of keys) {
    const value = asString(record[key])
    if (value && value.trim()) return value
  }
  return null
}

function normalizePoster(record: UnknownRecord): string {
  const posterValue = pickFirstString(record, [
    "poster",
    "poster_url",
    "poster_path",
    "image",
    "image_url",
  ])

  if (!posterValue) return DEFAULT_POSTER
  if (posterValue.startsWith("http://") || posterValue.startsWith("https://")) return posterValue
  if (posterValue.startsWith("/")) return posterValue

  return `/${posterValue}`
}

export function normalizeMovie(rawMovie: unknown): Movie | null {
  if (!isRecord(rawMovie)) return null

  const id = asNumber(rawMovie.id ?? rawMovie.movie_id)
  const title = pickFirstString(rawMovie, ["title", "name"])
  if (id === null || !title) return null

  const year = extractYear(rawMovie.year ?? rawMovie.release_year ?? rawMovie.release_date)
  const rating = asNumber(rawMovie.rating ?? rawMovie.vote_average ?? rawMovie.score) ?? 0
  const genres = normalizeGenres(rawMovie.genres)
  const overview =
    pickFirstString(rawMovie, ["overview", "description", "synopsis", "plot"]) || ""

  return {
    id,
    title,
    year,
    rating,
    genres,
    poster: normalizePoster(rawMovie),
    overview,
  }
}

function getCollection(raw: unknown): unknown[] {
  if (Array.isArray(raw)) return raw
  if (!isRecord(raw)) return []

  const candidates = [raw.items, raw.results, raw.movies, raw.data, raw.recommendations]
  for (const candidate of candidates) {
    if (Array.isArray(candidate)) return candidate
    if (isRecord(candidate) && Array.isArray(candidate.items)) return candidate.items
  }
  return []
}

export function normalizeMoviesPage(raw: unknown): MoviesPage {
  const items = getCollection(raw).map(normalizeMovie).filter((movie): movie is Movie => !!movie)

  if (!isRecord(raw)) {
    return {
      items,
      page: 1,
      pageSize: items.length,
      total: items.length,
      totalPages: items.length > 0 ? 1 : 0,
    }
  }

  const page = asNumber(raw.page ?? raw.current_page ?? raw.pageNumber) ?? 1
  const pageSize =
    asNumber(raw.page_size ?? raw.per_page ?? raw.pageSize ?? raw.limit) ?? items.length
  const total = asNumber(raw.total ?? raw.count ?? raw.total_items) ?? items.length
  const totalPages =
    asNumber(raw.total_pages ?? raw.totalPages) ??
    (pageSize > 0 ? Math.max(1, Math.ceil(total / pageSize)) : 1)

  return {
    items,
    page,
    pageSize,
    total,
    totalPages,
  }
}

function resolveRecommendationMovie(
  item: UnknownRecord,
  movieById: Map<number, Movie>,
): Movie | null {
  const embeddedMovie = normalizeMovie(item.movie ?? item.film)
  if (embeddedMovie) return embeddedMovie

  const movieId = asNumber(item.movie_id ?? item.id)
  if (movieId === null) return null

  // Try known movies first (from catalog/search)
  const known = movieById.get(movieId)
  if (known) return known

  // Try normalizing the item itself (backend may include title, genres, etc.)
  const fromItem = normalizeMovie(item)
  if (fromItem) return fromItem

  return {
    id: movieId,
    title: `Pelicula ${movieId}`,
    year: 0,
    rating: 0,
    genres: [],
    poster: DEFAULT_POSTER,
    overview: "",
  }
}

function normalizeMatchPercent(item: UnknownRecord): number {
  const probability =
    asNumber(item.probability ?? item.prob ?? item.score ?? item.match_percent ?? item.matchPercent) ??
    0

  if (probability <= 1) {
    return Math.round(probability * 100)
  }

  return Math.round(probability)
}

export function normalizeRecommendations(
  raw: unknown,
  knownMovies: Movie[] = [],
): Recommendation[] {
  const movieById = new Map<number, Movie>(knownMovies.map((movie) => [movie.id, movie]))
  const records = getCollection(raw).filter((item): item is UnknownRecord => isRecord(item))

  return records
    .map((item) => {
      const movie = resolveRecommendationMovie(item, movieById)
      if (!movie) return null

      return {
        movie,
        reason: pickFirstString(item, ["reason", "explanation"]) || DEFAULT_REASON,
        matchPercent: Math.max(0, Math.min(100, normalizeMatchPercent(item))),
      }
    })
    .filter((item): item is Recommendation => !!item)
}
