"use client"

import { useState, useEffect } from "react"
import { Star, RotateCcw, Play, ChevronDown, ChevronUp, Heart } from "lucide-react"
import type { Recommendation } from "@/lib/types"

interface RecommendationsProps {
  recommendations: Recommendation[]
  onBack: () => void
}

export function Recommendations({ recommendations, onBack }: RecommendationsProps) {
  const [revealed, setRevealed] = useState(0)
  const [expandedCard, setExpandedCard] = useState<number | null>(null)
  const [liked, setLiked] = useState<Set<number>>(new Set())

  useEffect(() => {
    // Reveal cards one by one
    if (revealed < recommendations.length) {
      const timer = setTimeout(() => setRevealed((prev) => prev + 1), 300)
      return () => clearTimeout(timer)
    }
  }, [revealed, recommendations.length])

  const toggleLike = (id: number) => {
    setLiked((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  return (
    <div className="flex flex-col gap-8 animate-in fade-in duration-500">
      {/* Header area */}
      <div className="flex flex-col gap-6">
        <div className="flex items-start justify-between">
          <div className="flex flex-col gap-1">
            <h2 className="text-2xl sm:text-3xl font-bold text-foreground text-balance">
              Listo, <span className="text-primary">Jersons</span>
            </h2>
            <p className="text-sm text-muted-foreground">
              Encontramos {recommendations.length} peliculas que creemos te van a encantar
            </p>
          </div>
          <button
            onClick={onBack}
            className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm text-muted-foreground hover:text-foreground hover:bg-secondary transition-all"
          >
            <RotateCcw className="w-4 h-4" />
            <span className="hidden sm:inline">Empezar de nuevo</span>
          </button>
        </div>
      </div>

      {/* Featured recommendation (first one) */}
      {recommendations.length > 0 && revealed > 0 && (
        <div
          className="relative rounded-2xl overflow-hidden bg-card border border-border/30 animate-in fade-in slide-in-from-bottom-4 duration-700"
        >
          <div className="flex flex-col sm:flex-row">
            {/* Large poster */}
            <div className="relative sm:w-64 md:w-72 shrink-0 aspect-[2/3] sm:aspect-auto overflow-hidden">
              <img
                src={recommendations[0].movie.poster || "/placeholder.svg"}
                alt={recommendations[0].movie.title}
                className="w-full h-full object-cover"
                crossOrigin="anonymous"
              />
              <div className="absolute inset-0 bg-gradient-to-r from-transparent to-card/80 hidden sm:block" />
              <div className="absolute inset-0 bg-gradient-to-t from-card via-transparent to-transparent sm:hidden" />

              {/* Match badge */}
              <div className="absolute top-4 left-4 px-3 py-1.5 rounded-full bg-primary text-primary-foreground text-xs font-bold">
                {recommendations[0].matchPercent}% match
              </div>
            </div>

            {/* Content */}
            <div className="flex flex-col justify-center gap-5 p-6 sm:p-8 flex-1">
              <div className="flex flex-col gap-2">
                <div className="flex items-center gap-3">
                  <span className="text-xs font-semibold text-primary tracking-wide uppercase">Recomendacion principal</span>
                </div>
                <h3 className="text-2xl sm:text-3xl font-bold text-foreground text-balance">
                  {recommendations[0].movie.title}
                </h3>
                <div className="flex items-center gap-3 text-sm text-muted-foreground">
                  <div className="flex items-center gap-1">
                    <Star className="w-4 h-4 text-primary fill-primary" />
                    <span className="font-semibold text-foreground">{recommendations[0].movie.rating}</span>
                  </div>
                  <span>{recommendations[0].movie.year}</span>
                  <span>{recommendations[0].movie.genres.join(", ")}</span>
                </div>
              </div>

              <p className="text-sm text-muted-foreground leading-relaxed max-w-md">
                {recommendations[0].movie.overview}
              </p>

              {/* Why badge */}
              <div className="flex flex-col gap-1.5 px-4 py-3 rounded-xl bg-primary/5 border border-primary/10 max-w-md">
                <span className="text-[11px] font-bold uppercase tracking-wider text-primary">
                  Por que te gustara
                </span>
                <p className="text-sm text-secondary-foreground leading-relaxed">
                  {recommendations[0].reason}
                </p>
              </div>

              <div className="flex items-center gap-3">
                <button className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-primary text-primary-foreground text-sm font-semibold hover:brightness-110 transition-all">
                  <Play className="w-4 h-4 fill-current" />
                  Ver trailer
                </button>
                <button
                  onClick={() => toggleLike(recommendations[0].movie.id)}
                  className={`p-2.5 rounded-xl border transition-all ${
                    liked.has(recommendations[0].movie.id)
                      ? "bg-primary/10 border-primary/30 text-primary"
                      : "border-border/50 text-muted-foreground hover:text-foreground hover:border-border"
                  }`}
                >
                  <Heart className={`w-4 h-4 ${liked.has(recommendations[0].movie.id) ? "fill-current" : ""}`} />
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Other recommendations grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {recommendations.slice(1).map((rec, index) => {
          const isRevealed = index + 1 < revealed
          const isExpanded = expandedCard === rec.movie.id

          return (
            <div
              key={rec.movie.id}
              className={`group flex flex-col rounded-2xl overflow-hidden bg-card border border-border/30 hover:border-primary/20 transition-all duration-500 ${
                isRevealed ? "animate-in fade-in slide-in-from-bottom-4 duration-700" : "opacity-0"
              }`}
              style={{ animationDelay: `${index * 150}ms`, animationFillMode: "both" }}
            >
              {/* Poster */}
              <div className="relative aspect-[2/3] w-full overflow-hidden">
                <img
                  src={rec.movie.poster || "/placeholder.svg"}
                  alt={rec.movie.title}
                  className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-105"
                  crossOrigin="anonymous"
                  loading="lazy"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-card via-transparent to-transparent" />

                {/* Match percent badge */}
                <div className="absolute top-3 left-3 px-2.5 py-1 rounded-full bg-background/70 backdrop-blur-sm">
                  <span className="text-xs font-bold text-primary">
                    {rec.matchPercent}%
                  </span>
                </div>

                {/* Like button */}
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    toggleLike(rec.movie.id)
                  }}
                  className={`absolute top-3 right-3 w-8 h-8 rounded-full flex items-center justify-center transition-all ${
                    liked.has(rec.movie.id)
                      ? "bg-primary/20 text-primary backdrop-blur-sm"
                      : "bg-background/50 text-muted-foreground backdrop-blur-sm opacity-0 group-hover:opacity-100"
                  }`}
                >
                  <Heart className={`w-3.5 h-3.5 ${liked.has(rec.movie.id) ? "fill-current" : ""}`} />
                </button>

                {/* Rating */}
                <div className="absolute bottom-3 right-3 flex items-center gap-1 px-2 py-1 rounded-md bg-background/70 backdrop-blur-sm">
                  <Star className="w-3 h-3 text-primary fill-primary" />
                  <span className="text-xs font-semibold text-foreground">{rec.movie.rating}</span>
                </div>
              </div>

              {/* Info */}
              <div className="flex flex-col gap-3 p-4">
                <div>
                  <h3 className="text-sm font-bold text-foreground leading-tight line-clamp-1">
                    {rec.movie.title}
                  </h3>
                  <div className="flex items-center gap-2 mt-1">
                    <span className="text-xs text-muted-foreground">{rec.movie.year}</span>
                    <span className="w-1 h-1 rounded-full bg-muted-foreground/40" />
                    <span className="text-xs text-muted-foreground line-clamp-1">
                      {rec.movie.genres.slice(0, 2).join(", ")}
                    </span>
                  </div>
                </div>

                {/* Expandable why badge */}
                <button
                  onClick={() => setExpandedCard(isExpanded ? null : rec.movie.id)}
                  className="flex items-center justify-between gap-2 px-3 py-2 rounded-lg bg-primary/5 border border-primary/10 text-left transition-all hover:bg-primary/8"
                >
                  <span className="text-[10px] font-bold uppercase tracking-wider text-primary">
                    Por que te gustara
                  </span>
                  {isExpanded ? (
                    <ChevronUp className="w-3 h-3 text-primary shrink-0" />
                  ) : (
                    <ChevronDown className="w-3 h-3 text-primary shrink-0" />
                  )}
                </button>
                {isExpanded && (
                  <p className="text-xs text-secondary-foreground leading-relaxed animate-in fade-in slide-in-from-top-2 duration-300 px-1">
                    {rec.reason}
                  </p>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
