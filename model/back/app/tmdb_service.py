import os
import json
import logging
from pathlib import Path
from typing import Optional

import requests

logger = logging.getLogger(__name__)

TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p"
DEFAULT_SIZE = "w342"


class TMDbService:

    def __init__(self, cache_dir: str = "artifacts/cache"):
        self.api_key = os.getenv("TMDB_API_KEY", "")
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._cache_file = self.cache_dir / "poster_cache.json"
        self._cache: dict[int, str] = {}
        self._load_cache()

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    def _load_cache(self):
        if self._cache_file.exists():
            try:
                with open(self._cache_file, "r") as f:
                    raw = json.load(f)
                self._cache = {int(k): v for k, v in raw.items()}
            except Exception:
                self._cache = {}

    def _save_cache(self):
        try:
            with open(self._cache_file, "w") as f:
                json.dump(self._cache, f)
        except Exception:
            pass

    def get_poster_url(self, movie_id: int, size: str = DEFAULT_SIZE) -> str:
        if movie_id in self._cache:
            poster_path = self._cache[movie_id]
            if poster_path:
                return f"{TMDB_IMAGE_BASE}/{size}{poster_path}"
            return ""

        if not self.is_configured:
            return ""

        poster_path = self._fetch_poster_path(movie_id)
        self._cache[movie_id] = poster_path or ""

        if len(self._cache) % 50 == 0:
            self._save_cache()

        if poster_path:
            return f"{TMDB_IMAGE_BASE}/{size}{poster_path}"
        return ""

    def _fetch_poster_path(self, movie_id: int) -> Optional[str]:
        url = f"https://api.themoviedb.org/3/movie/{movie_id}"
        try:
            resp = requests.get(url, params={"api_key": self.api_key}, timeout=5)
            if resp.status_code == 200:
                return resp.json().get("poster_path")
            return None
        except Exception:
            return None

    def get_poster_urls_batch(self, movie_ids: list[int],
                               size: str = DEFAULT_SIZE) -> dict[int, str]:
        return {mid: self.get_poster_url(mid, size) for mid in movie_ids}

    def flush_cache(self):
        self._save_cache()
