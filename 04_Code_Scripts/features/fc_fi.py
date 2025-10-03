from __future__ import annotations
import re
from typing import Dict, List, Optional
import pandas as pd

__all__ = [
    "apply_fc_fi",        # wrapper rétro-compatible (défaut v1)
    "apply_fc_fi_v1",     # version simple/rapide
    "apply_fc_fi_v2",     # version spaCy + TF-IDF léger
]

# =============== v1 : simple, rapide (baseline actuelle) ===============

def apply_fc_fi_v1(
    docs: pd.DataFrame,
    lexicon: Dict[str, Dict[str, List[str]]],
    text_col: str = "text",
) -> pd.DataFrame:
    r"""
    Fc/Fi v1 : comptage lexique naïf (tokens bruts en minuscules).
    - fc_mean : ratio d'occurrences pro / total tokens
    - fi_mean : ratio d'occurrences anti / total tokens
    - ambivalence_flag : |fc - fi| < 0.1
    - len_tokens : nb de tokens simples (\w+)   <-- docstring en "raw" pour éviter le warning
    """
    df = docs.copy()
    tok_re = re.compile(r"\w+", flags=re.UNICODE)

    # Prépare sets pro/anti (tous teloi confondus)
    pro = set()
    anti = set()
    for _, sides in lexicon.items():
        pro.update((w or "").lower() for w in sides.get("pro", []))
        anti.update((w or "").lower() for w in sides.get("anti", []))

    fc_vals, fi_vals, lengths = [], [], []
    for t in df[text_col].astype(str):
        toks = [w.lower() for w in tok_re.findall(t)]
        L = max(1, len(toks))
        pro_hits = sum(1 for w in toks if w in pro)
        anti_hits = sum(1 for w in toks if w in anti)
        fc_vals.append(pro_hits / L)
        fi_vals.append(anti_hits / L)
        lengths.append(len(toks))

    df["fc_mean"] = pd.Series(fc_vals).clip(0, 1)
    df["fi_mean"] = pd.Series(fi_vals).clip(0, 1)
    df["len_tokens"] = pd.Series(lengths).astype(int)
    df["ambivalence_flag"] = (df["fc_mean"] - df["fi_mean"]).abs().lt(0.1).astype(int)
    df["fcfi_version"] = "v1"
    return df


# =============== v2 : spaCy lemmatisation + TF-IDF léger ===============

def apply_fc_fi_v2(
    docs: pd.DataFrame,
    lexicon: Dict[str, Dict[str, List[str]]],
    lang_col: str = "language",
    text_col: str = "text",
) -> pd.DataFrame:
    """
    Fc/Fi v2 : lemmatisation spaCy (FR/EN), stopwords out, pondération TF-IDF (idf par domaine).
    - Requiert fr_core_news_lg & en_core_web_lg installés.
    - lexicon donné en surface -> on le passe en minuscules (approx simple).
    """
    import spacy  # import local pour éviter de charger spaCy quand v1 suffit
    nlp_fr = spacy.load("fr_core_news_lg", disable=["ner", "parser"])
    nlp_en = spacy.load("en_core_web_lg", disable=["ner", "parser"])

    def norm_lemmas(text: str, lang: str) -> list[str]:
        nlp = nlp_fr if str(lang).lower().startswith("fr") else nlp_en
        doc = nlp(text or "")
        return [t.lemma_.lower() for t in doc if t.is_alpha and not t.is_stop]

    # Lexique vers minuscules (proxy “lemmatisation lexique”)
    LEX = {}
    for tel, sides in lexicon.items():
        LEX[tel] = {}
        for side, words in sides.items():
            LEX[tel][side] = list({(w or "").lower() for w in words})

    df = docs.copy()
    df["_lemmas"] = [norm_lemmas(t, l) for t, l in zip(df[text_col], df.get(lang_col, "fr"))]

    # IDF lissé par domaine
    from collections import Counter, defaultdict
    import math

    idf = {}
    for dom, sub in df.groupby("domain_id"):
        dfreq = Counter()
        for lemmas in sub["_lemmas"]:
            for w in set(lemmas):
                dfreq[w] += 1
        N = max(1, len(sub))
        dmap = defaultdict(float)
        for w, dfw in dfreq.items():
            dmap[w] = math.log((N + 1) / (dfw + 1)) + 1.0
        idf[dom] = dmap

    fc_vals, fi_vals, lengths = [], [], []
    for (_, row) in df.iterrows():
        lemmas = row["_lemmas"]
        dom = row["domain_id"]
        weights = [idf.get(dom, {}).get(w, 0.0) for w in lemmas]
        totw = sum(weights) or 1.0

        pro_hits = 0.0
        anti_hits = 0.0
        for _, sides in LEX.items():
            pro_set = set(sides.get("pro", []))
            anti_set = set(sides.get("anti", []))
            for w, w_idf in zip(lemmas, weights):
                if w in pro_set:
                    pro_hits += w_idf
                if w in anti_set:
                    anti_hits += w_idf

        fc_vals.append(pro_hits / totw)
        fi_vals.append(anti_hits / totw)
        lengths.append(len(lemmas))

    df["fc_mean"] = pd.Series(fc_vals).clip(0, 1)
    df["fi_mean"] = pd.Series(fi_vals).clip(0, 1)
    df["len_tokens"] = pd.Series(lengths).astype(int)
    df["ambivalence_flag"] = (df["fc_mean"] - df["fi_mean"]).abs().lt(0.1).astype(int)
    df["fcfi_version"] = "v2"
    return df.drop(columns=["_lemmas"], errors="ignore")


# =============== wrapper rétro-compatible ===============

def apply_fc_fi(
    docs: pd.DataFrame,
    lexicon: Dict[str, Dict[str, List[str]]],
    *,
    mode: str = "v1",
    lang_col: str = "language",
    text_col: str = "text",
) -> pd.DataFrame:
    """
    Wrapper rétro-compatible :
    - mode="v1" (défaut) -> apply_fc_fi_v1
    - mode="v2" -> apply_fc_fi_v2 (spaCy + TF-IDF)
    Les colonnes de sortie restent : fc_mean, fi_mean, len_tokens, ambivalence_flag, fcfi_version.
    """
    m = (mode or "v1").lower()
    if m == "v2":
        return apply_fc_fi_v2(docs, lexicon, lang_col=lang_col, text_col=text_col)
    return apply_fc_fi_v1(docs, lexicon, text_col=text_col)
