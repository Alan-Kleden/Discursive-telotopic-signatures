# n_tel.py — cohérence pondérée + flag ambivalence
from __future__ import annotations
import numpy as np
import pandas as pd

# poids figés (pré-enregistrement)
ALPHA, BETA, GAMMA, DELTA, EPSILON = 0.30, 0.20, 0.25, 0.15, 0.10

def compute_ambivalence_flag(fc: float, fi: float, thr: float = 0.4) -> int:
    return int((fc >= thr) and (fi >= thr))

def compute_doclen_norm(n_tokens: int, cap: int = 200) -> float:
    return float(min(max(n_tokens, 0), cap) / cap)

def compute_n_tel_row(fc: float, fi: float, cos_t: float, ambiv: int, n_tokens: int) -> float:
    dl = compute_doclen_norm(n_tokens)
    # cohérence: favoriser Fc, pénaliser Fi & ambivalence, renforcer cosθ
    score = (ALPHA * fc) + (BETA * (1.0 - fi)) + (GAMMA * abs(cos_t)) + (DELTA * (1 - ambiv)) + (EPSILON * dl)
    return float(np.clip(score, 0.0, 1.0))

def apply_n_tel(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    amb = [compute_ambivalence_flag(f, i) for f,i in zip(out["fc_mean"], out["fi_mean"])]
    out["ambivalence_flag"] = amb
    out["n_tel"] = [compute_n_tel_row(f, i, c, a, n) for f,i,c,a,n in zip(out["fc_mean"], out["fi_mean"], out["cos_theta"], out["ambivalence_flag"], out["len_tokens"])]
    return out
