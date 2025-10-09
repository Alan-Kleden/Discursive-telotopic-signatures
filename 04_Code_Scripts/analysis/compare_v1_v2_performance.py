# 04_Code_Scripts/analysis/compare_v1_v2_performance.py
# -*- coding: utf-8 -*-
import os
import pandas as pd

OUT_DIR = os.path.join("artifacts","real","lexicon_comparison")
EVAL_DIR = os.path.join("artifacts","real","lexicon_v2_eval")

def _norm(df, is_v2=False):
    """Normalise colonnes -> actor_id, fc_mean, fi_mean"""
    df = df.copy()
    rename_map = {}
    cols = set(c.lower() for c in df.columns)
    # détecte noms possibles
    if "actor_id" not in df.columns:
        for c in df.columns:
            if c.lower() in ["actor","actorid","actor_name"]:
                rename_map[c] = "actor_id"
                break
    # fc
    if "fc_mean" not in df.columns:
        for c in df.columns:
            if c.lower() in ["fc_mean","mean_fc","fc_avg","fc_v2" if is_v2 else "fc"]:
                rename_map[c] = "fc_mean"; break
    # fi
    if "fi_mean" not in df.columns:
        for c in df.columns:
            if c.lower() in ["fi_mean","mean_fi","fi_avg","fi_v2" if is_v2 else "fi"]:
                rename_map[c] = "fi_mean"; break
    if rename_map: df = df.rename(columns=rename_map)
    keep = [c for c in ["actor_id","fc_mean","fi_mean"] if c in df.columns]
    return df[keep]

def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    v1_path = os.path.join(EVAL_DIR, "by_actor_conative_v1.csv")
    v2_path = os.path.join(EVAL_DIR, "by_actor_conative_v2.csv")
    if not os.path.exists(v1_path) or not os.path.exists(v2_path):
        raise FileNotFoundError("Fichiers by-actor v1/v2 introuvables. Lance d'abord validate_lexicon_v2.py")

    v1 = pd.read_csv(v1_path)
    v2 = pd.read_csv(v2_path)

    v1 = _norm(v1, is_v2=False)
    v2 = _norm(v2, is_v2=True)

    m = v1.merge(v2, on="actor_id", suffixes=("_v1","_v2"))
    print("=== Comparaison acteur (moyennes) ===")
    for _, r in m.iterrows():
        print(f"{r['actor_id']:<28} "
              f"Fc: {r['fc_mean_v1']:.3f} → {r['fc_mean_v2']:.3f} | "
              f"Fi: {r['fi_mean_v1']:.3f} → {r['fi_mean_v2']:.3f}")

    # export tableau comparatif
    m.to_csv(os.path.join(OUT_DIR,"by_actor_v1_vs_v2.csv"), index=False)
    print("[OK] Export →", os.path.join(OUT_DIR,"by_actor_v1_vs_v2.csv"))

if __name__ == "__main__":
    main()
