import {
  normalizeMovie,
  normalizeMoviesPage,
  normalizeRecommendations,
} from "@/lib/api/adapters"
import { DUMMY_MOVIE_CATALOG } from "@/tests/fixtures/movie-catalog"
import { describe, expect, it } from "vitest"

describe("API adapters", () => {
  it("normaliza movie con variantes de campos", () => {
    const movie = normalizeMovie({
      movie_id: "123",
      name: "Arrival",
      release_date: "2016-01-01",
      vote_average: "7.9",
      genres: [{ name: "Ciencia Ficcion" }, { name: "Drama" }],
      poster_url: "https://cdn.test/arrival.jpg",
      synopsis: "Descripcion",
    })

    expect(movie).toEqual({
      id: 123,
      title: "Arrival",
      year: 2016,
      rating: 7.9,
      genres: ["Ciencia Ficcion", "Drama"],
      poster: "https://cdn.test/arrival.jpg",
      overview: "Descripcion",
    })
  })

  it("normaliza paginas aunque la respuesta venga como arreglo", () => {
    const page = normalizeMoviesPage(DUMMY_MOVIE_CATALOG.slice(0, 2))

    expect(page.items).toHaveLength(2)
    expect(page.page).toBe(1)
    expect(page.totalPages).toBe(1)
  })

  it("normaliza recomendaciones con movie embebida", () => {
    const recommendations = normalizeRecommendations({
      recommendations: [
        {
          movie: DUMMY_MOVIE_CATALOG[0],
          probability: 0.87,
          reason: "Coincidencia alta",
        },
      ],
    })

    expect(recommendations).toHaveLength(1)
    expect(recommendations[0].movie.id).toBe(27205) // Inception TMDb ID
    expect(recommendations[0].matchPercent).toBe(87)
    expect(recommendations[0].reason).toBe("Coincidencia alta")
  })

  it("normaliza recomendaciones con fallback por id conocido", () => {
    const recommendations = normalizeRecommendations(
      {
        recommendations: [
          {
            movie_id: 603, // The Matrix TMDb ID
            match_percent: 91,
          },
        ],
      },
      DUMMY_MOVIE_CATALOG,
    )

    expect(recommendations).toHaveLength(1)
    expect(recommendations[0].movie.title).toBe("The Matrix")
    expect(recommendations[0].reason).toContain("Recomendacion generada")
    expect(recommendations[0].matchPercent).toBe(91)
  })

  it("normaliza genres cuando llegan como string separado por comas", () => {
    const movie = normalizeMovie({
      movie_id: 10,
      title: "Test",
      genres: "Action, Comedy, Drama",
    })

    expect(movie).not.toBeNull()
    expect(movie!.genres).toEqual(["Action", "Comedy", "Drama"])
  })

  it("normaliza recomendaciones usando datos del propio item como fallback", () => {
    const recommendations = normalizeRecommendations(
      {
        recommendations: [
          {
            movie_id: 999,
            title: "Pelicula Desconocida",
            genres: ["Sci-Fi"],
            year: 2023,
            vote_average: 7.5,
            probability: 0.75,
          },
        ],
      },
      [],
    )

    expect(recommendations).toHaveLength(1)
    expect(recommendations[0].movie.title).toBe("Pelicula Desconocida")
    expect(recommendations[0].movie.genres).toEqual(["Sci-Fi"])
    expect(recommendations[0].matchPercent).toBe(75)
  })

  it("devuelve pagina vacia cuando el payload no es record", () => {
    const page = normalizeMoviesPage("payload-invalido")

    expect(page.items).toHaveLength(0)
    expect(page.page).toBe(1)
    expect(page.totalPages).toBe(0)
  })

  it("normaliza recomendaciones sin probabilidad y usa 0 por defecto", () => {
    const recommendations = normalizeRecommendations({
      recommendations: [{ movie_id: 27205 }], // Inception TMDb ID
    }, DUMMY_MOVIE_CATALOG)

    expect(recommendations).toHaveLength(1)
    expect(recommendations[0].matchPercent).toBe(0)
  })
})
