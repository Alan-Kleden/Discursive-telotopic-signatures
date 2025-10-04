# 04_Code_Scripts/features/fc_fi_v3.py
from __future__ import annotations
import os
from typing import Optional, Dict, Tuple
import pandas as pd

# spaCy is required in v3
import spacy

from features.conative import (
    load_conative_lexicon,
    conative_from_text,
)

# λ (cross-term) fixed a priori per Appendix A4 clarification
_LAMBDA = 0.5

def _need_langs_from_df(df: pd.DataFrame, lang_col: Optional[str]) -> set[str]:
    if lang_col is None or lang_col not in df.columns:
        return {"FR"}  # default
    vals = set(str(x).upper() for x in df[lang_col].dropna().unique().tolist())
    keep = set()
    for v in vals:
        if v in {"FR", "FRENCH"}:
            keep.add("FR")
        elif v in {"EN", "ENGLISH"}:
            keep.add("EN")
    if not keep:
        keep = {"FR"}
    return keep

def _load_spacy_models(langs: set[str]) -> Dict[str, "spacy.Language"]:
    models: Dict[str, "spacy.Language"] = {}
    if "FR" in langs:
        try:
            models["FR"] = spacy.load("fr_core_news_lg")
        except Exception as e:
            raise RuntimeError("spaCy FR model 'fr_core_news_lg' not available") from e
    if "EN" in langs:
        try:
            models["EN"] = spacy.load("en_core_web_lg")
        except Exception as e:
            raise RuntimeError("spaCy EN model 'en_core_web_lg' not available") from e
    return models

def _resolve_alignment(row: pd.Series, alignment_col: Optional[str]) -> float:
    """
    Alignment a(d,T) ∈ [0,1]. If not provided, return neutral 0.5.
    """
    if alignment_col and alignment_col in row and pd.notna(row[alignment_col]):
        try:
            a = float(row[alignment_col])
            if a < 0.0: a = 0.0
            if a > 1.0: a = 1.0
            return a
        except Exception:
            pass
    return 0.5

def _compute_fc_fi_beta(text: str,
                        lang: str,
                        nlp_map: Dict[str, "spacy.Language"],
                        lexicon: Dict[str, Dict[str, float]],
                        alignment: float) -> Tuple[float, float, float]:
    lang = "FR" if str(lang).upper() in {"", "NONE", "NAN"} else str(lang).upper()
    if lang not in nlp_map:
        # fallback to FR if unknown label appears (row-level tolerant)
        lang = "FR"
    nlp = nlp_map[lang]

    push, inh, _dbg = conative_from_text(text, lang, nlp, lexicon)  # already in [0,1] after clipping
    # A4 clarification (λ=0.5 fixed):
    # Fc = p*a + λ*h*(1-a)
    # Fi = h*a + λ*p*(1-a)
    fc = push * alignment + _LAMBDA * inh * (1.0 - alignment)
    fi = inh  * alignment + _LAMBDA * push * (1.0 - alignment)

    # β = ( (Fc - Fi) + 1 ) / 2 ∈ [0,1]
    beta = ((fc - fi) + 1.0) / 2.0
    if beta < 0.0: beta = 0.0
    if beta > 1.0: beta = 1.0
    return float(fc), float(fi), float(beta)

def apply_fc_fi_v3(df: pd.DataFrame,
                   text_col: str = "text",
                   lang_col: Optional[str] = None,
                   alignment_col: Optional[str] = None,
                   lexicon_path: Optional[str] = None) -> pd.DataFrame:
    """
    Compute Fc, Fi, beta (A4 clarification with λ=0.5) for each row of df.

    Parameters
    ----------
    df : DataFrame
        Must contain at least `text_col`. If `lang_col` is provided, values should be 'FR' or 'EN'.
    text_col : str
        Column with raw text.
    lang_col : Optional[str]
        Optional column with language code per row (FR/EN). If None or missing, defaults to FR.
    alignment_col : Optional[str]
        Optional column with alignment a(d,T) in [0,1]. If None or missing, defaults to 0.5 (neutral).
    lexicon_path : Optional[str]
        Path to csv lexicon. If None, read from env CONATIVE_LEXICON_PATH or
        default '01_Protocoles/lexicon_conative_v1.csv'.

    Returns
    -------
    DataFrame
        df with added columns: 'fc', 'fi', 'beta'. It preserves other columns.
    """
    if text_col not in df.columns:
        raise ValueError(f"[fc_fi_v3] text_col '{text_col}' is missing in df")

    # Resolve lexicon path
    lex_path = (
        lexicon_path
        or os.environ.get("CONATIVE_LEXICON_PATH")
        or "01_Protocoles/lexicon_conative_v1.csv"
    )
    if not os.path.exists(lex_path):
        raise FileNotFoundError(f"[fc_fi_v3] conative lexicon not found at '{lex_path}'")
    lexicon = load_conative_lexicon(lex_path)  # fail-fast if malformed

    # Load spaCy models for needed langs (fail-fast on missing models)
    langs_needed = _need_langs_from_df(df, lang_col)
    nlp_map = _load_spacy_models(langs_needed)

    # Compute per row (row-level tolerant)
    out_fc, out_fi, out_beta = [], [], []
    for _, row in df.iterrows():
        txt = str(row[text_col]) if pd.notna(row[text_col]) else ""
        lang = str(row[lang_col]).upper() if (lang_col and lang_col in row and pd.notna(row[lang_col])) else "FR"
        a = _resolve_alignment(row, alignment_col)
        try:
            fc, fi, beta = _compute_fc_fi_beta(txt, lang, nlp_map, lexicon, a)
        except Exception:
            # tolerate the row, mark zeros (and continue the batch)
            fc, fi, beta = 0.0, 0.0, 0.5
        out_fc.append(fc); out_fi.append(fi); out_beta.append(beta)

    out = df.copy()
    out["fc"] = out_fc
    out["fi"] = out_fi
    out["beta"] = out_beta
    return out

def _precheck_or_fail() -> None:
    """
    Quick fail-fast check for CI / shell sanity:
      - lexicon file present & well-formed
      - spaCy FR/EN models load
    """
    lex_path = (
        os.environ.get("CONATIVE_LEXICON_PATH")
        or "01_Protocoles/lexicon_conative_v1.csv"
    )
    if not os.path.exists(lex_path):
        raise FileNotFoundError(f"[fc_fi_v3 precheck] missing lexicon at '{lex_path}'")
    load_conative_lexicon(lex_path)
    # Load both to fail-fast if pipeline will need EN later
    try:
        _ = spacy.load("fr_core_news_lg")
    except Exception as e:
        raise RuntimeError("Missing spaCy FR model 'fr_core_news_lg'") from e
    try:
        _ = spacy.load("en_core_web_lg")
    except Exception as e:
        raise RuntimeError("Missing spaCy EN model 'en_core_web_lg'") from e
