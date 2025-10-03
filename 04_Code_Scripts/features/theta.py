# 04_Code_Scripts/features/theta.py
from __future__ import annotations
import numpy as np
import pandas as pd

def _remap_01(x: pd.Series | np.ndarray) -> pd.Series:
    # remap from [-1,1] -> [0,1]
    return (x + 1.0) / 2.0

def add_theta_features(df: pd.DataFrame,
                       cos_col: str = "cos_theta",
                       align_col: str = "alignment") -> pd.DataFrame:
    """
    Ensure an 'alignment' scalar in [0,1] is present, derived from cos_theta if available.
    Falls back to a weak proxy if cos_theta is absent (safe for mock/v2).

    Inputs:
      - df must contain at least a document-level row; if 'cos_theta' exists in [-1,1],
        alignment := (cos_theta + 1)/2 ; else use a neutral default 0.5.

    Returns:
      df with ensured column `alignment` in [0,1].
    """
    out = df.copy()
    if cos_col in out.columns:
        # Robust clipping then remap
        out[cos_col] = out[cos_col].astype(float).clip(-1.0, 1.0)
        out[align_col] = _remap_01(out[cos_col])
    else:
        # Neutral fallback (keeps pipeline running on mock if cos_theta not produced yet)
        out[align_col] = 0.5

    # Safety: clip
    out[align_col] = out[align_col].astype(float).clip(0.0, 1.0)
    return out
