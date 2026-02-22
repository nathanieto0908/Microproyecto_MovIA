import type { Movie, Recommendation } from "@/lib/types"

export const MOVIE_CATALOG: Movie[] = [
  {
    id: 27205,
    title: "Inception",
    year: 2010,
    rating: 8.4,
    genres: ["Accion", "Ciencia Ficcion", "Aventura"],
    poster: "https://image.tmdb.org/t/p/w500/oYuLEt3zVCKq57qu2F8dT7NIa6f.jpg",
    overview:
      "Un ladron que roba secretos corporativos a traves de la tecnologia de los suenos recibe la tarea inversa de implantar una idea.",
  },
  {
    id: 603,
    title: "The Matrix",
    year: 1999,
    rating: 8.2,
    genres: ["Accion", "Ciencia Ficcion"],
    poster: "https://image.tmdb.org/t/p/w500/f89U3ADr1oiB1s9GkdPOEpXUk5H.jpg",
    overview:
      "Un hacker descubre que la realidad es una simulacion creada por maquinas y se une a la rebelion.",
  },
  {
    id: 496243,
    title: "Parasite",
    year: 2019,
    rating: 8.5,
    genres: ["Comedia", "Suspenso", "Drama"],
    poster: "https://image.tmdb.org/t/p/w500/7IiTTgloJzvGI1TAYymCfbfl3vT.jpg",
    overview:
      "Una familia pobre se infiltra en la vida de una familia adinerada con consecuencias inesperadas.",
  },
  {
    id: 550,
    title: "Fight Club",
    year: 1999,
    rating: 8.4,
    genres: ["Drama"],
    poster: "https://image.tmdb.org/t/p/w500/pB8BM7pdSp6B6Ih7QZ4DrQ3PmJK.jpg",
    overview:
      "Un oficinista insomne y un vendedor de jabon forman un club de lucha clandestino.",
  },
  {
    id: 335984,
    title: "Blade Runner 2049",
    year: 2017,
    rating: 7.5,
    genres: ["Ciencia Ficcion", "Drama"],
    poster: "https://image.tmdb.org/t/p/w500/gajva2L0rPYkEWjzgFlBXCAVBE5.jpg",
    overview:
      "Un nuevo blade runner descubre un secreto que podria sumir a la sociedad en el caos.",
  },
  {
    id: 438631,
    title: "Dune",
    year: 2021,
    rating: 7.8,
    genres: ["Ciencia Ficcion", "Aventura"],
    poster: "https://image.tmdb.org/t/p/w500/d5NXSklXo0qyIYkgV94XAgMIckC.jpg",
    overview:
      "Paul Atreides se une a los Fremen para vengar la destruccion de su familia en el planeta desertico Arrakis.",
  },
  {
    id: 120467,
    title: "The Grand Budapest Hotel",
    year: 2014,
    rating: 8.0,
    genres: ["Comedia", "Drama"],
    poster: "https://image.tmdb.org/t/p/w500/eWdyYQreja6JGCzqHWXpWHDrrPo.jpg",
    overview:
      "Las aventuras de un legendario conserje de hotel y su protegido en un famoso hotel europeo.",
  },
  {
    id: 274,
    title: "The Silence of the Lambs",
    year: 1991,
    rating: 8.3,
    genres: ["Crimen", "Drama", "Suspenso"],
    poster: "https://image.tmdb.org/t/p/w500/uS9m8OBk1RVFDUGc1HeNLGABn0L.jpg",
    overview:
      "Una joven agente del FBI busca la ayuda del encarcelado canibal Hannibal Lecter para atrapar a un asesino en serie.",
  },
  {
    id: 129,
    title: "Spirited Away",
    year: 2001,
    rating: 8.5,
    genres: ["Animacion", "Familia", "Fantasia"],
    poster: "https://image.tmdb.org/t/p/w500/39wmItIWsg5sZMyRUHLkWBcuVCM.jpg",
    overview:
      "Una nina de 10 anos queda atrapada en un mundo espiritual y debe encontrar la forma de liberar a sus padres.",
  },
  {
    id: 872585,
    title: "Oppenheimer",
    year: 2023,
    rating: 8.3,
    genres: ["Drama", "Historia"],
    poster: "https://image.tmdb.org/t/p/w500/8Gxv8gSFCU0XGDykEGv7zR1n2ua.jpg",
    overview:
      "La historia del fisico J. Robert Oppenheimer y su papel en el desarrollo de la bomba atomica.",
  },
  {
    id: 545611,
    title: "Everything Everywhere All at Once",
    year: 2022,
    rating: 7.8,
    genres: ["Accion", "Aventura", "Ciencia Ficcion"],
    poster: "https://image.tmdb.org/t/p/w500/w3LxiVYdWWRvEVdn5RYq6jIqkb1.jpg",
    overview:
      "Una inmigrante china descubre que puede acceder a versiones paralelas de si misma en el multiverso.",
  },
  {
    id: 1124,
    title: "The Prestige",
    year: 2006,
    rating: 8.2,
    genres: ["Drama", "Misterio", "Ciencia Ficcion"],
    poster: "https://image.tmdb.org/t/p/w500/bdN3gXuIZYaJP7ftKK2sU0nPtEA.jpg",
    overview:
      "Dos magos rivales se enfrentan en una batalla de ingenio con consecuencias devastadoras.",
  },
  {
    id: 313369,
    title: "La La Land",
    year: 2016,
    rating: 7.9,
    genres: ["Comedia", "Drama", "Romance", "Musica"],
    poster: "https://image.tmdb.org/t/p/w500/uDO8zWDhfWwoFdKS4fzkUJt0Rf0.jpg",
    overview:
      "Un musico de jazz y una aspirante a actriz se enamoran en Los Angeles mientras persiguen sus suenos.",
  },
  {
    id: 419430,
    title: "Get Out",
    year: 2017,
    rating: 7.6,
    genres: ["Misterio", "Suspenso", "Horror"],
    poster: "https://image.tmdb.org/t/p/w500/qbaIViX3tAMIRfg4AEeOrkH5M6.jpg",
    overview:
      "Un joven afroamericano descubre un secreto perturbador cuando visita a la familia de su novia.",
  },
  {
    id: 324857,
    title: "Spider-Man: Into the Spider-Verse",
    year: 2018,
    rating: 8.4,
    genres: ["Accion", "Aventura", "Animacion", "Ciencia Ficcion"],
    poster: "https://image.tmdb.org/t/p/w500/iiZZdoQBEYBv6id8su7ImL0oCbD.jpg",
    overview:
      "Miles Morales se convierte en Spider-Man y se une a otros Spider-People de dimensiones alternativas.",
  },
  {
    id: 152601,
    title: "Her",
    year: 2013,
    rating: 7.9,
    genres: ["Romance", "Ciencia Ficcion", "Drama"],
    poster: "https://image.tmdb.org/t/p/w500/eCOtqtfvn7mxGl6nfmq4b1exJRc.jpg",
    overview:
      "Un hombre solitario desarrolla una relacion con un sistema operativo de inteligencia artificial.",
  },
  {
    id: 238,
    title: "The Godfather",
    year: 1972,
    rating: 8.7,
    genres: ["Drama", "Crimen"],
    poster: "https://image.tmdb.org/t/p/w500/3bhkrj58Vtu7enYsRolD1fZdja1.jpg",
    overview:
      "El patriarca de una dinastia del crimen organizado transfiere el control de su imperio a su reacio hijo.",
  },
  {
    id: 424,
    title: "Schindler's List",
    year: 1993,
    rating: 8.6,
    genres: ["Drama", "Historia", "Guerra"],
    poster: "https://image.tmdb.org/t/p/w500/sF1U4EUQS8YHUYjNl3pMGNIQyr0.jpg",
    overview:
      "Oskar Schindler salva mas de mil refugiados judios del Holocausto empleandolos en sus fabricas.",
  },
  {
    id: 37165,
    title: "The Truman Show",
    year: 1998,
    rating: 8.1,
    genres: ["Comedia", "Drama"],
    poster: "https://image.tmdb.org/t/p/w500/vuza0WqY239yBXOadKlGwJsZJFE.jpg",
    overview:
      "Un hombre descubre que toda su vida ha sido un reality show televisado.",
  },
  {
    id: 98,
    title: "Gladiator",
    year: 2000,
    rating: 8.2,
    genres: ["Accion", "Drama", "Aventura"],
    poster: "https://image.tmdb.org/t/p/w500/ty8TGRuvJLPUmAR1H1nRIsgCLin.jpg",
    overview:
      "Un general romano traicionado busca venganza como gladiador en la arena del Coliseo.",
  },
  {
    id: 122,
    title: "The Lord of the Rings: The Return of the King",
    year: 2003,
    rating: 8.5,
    genres: ["Aventura", "Fantasia", "Accion"],
    poster: "https://image.tmdb.org/t/p/w500/rCzpDGLbOoPwLjy3OAm5NUPOTrC.jpg",
    overview:
      "Aragorn es revelado como heredero de los reyes antiguos mientras la comunidad lucha por salvar la Tierra Media de las fuerzas de Sauron.",
  },
  {
    id: 299536,
    title: "Avengers: Infinity War",
    year: 2018,
    rating: 8.3,
    genres: ["Aventura", "Accion", "Ciencia Ficcion"],
    poster: "https://image.tmdb.org/t/p/w500/7WsyChQLEftFiDOVTGkv3hFpyyt.jpg",
    overview:
      "Los Avengers y sus aliados enfrentan a Thanos, quien busca reunir las Gemas del Infinito para imponer su voluntad sobre el universo.",
  },
  {
    id: 11324,
    title: "Shutter Island",
    year: 2010,
    rating: 8.2,
    genres: ["Drama", "Suspenso", "Misterio"],
    poster: "https://image.tmdb.org/t/p/w500/nrmXQ0zcZUL8jFLrakWc90IR8z9.jpg",
    overview:
      "Un alguacil investiga la desaparicion de una paciente de un hospital para criminales dementes, pero visiones perturbadoras comprometen sus esfuerzos.",
  },
  {
    id: 497,
    title: "The Green Mile",
    year: 1999,
    rating: 8.5,
    genres: ["Fantasia", "Drama", "Crimen"],
    poster: "https://image.tmdb.org/t/p/w500/8VG8fDNiy50H4FedGwdSVUPoaJe.jpg",
    overview:
      "En el corredor de la muerte de una prision del sur, el gigante y amable John Coffey posee el misterioso poder de sanar a las personas.",
  },
  {
    id: 16869,
    title: "Inglourious Basterds",
    year: 2009,
    rating: 8.2,
    genres: ["Drama", "Suspenso", "Guerra"],
    poster: "https://image.tmdb.org/t/p/w500/7sfbEnaARXDDhKm0CZ7D7uc2sbo.jpg",
    overview:
      "En la Francia ocupada por los nazis, un grupo de soldados judeo-americanos siembra el terror en el Tercer Reich.",
  },
  {
    id: 105,
    title: "Back to the Future",
    year: 1985,
    rating: 8.3,
    genres: ["Aventura", "Comedia", "Ciencia Ficcion"],
    poster: "https://image.tmdb.org/t/p/w500/vN5B5WgYscRGcQpVhHl6p9DDTP0.jpg",
    overview:
      "Marty McFly viaja accidentalmente a 1955 y debe asegurarse de que sus padres se enamoren para no desaparecer del futuro.",
  },
  {
    id: 8587,
    title: "The Lion King",
    year: 1994,
    rating: 8.3,
    genres: ["Familia", "Animacion", "Drama"],
    poster: "https://image.tmdb.org/t/p/w500/sKCr78MXSLixwmZ8DyJLrpMsd15.jpg",
    overview:
      "Un joven principe leon es expulsado de su manada por su cruel tio y debe crecer para reclamar su trono.",
  },
  {
    id: 77338,
    title: "The Intouchables",
    year: 2011,
    rating: 8.3,
    genres: ["Drama", "Comedia"],
    poster: "https://image.tmdb.org/t/p/w500/1QU7HKgsQbGpzsJbJK4pAVQV9F5.jpg",
    overview:
      "La historia real de un aristocrata cuadriplejico y un joven de los suburbios que se convierten en amigos improbables.",
  },
  {
    id: 240,
    title: "The Godfather Part II",
    year: 1974,
    rating: 8.6,
    genres: ["Drama", "Crimen"],
    poster: "https://image.tmdb.org/t/p/w500/hek3koDUyRQq7bkV3Ud9IB4AKLY.jpg",
    overview:
      "La saga continua con el joven Vito Corleone en Sicilia y Nueva York, mientras Michael expande el imperio familiar.",
  },
  {
    id: 10681,
    title: "WALL-E",
    year: 2008,
    rating: 8.1,
    genres: ["Animacion", "Familia", "Ciencia Ficcion"],
    poster: "https://image.tmdb.org/t/p/w500/hbhFnRzzg6ZDmm8YAmxBnQpQIPh.jpg",
    overview:
      "Un pequeno robot de limpieza descubre un nuevo proposito en la vida cuando conoce a una elegante robot exploradora.",
  },
  {
    id: 372058,
    title: "Your Name.",
    year: 2016,
    rating: 8.5,
    genres: ["Romance", "Animacion", "Drama"],
    poster: "https://image.tmdb.org/t/p/w500/q719jXXEzOoYaps6babgKnONONX.jpg",
    overview:
      "Dos estudiantes de preparatoria descubren que estan intercambiando cuerpos misteriosamente y luchan por encontrarse en la realidad.",
  },
  {
    id: 24,
    title: "Kill Bill: Vol. 1",
    year: 2003,
    rating: 8.0,
    genres: ["Accion", "Crimen"],
    poster: "https://image.tmdb.org/t/p/w500/v7TaX8kXMXs5yFFGR41guUDNcnB.jpg",
    overview:
      "Una asesina es traicionada por su jefe y sobrevive para planear una venganza sangrienta.",
  },
  {
    id: 1422,
    title: "The Departed",
    year: 2006,
    rating: 8.2,
    genres: ["Drama", "Suspenso", "Crimen"],
    poster: "https://image.tmdb.org/t/p/w500/nT97ifVT2J1yMQmeq20Qblg61T.jpg",
    overview:
      "Un policia encubierto infiltra la mafia irlandesa de Boston sin saber que el sindicato ha hecho lo mismo con la policia.",
  },
  {
    id: 637,
    title: "Life Is Beautiful",
    year: 1997,
    rating: 8.5,
    genres: ["Comedia", "Drama"],
    poster: "https://image.tmdb.org/t/p/w500/mfnkSeeVOBVheuyn2lo4tfmOPQb.jpg",
    overview:
      "Un padre judio italiano usa su imaginacion para proteger a su hijo de los horrores de un campo de concentracion nazi.",
  },
  {
    id: 263115,
    title: "Logan",
    year: 2017,
    rating: 7.8,
    genres: ["Accion", "Drama", "Ciencia Ficcion"],
    poster: "https://image.tmdb.org/t/p/w500/fnbjcRDYn6YviCcePDnGdyAkYsB.jpg",
    overview:
      "En un futuro cercano, un envejecido Logan cuida al Profesor X enfermo hasta que una joven mutante llega buscando ayuda.",
  },
]

/** Mapa de peliculas por ID para busqueda rapida. */
export const MOVIE_BY_ID = new Map(MOVIE_CATALOG.map((m) => [m.id, m]))

/** Todos los generos unicos del catalogo, ordenados alfabeticamente. */
export const ALL_GENRES: string[] = Array.from(
  new Set(MOVIE_CATALOG.flatMap((m) => m.genres)),
).sort()

/**
 * Busqueda local: filtra por titulo (case-insensitive).
 */
export function searchCatalog(query: string): Movie[] {
  const q = query.trim().toLowerCase()
  if (!q) return MOVIE_CATALOG
  return MOVIE_CATALOG.filter((m) => m.title.toLowerCase().includes(q))
}

/**
 * Filtra peliculas por genero.
 */
export function filterByGenre(movies: Movie[], genre: string | null): Movie[] {
  if (!genre) return movies
  return movies.filter((m) => m.genres.includes(genre))
}

/**
 * Recomendacion local de respaldo (basada en generos).
 * Se usa SOLO si el backend no esta disponible.
 */
export function getLocalRecommendations(selectedMovies: Movie[]): Recommendation[] {
  const selectedIds = new Set(selectedMovies.map((m) => m.id))
  const genreCount: Record<string, number> = {}

  selectedMovies.forEach((movie) => {
    movie.genres.forEach((genre) => {
      genreCount[genre] = (genreCount[genre] || 0) + 1
    })
  })

  const topGenres = Object.entries(genreCount)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 3)
    .map(([genre]) => genre)

  const candidates = MOVIE_CATALOG.filter((m) => !selectedIds.has(m.id))
    .map((movie) => {
      const genreScore = movie.genres.reduce((score, genre) => {
        return score + (genreCount[genre] || 0)
      }, 0)
      return { movie, genreScore }
    })
    .sort((a, b) => b.genreScore - a.genreScore || b.movie.rating - a.movie.rating)
    .slice(0, 5)

  const maxScore = candidates[0]?.genreScore || 1

  const reasons = [
    "Basado en tu interes por el GENRE, esta pelicula comparte la misma intensidad narrativa.",
    "Tu gusto por el GENRE encaja perfectamente con el estilo de esta obra maestra.",
    "Como fan del GENRE, encontraras aqui una experiencia cinematografica que te atrapara.",
    "Tus selecciones revelan afinidad por el GENRE. Esta pelicula lleva ese genero a otro nivel.",
    "Detectamos tu pasion por el GENRE. Esta es una joya imperdible del genero.",
  ]

  return candidates.map(({ movie, genreScore }) => {
    const matchingGenres = movie.genres.filter((g) => topGenres.includes(g))
    const genreText =
      matchingGenres.length > 0
        ? matchingGenres.slice(0, 2).join(" y ").toLowerCase()
        : movie.genres[0]?.toLowerCase() ?? "cine"

    const reasonIndex = movie.id % reasons.length
    const matchPercent = Math.round((genreScore / maxScore) * 100)

    return {
      movie,
      reason: reasons[reasonIndex].replace("GENRE", genreText),
      matchPercent: Math.max(matchPercent, 72),
    }
  })
}
