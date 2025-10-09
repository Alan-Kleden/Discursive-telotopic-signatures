# 04_Code_Scripts/analysis/compare_v1_v2_performance.py
# -*- coding: utf-8 -*-
import os
import pandas as pd

ROOT = os.getcwd()
FEAT_PQ = os.path.join("artifacts","real","features_doc.parquet")
V2_BY_ACTOR = os.path.join("artifacts","real","lexicon_v2_eval","by_actor_conative_v2.csv")
OUT_DIR = os.path.join("artifacts","real","lexicon_comparison")
os.makedirs(OUT_DIR, exist_ok=True)

def load_v1_actor_means():
    if not os.path.exists(FEAT_PQ):
        raise FileNotFoundError(FEAT_PQ)
    df = pd.read_parquet(FEAT_PQ)
    # garde seulement ce qui est nécessaire
    need = ["actor_id","fc","fi"]
    miss = [c for c in need if c not in df.columns]
    if miss:
        raise ValueError(f"Colonnes manquantes dans features_doc.parquet: {miss}")
    g = df.groupby("actor_id").agg(
        fc_mean_v1=("fc","mean"),
        fi_mean_v1=("fi","mean"),
        n_docs_v1=("fc","size")
    ).reset_index()
    return g

def load_v2_actor_means():
    if not os.path.exists(V2_BY_ACTOR):
        raise FileNotFoundError(V2_BY_ACTOR)
    df = pd.read_csv(V2_BY_ACTOR)
    # tolérant aux noms de colonnes
    # attend au minimum: actor_id, fc_mean, fi_mean
    rename = {}
    if "fc_mean" not in df.columns:
        # essais de variantes
        for cand in ["fc_mean_v2","fc_avg","fc"]:
            if cand in df.columns:
                rename[cand] = "fc_mean"
                break
    if "fi_mean" not in df.columns:
        for cand in ["fi_mean_v2","fi_avg","fi"]:
            if cand in df.columns:
                rename[cand] = "fi_mean"
                break
    if rename:
        df = df.rename(columns=rename)

    need = ["actor_id","fc_mean","fi_mean"]
    miss = [c for c in need if c not in df.columns]
    if miss:
        raise ValueError(f"Colonnes manquantes dans by_actor_conative_v2.csv: {miss}")

    df = df[["actor_id","fc_mean","fi_mean"]].copy()
    df = df.rename(columns={"fc_mean":"fc_mean_v2","fi_mean":"fi_mean_v2"})
    return df

def main():
    v1 = load_v1_actor_means()
    v2 = load_v2_actor_means()
    merged = v1.merge(v2, on="actor_id", how="inner")

    print("\n=== Comparaison acteur (moyennes) ===")
    for _, r in merged.iterrows():
        print(f"{r['actor_id']:<28} "
              f"Fc: {r['fc_mean_v1']:.3f} → {r['fc_mean_v2']:.3f} | "
              f"Fi: {r['fi_mean_v1']:.3f} → {r['fi_mean_v2']:.3f} | "
              f"n={int(r['n_docs_v1'])}")

    merged.to_csv(os.path.join(OUT_DIR,"actor_means_v1_v2.csv"), index=False)
    print(f"\n[OK] {os.path.join(OUT_DIR,'actor_means_v1_v2.csv')}")

if __name__ == "__main__":
    main()
