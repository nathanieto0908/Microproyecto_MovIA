"use client"

import { Film } from "lucide-react"

interface HeaderProps {
  title?: string
  step?: number
}

export function Header({ title = "MovIA", step }: HeaderProps) {
  return (
    <header className="flex items-center justify-between px-6 py-4 border-b border-border/40">
      <div className="flex items-center gap-3">
        <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-primary/10">
          <Film className="w-4 h-4 text-primary" />
        </div>
        <span className="text-lg font-bold tracking-tight text-foreground">
          Mov<span className="text-primary">IA</span>
        </span>
      </div>

      <div className="flex items-center gap-4">
        {step && (
          <div className="hidden sm:flex items-center gap-2">
            {[1, 2, 3].map((s) => (
              <div
                key={s}
                className={`w-6 h-1 rounded-full transition-all duration-500 ${
                  s <= step ? "bg-primary" : "bg-border"
                }`}
              />
            ))}
          </div>
        )}
        <div className="flex items-center gap-2">
          <span className="text-sm text-muted-foreground font-medium hidden sm:block">Jersons</span>
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary/80 to-primary/40 flex items-center justify-center">
            <span className="text-xs font-semibold text-primary-foreground">J</span>
          </div>
        </div>
      </div>
    </header>
  )
}
