from pydantic import BaseModel, field_validator
from typing import List


class RecommendRequest(BaseModel):
    movie_ids: List[int]

    @field_validator("movie_ids")
    @classmethod
    def exactly_five(cls, v):
        if len(v) != 5:
            raise ValueError("Se requieren exactamente 5 movie_ids.")
        if len(set(v)) != 5:
            raise ValueError("Los movie_ids deben ser unicos.")
        return v


class MovieRecommendation(BaseModel):
    movie_id: int
    title: str
    genres: List[str]
    year: int
    vote_average: float
    overview: str = ""
    poster: str = ""
    probability: float
    probability_pct: str


class RecommendResponse(BaseModel):
    recommendations: List[MovieRecommendation]
    seed_movies: List[dict]
    user_profile_summary: dict


class MovieItem(BaseModel):
    movie_id: int
    title: str
    genres: List[str]
    year: int
    vote_average: float
    popularity: float
    overview: str = ""
    poster: str = ""


class MovieListResponse(BaseModel):
    movies: List[MovieItem]
    total: int
    page: int
    page_size: int


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    catalog_size: int


class ModelInfoResponse(BaseModel):
    training_date: str
    n_features: int
    test_auc_roc: float
    test_f1: float
    best_hyperparams: dict
    catalog_size: int
