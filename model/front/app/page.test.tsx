import { render, screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { http, HttpResponse } from "msw"
import Home from "@/app/page"
import { DUMMY_MOVIE_CATALOG } from "@/tests/fixtures/movie-catalog"
import { server } from "@/tests/mocks/server"
import { describe, expect, it } from "vitest"

function getMovieCardButtonByTitle(title: string): HTMLButtonElement {
  const movieTitle = screen.getByText(new RegExp(`^${title}$`, "i"))
  const button = movieTitle.closest("button")
  if (!button) {
    throw new Error(`No se encontro boton para la pelicula: ${title}`)
  }
  return button as HTMLButtonElement
}

async function goToSelectionStep() {
  const user = userEvent.setup()
  render(<Home />)
  await user.click(screen.getByRole("button", { name: /comenzar/i }))
  // Esperar a que carguen las peliculas desde la API (mock)
  await screen.findByText(/^inception$/i)
  return user
}

async function selectFiveMovies(user: ReturnType<typeof userEvent.setup>) {
  // Usar peliculas que existen en DUMMY_MOVIE_CATALOG (el mock de la API)
  await user.click(getMovieCardButtonByTitle("Inception"))
  await user.click(getMovieCardButtonByTitle("The Matrix"))
  await user.click(getMovieCardButtonByTitle("Parasite"))
  await user.click(getMovieCardButtonByTitle("Fight Club"))
  await user.click(getMovieCardButtonByTitle("Blade Runner 2049"))
}

describe("Home page flow", () => {
  it("completa flujo feliz: seleccion, confirmacion y recomendaciones", async () => {
    const user = await goToSelectionStep()

    await selectFiveMovies(user)

    expect(screen.getByText("5/5")).toBeInTheDocument()
    await user.click(screen.getByRole("button", { name: /continuar/i }))

    await screen.findByText(/estas son tus 5 peliculas/i)
    await user.click(screen.getByRole("button", { name: /ver recomendaciones/i }))

    await screen.findByText(/listo/i)
    await screen.findByText(/encontramos 3 peliculas/i)
    // Dune debe estar en las recomendaciones del mock
    await screen.findByText(/dune/i)
  })

  it("cae a recomendaciones locales si el backend falla", async () => {
    server.use(
      http.post("https://api.test.local/recommend", async () => {
        return HttpResponse.json(
          { message: "Modelo no disponible" },
          { status: 500 },
        )
      }),
    )

    const user = await goToSelectionStep()
    await selectFiveMovies(user)

    await user.click(screen.getByRole("button", { name: /continuar/i }))
    await screen.findByText(/estas son tus 5 peliculas/i)
    await user.click(screen.getByRole("button", { name: /ver recomendaciones/i }))

    // Debe caer al fallback local y mostrar recomendaciones
    await waitFor(() => {
      expect(screen.getByText(/encontramos 3 peliculas/i)).toBeInTheDocument()
    })
  })

  it("muestra las peliculas del catalogo de la API al entrar a seleccion", async () => {
    await goToSelectionStep()

    // Verificar peliculas del DUMMY_MOVIE_CATALOG (cargadas via API mock)
    expect(screen.getByText(/^inception$/i)).toBeInTheDocument()
    expect(screen.getByText(/^the matrix$/i)).toBeInTheDocument()
    expect(screen.getByText(/^the godfather$/i)).toBeInTheDocument()
    expect(screen.getByText(/^dune$/i)).toBeInTheDocument()
  })

  it("busqueda filtra peliculas via API", async () => {
    const user = await goToSelectionStep()

    const searchInput = screen.getByPlaceholderText(/buscar/i)
    await user.type(searchInput, "matrix")

    // Esperar debounce + busqueda API
    await waitFor(() => {
      expect(screen.getByText(/^the matrix$/i)).toBeInTheDocument()
      // Inception no deberia estar visible
      expect(screen.queryByText(/^inception$/i)).not.toBeInTheDocument()
    })
  })

  it("usa catalogo local como fallback si la API no esta disponible", async () => {
    // Forzar que la API falle para el catalogo
    server.use(
      http.get("https://api.test.local/movies", async () => {
        return HttpResponse.json(
          { message: "Backend no disponible" },
          { status: 503 },
        )
      }),
    )

    const user = userEvent.setup()
    render(<Home />)
    await user.click(screen.getByRole("button", { name: /comenzar/i }))

    // Debe caer al catalogo local estatico
    await screen.findByText(/^inception$/i)
    expect(screen.getByText(/^the godfather$/i)).toBeInTheDocument()
    expect(screen.getByText(/^logan$/i)).toBeInTheDocument()
  })
})
