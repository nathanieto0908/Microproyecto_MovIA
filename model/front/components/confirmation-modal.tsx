"use client"

import { useEffect } from "react"
import { X, Star, ArrowLeft, ChevronRight } from "lucide-react"
import type { Movie } from "@/lib/types"

interface ConfirmationModalProps {
  selected: Movie[]
  onConfirm: () => void
  onBack: () => void
  isLoading?: boolean
  errorMessage?: string | null
}

export function ConfirmationModal({
  selected,
  onConfirm,
  onBack,
  isLoading = false,
  errorMessage = null,
}: ConfirmationModalProps) {
  useEffect(() => {
    document.body.style.overflow = "hidden"
    return () => {
      document.body.style.overflow = ""
    }
  }, [])

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-background/80 backdrop-blur-md animate-in fade-in duration-300"
        onClick={onBack}
        onKeyDown={(e) => e.key === "Escape" && onBack()}
        role="button"
        tabIndex={0}
        aria-label="Cerrar modal"
      />

      {/* Modal */}
      <div className="relative z-10 w-full max-w-2xl flex flex-col gap-6 p-6 sm:p-8 rounded-3xl bg-card border border-border/50 shadow-2xl animate-in fade-in zoom-in-95 slide-in-from-bottom-4 duration-500">
        {/* Close */}
        <button
          onClick={onBack}
          className="absolute top-4 right-4 p-2 rounded-full hover:bg-secondary transition-colors"
          aria-label="Cerrar"
        >
          <X className="w-4 h-4 text-muted-foreground" />
        </button>

        {/* Header */}
        <div className="flex flex-col items-center gap-2 text-center">
          <h2 className="text-xl sm:text-2xl font-bold text-foreground text-balance">
            Estas son tus 5 peliculas
          </h2>
          <p className="text-sm text-muted-foreground">
            Confirma tu seleccion para obtener recomendaciones personalizadas
          </p>
        </div>

        {/* Movies grid */}
        <div className="grid grid-cols-5 gap-3">
          {selected.map((movie, i) => (
            <div
              key={movie.id}
              className="flex flex-col gap-2 animate-in fade-in slide-in-from-bottom-2 duration-500"
              style={{ animationDelay: `${i * 80}ms` }}
            >
              <div className="relative aspect-[2/3] rounded-xl overflow-hidden ring-1 ring-primary/20">
                <img
                  src={movie.poster || "/placeholder.svg"}
                  alt={movie.title}
                  className="w-full h-full object-cover"
                  crossOrigin="anonymous"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-background/60 to-transparent" />
                <div className="absolute bottom-1.5 left-1.5 flex items-center gap-0.5 px-1.5 py-0.5 rounded bg-background/70 backdrop-blur-sm">
                  <Star className="w-2.5 h-2.5 text-primary fill-primary" />
                  <span className="text-[10px] font-semibold text-foreground">{movie.rating}</span>
                </div>
              </div>
              <p className="text-xs font-medium text-foreground leading-tight line-clamp-2 text-center">
                {movie.title}
              </p>
            </div>
          ))}
        </div>

        {/* Actions */}
        <div className="flex items-center gap-3 pt-2">
          <button
            onClick={onBack}
            disabled={isLoading}
            className="flex-1 flex items-center justify-center gap-2 py-3 rounded-xl text-sm font-medium bg-secondary text-secondary-foreground hover:bg-muted transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            Cambiar seleccion
          </button>
          <button
            onClick={onConfirm}
            disabled={isLoading}
            className="flex-1 flex items-center justify-center gap-2 py-3 rounded-xl text-sm font-semibold bg-primary text-primary-foreground hover:brightness-110 shadow-lg shadow-primary/20 transition-all disabled:cursor-not-allowed disabled:opacity-70"
          >
            {isLoading ? "Consultando..." : "Ver recomendaciones"}
            {!isLoading && <ChevronRight className="w-4 h-4" />}
          </button>
        </div>

        {errorMessage && (
          <p className="text-sm text-destructive text-center" role="alert">
            {errorMessage}
          </p>
        )}
      </div>
    </div>
  )
}
