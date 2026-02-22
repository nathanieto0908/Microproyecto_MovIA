export interface Movie {
  id: number
  title: string
  year: number
  rating: number
  genres: string[]
  poster: string
  overview: string
}

export interface Recommendation {
  movie: Movie
  reason: string
  matchPercent: number
}

export interface MoviesPage {
  items: Movie[]
  page: number
  pageSize: number
  total: number
  totalPages: number
}
