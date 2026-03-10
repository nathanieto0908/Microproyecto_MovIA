import pytest
from fastapi.testclient import TestClient
from app.main import app, engine

client = TestClient(app)

FRONTEND_CATALOG_IDS = [
    27205, 603, 496243, 550, 335984, 438631, 120467, 274, 129,
    872585, 545611, 1124, 313369, 419430, 324857, 152601, 238,
    424, 37165, 98, 122, 299536, 11324, 497, 16869, 105,
    8587, 77338, 240, 10681, 372058, 24, 1422, 637, 263115,
]


@pytest.fixture(scope="module", autouse=True)
def ensure_loaded():
    if not engine.is_loaded:
        engine.load()
    yield


class TestFrontendBackendIntegration:

    def test_all_35_catalog_ids_exist_in_backend(self):
        cat = engine.transformer.movie_catalog
        missing = [mid for mid in FRONTEND_CATALOG_IDS if mid not in cat.index]
        assert missing == [], f"IDs del frontend no encontrados en backend: {missing}"

    def test_all_35_have_title_and_genres(self):
        cat = engine.transformer.movie_catalog
        for mid in FRONTEND_CATALOG_IDS:
            row = cat.loc[mid]
            assert str(row["title"]).strip(), f"Movie {mid} sin titulo"
            genres = row.get("_genres_list", [])
            assert len(genres) > 0 or row.get("num_genres", 0) > 0, f"Movie {mid} sin generos"

    def test_recommend_with_frontend_ids(self):
        selected = FRONTEND_CATALOG_IDS[:5]
        r = client.post("/recommend", json={"movie_ids": selected})
        assert r.status_code == 200

        data = r.json()
        recs = data["recommendations"]
        assert len(recs) == 3

        for rec in recs:
            assert isinstance(rec["movie_id"], int)
            assert len(rec["title"]) > 0
            assert isinstance(rec["genres"], list)
            assert isinstance(rec["year"], int)
            assert 0 < rec["probability"] <= 1
            assert "%" in rec["probability_pct"]

        rec_ids = {rec["movie_id"] for rec in recs}
        assert rec_ids.isdisjoint(set(selected))

    def test_recommend_with_different_selection(self):
        selected = [238, 240, 424, 122, 497]
        r = client.post("/recommend", json={"movie_ids": selected})
        assert r.status_code == 200
        data = r.json()
        assert len(data["recommendations"]) == 3

    def test_frontend_normalizeMovie_compatible_format(self):
        r = client.post("/recommend", json={"movie_ids": FRONTEND_CATALOG_IDS[:5]})
        data = r.json()
        for rec in data["recommendations"]:
            assert "movie_id" in rec
            assert "title" in rec
            assert isinstance(rec["genres"], list)
            assert "year" in rec
            assert "vote_average" in rec
            assert "probability" in rec

    def test_movies_list_format_compatible(self):
        r = client.get("/movies?page=1&page_size=5")
        data = r.json()
        assert "movies" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        for movie in data["movies"]:
            assert isinstance(movie["genres"], list)

    def test_search_format_compatible(self):
        r = client.get("/movies/search?q=Inception")
        data = r.json()
        assert "movies" in data
        assert data["total"] >= 1
        titles = [m["title"] for m in data["movies"]]
        assert "Inception" in titles
