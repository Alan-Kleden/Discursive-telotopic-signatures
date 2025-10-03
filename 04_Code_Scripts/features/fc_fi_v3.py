# 04_Code_Scripts/features/fc_fi_v3.py
from __future__ import annotations
import numpy as np
import pandas as pd
import re as _re_std
from .theta import add_theta_features

# --- try 'regex' (supports \p{L}); fallback to std 're' with Latin-extended class ---
try:
    import regex as _rx
    WORD_RE = _rx.compile(r"\p{L}+", flags=_rx.UNICODE)
except Exception:
    WORD_RE = _re_std.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ]+", flags=_re_std.UNICODE)

# --- fixed cross-term (preregistered) ---
LAMBDA = 0.5  # λ fixed a priori

# Minimal conative lexicon
PUSH = {
    "devoir": 0.9, "falloir": 0.85, "exiger": 0.85,
    "accélérer": 0.7, "renforcer": 0.6, "agir": 0.6,
    "imposer": 0.7, "décider": 0.6, "mettre_en_oeuvre": 0.65,
}
INHIBIT = {
    "empêcher": 0.9, "bloquer": 0.85, "s_opposer": 0.8,
    "refuser": 0.75, "ralentir": 0.6, "suspendre": 0.7,
    "abroger": 0.7,
}
AMP_WORDS = {"très": 0.15, "absolument": 0.2, "immédiatement": 0.1}

def _tokens(text: str) -> list[str]:
    if not isinstance(text, str) or not text:
        return []
    txt = text.replace(" ", "_")
    return [m.group(0).lower() for m in WORD_RE.finditer(txt)]

def _score_conation(text: str) -> tuple[float, float]:
    toks = _tokens(text)
    push = 0.0
    inh  = 0.0
    for t in toks:
        if t in PUSH:
            push += PUSH[t]
        if t in INHIBIT:
            inh += INHIBIT[t]
    amp = sum(AMP_WORDS.get(t, 0.0) for t in toks)
    push += amp
    inh  += amp
    return push, inh

def _p90_norm(x: pd.Series) -> pd.Series:
    if len(x) == 0:
        return x.astype(float)
    vals = x.astype(float).to_numpy()
    finite = vals[np.isfinite(vals)]
    p = np.nanpercentile(finite, 90) if finite.size else 1.0
    if p <= 1e-12:
        return pd.Series(0.0, index=x.index, dtype=float)
    return (x.astype(float) / p).clip(0.0, 1.0)

def apply_fc_fi_v3(df: pd.DataFrame,
                   text_col: str = "text",
                   align_col: str = "alignment") -> pd.DataFrame:
    """
    Compute fc/fi with λ cross term and derive beta_modality in [0,1].
    Ensures an 'alignment' column exists (via add_theta_features if needed).
    """
    out = df.copy()

    if align_col not in out.columns:
        out = add_theta_features(out, cos_col="cos_theta", align_col=align_col)

    tmp = out[text_col].apply(_score_conation)
    out["_push_raw"] = tmp.apply(lambda t: t[0]).astype(float)
    out["_inh_raw"]  = tmp.apply(lambda t: t[1]).astype(float)

    out["push"] = _p90_norm(out["_push_raw"])
    out["inh"]  = _p90_norm(out["_inh_raw"])

    a = out[align_col].astype(float).clip(0.0, 1.0)
    p = out["push"]
    h = out["inh"]

    # lowercase outputs expected downstream
    out["fc"] = (p * a) + (LAMBDA * h * (1.0 - a))
    out["fi"] = (h * a) + (LAMBDA * p * (1.0 - a))

    M = (out["fc"] - out["fi"]).clip(-1.0, 1.0)
    out["beta_modality"] = ((M + 1.0) / 2.0).clip(0.0, 1.0)

    out.drop(columns=["_push_raw", "_inh_raw"], inplace=True, errors="ignore")
    return out
