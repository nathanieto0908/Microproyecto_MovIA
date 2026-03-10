"use client"

import { X, ChevronRight } from "lucide-react"
import type { Movie } from "@/lib/types"

interface SelectionTrackerProps {
  selected: Movie[]
  onRemove: (movie: Movie) => void
  onGetRecommendations: () => void
  isSubmitting?: boolean
}

export function SelectionTracker({
  selected,
  onRemove,
  onGetRecommendations,
  isSubmitting = false,
}: SelectionTrackerProps) {
  const slots = Array.from({ length: 5 }, (_, i) => selected[i] || null)
  const isComplete = selected.length === 5

  return (
    <div className="flex flex-col gap-4 p-4 rounded-2xl bg-card/60 border border-border/40">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="text-sm font-semibold text-foreground">Tus selecciones</span>
          <span className="text-xs px-2 py-0.5 rounded-full bg-primary/10 text-primary font-medium">
            {selected.length}/5
          </span>
        </div>
        {/* Progress bar */}
        <div className="w-24 h-1.5 rounded-full bg-muted overflow-hidden">
          <div
            className="h-full rounded-full bg-primary transition-all duration-500 ease-out"
            style={{ width: `${(selected.length / 5) * 100}%` }}
          />
        </div>
      </div>

      {/* Selected movie chips */}
      <div className="flex items-center gap-2">
        {slots.map((movie, i) => (
          <div
            key={movie ? movie.id : `empty-${i}`}
            className={`relative flex-1 aspect-[2/3] rounded-lg overflow-hidden transition-all duration-500 ${
              movie ? "ring-1 ring-primary/30" : "border border-dashed border-muted-foreground/20"
            }`}
          >
            {movie ? (
              <>
                <img
                  src={movie.poster || "/placeholder.svg"}
                  alt={movie.title}
                  className="w-full h-full object-cover"
                  crossOrigin="anonymous"
                />
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    onRemove(movie)
                  }}
                  className="absolute top-1 right-1 w-5 h-5 rounded-full bg-background/80 backdrop-blur-sm flex items-center justify-center hover:bg-destructive hover:text-destructive-foreground transition-colors"
                  aria-label={`Remover ${movie.title}`}
                >
                  <X className="w-3 h-3" />
                </button>
              </>
            ) : (
              <div className="w-full h-full flex items-center justify-center bg-secondary/20">
                <span className="text-xs text-muted-foreground/50 font-medium">{i + 1}</span>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* CTA Button */}
      <button
        onClick={onGetRecommendations}
        disabled={!isComplete || isSubmitting}
        className={`flex items-center justify-center gap-2 w-full py-3 rounded-xl text-sm font-semibold transition-all duration-300 ${
          isComplete && !isSubmitting
            ? "bg-primary text-primary-foreground hover:brightness-110 shadow-lg shadow-primary/20"
            : "bg-muted/50 text-muted-foreground cursor-not-allowed"
        }`}
      >
        {isSubmitting ? (
          "Generando recomendaciones..."
        ) : isComplete ? (
          <>
            Continuar
            <ChevronRight className="w-4 h-4" />
          </>
        ) : (
          `Selecciona ${5 - selected.length} mas`
        )}
      </button>
    </div>
  )
}
