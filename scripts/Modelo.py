import pandas as pd
import numpy as np

from sklearn.model_selection import train_test_split
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors
from sklearn.ensemble import GradientBoostingClassifier
from functools import lru_cache
import mlflow
import mlflow.sklearn

Train = pd.read_csv(
    "/home/ubuntu/dvc-proj/data/Train_Data.csv",
    usecols=["user_id", "movie_id", "user_rating", "keywords","overview"]
)

movie_ids = set(Train['movie_id'])

chunks = []
for chunk in pd.read_csv(
    "/home/ubuntu/dvc-proj/data/Data_Movies_Clean.csv",
    usecols=['id', 'title', 'genres','keywords','overview'],
    chunksize=50_000
):
    chunk = chunk[chunk['id'].isin(movie_ids)]
    chunks.append(chunk)

Movies_clean = pd.concat(chunks, ignore_index=True)
#Movies_clean = pd.read_csv("~/dvc-proj/data/Data_Movies_Clean.csv", usecols=cols)

Train.columns

Movies_clean.columns

Train_eval = []
Test_eval = []

for user, df_u in Train.groupby("user_id"):
    if len(df_u) < 2:
        continue

    train_u, test_u = train_test_split(
        df_u, test_size=0.2, random_state=42
    )

    Train_eval.append(train_u)
    Test_eval.append(test_u)

Train_eval = pd.concat(Train_eval)
Test_eval = pd.concat(Test_eval)

from scipy.sparse import csr_matrix

user_codes = Train_eval["user_id"].astype("category").cat.codes
movie_codes = Train_eval["movie_id"].astype("category").cat.codes

user_movie_sparse = csr_matrix(
    (Train_eval["user_rating"], (user_codes, movie_codes))
)


def collaborative_score(user_id):
    sims = user_sim.loc[user_id]
    scores = np.dot(sims, user_movie)
    return pd.Series(scores, index=user_movie.columns)

##### Filtrado basado en contenido
Movies_clean = Movies_clean.reset_index(drop=True)

Movies_clean["content"] = (Movies_clean["genres"].fillna("") + " " +  Movies_clean["keywords"].fillna("") + " " +  Movies_clean["overview"].fillna(""))
Movies_clean = Movies_clean.nlargest(30000, "popularity")

##### Vectorización TF-IDF
tfidf = TfidfVectorizer(
    stop_words="english",
    max_features=5000,
    min_df=10
)

content_matrix = tfidf.fit_transform(Movies_clean["content"])

#### Definición Modelo 

nn = NearestNeighbors(
    n_neighbors=50,
    metric="cosine",
    algorithm="brute"
)

nn.fit(user_movie_sparse)

movie_neighbors = nn.kneighbors(
    content_matrix,
    return_distance=False
)
user_movie_sparsemovie_idx = pd.Series(
    Movies_clean.index,
    index=Movies_clean["id"]
)

#### Similaridad entre peliculas
def content_score(user_id):

    user_movies = Train_eval[Train_eval["user_id"] == user_id]
    if user_movies.empty:
        return pd.Series(dtype=float)

    scores = {}

    for _, row in user_movies.iterrows():
        movie_id = row.movie_id
        rating = row.user_rating

        # ✅ protección doble
        if movie_id not in movie_idx:
            continue

        idx = movie_idx[movie_id]

        # ✅ protección crítica
        if idx >= movie_neighbors.shape[0]:
            continue

        neighbors = movie_neighbors[idx]

        for i in neighbors:
            if i >= len(Movies_clean):
                continue

            m_id = Movies_clean.iloc[i].id
            if m_id == movie_id:
                continue

            scores[m_id] = scores.get(m_id, 0) + rating
    return pd.Series(scores, dtype=float)

Train_eval["target"] = (Train_eval["user_rating"] >= 4).astype(int)

#### Popularidad
movie_popularity = (
    Movies_clean
    .set_index("id")["popularity"]
    .to_dict()
)

rows = []

for user, df_u in Train_eval.groupby("user_id"):

    positives = df_u[df_u["target"] == 1]
    if positives.empty:
        continue

    negatives = df_u[df_u["target"] == 0]
    if not negatives.empty:
        negatives = negatives.sample(
            n=min(len(positives) * 5, len(negatives)),
            random_state=42
        )

    df_pairs = pd.concat([positives, negatives])

    # scores una sola vez por usuario
    cf_scores = collaborative_score(user)
    cb_scores = content_score(user)

    df_pairs = df_pairs.copy()

    df_pairs["cf_score"] = (
        df_pairs["movie_id"]
        .map(cf_scores)
        .fillna(0)
    )

    df_pairs["cb_score"] = (
        df_pairs["movie_id"]
        .map(cb_scores)
        .fillna(0)
    )

    df_pairs["popularity"] = (
        df_pairs["movie_id"]
        .map(movie_popularity)
        .fillna(0)
    )

    rows.append(
        df_pairs[["cf_score", "cb_score", "popularity", "target"]]
    )

supervised_df = pd.concat(rows, ignore_index=True)

#### Modelo hibrido
from sklearn.preprocessing import StandardScaler

X = supervised_df[["cf_score", "cb_score", "popularity"]]
scaler = StandardScaler()

X_scaled = scaler.fit_transform(X)


y = supervised_df["target"]


X_train, X_val, y_train, y_val = train_test_split(
    X_scaled, y, test_size=0.2, random_state=42
)

from sklearn.ensemble import HistGradientBoostingClassifier

model = HistGradientBoostingClassifier(
    max_depth=6,
    learning_rate=0.05,
    max_iter=200,
    random_state=42
)

model.fit(X_train, y_train)

#### Recomendacion
@lru_cache(maxsize=5000)
def supervised_recommendation(user_id, top_k=10):

    if user_id not in user_movie.index:
        return (
            Movies_clean
            .sort_values("popularity", ascending=False)
            .head(top_k)
            .set_index("id")["popularity"]
        )

    cf_scores = collaborative_score(user_id)
    cb_scores = content_score(user_id)

    data = []

    for movie_id in Movies_clean["id"].values:
        data.append({
            "movie_id": movie_id,
            "cf_score": cf_scores.get(movie_id, 0),
            "cb_score": cb_scores.get(movie_id, 0),
            "popularity": movie_popularity.get(movie_id, 0)
        })

    df_pred = pd.DataFrame(data)

    df_pred[["cf_score", "cb_score", "popularity"]] = (
        df_pred[["cf_score", "cb_score", "popularity"]]
        .fillna(0)
    )
    df_pred["score"] = model.predict_proba(
        df_pred[["cf_score", "cb_score", "popularity"]]
    )[:, 1]

    seen = Train_eval[Train_eval.user_id == user_id].movie_id
    df_pred = df_pred[~df_pred.movie_id.isin(seen)]

    return (
        df_pred
        .sort_values("score", ascending=False)
        .head(top_k)
        .set_index("movie_id")["score"]
    )
    
#### Evaluación Modelo

### Precisión

def precision_at_k(recommended, relevant, k):
    recommended_k = recommended[:k]
    hits = len(set(recommended_k) & set(relevant))
    return hits / k

### NDC
def ndcg_at_k(recommended, relevant, k):
    dcg = sum(
        1 / np.log2(i + 2)
        for i, movie in enumerate(recommended[:k])
        if movie in relevant
    )

    ideal = sum(
        1 / np.log2(i + 2)
        for i in range(min(len(relevant), k))
    )

    return dcg / ideal if ideal > 0 else 0

### Evaluación Modelo
def evaluate_model(model_func, Train_eval, Test_eval, users, k=10):

    precisions, ndcgs = [], []

    for user in users:
        relevant = (
            Test_eval[Test_eval.user_id == user]
            .query("user_rating >= 4")["movie_id"]
            .tolist()
        )

        if not relevant:
            continue

        recs = model_func(user, top_k=k).index.tolist()

        precisions.append(precision_at_k(recs, relevant, k))
        ndcgs.append(ndcg_at_k(recs, relevant, k))

    return {
        "precision_k": np.mean(precisions),
        "ndcg_k": np.mean(ndcgs),
        "n_users": len(precisions)
    }
    
import mlflow

mlflow.set_tracking_uri('http://localhost:5000')

mlflow.set_experiment("supervised_recommender_eval")

with mlflow.start_run(run_name="gbm_cf_cb_pop_k10"):

    # Parámetros clave del experimento
    mlflow.log_param("k", 10)
    mlflow.log_param("min_interactions_user", 5)
    mlflow.log_param("n_users_eval", 500)

    # === TU CÓDIGO ===
    eligible_users = (
        Train_eval.groupby("user_id")
        .size()
        .loc[lambda x: x >= 5]
        .index
    )

    users_to_eval = (
        Test_eval[Test_eval.user_id.isin(eligible_users)]
        .user_id.value_counts()
        .head(500)
        .index
    )

    results = evaluate_model(
        supervised_recommendation,
        Train_eval,
        Test_eval,
        users_to_eval,
        k=10
    )

    # === LOG DE MÉTRICAS ===
    for metric, value in results.items():
        mlflow.log_metric(metric, value)

    results
