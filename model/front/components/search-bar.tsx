"use client"

import { Loader2, Search, X } from "lucide-react"

interface SearchBarProps {
  value: string
  onChange: (value: string) => void
  isLoading?: boolean
  disabled?: boolean
}

export function SearchBar({ value, onChange, isLoading = false, disabled = false }: SearchBarProps) {
  return (
    <div className="relative">
      <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
      <input
        type="text"
        placeholder="Buscar peliculas por titulo, genero..."
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
        className="w-full pl-11 pr-10 py-3 bg-secondary/50 border border-border/50 rounded-xl text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary/50 transition-all"
      />
      {value && (
        <button
          onClick={() => onChange("")}
          disabled={disabled}
          className="absolute right-3 top-1/2 -translate-y-1/2 p-1 rounded-md hover:bg-muted/50 transition-colors"
          aria-label="Limpiar busqueda"
        >
          <X className="w-4 h-4 text-muted-foreground" />
        </button>
      )}

      {isLoading && (
        <Loader2 className="absolute right-10 top-1/2 -translate-y-1/2 w-4 h-4 animate-spin text-muted-foreground" />
      )}
    </div>
  )
}
