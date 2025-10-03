from __future__ import annotations
import pandas as pd
from typing import Iterable


def load_shocks(path: str = "data/mock/shocks.csv") -> pd.DataFrame:
    """Charge le CSV de chocs (doit contenir au minimum: domain_id, date, shock_id)."""
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"])
    return df


def tag_windows_with_shocks(
    win_df: pd.DataFrame,
    shocks_df: pd.DataFrame,
    lags: Iterable[int] = (0, 7, 14),
) -> pd.DataFrame:
    """
    Aligne les chocs sur les fenêtres, avec décalages (lags) en jours.

    Pour chaque lag L, crée:
      - n_shocks_lag{L} : nb de chocs dont la date ∈ [win_start+L, win_end+L]
      - has_shock_lag{L} : 1 si n_shocks_lag{L} > 0, sinon 0

    Conserve win_start / win_end en STRING (compat sliding_windows), utilise
    des colonnes datetime temporaires pour les comparaisons.
    """
    base = win_df.copy()
    base["_ws_dt"] = pd.to_datetime(base["win_start"])
    base["_we_dt"] = pd.to_datetime(base["win_end"])

    shocks = shocks_df.copy()
    shocks["date"] = pd.to_datetime(shocks["date"])

    out = base.copy()

    for L in lags:
        # Fenêtres décalées (datetime)
        ws = base["_ws_dt"] + pd.to_timedelta(L, unit="D")
        we = base["_we_dt"] + pd.to_timedelta(L, unit="D")

        tmp = base[["actor_id", "domain_id", "win_start", "win_end"]].copy()
        tmp["_ws_dt"] = ws
        tmp["_we_dt"] = we

        merged = tmp.merge(
            shocks[["domain_id", "date", "shock_id"]],
            on="domain_id",
            how="left",
        )
        hit = (merged["date"] >= merged["_ws_dt"]) & (merged["date"] <= merged["_we_dt"])
        merged["hit"] = hit.fillna(False)

        agg = (
            merged.groupby(["actor_id", "domain_id", "win_start", "win_end"], dropna=False)
            .agg(n=("hit", "sum"))
            .reset_index()
        )

        out = out.merge(
            agg.rename(columns={"n": f"n_shocks_lag{L}"}),
            on=["actor_id", "domain_id", "win_start", "win_end"],
            how="left",
        )
        out[f"n_shocks_lag{L}"] = out[f"n_shocks_lag{L}"].fillna(0).astype(int)
        out[f"has_shock_lag{L}"] = (out[f"n_shocks_lag{L}"] > 0).astype(int)

    # Compat héritée (colonnes sans suffixe quand lag 0 est présent)
    if 0 in lags:
        if "n_shocks" not in out.columns:
            out["n_shocks"] = out["n_shocks_lag0"]
        if "has_shock" not in out.columns:
            out["has_shock"] = out["has_shock_lag0"]

    return out.drop(columns=[c for c in ["_ws_dt", "_we_dt"] if c in out.columns])
