# 04_Code_Scripts/analysis/validate_lexicon_v2.py
# -*- coding: utf-8 -*-
import os, re, csv, math
import pandas as pd

ROOT = os.getcwd()
CORPUS_PQ = os.path.join("artifacts","real","corpus_final.parquet")
FEAT_PQ   = os.path.join("artifacts","real","features_doc.parquet")
V2_PATH   = os.path.join("07_Config","lexicons","lexicon_conative_v2_enhanced.csv")
OUT_DIR   = os.path.join("artifacts","real","lexicon_v2_eval")

def _stdcol(df):
    """Normalise colonnes des patterns: -> ['pattern','kind','klass','weight']"""
    df = df.copy()
    # 'class' pose pb avec itertuples -> renomme en 'klass'
    rename_map = {}
    if "class" in df.columns: rename_map["class"] = "klass"
    if "_class" in df.columns: rename_map["_class"] = "klass"
    if "type" in df.columns and "klass" not in df.columns: rename_map["type"] = "klass"
    if "weight" not in df.columns: df["weight"] = 1.0
    if "pattern" not in df.columns:
        # certains exports avaient 'regex' ou 'pattern_lemma_re'
        if "regex" in df.columns: rename_map["regex"] = "pattern"
        elif "pattern_lemma_re" in df.columns: rename_map["pattern_lemma_re"] = "pattern"
    if "kind" not in df.columns: df["kind"] = "regex"
    if rename_map: df = df.rename(columns=rename_map)
    # filtre colonnes utiles
    keep = [c for c in ["pattern","kind","klass","weight"] if c in df.columns]
    df = df[keep].dropna(subset=["pattern","klass"]).copy()
    # nettoyages
    df["klass"] = df["klass"].astype(str).str.lower().str.strip()
    df = df[df["klass"].isin(["fc","fi"])]
    # poids
    try:
        df["weight"] = df["weight"].astype(float)
    except Exception:
        df["weight"] = 1.0
    return df

def load_v2_patterns(path=V2_PATH):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Patterns V2 introuvables: {path}")
    raw = pd.read_csv(path)
    df = _stdcol(raw)
    # compile regex
    comp = []
    for _, r in df.iterrows():
        try:
            rx = re.compile(str(r["pattern"]), flags=re.IGNORECASE)
            comp.append({"rx": rx, "klass": r["klass"], "w": float(r["weight"])})
        except re.error:
            # on ignore les patterns invalides
            continue
    return comp

def score_text(text, patterns):
    if not isinstance(text, str) or not text:
        return 0.0, 0.0
    fc = fi = 0.0
    for p in patterns:
        # compte les occurrences pondérées
        m = p["rx"].findall(text)
        if not m: 
            continue
        incr = p["w"] * (len(m))
        if p["klass"] == "fc": fc += incr
        else: fi += incr
    # petite normalisation par longueur (évite les docs très longs)
    # APRES : normalisation plus douce (réf 200 tokens)
    toks = max(len(text.split())/200.0, 1.0)
    return fc / toks, fi / toks

def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    # 1) corpus
    corpus = pd.read_parquet(CORPUS_PQ)
    # 2) features V1 (serviront pour la comparaison et pour by-actor v1)
    feats = pd.read_parquet(FEAT_PQ)

    # 3) charger patterns V2
    pats = load_v2_patterns()

    # 4) scorer V2 doc-level
    df = corpus.merge(feats[["actor_id","date","url"]], on=["actor_id","date","url"], how="left")
    fc_v2, fi_v2 = [], []
    for t in df["text"].astype(str):
        s_fc, s_fi = score_text(t, pats)
        fc_v2.append(s_fc); fi_v2.append(s_fi)
    df["fc_v2"] = fc_v2
    df["fi_v2"] = fi_v2

    # sauvegarde doc-level
    doc_out = os.path.join(OUT_DIR, "doc_scores_v2.csv")
    df[["actor_id","date","url","fc_v2","fi_v2"]].to_csv(doc_out, index=False)

    # 5) by-actor V2 (mêmes noms que V1 pour merge futur)
    by_actor_v2 = df.groupby("actor_id")[["fc_v2","fi_v2"]].mean().reset_index()
    by_actor_v2 = by_actor_v2.rename(columns={"fc_v2":"fc_mean","fi_v2":"fi_mean"})
    by_actor_v2.to_csv(os.path.join(OUT_DIR,"by_actor_conative_v2.csv"), index=False)

    # 6) by-actor V1 — Recalcul propre depuis features_doc.parquet
    v1 = feats.groupby("actor_id")[["fc","fi"]].mean().reset_index()
    v1 = v1.rename(columns={"fc":"fc_mean","fi":"fi_mean"})
    v1.to_csv(os.path.join(OUT_DIR,"by_actor_conative_v1.csv"), index=False)

    # 7) corr rapides (info)
    merged = feats.merge(df[["actor_id","date","url","fc_v2","fi_v2"]],
                         on=["actor_id","date","url"], how="left")
    c = merged[["fc","fi","fc_v2","fi_v2"]].corr(method="spearman")
    c.to_csv(os.path.join(OUT_DIR,"doclevel_spearman_v1_v2.csv"))
    print("[OK] V2 doc-level/by-actor et corr exportés →", OUT_DIR)

if __name__ == "__main__":
    main()

