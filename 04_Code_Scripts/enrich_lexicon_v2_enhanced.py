# 04_Code_Scripts/analysis/enrich_lexicon_v2_enhanced.py
# -*- coding: utf-8 -*-
import os, re, csv, argparse
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from scipy.stats import mannwhitneyu

ROOT = os.getcwd()
V1_PATH = os.path.join("07_Config","lexicons","lexicon_conative_v1.clean.csv")
V2_PATH = os.path.join("07_Config","lexicons","lexicon_conative_v2_enhanced.csv")
CORPUS_PQ = os.path.join("artifacts","real","corpus_final.parquet")
FEATURES_PQ = os.path.join("artifacts","real","features_doc.parquet")
CHANGELOG_PATH = os.path.join("07_Config","lexicons","lexicon_v2_enhanced.changelog.md")

RANDOM_SEED = 42
TFIDF_MAX_FEATURES = 500
TFIDF_MIN_DF = 2
P_VALUE_THRESHOLD = 0.01

def autodetect_csv(path):
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        head = f.read(2048)
    c, s, t = head.count(','), head.count(';'), head.count('\t')
    sep = ','; mx = c
    if s > mx: sep, mx = ';', s
    if t > mx: sep = '\t'
    return sep

def load_v1(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"[ERR] Lexicon v1 introuvable: {path}")
    sep = autodetect_csv(path)
    df = pd.read_csv(path, sep=sep, encoding='utf-8', engine='python')
    # colonnes possibles
    lex_col = next((c for c in ["lemma","term","token","_lex"] if c in df.columns), None)
    cls_col = next((c for c in ["type","class","_class"] if c in df.columns), None)
    w_col   = "weight" if "weight" in df.columns else None
    if not lex_col or not cls_col:
        raise ValueError("[ERR] Colonnes lexicales/class manquantes (attendu: lemma|term + type|class).")
    keep = df[[lex_col, cls_col] + ([w_col] if w_col else [])].copy()
    keep.columns = ["_lex", "_class"] + (["_weight"] if w_col else [])
    if "_weight" not in keep.columns:
        keep["_weight"] = 1.0
    keep["_lex"] = keep["_lex"].astype(str).str.strip()
    keep["_class"] = keep["_class"].astype(str).str.lower().str.strip()
    keep = keep[keep["_class"].isin(["fc","fi"])].dropna(subset=["_lex"]).drop_duplicates()
    return keep

def load_corpus_with_features():
    if not os.path.exists(CORPUS_PQ):
        raise FileNotFoundError(f"[ERR] corpus parquet manquant: {CORPUS_PQ}")
    corpus = pd.read_parquet(CORPUS_PQ)
    if os.path.exists(FEATURES_PQ):
        features = pd.read_parquet(FEATURES_PQ)
        use = ["actor_id","date","url","fc","fi"]
        miss = [c for c in use if c not in features.columns]
        if any(miss):
            features = features[[c for c in use if c in features.columns]]
        merged = corpus.merge(features, on=[c for c in ["actor_id","date","url"] if c in corpus.columns], how="left")
        merged["fc"] = merged.get("fc", pd.Series(0.0, index=merged.index)).fillna(0.0)
        merged["fi"] = merged.get("fi", pd.Series(0.0, index=merged.index)).fillna(0.0)
    else:
        merged = corpus.copy()
        merged["fc"] = 0.0; merged["fi"] = 0.0
    # texte obligatoire
    if "text" not in merged.columns:
        # fallback: 'content' ou 'body'
        alt = next((c for c in ["content","body","raw_text"] if c in merged.columns), None)
        if not alt:
            raise ValueError("[ERR] colonne 'text' absente du corpus (pas de fallback).")
        merged["text"] = merged[alt]
    merged["text"] = merged["text"].fillna("").astype(str)
    return merged

def find_ambiguous_terms(df_v1):
    g = df_v1.groupby("_lex")["_class"].nunique()
    return g[g>1].index.tolist()

def resolve_ambiguities(df_v1, ambiguous_terms):
    # règle simple: priorité à fc si présent
    resolved_notes = []
    for term in ambiguous_terms:
        choices = df_v1[df_v1["_lex"] == term]["_class"].unique().tolist()
        if "fc" in choices:
            df_v1 = df_v1[~((df_v1["_lex"] == term) & (df_v1["_class"] == "fi"))]
            resolved_notes.append(f"{term} -> fc (priority)")
        else:
            df_v1 = df_v1[~((df_v1["_lex"] == term) & (df_v1["_class"] == "fc"))]
            resolved_notes.append(f"{term} -> fi (fallback)")
    return df_v1, resolved_notes

def extract_tfidf_candidates(corpus_df, klass="fc", top_n=50,
                             q_high=0.75, q_low=0.25, min_pattern_freq=5):
    np.random.seed(RANDOM_SEED)
    if klass not in corpus_df.columns:
        return []

    thr_hi = corpus_df[klass].quantile(q_high)
    thr_lo = corpus_df[klass].quantile(q_low)
    high_docs = corpus_df[corpus_df[klass] > thr_hi]["text"].tolist()
    low_docs  = corpus_df[corpus_df[klass] < thr_lo]["text"].tolist()

    if len(high_docs) < 3 or len(low_docs) < 3:
        print(f"⚠️  échantillon insuffisant pour TF-IDF ({klass}) "
              f"(high={len(high_docs)}, low={len(low_docs)})")
        return []

    vec = TfidfVectorizer(max_features=TFIDF_MAX_FEATURES,
                          ngram_range=(1,3),
                          stop_words='english',
                          min_df=TFIDF_MIN_DF)
    tfidf_high = vec.fit_transform(high_docs)
    tfidf_low  = vec.transform(low_docs)
    vocab = vec.get_feature_names_out()

    cands = []
    for i, term in enumerate(vocab):
        sh = tfidf_high[:, i].toarray().ravel()
        sl = tfidf_low[:, i].toarray().ravel()
        try:
            stat, p = mannwhitneyu(sh, sl, alternative='greater')
        except Exception:
            continue
        if p < P_VALUE_THRESHOLD:
            mean_diff = float(sh.mean() - sl.mean())
            freq_high = int((sh > 0).sum())
            if freq_high >= min_pattern_freq:
                cands.append({"pattern": term, "effect_size": mean_diff,
                              "p_value": float(p), "freq_high": freq_high,
                              "class": klass})
    cands = sorted(cands, key=lambda x: x["effect_size"], reverse=True)[:top_n]
    return cands

def validate_semantic_similarity(candidates, existing_terms, threshold=0.5):
    if not candidates:
        return []
    if not existing_terms:
        return candidates
    try:
        from sentence_transformers import SentenceTransformer
        from sklearn.metrics.pairwise import cosine_similarity
    except Exception:
        print("ℹ️ sentence-transformers non dispo — skip validation sémantique")
        return candidates
    model = SentenceTransformer('all-MiniLM-L6-v2')
    cand_txt = [c["pattern"] for c in candidates]
    emb_c = model.encode(cand_txt, convert_to_numpy=True, show_progress_bar=False)
    emb_e = model.encode(existing_terms, convert_to_numpy=True, show_progress_bar=False)
    sim = cosine_similarity(emb_c, emb_e)
    out = []
    for i, c in enumerate(candidates):
        max_sim = float(sim[i].max()) if sim.shape[1] else 0.0
        if max_sim >= threshold:
            c["semantic_similarity"] = max_sim
            out.append(c)
    return out

def add_contextual_patterns():
    rows = []
    # FC (engagement)
    fc = [
        (r"\b(?:we\s+)?will\s+(?!not\s)(take|implement|ensure|deliver|enforce)\b", 1.3, "commitment_action"),
        (r"\b(?:we\s+)?must\s+(?!not\s)(invest|protect|strengthen|advance|enforce)\b", 1.4, "imperative_action"),
        (r"\burge\s+(?:my\s+)?colleagues\b", 1.5, "us_congress_specific"),
        (r"\bcannot\s+stand\s+by\b", 1.3, "us_congress_specific"),
        (r"\bpolitical\s+will\b", 1.4, "volition_explicit"),
        (r"\btake\s+action\b", 1.2, "action_explicit"),
        (r"\bmove\s+forward\b", 1.1, "progress_oriented"),
    ]
    # FI (opposition/contrainte)
    fi = [
        (r"\bwill\s+(?!not\s)(harm|undermine|weaken|damage)\b", 1.2, "negative_consequence"),
        (r"\bmust\s+(?!not\s)(prevent|avoid|stop|halt)\b", 1.3, "imperative_prevention"),
        (r"\brise\s+in\s+opposition\b", 1.4, "us_congress_specific"),
        (r"\b(?:serious|grave)\s+concerns?\b", 1.2, "concern_expression"),
        (r"\bfail(?:s|ed|ure)?\s+to\b", 1.1, "failure_attribution"),
    ]
    # Négations -> neutres
    neg = [
        (r"\bwill\s+not\s+(take|implement|ensure)\b", 0.0, "negation_fc", "neutral"),
        (r"\bmust\s+not\s+(prevent|avoid|stop)\b", 0.0, "negation_fi", "neutral"),
    ]
    for pat,w,note in fc:
        rows.append({"pattern":pat,"kind":"regex","class":"fc","weight":w,"note":note,"source":"contextual"})
    for pat,w,note in fi:
        rows.append({"pattern":pat,"kind":"regex","class":"fi","weight":w,"note":note,"source":"contextual"})
    for pat,w,note,klass in neg:
        rows.append({"pattern":pat,"kind":"regex","class":klass,"weight":w,"note":note,"source":"negation"})
    return rows

def build_v2_lexicon(df_v1, tfidf_fc, tfidf_fi, contextual):
    rows = []
    # v1 -> regex tokens exacts
    for r in df_v1.itertuples(index=False):
        escaped = re.escape(r._lex)
        rows.append({"pattern": rf"\b{escaped}\b", "kind":"regex",
                     "class": r._class, "weight": float(r._weight),
                     "note": "from_v1_token", "source":"v1"})
    for c in tfidf_fc:
        esc = re.escape(c["pattern"])
        rows.append({"pattern": rf"\b{esc}\b", "kind":"regex",
                     "class":"fc","weight":1.0,
                     "note": f"tfidf_datadriven (p={c['p_value']:.4f})","source":"tfidf"})
    for c in tfidf_fi:
        esc = re.escape(c["pattern"])
        rows.append({"pattern": rf"\b{esc}\b", "kind":"regex",
                     "class":"fi","weight":1.0,
                     "note": f"tfidf_datadriven (p={c['p_value']:.4f})","source":"tfidf"})
    rows.extend(contextual)
    df_v2 = pd.DataFrame(rows).drop_duplicates(subset=["pattern","class"])
    return df_v2

def main():
    ap = argparse.ArgumentParser("Enrich lexicon v2 (exploratoire, data-driven + règles)")
    ap.add_argument("--quantile-high", type=float, default=0.75)
    ap.add_argument("--quantile-low",  type=float, default=0.25)
    ap.add_argument("--min-pattern-freq", type=int, default=5)
    ap.add_argument("--similarity-threshold", type=float, default=0.50)
    args = ap.parse_args()

    print("=== Lexicon V2 enhanced (exploratoire) ===")
    v1 = load_v1(V1_PATH)
    print(f"V1: {len(v1)} entrées")

    amb = find_ambiguous_terms(v1)
    if amb:
        v1, notes = resolve_ambiguities(v1, amb)
        print(f"Désambiguïsation fc/fi: {len(amb)} → conservé {len(v1)} termes")

    corpus = load_corpus_with_features()
    print(f"Corpus: {len(corpus)} docs")

    tfidf_fc = extract_tfidf_candidates(
        corpus, "fc", top_n=30,
        q_high=args.quantile_high, q_low=args.quantile_low,
        min_pattern_freq=args.min_pattern_freq
    )
    tfidf_fi = extract_tfidf_candidates(
        corpus, "fi", top_n=20,
        q_high=args.quantile_high, q_low=args.quantile_low,
        min_pattern_freq=args.min_pattern_freq
    )
    print(f"TF-IDF: fc={len(tfidf_fc)}, fi={len(tfidf_fi)}")

    existing_fc = v1[v1["_class"]=="fc"]["_lex"].tolist()
    existing_fi = v1[v1["_class"]=="fi"]["_lex"].tolist()
    tfidf_fc = validate_semantic_similarity(tfidf_fc, existing_fc, args.similarity_threshold)
    tfidf_fi = validate_semantic_similarity(tfidf_fi, existing_fi, args.similarity_threshold)
    print(f"Après validation sémantique: fc={len(tfidf_fc)}, fi={len(tfidf_fi)}")

    contextual = add_contextual_patterns()
    print(f"Patterns contextuels: {len(contextual)}")

    v2 = build_v2_lexicon(v1, tfidf_fc, tfidf_fi, contextual)
    print(f"V2 total: {len(v2)} (fc={len(v2[v2['class']=='fc'])}, fi={len(v2[v2['class']=='fi'])})")

    os.makedirs(os.path.dirname(V2_PATH), exist_ok=True)
    v2.to_csv(V2_PATH, index=False, quoting=csv.QUOTE_MINIMAL)

    os.makedirs(os.path.dirname(CHANGELOG_PATH), exist_ok=True)
    with open(CHANGELOG_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join([
            f"# Lexicon v2 enhanced — saved",
            f"- Input: {V1_PATH}",
            f"- Output: {V2_PATH}",
            f"- V1 terms: {len(v1)}",
            f"- V2 terms: {len(v2)} (Δ={len(v2)-len(v1)})",
            f"- TFIDF_MAX_FEATURES={TFIDF_MAX_FEATURES}, TFIDF_MIN_DF={TFIDF_MIN_DF}",
            f"- q_high={args.quantile_high}, q_low={args.quantile_low}, min_pattern_freq={args.min_pattern_freq}",
            f"- similarity_threshold={args.similarity_threshold}",
        ]))
    print(f"✓ V2 sauvegardé → {V2_PATH}")
    print(f"✓ Changelog     → {CHANGELOG_PATH}")

if __name__ == "__main__":
    main()
