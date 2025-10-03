#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
run_baselines.py — robust & idempotent
Lit artifacts/mock/features_win.parquet, fabrique une étiquette binaire
"stance" (fc_mean >= fi_mean), calcule 3 AUC baselines et écrit
artifacts/mock/scores_baselines.json.
"""

from __future__ import annotations
from pathlib import Path
import json
import sys
import numpy as np
import pandas as pd

# sklearn est déjà listé dans l'env
from sklearn.metrics import roc_auc_score


def _alias_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Tolère les variantes de noms de colonnes entre versions."""
    colmap = {}

    # Fc / Fi (fenêtres)
    if "fc_mean" not in df.columns and "fc" in df.columns:
        colmap["fc"] = "fc_mean"
    if "fi_mean" not in df.columns and "fi" in df.columns:
        colmap["fi"] = "fi_mean"

    # N_tel (fenêtres)
    if "n_tel_mean" not in df.columns and "n_tel" in df.columns:
        colmap["n_tel"] = "n_tel_mean"

    # Longueur/style (fenêtres)
    if "len_tokens_mean" not in df.columns and "len_tokens" in df.columns:
        colmap["len_tokens"] = "len_tokens_mean"

    # published_at (fenêtres)
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
    """AUC robuste : renvoie NaN si uniquement une classe présente."""
    y_true = np.asarray(y_true)
    y_score = np.asarray(y_score)
    # Besoin d'au moins 2 classes différentes
    if np.unique(y_true).size < 2:
        return float("nan")
    try:
        return float(roc_auc_score(y_true, y_score))
    except Exception:
        return float("nan")


def main():
    win_path = Path("artifacts/mock/features_win.parquet")
    if not win_path.exists():
        raise SystemExit("Need artifacts/mock/features_win.parquet — run features first.")

    df = pd.read_parquet(win_path)
    df = _alias_columns(df)

    # Colonnes minimales nécessaires
    _need(["actor_id", "domain_id"], df)

    # Fc / Fi obligatoires pour construire stance
    _need(["fc_mean", "fi_mean"], df)

    # Construire l'étiquette binaire "stance"
    df = df.assign(stance=(df["fc_mean"] >= df["fi_mean"]).astype(int))

    # Scores baselines :
    # 1) Telotopic linear (n_tel_mean)
    if "n_tel_mean" not in df.columns:
        # tolérance : si vraiment absent, fallback minimal = fc_mean - fi_mean
        telotopic_score = (df["fc_mean"] - df["fi_mean"]).fillna(0.0)
    else:
        telotopic_score = df["n_tel_mean"].fillna(0.0)

    # 2) Style only (len_tokens_mean normalisé)
    if "len_tokens_mean" in df.columns:
        lt = df["len_tokens_mean"].fillna(df["len_tokens_mean"].median())
        style_score = (lt - lt.min()) / (lt.max() - lt.min() + 1e-9)
    else:
        # fallback neutre si colonne manquante
        style_score = pd.Series(np.zeros(len(df)), index=df.index)

    # 3) Party-line baseline : proba = moyenne de stance par acteur (leave-in)
    actor_mean = df.groupby("actor_id")["stance"].transform("mean")
    party_line_score = actor_mean.fillna(actor_mean.mean()).astype(float)

    # AUCs
    y = df["stance"].astype(int)
    out = {
        "AUC_telotopic_linear": _safe_auc(y, telotopic_score),
        "AUC_style_only": _safe_auc(y, style_score),
        "AUC_party_line": _safe_auc(y, party_line_score),
    }

    out_dir = Path("artifacts/mock")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "scores_baselines.json"
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"Wrote {out_path.as_posix()}")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    try:
        main()
    except SystemExit as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)
