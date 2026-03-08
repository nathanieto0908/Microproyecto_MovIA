#!/usr/bin/env python
import argparse
import json
import os
import sys
import time
import warnings
from pathlib import Path

import lightgbm as lgb
import numpy as np
import optuna
import pandas as pd
from sklearn.metrics import (
    average_precision_score,
    classification_report,
    confusion_matrix,
    f1_score,
    log_loss,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold, train_test_split

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from src.feature_engineering import FeatureTransformer
from src.config import RANDOM_STATE, TARGET_THRESHOLD, TEST_SIZE, VAL_SIZE

warnings.filterwarnings("ignore")
optuna.logging.set_verbosity(optuna.logging.WARNING)

W = 70


def sec(title, c="="):
    print(f"\n{c * W}\n  {title}\n{c * W}")


def eval_cls_probs(y_true, y_prob, name):
    yb = (y_prob >= 0.5).astype(int)
    m = dict(
        auc_roc=roc_auc_score(y_true, y_prob),
        avg_prec=average_precision_score(y_true, y_prob),
        log_loss=log_loss(y_true, y_prob),
        precision=precision_score(y_true, yb, zero_division=0),
        recall=recall_score(y_true, yb, zero_division=0),
        f1=f1_score(y_true, yb, zero_division=0),
        accuracy=float((yb == y_true).mean()),
    )
    print(f"\n  {name}")
    print(f"   AUC-ROC ........... {m['auc_roc']:.4f}")
    print(f"   Avg Precision ..... {m['avg_prec']:.4f}")
    print(f"   Log Loss .......... {m['log_loss']:.4f}")
    print(f"   Precision ......... {m['precision']:.4f}")
    print(f"   Recall ............ {m['recall']:.4f}")
    print(f"   F1-Score .......... {m['f1']:.4f}")
    print(f"   Accuracy .......... {m['accuracy']:.4f}")
    return m


def resolve_data_path(preferred_path: str) -> Path:
    candidates = [
        Path(preferred_path),
        Path(__file__).resolve().parent / preferred_path,
        Path(__file__).resolve().parents[2] / preferred_path,
        Path(__file__).resolve().parents[3] / preferred_path,
        Path.cwd() / preferred_path,
    ]
    for p in candidates:
        if p.exists():
            return p.resolve()
    raise FileNotFoundError(
        f"No se encontro el dataset '{preferred_path}'. Candidatos: {candidates}"
    )


def parse_args():
    p = argparse.ArgumentParser(
        description="Entrenamiento LightGBM para MovIA (plug-and-play con artifacts actuales)."
    )
    p.add_argument(
        "--data-path",
        default=os.getenv("DATA_PATH", "Train_Data.csv"),
        help="Ruta al Train_Data.csv",
    )
    p.add_argument(
        "--artifacts-dir",
        default=os.getenv("ARTIFACTS_DIR", "artifacts"),
        help="Directorio base de artifacts",
    )
    p.add_argument(
        "--optuna-trials",
        type=int,
        default=int(os.getenv("OPTUNA_TRIALS_LGBM", "12")),
        help="Numero de trials Optuna",
    )
    p.add_argument(
        "--n-folds",
        type=int,
        default=int(os.getenv("N_FOLDS_LGBM", "5")),
        help="Numero de folds CV",
    )
    p.add_argument(
        "--neg-per-user",
        type=int,
        default=int(os.getenv("NEG_PER_USER_LGBM", "5")),
        help="Cantidad de negativos sinteticos por usuario",
    )
    p.add_argument(
        "--n-estimators-search",
        type=int,
        default=int(os.getenv("N_ESTIMATORS_SEARCH_LGBM", "1200")),
        help="Boosting rounds para fase Optuna",
    )
    p.add_argument(
        "--n-estimators-final",
        type=int,
        default=int(os.getenv("N_ESTIMATORS_FINAL_LGBM", "2400")),
        help="Boosting rounds para modelo final",
    )
    return p.parse_args()


def build_augmented_dataset(df_full: pd.DataFrame, neg_per_user: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    df_rated = df_full[df_full["interaction_type"] == "rated"].copy()
    df_rated["target"] = (df_rated["user_rating"] >= TARGET_THRESHOLD).astype(int)
    df_rated["is_synthetic"] = False

    user_all_movies = df_full.groupby("user_id")["movie_id"].apply(set).to_dict()
    all_catalog_ids = df_full["movie_id"].unique()

    neg_records = []
    if neg_per_user > 0:
        sample_size = min(max(neg_per_user * 3, neg_per_user), len(all_catalog_ids))
        for uid in df_rated["user_id"].unique():
            seen = user_all_movies.get(uid, set())
            cands = np.random.choice(all_catalog_ids, size=sample_size, replace=False)
            chosen = [int(m) for m in cands if m not in seen][:neg_per_user]
            for mid in chosen:
                neg_records.append(
                    {"user_id": uid, "movie_id": mid, "target": 0, "is_synthetic": True}
                )

    neg_df = pd.DataFrame(neg_records)
    if len(neg_df) == 0:
        df_aug = df_rated[["user_id", "movie_id", "target", "is_synthetic"]].copy()
    else:
        df_aug = pd.concat(
            [df_rated[["user_id", "movie_id", "target", "is_synthetic"]], neg_df],
            ignore_index=True,
        )
    return df_rated, df_aug


def main():
    args = parse_args()
    t0 = time.time()
    np.random.seed(RANDOM_STATE)

    sec("MovIA - ENTRENAMIENTO LIGHTGBM (PLUG-AND-PLAY)")
    data_path = resolve_data_path(args.data_path)
    artifacts_dir = Path(args.artifacts_dir)

    sec("1. CARGA DE DATOS", "-")
    print(f"  Dataset: {data_path}")
    df_full = pd.read_csv(data_path)
    print(
        f"  {len(df_full):,} filas | {df_full['user_id'].nunique():,} usuarios "
        f"| {df_full['movie_id'].nunique():,} peliculas"
    )

    sec("2. PREPARACION - RATED + NEGATIVE SAMPLING", "-")
    df_rated, df_aug = build_augmented_dataset(df_full, args.neg_per_user)
    n_pos = int(df_aug["target"].sum())
    n_neg = len(df_aug) - n_pos
    n_syn = int(df_aug["is_synthetic"].sum())
    print(
        f"  Dataset aumentado: {len(df_aug):,}  [pos={n_pos:,} ({n_pos/len(df_aug)*100:.1f}%), "
        f"neg={n_neg:,} ({n_neg/len(df_aug)*100:.1f}%)]"
    )
    print(f"  Negativos sinteticos: {n_syn:,}")

    sec("3. SPLIT ESTRATIFICADO TRAIN / VAL / TEST", "-")
    trv, test_df = train_test_split(
        df_aug,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=df_aug["target"],
    )
    adj = VAL_SIZE / (1 - TEST_SIZE)
    train_df, val_df = train_test_split(
        trv,
        test_size=adj,
        random_state=RANDOM_STATE,
        stratify=trv["target"],
    )
    for tag, d in [("Train", train_df), ("Val", val_df), ("Test", test_df)]:
        p = int(d["target"].sum())
        n = len(d) - p
        s = int(d["is_synthetic"].sum())
        r = len(d) - s
        print(
            f"  {tag:<6s} {len(d):>8,}  [pos={p:,} neg={n:,}]  "
            f"(rated={r:,}, synthetic={s:,})"
        )

    sec("4. FEATURE ENGINEERING (REUSE TRANSFORMER)", "-")
    trans_path = artifacts_dir / "transformers"
    if not trans_path.exists():
        raise FileNotFoundError(
            f"No existe {trans_path}. Entrena primero el pipeline base de XGBoost "
            "o provee artifacts/transformers."
        )

    transformer = FeatureTransformer.load(trans_path)
    print(f"  Transformer cargado desde: {trans_path}")
    print(f"  Generos: {len(transformer.genre_columns)}")
    print(f"  Idiomas: {', '.join(transformer.top_languages)}")
    print(f"  Catalogo: {len(transformer.movie_catalog):,} peliculas")

    train_rated_ids = train_df[~train_df["is_synthetic"]][["user_id", "movie_id"]]
    train_rated_full = train_rated_ids.merge(
        df_full.drop_duplicates(subset=["user_id", "movie_id"]),
        on=["user_id", "movie_id"],
        how="left",
    )
    watched = df_full[df_full["interaction_type"] == "watched"][["user_id", "movie_id"]]
    prof_src = (
        pd.concat([watched, train_rated_full[["user_id", "movie_id"]]], ignore_index=True)
        .drop_duplicates(subset=["user_id", "movie_id"])
    )
    user_profiles = transformer.build_user_profiles(prof_src)
    avg_m = prof_src.groupby("user_id")["movie_id"].count().mean()
    print(f"  Perfiles: {len(user_profiles):,} usuarios ({avg_m:.0f} pelis/perfil)")

    sec("5. TRANSFORMACION", "-")
    t1 = time.time()
    X_tr, m_tr = transformer.transform(train_df, user_profiles)
    y_tr = m_tr["target"].values.astype(np.float32)
    print(f"  X_train: {X_tr.shape}  ({time.time()-t1:.1f}s)")

    t1 = time.time()
    X_va, m_va = transformer.transform(val_df, user_profiles)
    y_va = m_va["target"].values.astype(np.float32)
    print(f"  X_val:   {X_va.shape}  ({time.time()-t1:.1f}s)")

    t1 = time.time()
    X_te, m_te = transformer.transform(test_df, user_profiles)
    y_te = m_te["target"].values.astype(np.float32)
    print(f"  X_test:  {X_te.shape}  ({time.time()-t1:.1f}s)")

    feat_names = X_tr.columns.tolist()
    print(f"  Features: {len(feat_names)}")

    Xtr = np.nan_to_num(X_tr.values.astype(np.float32), nan=0.0)
    Xva = np.nan_to_num(X_va.values.astype(np.float32), nan=0.0)
    Xte = np.nan_to_num(X_te.values.astype(np.float32), nan=0.0)

    spw = float(y_tr.shape[0] - y_tr.sum()) / max(float(y_tr.sum()), 1.0)
    print(f"  scale_pos_weight: {spw:.2f}")

    sec("6. OPTUNA + STRATIFIED K-FOLD CV", "-")

    def objective(trial):
        params = dict(
            objective="binary",
            boosting_type="gbdt",
            metric="auc",
            learning_rate=trial.suggest_float("learning_rate", 0.01, 0.2, log=True),
            num_leaves=trial.suggest_int("num_leaves", 16, 160),
            max_depth=trial.suggest_int("max_depth", 3, 12),
            min_child_samples=trial.suggest_int("min_child_samples", 20, 300),
            subsample=trial.suggest_float("subsample", 0.6, 1.0),
            colsample_bytree=trial.suggest_float("colsample_bytree", 0.6, 1.0),
            reg_alpha=trial.suggest_float("reg_alpha", 1e-3, 10.0, log=True),
            reg_lambda=trial.suggest_float("reg_lambda", 1e-3, 10.0, log=True),
            min_split_gain=trial.suggest_float("min_split_gain", 0.0, 1.0),
            n_estimators=args.n_estimators_search,
            random_state=RANDOM_STATE,
            n_jobs=-1,
            scale_pos_weight=spw,
            verbosity=-1,
        )

        skf = StratifiedKFold(
            n_splits=args.n_folds, shuffle=True, random_state=RANDOM_STATE
        )
        aucs = []
        best_iterations = []
        for ti, vi in skf.split(Xtr, y_tr):
            model = lgb.LGBMClassifier(**params)
            model.fit(
                Xtr[ti],
                y_tr[ti],
                eval_set=[(Xtr[vi], y_tr[vi])],
                eval_metric="auc",
                callbacks=[lgb.early_stopping(40, verbose=False)],
            )
            yp = model.predict_proba(Xtr[vi])[:, 1]
            aucs.append(roc_auc_score(y_tr[vi], yp))
            best_iterations.append(int(model.best_iteration_ or params["n_estimators"]))

        ma = float(np.mean(aucs))
        sa = float(np.std(aucs))
        trial.set_user_attr("best_iteration_mean", int(np.mean(best_iterations)))
        print(
            f"  Trial {trial.number+1:3d}/{args.optuna_trials}  "
            f"AUC={ma:.4f}+/-{sa:.4f}  leaves={params['num_leaves']} "
            f"depth={params['max_depth']} lr={params['learning_rate']:.4f}"
        )
        return ma

    study = optuna.create_study(
        direction="maximize",
        sampler=optuna.samplers.TPESampler(seed=RANDOM_STATE),
    )
    study.optimize(objective, n_trials=args.optuna_trials)

    bp = study.best_params
    best_iter_search = int(study.best_trial.user_attrs.get("best_iteration_mean", 200))
    print(f"\n  Mejores params (CV AUC={study.best_value:.4f}):")
    for k, v in bp.items():
        print(f"    {k}: {v}")
    print(f"    best_iteration_promedio_cv: {best_iter_search}")

    sec("7. K-FOLD CV CON MEJORES HIPERPARAMETROS", "-")
    cv_params = dict(
        objective="binary",
        boosting_type="gbdt",
        metric="auc",
        random_state=RANDOM_STATE,
        n_jobs=-1,
        scale_pos_weight=spw,
        verbosity=-1,
        n_estimators=max(args.n_estimators_search, best_iter_search * 2),
        **bp,
    )
    skf = StratifiedKFold(
        n_splits=args.n_folds, shuffle=True, random_state=RANDOM_STATE
    )
    frows = []
    for fold, (ti, vi) in enumerate(skf.split(Xtr, y_tr)):
        mdl = lgb.LGBMClassifier(**cv_params)
        mdl.fit(
            Xtr[ti],
            y_tr[ti],
            eval_set=[(Xtr[vi], y_tr[vi])],
            eval_metric="auc",
            callbacks=[lgb.early_stopping(50, verbose=False)],
        )
        p_tr = mdl.predict_proba(Xtr[ti])[:, 1]
        p_va = mdl.predict_proba(Xtr[vi])[:, 1]
        atr = roc_auc_score(y_tr[ti], p_tr)
        ava = roc_auc_score(y_tr[vi], p_va)
        llv = log_loss(y_tr[vi], p_va)
        bi = int(mdl.best_iteration_ or cv_params["n_estimators"])
        frows.append(dict(fold=fold + 1, auc_tr=atr, auc_va=ava, ll=llv, gap=atr - ava, it=bi))
        print(
            f"  Fold {fold+1}: AUC_tr={atr:.4f}  AUC_va={ava:.4f}  "
            f"Gap={atr-ava:+.4f}  LL={llv:.4f}  iter={bi}"
        )

    fdf = pd.DataFrame(frows)
    cv_best_iter = int(fdf["it"].mean()) if len(fdf) > 0 else 300
    print("\n  Resumen:")
    print(f"  AUC Train: {fdf['auc_tr'].mean():.4f} +/- {fdf['auc_tr'].std():.4f}")
    print(f"  AUC Val:   {fdf['auc_va'].mean():.4f} +/- {fdf['auc_va'].std():.4f}")
    print(f"  LL Val:    {fdf['ll'].mean():.4f} +/- {fdf['ll'].std():.4f}")
    print(f"  Gap:       {fdf['gap'].mean():.4f} +/- {fdf['gap'].std():.4f}")

    sec("8. MODELO FINAL", "-")
    final_estimators = min(max(cv_best_iter * 2, 500), args.n_estimators_final)
    final_params = dict(
        objective="binary",
        boosting_type="gbdt",
        metric="auc",
        random_state=RANDOM_STATE,
        n_jobs=-1,
        scale_pos_weight=spw,
        verbosity=-1,
        n_estimators=final_estimators,
        **bp,
    )

    final_model = lgb.LGBMClassifier(**final_params)
    t1 = time.time()
    final_model.fit(
        Xtr,
        y_tr,
        eval_set=[(Xva, y_va)],
        eval_metric="auc",
        callbacks=[lgb.early_stopping(80, verbose=False)],
    )
    print(f"  Tiempo: {time.time()-t1:.1f}s")
    print(f"  Mejor iter: {final_model.best_iteration_} / {final_estimators}")

    sec("9. EVALUACION FINAL", "-")
    p_tr = final_model.predict_proba(Xtr)[:, 1]
    p_va = final_model.predict_proba(Xva)[:, 1]
    p_te = final_model.predict_proba(Xte)[:, 1]

    mtr = eval_cls_probs(y_tr, p_tr, "TRAIN")
    mva = eval_cls_probs(y_va, p_va, "VALIDATION")
    mte = eval_cls_probs(y_te, p_te, "TEST")

    g1 = mtr["auc_roc"] - mva["auc_roc"]
    g2 = mtr["auc_roc"] - mte["auc_roc"]
    g3 = mva["auc_roc"] - mte["auc_roc"]
    print(f"\n   AUC Train-Val:  {g1:+.4f}  {'OK' if abs(g1)<0.05 else 'WARN'}")
    print(f"   AUC Train-Test: {g2:+.4f}  {'OK' if abs(g2)<0.05 else 'WARN'}")
    print(f"   AUC Val-Test:   {g3:+.4f}  {'OK' if abs(g3)<0.03 else 'WARN'}")

    ytp = (p_te >= 0.5).astype(int)
    cm = confusion_matrix(y_te.astype(int), ytp)
    print("\n  Confusion Matrix (Test):")
    print("                  Pred-  Pred+")
    print(f"  Actual-     {cm[0,0]:>8,}{cm[0,1]:>8,}")
    print(f"  Actual+     {cm[1,0]:>8,}{cm[1,1]:>8,}")
    print(
        f"\n{classification_report(y_te.astype(int), ytp, target_names=['No gusto','Gusto'], digits=4)}"
    )

    sec("10. GUARDANDO ARTEFACTOS", "-")
    art = artifacts_dir
    model_dir = art / "model"
    model_dir.mkdir(parents=True, exist_ok=True)
    model_path = model_dir / "lightgbm_recommender.txt"
    final_model.booster_.save_model(str(model_path))
    print(f"  Modelo:      {model_path}")

    meta_dir = art / "metadata"
    meta_dir.mkdir(parents=True, exist_ok=True)
    meta_path = meta_dir / "training_metadata_lightgbm.json"
    feature_names_path = meta_dir / "feature_names_lightgbm.json"

    meta = dict(
        training_date=time.strftime("%Y-%m-%d %H:%M:%S"),
        model_type="LGBMClassifier",
        model_file=str(model_path.name),
        dataset_total=len(df_full),
        dataset_rated=len(df_rated),
        neg_per_user=args.neg_per_user,
        train_size=len(X_tr),
        val_size=len(X_va),
        test_size=len(X_te),
        n_features=len(feat_names),
        feature_names=feat_names,
        best_hyperparams=bp,
        best_cv_auc=float(study.best_value),
        best_iteration=int(final_model.best_iteration_ or final_estimators),
        metrics=dict(train=mtr, validation=mva, test=mte),
        kfold_results=frows,
        config=dict(
            n_folds=args.n_folds,
            optuna_trials=args.optuna_trials,
            target_threshold=TARGET_THRESHOLD,
            random_state=RANDOM_STATE,
            n_estimators_search=args.n_estimators_search,
            n_estimators_final=args.n_estimators_final,
            reused_transformer=True,
        ),
    )
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)
    with open(feature_names_path, "w", encoding="utf-8") as f:
        json.dump(feat_names, f, indent=2, ensure_ascii=False)
    print(f"  Metadata:    {meta_path}")
    print(f"  Features:    {feature_names_path}")

    sec("11. DEMO", "-")
    pop = transformer.movie_catalog.nlargest(200, "log_popularity")
    seeds = pop.sample(5, random_state=42).index.tolist()
    print("  Semillas:")
    for mid in seeds:
        r = transformer.movie_catalog.loc[mid]
        print(f"    [{mid}] {r['title']}  ({r['genres_raw']})")

    Xc, ci = transformer.prepare_inference(seeds, top_n_candidates=500)
    if len(Xc) > 0:
        Xcn = np.nan_to_num(Xc.values.astype(np.float32), nan=0.0)
        probs = final_model.predict_proba(Xcn)[:, 1]
        ci["probability"] = probs
        top3 = ci.nlargest(3, "probability")
        print("\n  TOP 3 RECOMENDACIONES:")
        for _, r in top3.iterrows():
            print(f"    [{r['movie_id']}] {r['title']}  {r['probability']*100:.1f}%")

    elapsed = time.time() - t0
    sec(f"COMPLETADO en {elapsed/60:.1f} minutos")


if __name__ == "__main__":
    main()
