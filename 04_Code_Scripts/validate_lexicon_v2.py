# scripts/validate_lexicon_v2.py
# -*- coding: utf-8 -*-
import os, re, json
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
import matplotlib.pyplot as plt

CORPUS_PQ   = os.path.join("artifacts","real","corpus_final.parquet")
FEATURES_PQ = os.path.join("artifacts","real","features_doc.parquet")  # v1 scores (fc/fi)
V2_PATH     = os.path.join("07_Config","lexicons","lexicon_conative_v2_enhanced.csv")
OUT_DIR     = os.path.join("artifacts","real","lexicon_v2_eval")
MANUAL_CSV  = os.path.join("07_Config","validation_manual.csv")

def load_patterns():
    if not os.path.exists(V2_PATH):
        raise FileNotFoundError(V2_PATH)
    df = pd.read_csv(V2_PATH)
    need = {"pattern","class","weight"}
    if not need.issubset(set(df.columns)):
        raise ValueError(f"Colonnes manquantes dans V2: {need - set(df.columns)}")
    # Compile regex
    comp = []
    for r in df.itertuples(index=False):
        try:
            rx = re.compile(r.pattern, flags=re.IGNORECASE)
            comp.append({"rx":rx,"klass":r._asdict().get("class"),"w":float(r._asdict().get("weight",1.0))})
        except re.error:
            # ignore regex invalides
            continue
    return comp

def score_doc(text, patterns):
    if not isinstance(text, str) or not text:
        return 0.0, 0.0
    fc, fi = 0.0, 0.0
    for p in patterns:
        matches = list(p["rx"].finditer(text))
        if not matches:
            continue
        if p["klass"] == "fc":
            fc += p["w"] * len(matches)
        elif p["klass"] == "fi":
            fi += p["w"] * len(matches)
        else:
            # "neutral" (négation) ou autre → pas de contribution
            pass
    # Normalisation simple par longueur (k tokens) si dispo
    # Ici, on normalise par 1000 tokens si la colonne existe
    return fc, fi

def load_corpus_and_v1():
    if not os.path.exists(CORPUS_PQ):
        raise FileNotFoundError(CORPUS_PQ)
    corpus = pd.read_parquet(CORPUS_PQ)
    v1 = None
    if os.path.exists(FEATURES_PQ):
        v1 = pd.read_parquet(FEATURES_PQ)
        v1 = v1[["actor_id","date","url","fc","fi"]].drop_duplicates()
    return corpus, v1

def load_manual():
    if not os.path.exists(MANUAL_CSV):
        print("ℹ️ Pas d’annotations manuelles — skip gold standard")
        return None
    df = pd.read_csv(MANUAL_CSV)
    # on suppose doc_id unique ; si plusieurs annotateurs: moyennes
    agg = df.groupby("doc_id")[["fc_manual","fi_manual"]].mean()
    meta = df.drop_duplicates(subset=["doc_id"])[["doc_id","actor_id","date","url"]]
    return agg, meta

def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    patterns = load_patterns()
    corpus, v1 = load_corpus_and_v1()

    # score V2
    rows = []
    for r in corpus.itertuples(index=False):
        fc2, fi2 = score_doc(r.text, patterns)
        rows.append({"actor_id":r.actor_id, "date":r.date, "url":r.url,
                     "tokens": getattr(r, "tokens", np.nan),
                     "fc_v2":fc2, "fi_v2":fi2})
    v2 = pd.DataFrame(rows)

    # normalisation simple si tokens dispo
    if "tokens" in v2.columns and v2["tokens"].notna().any():
        scale = v2["tokens"].fillna(v2["tokens"].median()).replace(0, np.nan)
        v2["fc_v2"] = v2["fc_v2"] / (scale/1000.0)
        v2["fi_v2"] = v2["fi_v2"] / (scale/1000.0)

    # Aggrégations acteur
    actor = v2.groupby("actor_id").agg(fc_mean=("fc_v2","mean"),
                                       fi_mean=("fi_v2","mean"),
                                       n=("fc_v2","size")).reset_index()
    actor.to_csv(os.path.join(OUT_DIR,"by_actor_conative_v2.csv"), index=False)

    # Histogrammes (vue rapide)
    for col in ["fc_v2","fi_v2"]:
        plt.figure(figsize=(5,4))
        v2[col].hist(bins=30)
        plt.title(f"Histogram {col}")
        plt.xlabel(col); plt.ylabel("count")
        plt.tight_layout()
        plt.savefig(os.path.join(OUT_DIR, f"hist_{col}.png"), dpi=120)
        plt.close()

    # Comparaison v1 (si dispo)
    if v1 is not None:
        merged = v2.merge(v1, on=["actor_id","date","url"], how="left", suffixes=("_v2",""))
        corr = merged[["fc_v2","fi_v2","fc","fi"]].corr(method="spearman")
        corr.to_csv(os.path.join(OUT_DIR,"compare_v1_v2_corr.csv"))
        print("\n== Corrélation Spearman (doc-level) v2 vs v1 ==")
        print(corr)

    # Gold standard (si dispo)
    gold = load_manual()
    if gold is not None:
        agg, meta = gold
        # map sur doc_id via meta (actor_id+date+url)
        key = ["actor_id","date","url"]
        # relie doc_id à corpus
        m = meta.merge(v2, on=key, how="inner").set_index("doc_id")
        joined = m.join(agg, how="inner")
        if len(joined) >= 3:
            r_fc, p_fc = spearmanr(joined["fc_v2"], joined["fc_manual"])
            r_fi, p_fi = spearmanr(joined["fi_v2"], joined["fi_manual"])
            print(f"\n== Gold standard (n={len(joined)}) ==")
            print(f"Fc: r={r_fc:.3f}, p={p_fc:.4f}")
            print(f"Fi: r={r_fi:.3f}, p={p_fi:.4f}")
            pd.DataFrame({"metric":["fc","fi"],"r":[r_fc,r_fi],"p":[p_fc,p_fi]}).to_csv(
                os.path.join(OUT_DIR,"gold_correlation.csv"), index=False
            )
        else:
            print("⚠️ Pas de recouvrement suffisant avec annotations manuelles")

    print(f"\n[OK] Résultats V2 → {OUT_DIR}")

if __name__ == "__main__":
    main()
