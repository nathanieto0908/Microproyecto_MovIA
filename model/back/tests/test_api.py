import pytest
from fastapi.testclient import TestClient
from app.main import app, engine

client = TestClient(app)

VALID_IDS = [27205, 603, 496243, 550, 335984]


@pytest.fixture(scope="module", autouse=True)
def ensure_model_loaded():
    if not engine.is_loaded:
        engine.load()
    yield


class TestHealth:
    def test_health_ok(self):
        r = client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "ok"
        assert data["model_loaded"] is True
        assert data["catalog_size"] > 0

    def test_health_catalog_size_coherent(self):
        r = client.get("/health")
        data = r.json()
        assert data["catalog_size"] > 100_000


class TestModelInfo:
    def test_model_info_returns_metadata(self):
        r = client.get("/model/info")
        assert r.status_code == 200
        data = r.json()
        assert "training_date" in data
        assert data["n_features"] > 0
        assert "best_hyperparams" in data

    def test_model_info_has_metrics(self):
        r = client.get("/model/info")
        data = r.json()
        assert "test_auc_roc" in data
        assert "test_f1" in data


class TestMoviesList:
    def test_list_default_page(self):
        r = client.get("/movies")
        assert r.status_code == 200
        data = r.json()
        assert "movies" in data
        assert data["page"] == 1
        assert len(data["movies"]) <= 20

    def test_list_custom_pagination(self):
        r = client.get("/movies?page=1&page_size=5")
        assert r.status_code == 200
        data = r.json()
        assert len(data["movies"]) == 5

    def test_movie_item_has_required_fields(self):
        r = client.get("/movies?page=1&page_size=1")
        data = r.json()
        movie = data["movies"][0]
        assert "movie_id" in movie
        assert "title" in movie
        assert isinstance(movie["genres"], list)
        assert "year" in movie
        assert "vote_average" in movie
        assert "popularity" in movie

    def test_list_page_out_of_range(self):
        r = client.get("/movies?page=999999&page_size=20")
        assert r.status_code == 200
        data = r.json()
        assert data["movies"] == []


class TestMoviesSearch:
    def test_search_by_title(self):
        r = client.get("/movies/search?q=Inception")
        assert r.status_code == 200
        data = r.json()
        assert data["total"] >= 1
        titles = [m["title"] for m in data["movies"]]
        assert "Inception" in titles

    def test_search_case_insensitive(self):
        r = client.get("/movies/search?q=inception")
        data = r.json()
        assert data["total"] >= 1

    def test_search_no_results(self):
        r = client.get("/movies/search?q=xyznonexistent123")
        assert r.status_code == 200
        data = r.json()
        assert data["total"] == 0

    def test_search_pagination(self):
        r = client.get("/movies/search?q=the&page=1&page_size=3")
        assert r.status_code == 200
        data = r.json()
        assert len(data["movies"]) <= 3

    def test_search_requires_q(self):
        r = client.get("/movies/search")
        assert r.status_code == 422


class TestRecommend:
    def test_recommend_happy_path(self):
        r = client.post("/recommend", json={"movie_ids": VALID_IDS})
        assert r.status_code == 200
        data = r.json()
        assert len(data["recommendations"]) == 3
        assert "seed_movies" in data

    def test_recommend_fields_complete(self):
        r = client.post("/recommend", json={"movie_ids": VALID_IDS})
        data = r.json()
        rec = data["recommendations"][0]
        assert "movie_id" in rec
        assert "title" in rec
        assert isinstance(rec["genres"], list)
        assert "year" in rec
        assert 0 < rec["probability"] <= 1

    def test_recommend_probabilities_sorted(self):
        r = client.post("/recommend", json={"movie_ids": VALID_IDS})
        data = r.json()
        probs = [rec["probability"] for rec in data["recommendations"]]
        assert probs == sorted(probs, reverse=True)

    def test_recommend_no_seed_in_results(self):
        r = client.post("/recommend", json={"movie_ids": VALID_IDS})
        data = r.json()
        rec_ids = {rec["movie_id"] for rec in data["recommendations"]}
        assert rec_ids.isdisjoint(set(VALID_IDS))

    def test_recommend_user_profile_summary(self):
        r = client.post("/recommend", json={"movie_ids": VALID_IDS})
        data = r.json()
        profile = data["user_profile_summary"]
        assert "avg_vote_average" in profile
        assert profile["n_seed_movies"] == 5

    def test_recommend_requires_5_ids(self):
        r = client.post("/recommend", json={"movie_ids": [27205, 603]})
        assert r.status_code == 422

    def test_recommend_rejects_duplicates(self):
        r = client.post("/recommend", json={"movie_ids": [27205, 27205, 603, 550, 496243]})
        assert r.status_code == 422

    def test_recommend_empty_body(self):
        r = client.post("/recommend", json={})
        assert r.status_code == 422

    def test_recommend_invalid_body(self):
        r = client.post("/recommend", json={"movie_ids": "not_a_list"})
        assert r.status_code == 422
