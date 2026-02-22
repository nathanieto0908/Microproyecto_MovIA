import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from app.schemas import (
    RecommendRequest,
    RecommendResponse,
    MovieRecommendation,
    MovieListResponse,
    MovieItem,
    HealthResponse,
    ModelInfoResponse,
)
from app.recommender import RecommenderEngine

ARTIFACTS_DIR = os.getenv("ARTIFACTS_DIR", "artifacts")
engine = RecommenderEngine(artifacts_dir=ARTIFACTS_DIR)


@asynccontextmanager
async def lifespan(app: FastAPI):
    engine.load()
    catalog_size = len(engine.transformer.movie_catalog)
    tmdb_status = "configurado" if engine.tmdb.is_configured else "no configurado (set TMDB_API_KEY)"
    print(f"Modelo cargado - Catalogo: {catalog_size:,} peliculas | TMDb: {tmdb_status}")
    yield
    engine.tmdb.flush_cache()


app = FastAPI(
    title="MovIA Recommender API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/recommend", response_model=RecommendResponse)
def recommend(req: RecommendRequest):
    try:
        result = engine.recommend(req.movie_ids, top_n=3)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

    return RecommendResponse(
        recommendations=[MovieRecommendation(**r) for r in result["recommendations"]],
        seed_movies=result["seed_movies"],
        user_profile_summary=result["user_profile_summary"],
    )


@app.get("/movies", response_model=MovieListResponse)
def list_movies(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    data = engine.list_movies(page=page, page_size=page_size)
    return MovieListResponse(
        movies=[MovieItem(**m) for m in data["movies"]],
        total=data["total"],
        page=data["page"],
        page_size=data["page_size"],
    )


@app.get("/movies/search", response_model=MovieListResponse)
def search_movies(
    q: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    data = engine.search_movies(q, page=page, page_size=page_size)
    return MovieListResponse(
        movies=[MovieItem(**m) for m in data["movies"]],
        total=data["total"],
        page=data["page"],
        page_size=data["page_size"],
    )


@app.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(
        status="ok" if engine.is_loaded else "loading",
        model_loaded=engine.is_loaded,
        catalog_size=len(engine.transformer.movie_catalog) if engine.is_loaded else 0,
    )


@app.get("/model/info", response_model=ModelInfoResponse)
def model_info():
    if not engine.is_loaded:
        raise HTTPException(status_code=503, detail="Modelo aun no cargado.")
    meta = engine.metadata
    return ModelInfoResponse(
        training_date=meta.get("training_date", "unknown"),
        n_features=meta.get("n_features", 0),
        test_auc_roc=meta.get("metrics", {}).get("test", {}).get("auc_roc", 0),
        test_f1=meta.get("metrics", {}).get("test", {}).get("f1", 0),
        best_hyperparams=meta.get("best_hyperparams", {}),
        catalog_size=len(engine.transformer.movie_catalog),
    )
