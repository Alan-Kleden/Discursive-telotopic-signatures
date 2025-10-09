# 04_Code_Scripts/features/windows.py
from __future__ import annotations
import pandas as pd
import numpy as np

def _pick_timestamp_column(df: pd.DataFrame) -> str:
    """
    Choisit la colonne temporelle à utiliser.
    Priorité : 'published_at' -> 'date' -> 'created_at' -> 'timestamp'.
    """
    for c in ["published_at", "date", "created_at", "timestamp"]:
        if c in df.columns:
            return c
    raise SystemExit(
        "No timestamp column found. Expected one of: "
        "'published_at', 'date', 'created_at', 'timestamp'."
    )

def sliding_windows(df: pd.DataFrame, window_days: int = 30, step_days: int = 7) -> pd.DataFrame:
    """
    Agrège par fenêtres glissantes (par actor_id, domain_id).
    Colonnes attendues au minimum :
      - actor_id, domain_id
      - une colonne temporelle parmi: published_at/date/created_at/timestamp
    Colonnes optionnelles :
      - fc, fi, n_tel, ambivalence_flag
    Sort :
      - fc_mean, fi_mean, n_tel_mean, ambiv_rate, n_docs, win_start, win_end
    """
    if df.empty:
        return pd.DataFrame()

    out = df.copy()

    # Déterminer la colonne date
    ts_col = _pick_timestamp_column(out)
    out["__ts__"] = pd.to_datetime(out[ts_col], errors="coerce")

    # Colonnes optionnelles -> créées si absentes
    for col in ["fc", "fi", "n_tel"]:
        if col not in out.columns:
            out[col] = np.nan
    if "ambivalence_flag" not in out.columns:
        out["ambivalence_flag"] = np.nan

    # Sanity sur clés de groupby
    for key in ["actor_id", "domain_id"]:
        if key not in out.columns:
            raise SystemExit(f"Missing required column '{key}' in features_doc.parquet")

    records = []
    for (actor, domain), grp in out.groupby(["actor_id", "domain_id"], dropna=False):
        g = grp.sort_values("__ts__").reset_index(drop=True)
        if g.empty or g["__ts__"].isna().all():
            continue

        tmin = g["__ts__"].min().normalize()
        tmax = g["__ts__"].max().normalize()

        win_len = pd.Timedelta(days=window_days)
        step = pd.Timedelta(days=step_days)
        cur = tmin

        while cur <= tmax:
            win_start = cur
            win_end = cur + win_len
            mask = (g["__ts__"] >= win_start) & (g["__ts__"] < win_end)
            win = g.loc[mask]
            n_docs = int(mask.sum())

            if n_docs > 0:
                fc_mean    = float(win["fc"].mean())
                fi_mean    = float(win["fi"].mean())
                n_tel_mean = float(win["n_tel"].mean())
                ambiv_rate = float(win["ambivalence_flag"].mean())
            else:
                fc_mean = fi_mean = n_tel_mean = ambiv_rate = np.nan

            records.append({
                "actor_id": actor,
                "domain_id": domain,
                "win_start": win_start,
                "win_end":   win_end,
                "n_docs":    n_docs,
                "fc_mean":   fc_mean,
                "fi_mean":   fi_mean,
                "n_tel_mean": n_tel_mean,
                "ambiv_rate": ambiv_rate,
            })
            cur = cur + step

    win_df = pd.DataFrame.from_records(records)
    if not win_df.empty:
        win_df = win_df.sort_values(["actor_id","domain_id","win_start"]).reset_index(drop=True)
    return win_df

