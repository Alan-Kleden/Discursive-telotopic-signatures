# features/shocks.py — aligner shocks sur fenêtres
from __future__ import annotations
import pandas as pd

def load_shocks(path: str | None = "data/mock/shocks.csv") -> pd.DataFrame:
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"])
    return df

def tag_windows_with_shocks(win_df: pd.DataFrame, shocks_df: pd.DataFrame) -> pd.DataFrame:
    """
    Jointure robuste :
    - conserve win_start / win_end en STRING (pour compat avec sliding_windows)
    - crée des colonnes datetime temporaires pour le test d'intersection
    - agrège n_shocks par (actor_id, domain_id, win_start, win_end) en gardant les types d'origine
    """
    # Copie de travail (on garde les strings d'origine)
    base = win_df.copy()

    # Colonnes datetime TEMPORAIRES pour le test d'intersection
    work = base.copy()
    work["_ws"] = pd.to_datetime(work["win_start"])
    work["_we"] = pd.to_datetime(work["win_end"])

    shocks = shocks_df.copy()  # date déjà en datetime

    # Merge par domaine, puis marquer si le shock tombe dans [ws, we]
    work = work.merge(shocks[["domain_id", "date", "shock_id"]], on="domain_id", how="left")
    hits = (work["date"] >= work["_ws"]) & (work["date"] <= work["_we"])
    work["shock_in_window"] = hits.fillna(False)

    # Agréger par clés TEXTE d'origine (pas les colonnes datetime)
    agg = (
        work.groupby(["actor_id", "domain_id", "win_start", "win_end"], dropna=False)
            .agg(n_shocks=("shock_in_window", "sum"))
            .reset_index()
    )

    # Merge des agrégats sur le DataFrame original (types identiques → pas de conflit)
    final = base.merge(
        agg,
        on=["actor_id", "domain_id", "win_start", "win_end"],
        how="left"
    )
    final["n_shocks"] = final["n_shocks"].fillna(0).astype(int)
    final["has_shock"] = (final["n_shocks"] > 0).astype(int)

    # Nettoyage des temporaires (elles ne sont pas dans `final`, mais au cas où)
    for c in ("_ws", "_we", "date", "shock_id", "shock_in_window"):
        if c in final.columns:
            final = final.drop(columns=[c])

    return final
