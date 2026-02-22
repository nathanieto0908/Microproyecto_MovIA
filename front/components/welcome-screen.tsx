"use client"

import React from "react"

import { Film, ChevronRight, Search, Clapperboard, Zap } from "lucide-react"

interface WelcomeScreenProps {
  onContinue: () => void
}

export function WelcomeScreen({ onContinue }: WelcomeScreenProps) {
  return (
    <div className="min-h-screen flex flex-col">
      <header className="flex items-center justify-between px-6 py-4 border-b border-border/40">
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-primary/10">
            <Film className="w-4 h-4 text-primary" />
          </div>
          <span className="text-lg font-bold tracking-tight text-foreground">
            Mov<span className="text-primary">IA</span>
          </span>
        </div>
      </header>

      <div className="flex-1 flex flex-col items-center justify-center px-4 relative overflow-hidden">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] rounded-full bg-primary/4 blur-[100px] pointer-events-none" />

        <div className="relative z-10 flex flex-col items-center gap-10 max-w-lg text-center animate-in fade-in slide-in-from-bottom-6 duration-700">
          <div className="flex flex-col gap-3">
            <p className="text-sm font-medium text-muted-foreground tracking-wide">Hola de nuevo</p>
            <h1 className="text-4xl sm:text-5xl font-bold text-foreground leading-tight text-balance">
              {"Bienvenido, "}<span className="text-primary">Jersons</span>
            </h1>
            <p className="text-base text-muted-foreground leading-relaxed max-w-md mx-auto text-pretty">
              Vamos a descubrir tus proximas peliculas favoritas. El proceso es simple y rapido.
            </p>
          </div>

          <div className="flex flex-col sm:flex-row items-center gap-4 w-full max-w-md">
            <StepCard
              icon={<Search className="w-5 h-5" />}
              number="1"
              title="Busca y elige"
              desc="Selecciona 5 peliculas que ya te gusten"
            />
            <div className="w-6 h-px sm:w-px sm:h-6 bg-border" />
            <StepCard
              icon={<Clapperboard className="w-5 h-5" />}
              number="2"
              title="Confirma"
              desc="Revisa tu seleccion antes de continuar"
            />
            <div className="w-6 h-px sm:w-px sm:h-6 bg-border" />
            <StepCard
              icon={<Zap className="w-5 h-5" />}
              number="3"
              title="Descubre"
              desc="Recibe recomendaciones a tu medida"
            />
          </div>

          <div className="flex flex-col items-center gap-3">
            <button
              onClick={onContinue}
              className="group flex items-center gap-3 px-8 py-4 rounded-2xl bg-primary text-primary-foreground font-semibold text-base transition-all duration-300 hover:brightness-110 hover:shadow-xl hover:shadow-primary/20 hover:gap-4"
            >
              Comenzar
              <ChevronRight className="w-4 h-4 transition-transform duration-300 group-hover:translate-x-0.5" />
            </button>
            <p className="text-xs text-muted-foreground">Solo toma un momento</p>
          </div>
        </div>
      </div>
    </div>
  )
}

function StepCard({
  icon,
  number,
  title,
  desc,
}: {
  icon: React.ReactNode
  number: string
  title: string
  desc: string
}) {
  return (
    <div className="flex flex-col items-center gap-2 flex-1 p-4 rounded-xl bg-card/50 border border-border/30">
      <div className="flex items-center justify-center w-10 h-10 rounded-full bg-primary/10 text-primary">
        {icon}
      </div>
      <span className="text-sm font-semibold text-foreground">{title}</span>
      <span className="text-xs text-muted-foreground leading-relaxed text-center">{desc}</span>
    </div>
  )
}
