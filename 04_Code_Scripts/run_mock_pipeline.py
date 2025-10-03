# 04_Code_Scripts/run_mock_pipeline.py
from __future__ import annotations
import pandas as pd
import numpy as np
from pathlib import Path

from features.theta import add_theta_features
from features.fc_fi_v3 import apply_fc_fi_v3

IN_PATH  = Path("data/mock/docs.parquet")
OUT_PATH = Path("artifacts/mock/features_doc.parquet")

def _ensure_timestamp(df: pd.DataFrame) -> pd.DataFrame:
    """S’assure qu’au moins une colonne temporelle standard est présente."""
    if any(c in df.columns for c in ["published_at", "date", "created_at", "timestamp"]):
        return df
    # Essai de récupération si un nom exotique existe (fallback très conservateur)
    # Sinon on abandonne proprement avec un message clair.
    raise SystemExit(
        "Input docs have no timestamp column. Expected one of: "
        "'published_at', 'date', 'created_at', 'timestamp'. "
        "Fix mock_data or map your column to one of these names."
    )

def main():
    if not IN_PATH.exists():
        raise SystemExit("Run mock generator first: .\\tasks.ps1 mock:gen")

    # On garde un backup pour ne pas perdre de colonnes si une fonction renvoie un sous-ensemble
    orig = pd.read_parquet(IN_PATH)
    orig = _ensure_timestamp(orig)

    # 1) alignement si absent
    df = add_theta_features(orig.copy(), cos_col="cos_theta", align_col="alignment")

    # 2) Fc/Fi v3 -> ajoute fc, fi, beta_modality sans supprimer les autres colonnes
    res = apply_fc_fi_v3(df, text_col="text", align_col="alignment")
    # Si apply_fc_fi_v3 a renvoyé un DataFrame réduit, on réinjecte proprement
    for col in ["fc", "fi", "beta_modality"]:
        if col in res.columns and col not in df.columns:
            df[col] = res[col]

    # 3) n_tel minimal (placeholder borné)
    df["n_tel"] = df["beta_modality"].astype(float).clip(0.0, 1.0)

    # 4) ambivalence_flag si absent (par défaut: 0)
    if "ambivalence_flag" not in df.columns:
        df["ambivalence_flag"] = 0

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUT_PATH, index=False)
    print("OK: artifacts/mock/features_doc.parquet (mode=v2+v3)")

if __name__ == "__main__":
    main()
