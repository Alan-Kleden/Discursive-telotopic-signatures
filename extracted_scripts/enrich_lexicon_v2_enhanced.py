# -*- coding: utf-8 -*-
"""
enrich_lexicon_v2_enhanced.py  —  ANNULLE & REMPLACE

Objectif:
- Lire le lexique v1 depuis un fichier au choix:
    * v1 "clean" (ex: 07_Config/lexicons/lexicon_conative_v1.clean.csv)
      -> colonnes attendues: lemma|concept_id + type (push/inhibit) + pattern_lemma_re? + weight?
    * v1 "mapped" (ex: 07_Config/lexicons/lexicon_conative_v1.mapped.csv)
      -> colonnes attendues: pattern,class
- Construire un v2 = (v1 normalisé en regex) + patterns contextuels
- TF-IDF data-driven optionnel (sauté automatiquement si dataset trop petit ou sklearn indispo)
- Pas de dépendances “dures” à sentence-transformers : si absent, on saute la validation sémantique.

Sorties:
- 07_Config/lexicons/lexicon_conative_v2_enhanced.csv
- 07_Config/lexicons/lexicon_v2_enhanced.changelog.md
"""

import os, re, csv, argparse, math
import pandas as pd
from datetime import datetime

ROOT = os.getcwd()

# chemins par défaut (modifiables par CLI)
DEF_V1_PATH = os.path.join("07_Config","lexicons","lexicon_conative_v1.clean.csv")
DEF_V1_MAPPED = os.path.join("07_Config","lexicons","lexicon_conative_v1.mapped.csv")
OUT_V2_PATH = os.path.join("07_Config","lexicons","lexicon_conative_v2_enhanced.csv")
CHANGELOG_PATH = os.path.join("07_Config","lexicons","lexicon_v2_enhanced.changelog.md")

CORPUS_PQ   = os.path.join("artifacts","real","corpus_final.parquet")
FEATURES_PQ = os.path.join("artifacts","real","features_doc.parquet")

# ==========
# Utilitaires
# ==========

def _exists(p: str) -> bool:
    return p and os.path.exists(p)

def _coalesce(*paths):
    """retourne le premier chemin existant"""
    for p in paths:
        if _exists(p): return p
    return None

def _safe_read_csv(fp: str) -> pd.DataFrame:
    return pd.read_csv(fp, encoding="utf-8", on_bad_lines="skip")

# ==========
# Chargement V1 (2 formats acceptés)
# ==========

def load_v1_flexible(path_clean: str|None, path_mapped: str|None) -> pd.DataFrame:
    """
    Retourne un DataFrame normalisé avec colonnes:
        pattern (regex, str) | class ('fc' ou 'fi') | weight (float)
    Tolère :
      - v1.clean  : colonnes lemma/type/(pattern_lemma_re)/weight
      - v1.mapped : colonnes pattern/class
    """
    # 1) choix de la source
    src = _coalesce(path_mapped, path_clean)
    if not src:
        raise FileNotFoundError("Aucun v1 trouvé (ni mapped, ni clean).")
    df = _safe_read_csv(src)

    # 2) Cas v1.mapped (pattern,class)
    if {"pattern","class"}.issubset(df.columns):
        out = df[["pattern","class"]].copy()
        out["class"] = out["class"].str.strip().str.lower().map({"fc":"fc","fi":"fi"})
        out = out[out["class"].isin(["fc","fi"])].dropna(subset=["pattern"])
        out["weight"] = 1.0
        # nettoyage pattern (laisser tel quel: on considère déjà regex prêt)
        out["pattern"] = out["pattern"].astype(str).str.strip()
        return out.reset_index(drop=True)

    # 3) Cas v1.clean
    # colonnes candidates:
    lex_col = None
    for c in ["pattern_lemma_re","lemma","concept_id","token","term"]:
        if c in df.columns:
            lex_col = c; break
    typ_col = None
    for c in ["type","class"]:
        if c in df.columns:
            typ_col = c; break
    w_col = "weight" if "weight" in df.columns else None

    if not typ_col or not lex_col:
        raise ValueError("Colonnes lexicale/class manquantes dans v1.clean")

    tmp = df[[lex_col, typ_col] + ([w_col] if w_col else [])].copy()
    tmp.columns = ["_lex","_type"] + (["_w"] if w_col else [])
    tmp["_type"] = tmp["_type"].astype(str).str.lower().str.strip()
    # map: push -> fc / inhibit -> fi
    cls_map = {"push":"fc","inhibit":"fi","fc":"fc","fi":"fi"}
    tmp["class"] = tmp["_type"].map(cls_map)
    tmp = tmp[tmp["class"].isin(["fc","fi"])].dropna(subset=["_lex"])

    # normalisation en regex
    def to_pattern(s: str) -> str:
        s = str(s)
        # si l'entrée est déjà une regex (ex: \bhave\s+to\b) on la garde
        looks_regex = bool(re.search(r"\\b|\\s|\[|\]|\(|\)|\?|\.|\+|\{", s))
        if looks_regex:
            return s
        esc = re.escape(s.strip())
        return rf"\b{esc}\b"

    out = pd.DataFrame({
        "pattern": [to_pattern(x) for x in tmp["_lex"]],
        "class": tmp["class"].values,
        "weight": tmp["_w"].fillna(1.0).astype(float) if "_w" in tmp.columns else 1.0
    })
    out = out.dropna(subset=["pattern"]).drop_duplicates(subset=["pattern","class"])
    return out.reset_index(drop=True)

# ==========
# Corpus (optionnel, pour TF-IDF)
# ==========

def load_corpus_and_features():
    if not _exists(CORPUS_PQ):
        return None
    corpus = pd.read_parquet(CORPUS_PQ)
    feat = pd.read_parquet(FEATURES_PQ) if _exists(FEATURES_PQ) else None
    if feat is None:
        corpus["fc"] = 0.0; corpus["fi"] = 0.0
        return corpus
    cols = ["actor_id","date","url","fc","fi"]
    feat = feat[[c for c in cols if c in feat.columns]]
    merged = corpus.merge(feat, on=["actor_id","date","url"], how="left")
    for c in ["fc","fi"]:
        if c not in merged.columns: merged[c] = 0.0
        merged[c] = merged[c].fillna(0.0)
    return merged

# ==========
# TF-IDF (optionnel)
# ==========

def tfidf_candidates(corpus_df: pd.DataFrame, klass: str, q_hi: float, q_lo: float,
                     max_features=500, min_df=2, min_freq=3, top_n=30):
    """
    Retourne une liste de dicts {pattern,class,weight=1.0, note="tfidf"}
    ou [] si conditions non réunies.
    """
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from scipy.stats import mannwhitneyu
    except Exception:
        print("ℹ️ sklearn indisponible — TF-IDF ignoré")
        return []

    if corpus_df is None or "text" not in corpus_df.columns:
        return []

    if klass not in {"fc","fi"}: return []
    series = corpus_df[klass]
    if series.isna().all():
        return []

    # subsets
    hi = corpus_df.loc[series > series.quantile(q_hi), "text"].tolist()
    lo = corpus_df.loc[series < series.quantile(q_lo), "text"].tolist()
    if len(hi) < 5 or len(lo) < 5:
        print(f"⚠️ échantillon insuffisant pour TF-IDF ({klass})")
        return []

    vect = TfidfVectorizer(max_features=max_features, ngram_range=(1,3),
                           stop_words="english", min_df=min_df)
    X_hi = vect.fit_transform(hi)
    X_lo = vect.transform(lo)
    vocab = vect.get_feature_names_out()

    out = []
    for i, term in enumerate(vocab):
        a = X_hi[:, i].toarray().ravel()
        b = X_lo[:, i].toarray().ravel()
        # fréquence dans hi
        freq = int((a > 0).sum())
        if freq < min_freq: continue
        try:
            from scipy.stats import mannwhitneyu as mwu
            stat, p = mwu(a, b, alternative="greater")
        except Exception:
            continue
        if p < 0.01:
            pat = rf"\b{re.escape(term)}\b"
            out.append({"pattern": pat, "class": klass, "weight": 1.0,
                        "note": f"tfidf(p<{p:.4f},freq={freq})"})
    # trier par “importance” approximative (freq décroissante)
    out.sort(key=lambda d: int(d["note"].split("freq=")[-1].rstrip(")")), reverse=True)
    return out[:top_n]

# ==========
# Patterns contextuels (inclut gestion des négations)
# ==========

def contextual_patterns():
    ctx = []

    # FC (engagement / action)
    fc = [
        (r"\b(?:we\s+)?will\s+(?!not\s)(take|implement|ensure|deliver|enforce)\b", 1.30, "commitment_action"),
        (r"\b(?:we\s+)?must\s+(?!not\s)(invest|protect|strengthen|advance|enforce)\b", 1.40, "imperative_action"),
        (r"\burge\s+(?:my\s+)?colleagues\b", 1.50, "us_congress_specific"),
        (r"\bcannot\s+stand\s+by\b", 1.30, "us_congress_specific"),
        (r"\bpolitical\s+will\b", 1.40, "volition_explicit"),
        (r"\btake\s+action\b", 1.20, "action_explicit"),
        (r"\bmove\s+forward\b", 1.10, "progress_oriented"),
    ]
    # FI (opposition / contrainte)
    fi = [
        (r"\bwill\s+(?!not\s)(harm|undermine|weaken|damage)\b", 1.20, "negative_consequence"),
        (r"\bmust\s+(?!not\s)(prevent|avoid|stop|halt)\b", 1.30, "imperative_prevention"),
        (r"\brise\s+in\s+opposition\b", 1.40, "us_congress_specific"),
        (r"\b(?:serious|grave)\s+concerns?\b", 1.20, "concern_expression"),
        (r"\bfail(?:s|ed|ure)?\s+to\b", 1.10, "failure_attribution"),
    ]
    # Négations -> classe “neutral” (weight 0)
    neg = [
        (r"\bwill\s+not\s+(take|implement|ensure)\b", 0.0, "negation_fc", "neutral"),
        (r"\bmust\s+not\s+(prevent|avoid|stop)\b", 0.0, "negation_fi", "neutral"),
    ]

    for pat, w, note in fc:
        ctx.append({"pattern": pat, "class": "fc", "weight": w, "note": note, "source":"context"})
    for pat, w, note in fi:
        ctx.append({"pattern": pat, "class": "fi", "weight": w, "note": note, "source":"context"})
    for pat, w, note, klass in neg:
        ctx.append({"pattern": pat, "class": klass, "weight": w, "note": note, "source":"negation"})
    return ctx

# ==========
# MAIN
# ==========

def main():
    ap = argparse.ArgumentParser(description="Build lexicon v2 (flexible v1 reader).")
    ap.add_argument("--v1-clean", default=DEF_V1_PATH, help="Chemin v1 clean (lemma/type/...)")
    ap.add_argument("--v1-mapped", default=DEF_V1_MAPPED, help="Chemin v1 mapped (pattern,class)")
    ap.add_argument("--out", default=OUT_V2_PATH, help="Chemin sortie v2")
    ap.add_argument("--changelog", default=CHANGELOG_PATH)
    # TF-IDF options “petit dataset”
    ap.add_argument("--quantile-high", type=float, default=0.60)
    ap.add_argument("--quantile-low",  type=float, default=0.40)
    ap.add_argument("--min-pattern-freq", type=int, default=3)
    ap.add_argument("--similarity-threshold", type=float, default=0.50)  # placeholder si on ajoute ST plus tard
    args = ap.parse_args()

    print("=== Lexicon V2 enhanced (exploratoire) ===")
    # 1) Charger v1 (flex)
    v1 = load_v1_flexible(args.v1_clean, args.v1_mapped)
    print(f"V1: {len(v1)} entrées (fc={ (v1['class']=='fc').sum() } ; fi={ (v1['class']=='fi').sum() })")

    # 2) Corpus
    corpus = load_corpus_and_features()
    if corpus is None:
        print("ℹ️ corpus_final.parquet introuvable — TF-IDF ignoré")

    # 3) TF-IDF (optionnel)
    tf_fc = tfidf_candidates(corpus, "fc", args.quantile_high, args.quantile_low,
                             max_features=500, min_df=2, min_freq=args.min_pattern_freq, top_n=30)
    tf_fi = tfidf_candidates(corpus, "fi", args.quantile_high, args.quantile_low,
                             max_features=500, min_df=2, min_freq=args.min_pattern_freq, top_n=20)
    print(f"TF-IDF: fc={len(tf_fc)}, fi={len(tf_fi)}")

    # 4) Contextuels
    ctx = contextual_patterns()
    print(f"Patterns contextuels: {len(ctx)}")

    # 5) Assembler V2
    rows = []
    # v1
    for _, r in v1.iterrows():
        rows.append({
            "pattern": str(r["pattern"]).strip(),
            "class":   str(r["class"]).strip().lower(),
            "weight":  float(r.get("weight", 1.0)),
            "note":    "from_v1",
            "source":  "v1"
        })
# tfidf
    rows.extend(tf_fc); rows.extend(tf_fi)
    # context
    rows.extend(ctx)

    v2 = pd.DataFrame(rows)
    # normaliser colonnes
    if "class_" in v2.columns and "class" not in v2.columns:
        v2 = v2.rename(columns={"class_":"class"})
    v2["class"] = v2["class"].astype(str).str.lower()
    valid_classes = {"fc","fi","neutral"}
    v2 = v2[v2["class"].isin(valid_classes)]
    v2 = v2.drop_duplicates(subset=["pattern","class"]).reset_index(drop=True)

    # 6) Ecrire
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    v2.to_csv(args.out, index=False, quoting=csv.QUOTE_MINIMAL)

    # 7) Changelog
    os.makedirs(os.path.dirname(args.changelog), exist_ok=True)
    with open(args.changelog, "w", encoding="utf-8") as f:
        f.write(f"# Lexicon v2 enhanced — {datetime.now().isoformat()}\n")
        f.write(f"- v1_clean:  {args.v1_clean}\n")
        f.write(f"- v1_mapped: {args.v1_mapped}\n")
        f.write(f"- out:       {args.out}\n\n")
        f.write(f"## Stats\n")
        f.write(f"- v1 entries: {len(v1)} (fc={(v1['class']=='fc').sum()}, fi={(v1['class']=='fi').sum()})\n")
        f.write(f"- tfidf fc:   {len(tf_fc)}\n")
        f.write(f"- tfidf fi:   {len(tf_fi)}\n")
        f.write(f"- contextual: {len(ctx)}\n")
        f.write(f"- v2 total:   {len(v2)}\n")

    print(f"✓ V2 sauvegardé → {args.out}")
    print(f"✓ Changelog     → {args.changelog}")

if __name__ == "__main__":
    main()


