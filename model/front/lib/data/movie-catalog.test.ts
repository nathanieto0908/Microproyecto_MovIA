import { describe, expect, it } from "vitest"
import {
  MOVIE_CATALOG,
  MOVIE_BY_ID,
  ALL_GENRES,
  searchCatalog,
  filterByGenre,
  getLocalRecommendations,
} from "@/lib/data/movie-catalog"

describe("MOVIE_CATALOG", () => {
  it("contiene 35 peliculas", () => {
    expect(MOVIE_CATALOG).toHaveLength(35)
  })

  it("cada pelicula tiene todos los campos requeridos", () => {
    for (const movie of MOVIE_CATALOG) {
      expect(movie.id).toBeGreaterThan(0)
      expect(movie.title).toBeTruthy()
      expect(movie.year).toBeGreaterThanOrEqual(1970)
      expect(movie.rating).toBeGreaterThan(0)
      expect(movie.genres.length).toBeGreaterThan(0)
      expect(movie.poster).toMatch(/^https:\/\/image\.tmdb\.org/)
      expect(movie.overview).toBeTruthy()
    }
  })

  it("no tiene IDs duplicados", () => {
    const ids = MOVIE_CATALOG.map((m) => m.id)
    expect(new Set(ids).size).toBe(ids.length)
  })

  it("todos los poster URLs apuntan al CDN de TMDb", () => {
    for (const movie of MOVIE_CATALOG) {
      expect(movie.poster).toContain("image.tmdb.org/t/p/w500/")
    }
  })
})

describe("MOVIE_BY_ID", () => {
  it("permite buscar por ID", () => {
    const inception = MOVIE_BY_ID.get(27205)
    expect(inception).toBeDefined()
    expect(inception!.title).toBe("Inception")
  })

  it("retorna undefined para ID inexistente", () => {
    expect(MOVIE_BY_ID.get(999999)).toBeUndefined()
  })
})

describe("ALL_GENRES", () => {
  it("contiene generos sin duplicados", () => {
    const uniqueGenres = new Set(ALL_GENRES)
    expect(uniqueGenres.size).toBe(ALL_GENRES.length)
  })

  it("esta ordenado alfabeticamente", () => {
    const sorted = [...ALL_GENRES].sort()
    expect(ALL_GENRES).toEqual(sorted)
  })

  it("incluye generos principales", () => {
    expect(ALL_GENRES).toContain("Drama")
    expect(ALL_GENRES).toContain("Accion")
    expect(ALL_GENRES).toContain("Ciencia Ficcion")
  })
})

describe("searchCatalog", () => {
  it("retorna todas si la query esta vacia", () => {
    expect(searchCatalog("")).toHaveLength(35)
    expect(searchCatalog("  ")).toHaveLength(35)
  })

  it("busca por titulo case-insensitive", () => {
    const results = searchCatalog("matrix")
    expect(results).toHaveLength(1)
    expect(results[0].title).toBe("The Matrix")
  })

  it("retorna vacio si no hay coincidencias", () => {
    expect(searchCatalog("zzzzz")).toHaveLength(0)
  })

  it("busca parcialmente", () => {
    const results = searchCatalog("the")
    expect(results.length).toBeGreaterThan(1)
  })
})

describe("filterByGenre", () => {
  it("retorna todas si genre es null", () => {
    expect(filterByGenre(MOVIE_CATALOG, null)).toHaveLength(35)
  })

  it("filtra por genero especifico", () => {
    const dramas = filterByGenre(MOVIE_CATALOG, "Drama")
    expect(dramas.length).toBeGreaterThan(0)
    dramas.forEach((m) => {
      expect(m.genres).toContain("Drama")
    })
  })

  it("retorna vacio si no hay peliculas del genero", () => {
    expect(filterByGenre(MOVIE_CATALOG, "GeneroInexistente")).toHaveLength(0)
  })
})

describe("getLocalRecommendations", () => {
  it("genera recomendaciones basadas en generos", () => {
    const selected = MOVIE_CATALOG.slice(0, 5)
    const recs = getLocalRecommendations(selected)

    expect(recs.length).toBeGreaterThan(0)
    expect(recs.length).toBeLessThanOrEqual(5)
  })

  it("no recomienda peliculas ya seleccionadas", () => {
    const selected = MOVIE_CATALOG.slice(0, 5)
    const selectedIds = new Set(selected.map((m) => m.id))
    const recs = getLocalRecommendations(selected)

    recs.forEach((rec) => {
      expect(selectedIds.has(rec.movie.id)).toBe(false)
    })
  })

  it("cada recomendacion tiene movie, reason y matchPercent", () => {
    const selected = MOVIE_CATALOG.slice(0, 5)
    const recs = getLocalRecommendations(selected)

    recs.forEach((rec) => {
      expect(rec.movie).toBeDefined()
      expect(rec.movie.id).toBeGreaterThan(0)
      expect(rec.reason).toBeTruthy()
      expect(rec.matchPercent).toBeGreaterThanOrEqual(72)
      expect(rec.matchPercent).toBeLessThanOrEqual(100)
    })
  })
})
