"use client"

import { useCallback, useEffect, useMemo, useRef, useState } from "react"
import { Header } from "@/components/header"
import { WelcomeScreen } from "@/components/welcome-screen"
import { SearchBar } from "@/components/search-bar"
import { MovieCard } from "@/components/movie-card"
import { SelectionTracker } from "@/components/selection-tracker"
import { ConfirmationModal } from "@/components/confirmation-modal"
import { Recommendations } from "@/components/recommendations"
import {
  getMovies,
  searchMovies as apiSearchMovies,
  getRecommendations as requestRecommendations,
} from "@/lib/api/endpoints"
import {
  MOVIE_CATALOG,
  MOVIE_BY_ID,
  searchCatalog,
  filterByGenre,
  getLocalRecommendations,
} from "@/lib/data/movie-catalog"
import type { Movie, Recommendation } from "@/lib/types"
import { Film, Loader2 } from "lucide-react"

type Step = "welcome" | "selection" | "results"
const SEARCH_DEBOUNCE_MS = 300

function getErrorMessage(error: unknown, fallback: string): string {
  if (error instanceof Error && error.message.trim()) {
    return error.message
  }
  return fallback
}

export default function Home() {
  const [step, setStep] = useState<Step>("welcome")
  const [search, setSearch] = useState("")
  const [selected, setSelected] = useState<Movie[]>([])
  const [recommendations, setRecommendations] = useState<Recommendation[] | null>(null)
  const [recommendError, setRecommendError] = useState<string | null>(null)
  const [isSubmittingRecommendation, setIsSubmittingRecommendation] = useState(false)
  const [activeGenre, setActiveGenre] = useState<string | null>(null)
  const [showConfirmation, setShowConfirmation] = useState(false)
  const [debouncedSearch, setDebouncedSearch] = useState("")
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  // API state
  const [apiMovies, setApiMovies] = useState<Movie[]>([])
  const [backendAvailable, setBackendAvailable] = useState(false)
  const [isLoadingMovies, setIsLoadingMovies] = useState(true)
  const [isSearching, setIsSearching] = useState(false)
  const [totalMovies, setTotalMovies] = useState(0)
  const fetchIdRef = useRef(0)

  // Load movies from backend on mount
  useEffect(() => {
    let cancelled = false
    setIsLoadingMovies(true)

    getMovies({ page: 1, pageSize: 60 })
      .then((page) => {
        if (cancelled) return
        setApiMovies(page.items)
        setTotalMovies(page.total)
        setBackendAvailable(true)
      })
      .catch(() => {
        if (!cancelled) setBackendAvailable(false)
      })
      .finally(() => {
        if (!cancelled) setIsLoadingMovies(false)
      })

    return () => {
      cancelled = true
    }
  }, [])

  // Debounce search
  useEffect(() => {
    if (timerRef.current) clearTimeout(timerRef.current)
    timerRef.current = setTimeout(() => {
      setDebouncedSearch(search)
    }, SEARCH_DEBOUNCE_MS)
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current)
    }
  }, [search])

  // Fetch from backend when search changes (API mode)
  useEffect(() => {
    if (!backendAvailable) return

    const currentId = ++fetchIdRef.current
    const q = debouncedSearch.trim()

    if (!q) {
      // Reset to full catalog from API
      setIsSearching(true)
      getMovies({ page: 1, pageSize: 60 })
        .then((page) => {
          if (currentId === fetchIdRef.current) {
            setApiMovies(page.items)
            setTotalMovies(page.total)
          }
        })
        .catch(() => {})
        .finally(() => {
          if (currentId === fetchIdRef.current) setIsSearching(false)
        })
      return
    }

    setIsSearching(true)
    apiSearchMovies(q, { pageSize: 60 })
      .then((results) => {
        if (currentId === fetchIdRef.current) {
          setApiMovies(results)
        }
      })
      .catch(() => {})
      .finally(() => {
        if (currentId === fetchIdRef.current) setIsSearching(false)
      })
  }, [debouncedSearch, backendAvailable])

  // Compute displayed movies
  const movies = useMemo(() => {
    if (backendAvailable) return apiMovies
    return MOVIE_CATALOG
  }, [backendAvailable, apiMovies])

  // Compute genres from current movies
  const allGenres = useMemo(() => {
    return Array.from(new Set(movies.flatMap((m) => m.genres))).sort()
  }, [movies])

  // Filter by search (local only when backend unavailable) and genre
  const filtered = useMemo(() => {
    let result = movies

    // Local search only when backend is not available
    if (!backendAvailable && debouncedSearch.trim()) {
      result = searchCatalog(debouncedSearch)
    }

    return filterByGenre(result, activeGenre)
  }, [movies, debouncedSearch, backendAvailable, activeGenre])

  const toggleMovie = (movie: Movie) => {
    setSelected((prev) => {
      const exists = prev.find((m) => m.id === movie.id)
      if (exists) return prev.filter((m) => m.id !== movie.id)
      if (prev.length >= 5) return prev
      return [...prev, movie]
    })
  }

  const handleShowConfirmation = () => {
    if (selected.length === 5 && !isSubmittingRecommendation) {
      setRecommendError(null)
      setShowConfirmation(true)
    }
  }

  const handleConfirm = async () => {
    if (selected.length !== 5 || isSubmittingRecommendation) return

    setIsSubmittingRecommendation(true)
    setRecommendError(null)

    try {
      const recs = await requestRecommendations(
        selected.map((movie) => movie.id),
        movies,
      )

      if (recs.length === 0) {
        throw new Error("El backend no devolvio recomendaciones.")
      }

      // Enrich with poster from known movies
      const knownMovies = new Map([
        ...MOVIE_CATALOG.map((m) => [m.id, m] as const),
        ...movies.map((m) => [m.id, m] as const),
      ])
      const enriched = recs.map((rec) => {
        const known = knownMovies.get(rec.movie.id)
        if (known && (!rec.movie.poster || rec.movie.poster === "/placeholder.svg")) {
          return { ...rec, movie: { ...rec.movie, poster: known.poster } }
        }
        return rec
      })

      setRecommendations(enriched.slice(0, 3))
      setShowConfirmation(false)
      setStep("results")
    } catch (error) {
      console.warn("Backend no disponible, usando recomendacion local:", error)
      const localRecs = getLocalRecommendations(selected)
      if (localRecs.length > 0) {
        setRecommendations(localRecs.slice(0, 3))
        setShowConfirmation(false)
        setStep("results")
      } else {
        setRecommendError(getErrorMessage(error, "No se pudieron generar recomendaciones."))
      }
    } finally {
      setIsSubmittingRecommendation(false)
    }
  }

  const handleStartOver = () => {
    setStep("welcome")
    setSelected([])
    setRecommendations(null)
    setSearch("")
    setDebouncedSearch("")
    setRecommendError(null)
    setActiveGenre(null)
    setShowConfirmation(false)
  }

  // --- STEP 1: Welcome ---
  if (step === "welcome") {
    return <WelcomeScreen onContinue={() => setStep("selection")} />
  }

  // --- STEP 3: Results ---
  if (step === "results" && recommendations) {
    return (
      <div className="min-h-screen flex flex-col bg-background">
        <Header title="MovIA" step={3} />
        <main className="flex-1 w-full max-w-6xl mx-auto px-4 py-8">
          <Recommendations recommendations={recommendations} onBack={handleStartOver} />
        </main>
      </div>
    )
  }

  // --- STEP 2: Selection ---
  return (
    <div className="min-h-screen flex flex-col bg-background">
      <Header title="MovIA" step={2} />

      <main className="flex-1 w-full max-w-6xl mx-auto px-4 py-6">
        <div className="flex flex-col gap-5 animate-in fade-in slide-in-from-bottom-4 duration-500">
          {/* Selection tracker at top */}
          <SelectionTracker
            selected={selected}
            onRemove={toggleMovie}
            onGetRecommendations={handleShowConfirmation}
            isSubmitting={isSubmittingRecommendation}
          />

          {/* Search + Filters */}
          <div className="flex flex-col gap-3">
            <SearchBar
              value={search}
              onChange={setSearch}
              isLoading={isSearching}
              disabled={false}
            />

            <div className="flex items-center gap-2 overflow-x-auto pb-1 scrollbar-hide">
              <button
                onClick={() => setActiveGenre(null)}
                className={`shrink-0 px-3 py-1.5 rounded-full text-xs font-medium transition-all ${
                  !activeGenre
                    ? "bg-primary text-primary-foreground"
                    : "bg-secondary text-secondary-foreground hover:bg-muted"
                }`}
              >
                Todas
              </button>
              {allGenres.map((genre) => (
                <button
                  key={genre}
                  onClick={() => setActiveGenre(genre === activeGenre ? null : genre)}
                  className={`shrink-0 px-3 py-1.5 rounded-full text-xs font-medium transition-all ${
                    activeGenre === genre
                      ? "bg-primary text-primary-foreground"
                      : "bg-secondary text-secondary-foreground hover:bg-muted"
                  }`}
                >
                  {genre}
                </button>
              ))}
            </div>
          </div>

          {recommendError && (
            <div className="px-4 py-3 rounded-xl bg-destructive/10 border border-destructive/20">
              <p className="text-sm text-destructive">{recommendError}</p>
            </div>
          )}

          {/* Catalog info */}
          {backendAvailable && !isLoadingMovies && (
            <p className="text-xs text-muted-foreground">
              Mostrando {filtered.length} de {totalMovies.toLocaleString()} peliculas del catalogo
            </p>
          )}

          {/* Loading state */}
          {isLoadingMovies && (
            <div className="flex flex-col items-center justify-center py-16 gap-3">
              <Loader2 className="w-8 h-8 animate-spin text-primary" />
              <p className="text-sm text-muted-foreground">Cargando catalogo de peliculas...</p>
            </div>
          )}

          {/* Movie grid */}
          {!isLoadingMovies && filtered.length > 0 && (
            <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 lg:grid-cols-6 gap-3">
              {filtered.map((movie) => (
                <MovieCard
                  key={movie.id}
                  movie={movie}
                  isSelected={!!selected.find((m) => m.id === movie.id)}
                  onToggle={toggleMovie}
                  disabled={selected.length >= 5}
                />
              ))}
            </div>
          )}

          {/* Empty state */}
          {!isLoadingMovies && filtered.length === 0 && (
            <div className="flex flex-col items-center justify-center py-16 gap-3">
              <Film className="w-10 h-10 text-muted-foreground/50" />
              <p className="text-sm text-muted-foreground">
                {search.trim()
                  ? "No se encontraron peliculas para tu busqueda."
                  : "No hay peliculas disponibles por ahora."}
              </p>
            </div>
          )}
        </div>
      </main>

      {/* Confirmation Modal */}
      {showConfirmation && (
        <ConfirmationModal
          selected={selected}
          onConfirm={handleConfirm}
          onBack={() => setShowConfirmation(false)}
          isLoading={isSubmittingRecommendation}
          errorMessage={recommendError}
        />
      )}
    </div>
  )
}
