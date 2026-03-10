import type { Movie } from "@/lib/types"

/**
 * Subconjunto del catalogo para tests.
 * Los IDs coinciden con los TMDb IDs reales del backend.
 */
export const DUMMY_MOVIE_CATALOG: Movie[] = [
  {
    id: 27205,
    title: "Inception",
    year: 2010,
    rating: 8.4,
    genres: ["Accion", "Ciencia Ficcion", "Aventura"],
    poster: "https://image.tmdb.org/t/p/w500/oYuLEt3zVCKq57qu2F8dT7NIa6f.jpg",
    overview: "Un ladron que roba secretos corporativos mediante suenos compartidos.",
  },
  {
    id: 603,
    title: "The Matrix",
    year: 1999,
    rating: 8.2,
    genres: ["Accion", "Ciencia Ficcion"],
    poster: "https://image.tmdb.org/t/p/w500/f89U3ADr1oiB1s9GkdPOEpXUk5H.jpg",
    overview: "Un hacker descubre que la realidad es una simulacion.",
  },
  {
    id: 496243,
    title: "Parasite",
    year: 2019,
    rating: 8.5,
    genres: ["Comedia", "Suspenso", "Drama"],
    poster: "https://image.tmdb.org/t/p/w500/7IiTTgloJzvGI1TAYymCfbfl3vT.jpg",
    overview: "Una familia pobre se infiltra en una familia adinerada.",
  },
  {
    id: 550,
    title: "Fight Club",
    year: 1999,
    rating: 8.4,
    genres: ["Drama"],
    poster: "https://image.tmdb.org/t/p/w500/pB8BM7pdSp6B6Ih7QZ4DrQ3PmJK.jpg",
    overview: "Un oficinista insomne forma un club de lucha clandestino.",
  },
  {
    id: 335984,
    title: "Blade Runner 2049",
    year: 2017,
    rating: 7.5,
    genres: ["Ciencia Ficcion", "Drama"],
    poster: "https://image.tmdb.org/t/p/w500/gajva2L0rPYkEWjzgFlBXCAVBE5.jpg",
    overview: "Un blade runner descubre un secreto enterrado por decadas.",
  },
  {
    id: 438631,
    title: "Dune",
    year: 2021,
    rating: 7.8,
    genres: ["Ciencia Ficcion", "Aventura"],
    poster: "https://image.tmdb.org/t/p/w500/d5NXSklXo0qyIYkgV94XAgMIckC.jpg",
    overview: "Paul Atreides busca justicia y supervivencia en Arrakis.",
  },
  {
    id: 1124,
    title: "The Prestige",
    year: 2006,
    rating: 8.2,
    genres: ["Drama", "Misterio", "Ciencia Ficcion"],
    poster: "https://image.tmdb.org/t/p/w500/bdN3gXuIZYaJP7ftKK2sU0nPtEA.jpg",
    overview: "Dos magos rivales arriesgan todo por el truco definitivo.",
  },
  {
    id: 238,
    title: "The Godfather",
    year: 1972,
    rating: 8.7,
    genres: ["Drama", "Crimen"],
    poster: "https://image.tmdb.org/t/p/w500/3bhkrj58Vtu7enYsRolD1fZdja1.jpg",
    overview: "El patriarca del crimen organizado transfiere el control a su hijo.",
  },
]

export const DUMMY_RECOMMENDATION_IDS = [438631, 1124, 238]
