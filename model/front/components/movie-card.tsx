"use client"

import { Star, Check, Plus } from "lucide-react"
import type { Movie } from "@/lib/types"

interface MovieCardProps {
  movie: Movie
  isSelected: boolean
  onToggle: (movie: Movie) => void
  disabled: boolean
}

export function MovieCard({ movie, isSelected, onToggle, disabled }: MovieCardProps) {
  const canSelect = !disabled || isSelected

  return (
    <button
      onClick={() => canSelect && onToggle(movie)}
      disabled={!canSelect}
      className={`group relative flex flex-col rounded-xl overflow-hidden transition-all duration-300 text-left ${
        isSelected
          ? "ring-2 ring-primary shadow-lg shadow-primary/10 scale-[1.02]"
          : canSelect
            ? "hover:scale-[1.03] hover:shadow-lg hover:shadow-primary/5"
            : "opacity-40 cursor-not-allowed"
      }`}
    >
      {/* Poster */}
      <div className="relative aspect-[2/3] w-full overflow-hidden bg-secondary">
        <img
          src={movie.poster || "/placeholder.svg"}
          alt={`Poster de ${movie.title}`}
          className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
          crossOrigin="anonymous"
          loading="lazy"
        />

        {/* Overlay gradient */}
        <div className="absolute inset-0 bg-gradient-to-t from-background/90 via-background/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />

        {/* Selection indicator */}
        <div
          className={`absolute top-2 right-2 w-8 h-8 rounded-full flex items-center justify-center transition-all duration-300 ${
            isSelected
              ? "bg-primary text-primary-foreground scale-100"
              : "bg-background/60 text-foreground backdrop-blur-sm scale-0 group-hover:scale-100"
          }`}
        >
          {isSelected ? (
            <Check className="w-4 h-4" strokeWidth={3} />
          ) : (
            <Plus className="w-4 h-4" />
          )}
        </div>

        {/* Rating badge */}
        <div className="absolute bottom-2 left-2 flex items-center gap-1 px-2 py-1 rounded-md bg-background/70 backdrop-blur-sm">
          <Star className="w-3 h-3 text-primary fill-primary" />
          <span className="text-xs font-semibold text-foreground">{movie.rating}</span>
        </div>
      </div>

      {/* Info */}
      <div className="flex flex-col gap-1 p-3 bg-card">
        <h3 className="text-sm font-semibold text-foreground leading-tight line-clamp-1">
          {movie.title}
        </h3>
        <div className="flex items-center gap-2">
          <span className="text-xs text-muted-foreground">{movie.year}</span>
          <span className="w-1 h-1 rounded-full bg-muted-foreground/50" />
          <span className="text-xs text-muted-foreground line-clamp-1">
            {movie.genres.slice(0, 2).join(", ")}
          </span>
        </div>
      </div>
    </button>
  )
}
