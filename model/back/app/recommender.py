import numpy as np
import xgboost as xgb
import json
from pathlib import Path
import joblib

try:
    import lightgbm as lgb
except Exception:
    lgb = None

from src.feature_engineering import FeatureTransformer
from app.tmdb_service import TMDbService


class RecommenderEngine:

    def __init__(self, artifacts_dir: str = "artifacts", model_type: str = "xgboost"):
        self.artifacts_dir = Path(artifacts_dir)
        self.model_type = (model_type or "xgboost").strip().lower()
        self.model = None
        self.transformer = None
        self.metadata = None
        self.tmdb = TMDbService(cache_dir=str(Path(artifacts_dir) / "cache"))
        self._loaded = False

    def _resolve_model_path(self) -> Path:
        model_dir = self.artifacts_dir / "model"
        if self.model_type == "xgboost":
            return model_dir / "xgboost_recommender.ubj"
        if self.model_type == "lightgbm":
            return model_dir / "lightgbm_recommender.txt"
        if self.model_type == "random_forest":
            return model_dir / "random_forest_recommender.joblib"
        raise ValueError(
            f"model_type invalido: {self.model_type}. Usa 'xgboost', 'lightgbm' o 'random_forest'."
        )

    def _resolve_metadata_path(self) -> Path:
        md = self.artifacts_dir / "metadata"
        if self.model_type == "lightgbm":
            candidates = [md / "training_metadata_lightgbm.json", md / "training_metadata.json"]
        elif self.model_type == "random_forest":
            candidates = [md / "training_metadata_random_forest.json", md / "training_metadata.json"]
        else:
            candidates = [md / "training_metadata_xgboost.json", md / "training_metadata.json"]

        for p in candidates:
            if p.exists():
                return p
        raise FileNotFoundError(f"No se encontro metadata para model_type={self.model_type} en {md}")

    def load(self):
        model_path = self._resolve_model_path()
        if not model_path.exists():
            raise FileNotFoundError(f"No se encontro el artefacto del modelo: {model_path}")

        if self.model_type == "xgboost":
            self.model = xgb.XGBClassifier()
            self.model.load_model(str(model_path))
        elif self.model_type == "lightgbm":
            if lgb is None:
                raise RuntimeError(
                    "lightgbm no esta instalado. Instala dependencias o usa MODEL_TYPE=xgboost."
                )
            self.model = lgb.Booster(model_file=str(model_path))
        elif self.model_type == "random_forest":
            self.model = joblib.load(model_path)

        trans_path = self.artifacts_dir / "transformers"
        self.transformer = FeatureTransformer.load(trans_path)

        meta_path = self._resolve_metadata_path()
        with open(meta_path, "r", encoding="utf-8") as f:
            self.metadata = json.load(f)

        self._loaded = True

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    def _predict_positive_proba(self, X_np: np.ndarray) -> np.ndarray:
        if self.model_type == "xgboost":
            return self.model.predict_proba(X_np)[:, 1]
        if self.model_type == "random_forest":
            return self.model.predict_proba(X_np)[:, 1]

        probs = self.model.predict(X_np)
        probs_np = np.asarray(probs, dtype=np.float32)
        if probs_np.ndim == 2 and probs_np.shape[1] >= 2:
            return probs_np[:, 1]
        return probs_np.reshape(-1)

    def _movie_dict(self, mid: int, cat_row=None, include_popularity: bool = False) -> dict:
        if cat_row is None:
            if mid not in self.transformer.movie_catalog.index:
                return {
                    "movie_id": mid, "title": f"Movie {mid}",
                    "genres": [], "year": 0, "vote_average": 0.0,
                    "overview": "", "poster": "",
                }
            cat_row = self.transformer.movie_catalog.loc[mid]

        overview_raw = cat_row.get("overview", "")
        overview = str(overview_raw) if overview_raw and str(overview_raw) != "nan" else ""

        d = {
            "movie_id": int(mid),
            "title": str(cat_row["title"]),
            "genres": list(cat_row.get("_genres_list", [])),
            "year": int(cat_row.get("movie_year", 0)),
            "vote_average": round(float(cat_row.get("vote_average", 0)), 1),
            "overview": overview,
            "poster": self.tmdb.get_poster_url(int(mid)),
        }
        if include_popularity:
            d["popularity"] = round(float(np.expm1(cat_row.get("log_popularity", 0))), 2)
        return d

    def recommend(self, movie_ids: list[int], top_n: int = 3,
                  n_candidates: int = 500) -> dict:
        if not self._loaded:
            raise RuntimeError("El motor no esta cargado. Llama a load() primero.")

        seed_info = []
        for mid in movie_ids:
            if mid in self.transformer.movie_catalog.index:
                seed_info.append(self._movie_dict(mid))

        X_cand, cand_info = self.transformer.prepare_inference(
            movie_ids, top_n_candidates=n_candidates
        )

        if len(X_cand) == 0:
            return {
                "recommendations": [],
                "seed_movies": seed_info,
                "user_profile_summary": {},
            }

        X_np = np.nan_to_num(X_cand.values.astype(np.float32), nan=0.0)
        probs = self._predict_positive_proba(X_np)
        cand_info = cand_info.copy()
        cand_info["probability"] = probs

        top = cand_info.nlargest(top_n, "probability")

        recommendations = []
        for _, r in top.iterrows():
            mid = int(r["movie_id"])
            rec_dict = self._movie_dict(mid)
            rec_dict["probability"] = round(float(r["probability"]), 4)
            rec_dict["probability_pct"] = f"{float(r['probability'])*100:.1f}%"
            recommendations.append(rec_dict)

        valid_seeds = [m for m in movie_ids
                       if m in self.transformer.movie_catalog.index]
        seed_movies_df = self.transformer.movie_catalog.loc[valid_seeds]
        profile_summary = {
            "avg_vote_average": round(float(seed_movies_df["vote_average"].mean()), 2),
            "avg_popularity": round(float(np.expm1(seed_movies_df["log_popularity"].mean())), 2),
            "avg_runtime": round(float(seed_movies_df["runtime"].mean()), 1),
            "n_seed_movies": len(valid_seeds),
            "genres_in_seeds": list(set(
                g for gl in seed_movies_df["_genres_list"] for g in gl
            )),
        }

        self.tmdb.flush_cache()

        return {
            "recommendations": recommendations,
            "seed_movies": seed_info,
            "user_profile_summary": profile_summary,
        }

    def search_movies(self, query: str, page: int = 1, page_size: int = 20) -> dict:
        cat = self.transformer.movie_catalog
        mask = cat["title"].str.contains(query, case=False, na=False)
        results = cat[mask]
        total = len(results)
        start = (page - 1) * page_size
        end = start + page_size
        page_data = results.iloc[start:end]
        movies = [
            self._movie_dict(int(mid), row, include_popularity=True)
            for mid, row in page_data.iterrows()
        ]
        return {"movies": movies, "total": total, "page": page, "page_size": page_size}

    def list_movies(self, page: int = 1, page_size: int = 20) -> dict:
        cat = self.transformer.movie_catalog.sort_values(
            "log_popularity", ascending=False
        )
        total = len(cat)
        start = (page - 1) * page_size
        end = start + page_size
        page_data = cat.iloc[start:end]

        movies = [
            self._movie_dict(int(mid), row, include_popularity=True)
            for mid, row in page_data.iterrows()
        ]
        return {"movies": movies, "total": total, "page": page, "page_size": page_size}
