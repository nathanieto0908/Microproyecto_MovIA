#!/usr/bin/env python
import os, sys, time, json, warnings
import numpy as np
import pandas as pd
import xgboost as xgb
import optuna
from sklearn.model_selection import train_test_split, StratifiedKFold
from sklearn.metrics import (
    roc_auc_score, average_precision_score, precision_score, recall_score,
    f1_score, log_loss, confusion_matrix, classification_report,
)
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from src.feature_engineering import FeatureTransformer
from src.config import *

warnings.filterwarnings("ignore")
optuna.logging.set_verbosity(optuna.logging.WARNING)

W = 70


def sec(title, c="="):
    print(f"\n{c * W}\n  {title}\n{c * W}")


def eval_cls(model, X, y, name):
    yp = model.predict_proba(X)[:, 1]
    yb = (yp >= 0.5).astype(int)
    m = dict(
        auc_roc=roc_auc_score(y, yp),
        avg_prec=average_precision_score(y, yp),
        log_loss=log_loss(y, yp),
        precision=precision_score(y, yb, zero_division=0),
        recall=recall_score(y, yb, zero_division=0),
        f1=f1_score(y, yb, zero_division=0),
        accuracy=float((yb == y).mean()),
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


def main():
    t0 = time.time()
    np.random.seed(RANDOM_STATE)

    sec("MovIA - ENTRENAMIENTO SUPERVISADO CON XGBOOST")

    sec("1. CARGA DE DATOS", "-")
    df_full = pd.read_csv(DATA_PATH)
    print(f"  {len(df_full):,} filas | {df_full['user_id'].nunique():,} usuarios "
          f"| {df_full['movie_id'].nunique():,} peliculas")

    sec("2. PREPARACION - RATED + NEGATIVE SAMPLING", "-")
    df_rated = df_full[df_full["interaction_type"] == "rated"].copy()
    df_rated["target"] = (df_rated["user_rating"] >= TARGET_THRESHOLD).astype(int)
    df_rated["is_synthetic"] = False

    n_pos = int(df_rated["target"].sum())
    n_neg = len(df_rated) - n_pos
    print(f"  Rated: {len(df_rated):,}  [pos={n_pos:,} ({n_pos/len(df_rated)*100:.1f}%), "
          f"neg={n_neg:,} ({n_neg/len(df_rated)*100:.1f}%)]")

    NEG_PER_USER = 5
    user_all_movies = df_full.groupby("user_id")["movie_id"].apply(set).to_dict()
    all_catalog_ids = df_full["movie_id"].unique()

    neg_records = []
    for uid in df_rated["user_id"].unique():
        seen = user_all_movies.get(uid, set())
        cands = np.random.choice(all_catalog_ids, size=NEG_PER_USER * 3, replace=False)
        chosen = [int(m) for m in cands if m not in seen][:NEG_PER_USER]
        for mid in chosen:
            neg_records.append({"user_id": uid, "movie_id": mid,
                                "target": 0, "is_synthetic": True})

    neg_df = pd.DataFrame(neg_records)
    df_aug = pd.concat([df_rated[["user_id", "movie_id", "target", "is_synthetic"]],
                        neg_df], ignore_index=True)
    n_p = int(df_aug["target"].sum())
    n_n = len(df_aug) - n_p
    print(f"  Negativos sinteticos: {len(neg_df):,}")
    print(f"  Dataset aumentado: {len(df_aug):,}  [pos={n_p:,} ({n_p/len(df_aug)*100:.1f}%), "
          f"neg={n_n:,} ({n_n/len(df_aug)*100:.1f}%)]")

    sec("3. SPLIT ESTRATIFICADO TRAIN / VAL / TEST", "-")
    trv, test_df = train_test_split(df_aug, test_size=TEST_SIZE,
                                    random_state=RANDOM_STATE, stratify=df_aug["target"])
    adj = VAL_SIZE / (1 - TEST_SIZE)
    train_df, val_df = train_test_split(trv, test_size=adj,
                                        random_state=RANDOM_STATE, stratify=trv["target"])

    for tag, d in [("Train", train_df), ("Val", val_df), ("Test", test_df)]:
        p = int(d["target"].sum()); n = len(d) - p
        s = int(d["is_synthetic"].sum()); r = len(d) - s
        print(f"  {tag:<6s} {len(d):>8,}  [pos={p:,} neg={n:,}]  "
              f"(rated={r:,}, synthetic={s:,})")

    assert not (set(train_df.index) & set(test_df.index))
    print("  Sin leakage entre splits")

    sec("4. FEATURE ENGINEERING (fit en TRAIN)", "-")
    train_rated_ids = train_df[~train_df["is_synthetic"]][["user_id", "movie_id"]]
    train_rated_full = train_rated_ids.merge(
        df_full.drop_duplicates(subset=["user_id", "movie_id"]),
        on=["user_id", "movie_id"], how="left",
    )
    transformer = FeatureTransformer()
    transformer.fit(train_rated_full, df_full)
    print(f"  Generos: {len(transformer.genre_columns)}")
    print(f"  Idiomas: {', '.join(transformer.top_languages)}")
    print(f"  Catalogo: {len(transformer.movie_catalog):,} peliculas")

    watched = df_full[df_full["interaction_type"] == "watched"][["user_id", "movie_id"]]
    prof_src = pd.concat([watched, train_rated_full[["user_id", "movie_id"]]],
                         ignore_index=True).drop_duplicates(subset=["user_id", "movie_id"])
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
    for i, fn in enumerate(feat_names):
        print(f"    {i+1:3d}. {fn}")

    Xtr = np.nan_to_num(X_tr.values.astype(np.float32), nan=0.0)
    Xva = np.nan_to_num(X_va.values.astype(np.float32), nan=0.0)
    Xte = np.nan_to_num(X_te.values.astype(np.float32), nan=0.0)

    spw = float(y_tr.shape[0] - y_tr.sum()) / max(float(y_tr.sum()), 1.0)
    print(f"  scale_pos_weight: {spw:.2f}")

    sec("6. OPTUNA + STRATIFIED 5-FOLD CV", "-")

    def objective(trial):
        p = dict(
            max_depth=trial.suggest_int("max_depth", 3, 8),
            learning_rate=trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
            n_estimators=1500,
            subsample=trial.suggest_float("subsample", 0.6, 1.0),
            colsample_bytree=trial.suggest_float("colsample_bytree", 0.6, 1.0),
            reg_alpha=trial.suggest_float("reg_alpha", 1e-3, 10.0, log=True),
            reg_lambda=trial.suggest_float("reg_lambda", 1e-3, 10.0, log=True),
            min_child_weight=trial.suggest_int("min_child_weight", 1, 15),
            gamma=trial.suggest_float("gamma", 0.0, 5.0),
            scale_pos_weight=spw,
            objective="binary:logistic",
            eval_metric="auc",
            tree_method="hist",
            random_state=RANDOM_STATE,
            n_jobs=-1,
            early_stopping_rounds=30,
        )
        skf = StratifiedKFold(n_splits=N_FOLDS, shuffle=True, random_state=RANDOM_STATE)
        aucs = []
        for ti, vi in skf.split(Xtr, y_tr):
            m = xgb.XGBClassifier(**p)
            m.fit(Xtr[ti], y_tr[ti], eval_set=[(Xtr[vi], y_tr[vi])], verbose=False)
            aucs.append(roc_auc_score(y_tr[vi], m.predict_proba(Xtr[vi])[:, 1]))
        ma = np.mean(aucs); sa = np.std(aucs)
        print(f"  Trial {trial.number+1:3d}/{OPTUNA_TRIALS}  "
              f"AUC={ma:.4f}+/-{sa:.4f}  d={p['max_depth']} "
              f"lr={p['learning_rate']:.4f} sub={p['subsample']:.2f}")
        return ma

    study = optuna.create_study(direction="maximize",
                                sampler=optuna.samplers.TPESampler(seed=RANDOM_STATE))
    study.optimize(objective, n_trials=OPTUNA_TRIALS)

    bp = study.best_params
    print(f"\n  Mejores params (CV AUC={study.best_value:.4f}):")
    for k, v in bp.items():
        print(f"    {k}: {v}")

    sec("7. K-FOLD CV CON MEJORES HIPERPARAMETROS", "-")
    fhp = dict(**bp, n_estimators=2000, scale_pos_weight=spw,
               objective="binary:logistic", eval_metric="auc",
               tree_method="hist", random_state=RANDOM_STATE,
               n_jobs=-1, early_stopping_rounds=50)

    skf = StratifiedKFold(n_splits=N_FOLDS, shuffle=True, random_state=RANDOM_STATE)
    frows = []
    for fold, (ti, vi) in enumerate(skf.split(Xtr, y_tr)):
        mdl = xgb.XGBClassifier(**fhp)
        mdl.fit(Xtr[ti], y_tr[ti], eval_set=[(Xtr[vi], y_tr[vi])], verbose=False)
        atr = roc_auc_score(y_tr[ti], mdl.predict_proba(Xtr[ti])[:, 1])
        ava = roc_auc_score(y_tr[vi], mdl.predict_proba(Xtr[vi])[:, 1])
        llv = log_loss(y_tr[vi], mdl.predict_proba(Xtr[vi])[:, 1])
        frows.append(dict(fold=fold+1, auc_tr=atr, auc_va=ava,
                          ll=llv, gap=atr-ava, it=mdl.best_iteration))
        print(f"  Fold {fold+1}: AUC_tr={atr:.4f}  AUC_va={ava:.4f}  "
              f"Gap={atr-ava:+.4f}  LL={llv:.4f}  iter={mdl.best_iteration}")

    fdf = pd.DataFrame(frows)
    print(f"\n  Resumen:")
    print(f"  AUC Train: {fdf['auc_tr'].mean():.4f} +/- {fdf['auc_tr'].std():.4f}")
    print(f"  AUC Val:   {fdf['auc_va'].mean():.4f} +/- {fdf['auc_va'].std():.4f}")
    print(f"  LL Val:    {fdf['ll'].mean():.4f} +/- {fdf['ll'].std():.4f}")
    print(f"  Gap:       {fdf['gap'].mean():.4f} +/- {fdf['gap'].std():.4f}")
    gap_ok = fdf["gap"].mean() < 0.05
    print(f"  {'OK' if gap_ok else 'WARN'}: Gap {'< 5%' if gap_ok else '>= 5%'}")

    sec("8. MODELO FINAL", "-")
    final_model = xgb.XGBClassifier(**fhp)
    t1 = time.time()
    final_model.fit(Xtr, y_tr, eval_set=[(Xva, y_va)], verbose=False)
    print(f"  Tiempo: {time.time()-t1:.1f}s")
    print(f"  Mejor iter: {final_model.best_iteration} / {fhp['n_estimators']}")

    sec("9. EVALUACION FINAL", "-")
    mtr = eval_cls(final_model, Xtr, y_tr, "TRAIN")
    mva = eval_cls(final_model, Xva, y_va, "VALIDATION")
    mte = eval_cls(final_model, Xte, y_te, "TEST")

    g1 = mtr["auc_roc"] - mva["auc_roc"]
    g2 = mtr["auc_roc"] - mte["auc_roc"]
    g3 = mva["auc_roc"] - mte["auc_roc"]
    print(f"\n   AUC Train-Val:  {g1:+.4f}  {'OK' if abs(g1)<0.05 else 'WARN'}")
    print(f"   AUC Train-Test: {g2:+.4f}  {'OK' if abs(g2)<0.05 else 'WARN'}")
    print(f"   AUC Val-Test:   {g3:+.4f}  {'OK' if abs(g3)<0.03 else 'WARN'}")

    ytp = (final_model.predict_proba(Xte)[:, 1] >= 0.5).astype(int)
    cm = confusion_matrix(y_te.astype(int), ytp)
    print(f"\n  Confusion Matrix (Test):")
    print(f"                  Pred-  Pred+")
    print(f"  Actual-     {cm[0,0]:>8,}{cm[0,1]:>8,}")
    print(f"  Actual+     {cm[1,0]:>8,}{cm[1,1]:>8,}")
    print(f"\n{classification_report(y_te.astype(int), ytp, target_names=['No gusto','Gusto'], digits=4)}")

    print(f"  TOP 20 FEATURES")
    imp = final_model.feature_importances_
    pairs = sorted(zip(feat_names, imp), key=lambda x: -x[1])
    mx = pairs[0][1] if pairs[0][1] > 0 else 1
    for i, (nm, v) in enumerate(pairs[:20]):
        print(f"   {i+1:2d}. {nm:<32s} {v:.4f}  {'#'*int(v/mx*25)}")

    sec("10. GUARDANDO ARTEFACTOS", "-")
    art = Path(ARTIFACTS_DIR)

    md = art / "model"; md.mkdir(parents=True, exist_ok=True)
    mp = md / "xgboost_recommender.ubj"
    final_model.save_model(str(mp))
    print(f"  Modelo:      {mp}")

    td = art / "transformers"
    transformer.save(td)
    print(f"  Transformer: {td}")

    mtd = art / "metadata"; mtd.mkdir(parents=True, exist_ok=True)
    meta = dict(
        training_date=time.strftime("%Y-%m-%d %H:%M:%S"),
        model_type="XGBClassifier",
        dataset_total=len(df_full), dataset_rated=len(df_rated),
        neg_per_user=NEG_PER_USER,
        train_size=len(X_tr), val_size=len(X_va), test_size=len(X_te),
        n_features=len(feat_names), feature_names=feat_names,
        best_hyperparams=bp, best_cv_auc=study.best_value,
        metrics=dict(train=mtr, validation=mva, test=mte),
        kfold_results=frows,
        config=dict(n_folds=N_FOLDS, optuna_trials=OPTUNA_TRIALS,
                    target_threshold=TARGET_THRESHOLD, random_state=RANDOM_STATE),
    )
    with open(mtd / "training_metadata.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, default=str, ensure_ascii=False)
    print(f"  Metadata:    {mtd / 'training_metadata.json'}")

    with open(mtd / "feature_names.json", "w") as f:
        json.dump(feat_names, f, indent=2)
    print(f"  Features:    {mtd / 'feature_names.json'}")

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
        print(f"\n  TOP 3 RECOMENDACIONES:")
        for _, r in top3.iterrows():
            print(f"    [{r['movie_id']}] {r['title']}  {r['probability']*100:.1f}%")

    elapsed = time.time() - t0
    sec(f"COMPLETADO en {elapsed/60:.1f} minutos")


if __name__ == "__main__":
    main()
