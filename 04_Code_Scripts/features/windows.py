# windows.py — fenêtrage 30j / step 7j + deltas
from __future__ import annotations
import pandas as pd
import numpy as np
from datetime import timedelta

def sliding_windows(df_docs: pd.DataFrame, window_days: int = 30, step_days: int = 7) -> pd.DataFrame:
    df = df_docs.copy()
    df["date"] = pd.to_datetime(df["date"])
    results = []
    for (actor, domain), g in df.groupby(["actor_id","domain_id"]):
        if g.empty: 
            continue
        start = g["date"].min().normalize()
        end   = g["date"].max().normalize()
        cur = start
        while cur <= end:
            w_start = cur
            w_end = cur + pd.Timedelta(days=window_days-1)
            mask = (g["date"] >= w_start) & (g["date"] <= w_end)
            win = g.loc[mask]
            n_docs = int(len(win))
            n_tel_mean = float(win["n_tel"].mean()) if n_docs>0 else np.nan
            ambiv_rate = float(win["ambivalence_flag"].mean()) if n_docs>0 else np.nan
            results.append({
                "actor_id": actor,
                "domain_id": domain,
                "win_start": w_start.date().isoformat(),
                "win_end": w_end.date().isoformat(),
                "n_docs": n_docs,
                "n_tel_mean": n_tel_mean,
                "ambivalence_rate": ambiv_rate
            })
            cur = cur + pd.Timedelta(days=step_days)
    out = pd.DataFrame(results)
    # Delta n_tel par acteur/domaine (diff 1 step)
    out["Delta_n_tel"] = out.groupby(["actor_id","domain_id"])["n_tel_mean"].diff()
    return out
