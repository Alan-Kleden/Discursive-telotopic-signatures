# hypotheses.py — H1 (ΔAUC + CI) et H3 (LRT sur fenêtres)
from __future__ import annotations
import numpy as np, pandas as pd
from sklearn.metrics import roc_auc_score
from scipy.stats import chi2

def bootstrap_ci_delta(y_true, s1, s2, n_resamples=2000, seed=1337):
    """BCa simplifié -> ici percentile pour vitesse."""
    rng = np.random.default_rng(seed)
    n = len(y_true)
    deltas = []
    for _ in range(n_resamples):
        idx = rng.integers(0, n, size=n)
        y = y_true[idx]; a1 = s1[idx]; a2 = s2[idx]
        if len(np.unique(y)) < 2: 
            continue
        deltas.append(roc_auc_score(y, a1) - roc_auc_score(y, a2))
    if not deltas:
        return np.nan, (np.nan, np.nan)
    deltas = np.array(deltas)
    lo, hi = np.percentile(deltas, [2.5, 97.5])
    return float(np.mean(deltas)), (float(lo), float(hi))

def lrt_from_ll(ll_base, ll_full, df_added):
    stat = -2.0 * (ll_base - ll_full)
    p = float(chi2.sf(stat, df=df_added))
    return float(stat), p
