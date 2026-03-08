#!/usr/bin/env python
import argparse
import json
import os
import sys
import time
import warnings
from pathlib import Path

import joblib
import numpy as np
import optuna
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
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
from src.config import RANDOM_STATE, TARGET_THRESHOLD, TEST_SIZE, VAL_SIZE
from src.feature_engineering import FeatureTransformer

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
        description="Entrenamiento RandomForest para MovIA (plug-and-play con artifacts actuales)."
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
        default=int(os.getenv("OPTUNA_TRIALS_RF", "8")),
        help="Numero de trials Optuna",
    )
    p.add_argument(
        "--n-folds",
        type=int,
        default=int(os.getenv("N_FOLDS_RF", "5")),
        help="Numero de folds CV",
    )
    p.add_argument(
        "--neg-per-user",
        type=int,
        default=int(os.getenv("NEG_PER_USER_RF", "5")),
        help="Cantidad de negativos sinteticos por usuario",
    )
    p.add_argument(
        "--n-estimators-search",
        type=int,
        default=int(os.getenv("N_ESTIMATORS_SEARCH_RF", "220")),
        help="Cantidad de arboles usada para Optuna + CV",
    )
    p.add_argument(
        "--n-estimators-final",
        type=int,
        default=int(os.getenv("N_ESTIMATORS_FINAL_RF", "360")),
        help="Cantidad de arboles para modelo final",
    )
    p.add_argument(
        "--tune-sample-frac",
        type=float,
        default=float(os.getenv("TUNE_SAMPLE_FRAC_RF", "0.5")),
        help="Fraccion de train usada en Optuna para acelerar busqueda",
    )
    return p.parse_args()


def build_augmented_dataset(
    df_full: pd.DataFrame, neg_per_user: int
) -> tuple[pd.DataFrame, pd.DataFrame]:
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


def sanitize_class_weight(value, bootstrap: bool):
    if value == "balanced_subsample" and not bootstrap:
        return "balanced"
    return value


def main():
    args = parse_args()
    t0 = time.time()
    np.random.seed(RANDOM_STATE)

    sec("MovIA - ENTRENAMIENTO RANDOM FOREST (PLUG-AND-PLAY)")
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

    sec("6. OPTUNA + STRATIFIED K-FOLD CV", "-")
    tune_frac = float(args.tune_sample_frac)
    if 0 < tune_frac < 1:
        X_tune, _, y_tune, _ = train_test_split(
            Xtr, y_tr, train_size=tune_frac, random_state=RANDOM_STATE, stratify=y_tr
        )
        print(f"  Submuestra para Optuna: {len(X_tune):,} filas ({tune_frac:.0%} de train)")
    else:
        X_tune, y_tune = Xtr, y_tr
        print(f"  Optuna usa train completo: {len(X_tune):,} filas")

    def objective(trial):
        bootstrap = trial.suggest_categorical("bootstrap", [True, False])
        class_weight = sanitize_class_weight(
            trial.suggest_categorical(
                "class_weight", [None, "balanced", "balanced_subsample"]
            ),
            bootstrap=bootstrap,
        )

        params = dict(
            n_estimators=args.n_estimators_search,
            criterion=trial.suggest_categorical("criterion", ["gini", "entropy", "log_loss"]),
            max_depth=trial.suggest_categorical("max_depth", [None, 8, 12, 16, 20, 24, 28]),
            min_samples_split=trial.suggest_int("min_samples_split", 2, 40),
            min_samples_leaf=trial.suggest_int("min_samples_leaf", 1, 20),
            max_features=trial.suggest_categorical(
                "max_features", ["sqrt", "log2", 0.5, 0.8, 1.0]
            ),
            bootstrap=bootstrap,
            class_weight=class_weight,
            n_jobs=-1,
            random_state=RANDOM_STATE,
        )

        skf = StratifiedKFold(
            n_splits=args.n_folds, shuffle=True, random_state=RANDOM_STATE
        )
        aucs = []
        for ti, vi in skf.split(X_tune, y_tune):
            m = RandomForestClassifier(**params)
            m.fit(X_tune[ti], y_tune[ti])
            yp = m.predict_proba(X_tune[vi])[:, 1]
            aucs.append(roc_auc_score(y_tune[vi], yp))

        ma = float(np.mean(aucs))
        sa = float(np.std(aucs))
        depth_txt = str(params["max_depth"])
        print(
            f"  Trial {trial.number+1:3d}/{args.optuna_trials}  "
            f"AUC={ma:.4f}+/-{sa:.4f}  depth={depth_txt} "
            f"leaf={params['min_samples_leaf']} split={params['min_samples_split']}"
        )
        return ma

    study = optuna.create_study(
        direction="maximize", sampler=optuna.samplers.TPESampler(seed=RANDOM_STATE)
    )
    study.optimize(objective, n_trials=args.optuna_trials)

    bp = study.best_params
    bp["class_weight"] = sanitize_class_weight(
        bp["class_weight"], bootstrap=bool(bp["bootstrap"])
    )
    print(f"\n  Mejores params (CV AUC={study.best_value:.4f}):")
    for k, v in bp.items():
        print(f"    {k}: {v}")

    sec("7. K-FOLD CV CON MEJORES HIPERPARAMETROS", "-")
    cv_params = dict(
        n_estimators=args.n_estimators_search,
        n_jobs=-1,
        random_state=RANDOM_STATE,
        **bp,
    )
    skf = StratifiedKFold(
        n_splits=args.n_folds, shuffle=True, random_state=RANDOM_STATE
    )
    frows = []
    for fold, (ti, vi) in enumerate(skf.split(Xtr, y_tr)):
        mdl = RandomForestClassifier(**cv_params)
        mdl.fit(Xtr[ti], y_tr[ti])
        p_tr = mdl.predict_proba(Xtr[ti])[:, 1]
        p_va = mdl.predict_proba(Xtr[vi])[:, 1]
        atr = roc_auc_score(y_tr[ti], p_tr)
        ava = roc_auc_score(y_tr[vi], p_va)
        llv = log_loss(y_tr[vi], p_va)
        frows.append(
            dict(
                fold=fold + 1,
                auc_tr=float(atr),
                auc_va=float(ava),
                ll=float(llv),
                gap=float(atr - ava),
                it=args.n_estimators_search,
            )
        )
        print(
            f"  Fold {fold+1}: AUC_tr={atr:.4f}  AUC_va={ava:.4f}  "
            f"Gap={atr-ava:+.4f}  LL={llv:.4f}  trees={args.n_estimators_search}"
        )

    fdf = pd.DataFrame(frows)
    print("\n  Resumen:")
    print(f"  AUC Train: {fdf['auc_tr'].mean():.4f} +/- {fdf['auc_tr'].std():.4f}")
    print(f"  AUC Val:   {fdf['auc_va'].mean():.4f} +/- {fdf['auc_va'].std():.4f}")
    print(f"  LL Val:    {fdf['ll'].mean():.4f} +/- {fdf['ll'].std():.4f}")
    print(f"  Gap:       {fdf['gap'].mean():.4f} +/- {fdf['gap'].std():.4f}")

    sec("8. MODELO FINAL", "-")
    final_params = dict(
        n_estimators=args.n_estimators_final,
        n_jobs=-1,
        random_state=RANDOM_STATE,
        **bp,
    )
    final_model = RandomForestClassifier(**final_params)
    t1 = time.time()
    final_model.fit(Xtr, y_tr)
    print(f"  Tiempo: {time.time()-t1:.1f}s")
    print(f"  Arboles: {args.n_estimators_final}")

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

    sec("10. TOP FEATURES", "-")
    imp = final_model.feature_importances_
    pairs = sorted(zip(feat_names, imp), key=lambda x: -x[1])
    mx = pairs[0][1] if pairs and pairs[0][1] > 0 else 1
    top_feats = []
    for i, (nm, v) in enumerate(pairs[:20]):
        print(f"   {i+1:2d}. {nm:<32s} {v:.4f}  {'#'*int(v/mx*25)}")
        top_feats.append({"feature": nm, "importance": float(v)})

    sec("11. GUARDANDO ARTEFACTOS", "-")
    art = artifacts_dir
    model_dir = art / "model"
    model_dir.mkdir(parents=True, exist_ok=True)
    model_path = model_dir / "random_forest_recommender.joblib"
    joblib.dump(final_model, model_path)
    print(f"  Modelo:      {model_path}")

    meta_dir = art / "metadata"
    meta_dir.mkdir(parents=True, exist_ok=True)
    meta_path = meta_dir / "training_metadata_random_forest.json"
    feature_names_path = meta_dir / "feature_names_random_forest.json"

    meta = dict(
        training_date=time.strftime("%Y-%m-%d %H:%M:%S"),
        model_type="RandomForestClassifier",
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
        best_iteration=args.n_estimators_final,
        metrics=dict(train=mtr, validation=mva, test=mte),
        kfold_results=frows,
        top_feature_importances=top_feats,
        config=dict(
            n_folds=args.n_folds,
            optuna_trials=args.optuna_trials,
            target_threshold=TARGET_THRESHOLD,
            random_state=RANDOM_STATE,
            n_estimators_search=args.n_estimators_search,
            n_estimators_final=args.n_estimators_final,
            tune_sample_frac=args.tune_sample_frac,
            reused_transformer=True,
        ),
    )
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)
    with open(feature_names_path, "w", encoding="utf-8") as f:
        json.dump(feat_names, f, indent=2, ensure_ascii=False)
    print(f"  Metadata:    {meta_path}")
    print(f"  Features:    {feature_names_path}")

    sec("12. DEMO", "-")
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
