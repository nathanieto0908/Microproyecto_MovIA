import pandas as pd
import numpy as np
from sklearn.preprocessing import MultiLabelBinarizer
import joblib
import json
from pathlib import Path


def parse_genres(value):
    if pd.isna(value) or str(value).strip() == "":
        return []
    return [g.strip() for g in str(value).split(",") if g.strip()]


def extract_year(date_str):
    if pd.isna(date_str):
        return np.nan
    try:
        return int(str(date_str)[:4])
    except (ValueError, IndexError):
        return np.nan


class FeatureTransformer:

    def __init__(self):
        self.genre_mlb = None
        self.genre_columns = None
        self.top_languages = None
        self.median_year = None
        self.median_runtime = None
        self.movie_catalog = None
        self.feature_names_ = None
        self._fitted = False

    def fit(self, train_df, all_movies_df):
        genre_lists = train_df["genres"].apply(parse_genres)
        all_genres_flat = [g for gl in genre_lists for g in gl]
        genre_counts = pd.Series(all_genres_flat).value_counts()
        min_count = max(int(len(train_df) * 0.003), 10)
        valid_genres = sorted(
            genre_counts[genre_counts >= min_count].index.tolist()
        )

        self.genre_mlb = MultiLabelBinarizer(classes=valid_genres)
        self.genre_mlb.fit([valid_genres])
        self.genre_columns = [f"genre_{g}" for g in valid_genres]

        lang_counts = train_df["original_language"].value_counts()
        self.top_languages = lang_counts.head(10).index.tolist()

        years = train_df["release_date"].apply(extract_year).dropna()
        self.median_year = int(years.median()) if len(years) > 0 else 2000
        self.median_runtime = int(train_df["runtime"].median())

        self.movie_catalog = self._build_catalog(all_movies_df)
        self._fitted = True
        return self

    def _build_catalog(self, df):
        movies = df.drop_duplicates(subset="movie_id").set_index("movie_id").copy()

        cat = pd.DataFrame(index=movies.index)
        cat["title"] = movies["title"]
        cat["genres_raw"] = movies["genres"].fillna("")
        cat["_genres_list"] = movies["genres"].apply(parse_genres)

        cat["vote_average"] = movies["vote_average"].fillna(0).astype(float)
        cat["log_vote_count"] = np.log1p(movies["vote_count"].fillna(0).astype(float))
        cat["log_popularity"] = np.log1p(movies["popularity"].fillna(0).astype(float))
        cat["runtime"] = movies["runtime"].fillna(self.median_runtime).astype(float)
        cat["movie_year"] = (
            movies["release_date"]
            .apply(extract_year)
            .fillna(self.median_year)
            .astype(float)
        )
        cat["movie_age"] = 2026.0 - cat["movie_year"]

        cat["has_overview"] = movies["overview"].notna().astype(int)
        cat["has_keywords"] = movies["keywords"].notna().astype(int)
        cat["num_genres"] = cat["_genres_list"].apply(len)

        cat["overview_len"] = (
            movies["overview"]
            .fillna("")
            .apply(lambda x: len(str(x)))
            .clip(upper=2000)
            .astype(float)
        )
        cat["n_keywords"] = (
            movies["keywords"]
            .fillna("")
            .apply(lambda x: len([k for k in str(x).split(",") if k.strip()]))
            .astype(float)
        )
        cat["is_cold"] = (movies["vote_count"].fillna(0) == 0).astype(int)

        for lang in self.top_languages:
            cat[f"lang_{lang}"] = (movies["original_language"] == lang).astype(int)

        genre_matrix = self.genre_mlb.transform(cat["_genres_list"])
        genre_df = pd.DataFrame(
            genre_matrix, index=cat.index, columns=self.genre_columns
        )
        cat = pd.concat([cat, genre_df], axis=1)

        return cat

    def _movie_feature_cols(self):
        base = [
            "vote_average", "log_vote_count", "log_popularity",
            "runtime", "movie_year", "movie_age",
            "has_overview", "has_keywords", "num_genres",
            "overview_len", "n_keywords", "is_cold",
        ]
        lang = [f"lang_{l}" for l in self.top_languages]
        return base + lang + self.genre_columns

    def build_user_profiles(self, train_df):
        profiles = {}
        for user_id, grp in train_df.groupby("user_id"):
            mids = grp["movie_id"].values
            valid = [m for m in mids if m in self.movie_catalog.index]
            if not valid:
                continue
            movies = self.movie_catalog.loc[valid]
            profiles[user_id] = self._aggregate_profile(movies)
        return profiles

    def _aggregate_profile(self, movies_df):
        p = {}

        p["user_avg_vote_average"] = float(movies_df["vote_average"].mean())
        p["user_std_vote_average"] = (
            float(movies_df["vote_average"].std()) if len(movies_df) > 1 else 0.0
        )
        p["user_avg_log_popularity"] = float(movies_df["log_popularity"].mean())
        p["user_avg_runtime"] = float(movies_df["runtime"].mean())
        p["user_avg_log_vote_count"] = float(movies_df["log_vote_count"].mean())
        p["user_avg_movie_year"] = float(movies_df["movie_year"].mean())
        p["user_num_movies"] = float(len(movies_df))

        p["user_max_vote_average"] = float(movies_df["vote_average"].max())
        p["user_min_vote_average"] = float(movies_df["vote_average"].min())
        p["user_max_runtime"] = float(movies_df["runtime"].max())
        p["user_min_runtime"] = float(movies_df["runtime"].min())
        p["user_median_runtime"] = float(movies_df["runtime"].median())
        p["user_max_log_popularity"] = float(movies_df["log_popularity"].max())
        p["user_min_log_popularity"] = float(movies_df["log_popularity"].min())
        p["user_pct_cold"] = float(movies_df.get("is_cold", pd.Series([0])).mean())

        genre_sums = movies_df[self.genre_columns].sum()
        total = genre_sums.sum()
        genre_prefs = genre_sums / total if total > 0 else genre_sums * 0
        for col in self.genre_columns:
            p[f"user_pref_{col}"] = float(genre_prefs[col])

        all_genres = set()
        for gl in movies_df["_genres_list"]:
            all_genres.update(gl)
        p["user_num_unique_genres"] = float(len(all_genres))

        probs = genre_prefs[genre_prefs > 0].values.astype(float)
        if len(probs) > 0:
            p["user_genre_entropy"] = float(-np.sum(probs * np.log2(probs + 1e-10)))
        else:
            p["user_genre_entropy"] = 0.0

        lang_cols = [f"lang_{l}" for l in self.top_languages]
        lang_sums = movies_df[lang_cols].sum()
        p["_user_top_lang"] = (
            lang_sums.idxmax() if lang_sums.max() > 0 else f"lang_{self.top_languages[0]}"
        )
        p["_user_genre_set"] = all_genres

        return p

    def transform(self, df, user_profiles):
        sample_profile = next(iter(user_profiles.values()))
        user_feat_keys = sorted(
            [k for k in sample_profile if not k.startswith("_")]
        )
        internal_keys = ["_user_top_lang"]

        user_records = []
        for uid, prof in user_profiles.items():
            rec = {"user_id": uid}
            for k in user_feat_keys:
                rec[k] = prof.get(k, 0.0)
            for k in internal_keys:
                rec[k] = prof.get(k, "")
            user_records.append(rec)
        user_feat_df = pd.DataFrame(user_records)

        keep = ["user_id", "movie_id"]
        has_target = "target" in df.columns
        if has_target:
            keep.append("target")

        df_sub = df[keep].copy()
        merged = df_sub.merge(user_feat_df, on="user_id", how="inner")

        valid = merged["movie_id"].isin(self.movie_catalog.index)
        merged = merged[valid].reset_index(drop=True)

        if len(merged) == 0:
            return pd.DataFrame(), pd.DataFrame(columns=keep)

        mf_cols = self._movie_feature_cols()
        movie_feats = (
            self.movie_catalog.loc[merged["movie_id"].values, mf_cols]
            .reset_index(drop=True)
        )

        user_feats = merged[user_feat_keys].reset_index(drop=True)
        inter_feats = self._compute_interactions(merged, movie_feats, user_feats)

        X = pd.concat([movie_feats, user_feats, inter_feats], axis=1)
        X = X.fillna(0)

        self.feature_names_ = X.columns.tolist()
        meta = merged[keep].reset_index(drop=True)
        return X, meta

    def _compute_interactions(self, merged, movie_feats, user_feats):
        n = len(merged)

        runtime_diff = movie_feats["runtime"].values - user_feats["user_avg_runtime"].values
        pop_diff = movie_feats["log_popularity"].values - user_feats["user_avg_log_popularity"].values
        vote_diff = movie_feats["vote_average"].values - user_feats["user_avg_vote_average"].values
        year_diff = movie_feats["movie_year"].values - user_feats["user_avg_movie_year"].values

        movie_gm = movie_feats[self.genre_columns].values.astype(float)
        user_pref_cols = [f"user_pref_{gc}" for gc in self.genre_columns]
        user_gp = user_feats[user_pref_cols].values.astype(float)
        user_gb = (user_gp > 0).astype(float)

        overlap = (movie_gm * user_gb).sum(axis=1)
        movie_ng = movie_gm.sum(axis=1)
        overlap_ratio = np.where(movie_ng > 0, overlap / movie_ng, 0.0)
        union = ((movie_gm + user_gb) > 0).astype(float).sum(axis=1)
        jaccard = np.where(union > 0, overlap / union, 0.0)

        genre_affinity = (movie_gm * user_gp).sum(axis=1)
        norm_movie = np.sqrt((movie_gm ** 2).sum(axis=1) + 1e-10)
        norm_user = np.sqrt((user_gp ** 2).sum(axis=1) + 1e-10)
        genre_cosine = genre_affinity / (norm_movie * norm_user + 1e-10)

        u_max_va = user_feats["user_max_vote_average"].values
        u_min_va = user_feats["user_min_vote_average"].values
        u_max_rt = user_feats["user_max_runtime"].values
        u_min_rt = user_feats["user_min_runtime"].values
        m_va = movie_feats["vote_average"].values
        m_rt = movie_feats["runtime"].values

        in_vote_range = ((m_va >= u_min_va) & (m_va <= u_max_va)).astype(float)
        in_runtime_range = ((m_rt >= u_min_rt) & (m_rt <= u_max_rt)).astype(float)

        u_avg_vc = user_feats["user_avg_log_vote_count"].values
        vote_count_ratio = movie_feats["log_vote_count"].values / (u_avg_vc + 1e-6)

        lang_cols = [f"lang_{l}" for l in self.top_languages]
        lang_matrix = movie_feats[lang_cols].values.astype(float)
        user_top_langs = merged["_user_top_lang"].values
        col_to_idx = {c: i for i, c in enumerate(lang_cols)}
        lang_indices = np.array([col_to_idx.get(str(l), 0) for l in user_top_langs])
        lang_match = lang_matrix[np.arange(n), lang_indices]

        return pd.DataFrame({
            "runtime_diff": runtime_diff,
            "abs_runtime_diff": np.abs(runtime_diff),
            "popularity_diff": pop_diff,
            "vote_avg_diff": vote_diff,
            "year_diff": year_diff,
            "abs_year_diff": np.abs(year_diff),
            "genre_overlap_count": overlap,
            "genre_overlap_ratio": overlap_ratio,
            "genre_jaccard": jaccard,
            "genre_affinity": genre_affinity,
            "genre_cosine": genre_cosine,
            "in_vote_range": in_vote_range,
            "in_runtime_range": in_runtime_range,
            "vote_count_ratio": vote_count_ratio,
            "lang_match": lang_match,
        })

    def prepare_inference(self, seed_movie_ids, candidate_movie_ids=None,
                          top_n_candidates=500):
        valid_seeds = [m for m in seed_movie_ids if m in self.movie_catalog.index]
        if not valid_seeds:
            raise ValueError("Ninguno de los movie_ids proporcionados esta en el catalogo.")

        seed_movies = self.movie_catalog.loc[valid_seeds]
        user_profile = self._aggregate_profile(seed_movies)

        if candidate_movie_ids is None:
            user_genres = user_profile["_user_genre_set"]
            if user_genres:
                scores = self.movie_catalog["_genres_list"].apply(
                    lambda gl: len(set(gl) & user_genres)
                )
                scores = scores.drop(valid_seeds, errors="ignore")
                scores = scores[scores > 0]
                candidate_movie_ids = scores.nlargest(top_n_candidates).index.tolist()
            else:
                pool = self.movie_catalog.drop(valid_seeds, errors="ignore")
                candidate_movie_ids = (
                    pool.nlargest(top_n_candidates, "log_popularity").index.tolist()
                )
        else:
            candidate_movie_ids = [
                m for m in candidate_movie_ids
                if m in self.movie_catalog.index and m not in valid_seeds
            ]

        if not candidate_movie_ids:
            return pd.DataFrame(), pd.DataFrame()

        fake_df = pd.DataFrame({
            "user_id": ["__inference__"] * len(candidate_movie_ids),
            "movie_id": candidate_movie_ids,
        })
        fake_profiles = {"__inference__": user_profile}
        X, meta = self.transform(fake_df, fake_profiles)

        surviving_ids = meta["movie_id"].values
        info = (
            self.movie_catalog.loc[surviving_ids, ["title", "genres_raw"]]
            .reset_index()
        )
        info.columns = ["movie_id", "title", "genres"]

        return X, info

    def save(self, path):
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)

        joblib.dump(self.genre_mlb, path / "genre_mlb.joblib")

        cat_save = self.movie_catalog.copy()
        cat_save["_genres_list_str"] = cat_save["_genres_list"].apply(
            lambda x: "|".join(x) if x else ""
        )
        cat_save = cat_save.drop(columns=["_genres_list"])
        cat_save.to_parquet(path / "movie_catalog.parquet")

        meta = {
            "genre_columns": self.genre_columns,
            "top_languages": self.top_languages,
            "median_year": self.median_year,
            "median_runtime": self.median_runtime,
            "feature_names": self.feature_names_,
        }
        with open(path / "transformer_meta.json", "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2, ensure_ascii=False)

    @classmethod
    def load(cls, path):
        path = Path(path)
        t = cls()

        t.genre_mlb = joblib.load(path / "genre_mlb.joblib")

        cat = pd.read_parquet(path / "movie_catalog.parquet")
        cat["_genres_list"] = cat["_genres_list_str"].apply(
            lambda x: x.split("|") if x else []
        )
        cat = cat.drop(columns=["_genres_list_str"])
        t.movie_catalog = cat

        with open(path / "transformer_meta.json", "r", encoding="utf-8") as f:
            meta = json.load(f)

        t.genre_columns = meta["genre_columns"]
        t.top_languages = meta["top_languages"]
        t.median_year = meta["median_year"]
        t.median_runtime = meta["median_runtime"]
        t.feature_names_ = meta["feature_names"]
        t._fitted = True

        return t
