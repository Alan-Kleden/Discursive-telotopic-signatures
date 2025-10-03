#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
run_hypotheses.py — robust & idempotent
Hypothèse H1 : ΔAUC (telotopic vs style-only) + IC95 bootstrap
Hypothèse H3 : LRT (logit) entre modèle style vs style + telotopic
Écrit artifacts/mock/hypotheses.json et imprime le JSON.
"""

from __future__ import annotations
from pathlib import Path
import json
import sys
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score
import statsmodels.api as sm
from scipy.stats import chi2


def _alias_columns(df: pd.DataFrame) -> pd.DataFrame:
    colmap = {}
    # Fc/Fi
    if "fc_mean" not in df.columns and "fc" in df.columns:
        colmap["fc"] = "fc_mean"
    if "fi_mean" not in df.columns and "fi" in df.columns:
        colmap["fi"] = "fi_mean"
    # N_tel
    if "n_tel_mean" not in df.columns and "n_tel" in df.columns:
        colmap["n_tel"] = "n_tel_mean"
    # Style
    if "len_tokens_mean" not in df.columns and "len_tokens" in df.columns:
        colmap["len_tokens"] = "len_tokens_mean"
    # published_at
    if "published_at" not in df.columns and "doc_time" in df.columns:
        colmap["doc_time"] = "published_at"

    if colmap:
        df = df.rename(columns=colmap)
    return df


def _need(cols, df):
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise SystemExit(
            "Missing columns {} in features_win.parquet. "
            "Regenerate windows: .\\tasks.ps1 features:win".format(missing)
        )


def _safe_auc(y_true, y_score):
    y_true = np.asarray(y_true)
    y_score = np.asarray(y_score)
    if np.unique(y_true).size < 2:
        return float("nan")
    try:
        return float(roc_auc_score(y_true, y_score))
    except Exception:
        return float("nan")


def _bootstrap_ci_delta_auc(y, s_tel, s_style, n_boot=400, seed=42):
    rng = np.random.default_rng(seed)
    deltas = []
    n = len(y)
    idx = np.arange(n)
    for _ in range(n_boot):
        b = rng.choice(idx, size=n, replace=True)
        yb = y[b]
        dt = _safe_auc(yb, s_tel[b]) - _safe_auc(yb, s_style[b])
        deltas.append(dt)
    lo, hi = np.nanpercentile(deltas, [2.5, 97.5])
    return float(lo), float(hi)


def main():
    win_path = Path("artifacts/mock/features_win.parquet")
    if not win_path.exists():
        raise SystemExit("Need artifacts/mock/features_win.parquet — run features first.")

    df = pd.read_parquet(win_path)
    df = _alias_columns(df)

    # Colonnes minimales
    _need(["fc_mean", "fi_mean"], df)

    # Étiquette "stance"
    df = df.assign(stance=(df["fc_mean"] >= df["fi_mean"]).astype(int))

    # Telotopic score (n_tel_mean ou fallback fc-fi)
    if "n_tel_mean" in df.columns:
        s_tel = df["n_tel_mean"].fillna(0.0).to_numpy(dtype=float)
    else:
        s_tel = (df["fc_mean"] - df["fi_mean"]).fillna(0.0).to_numpy(dtype=float)

    # Style score (len_tokens_mean normalisé)
    if "len_tokens_mean" in df.columns:
        lt = df["len_tokens_mean"].fillna(df["len_tokens_mean"].median()).to_numpy(dtype=float)
        s_style = (lt - lt.min()) / (lt.max() - lt.min() + 1e-9)
    else:
        s_style = np.zeros(len(df), dtype=float)

    y = df["stance"].to_numpy(dtype=int)

    # H1: ΔAUC + IC95 bootstrap
    auc_tel = _safe_auc(y, s_tel)
    auc_style = _safe_auc(y, s_style)
    delta_auc = float(auc_tel - auc_style)
    ci_lo, ci_hi = _bootstrap_ci_delta_auc(y, s_tel, s_style, n_boot=400, seed=42)

    # H3: LRT (logit) — style vs style + telotopic
    # X1 = style only
    X1 = sm.add_constant(pd.DataFrame({"style": s_style}))
    # X2 = style + telotopic
    X2 = sm.add_constant(pd.DataFrame({"style": s_style, "tel": s_tel}))

    # GLM Binomial (logit); on force une convergence robuste
    try:
        m1 = sm.GLM(y, X1, family=sm.families.Binomial()).fit(maxiter=100, disp=0)
        m2 = sm.GLM(y, X2, family=sm.families.Binomial()).fit(maxiter=100, disp=0)
        ll1 = float(m1.llf)
        ll2 = float(m2.llf)
        lrt_stat = 2.0 * (ll2 - ll1)
        lrt_p = float(chi2.sf(lrt_stat, df=1))
    except Exception:
        # Si séparation parfaite ou hic numérique : renvoie stat/p NaN
        lrt_stat, lrt_p = float("nan"), float("nan")

    out = {
        "H1_delta_auc_telotopic_minus_style": delta_auc,
        "H1_delta_auc_ci95": [ci_lo, ci_hi],
        "H3_lrt_stat": lrt_stat,
        "H3_lrt_p": lrt_p,
    }

    out_dir = Path("artifacts/mock")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "hypotheses.json"
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    try:
        main()
    except SystemExit as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)
