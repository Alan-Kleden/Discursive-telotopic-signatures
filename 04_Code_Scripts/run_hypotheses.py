from __future__ import annotations
import json
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

from eval.hypotheses import bootstrap_ci_delta, lrt_from_ll


def main() -> None:
    # =================== H1 : ΔAUC (télotopique vs style-only) ===================
    fdoc = Path("artifacts/mock/features_doc.parquet")
    if not fdoc.exists():
        raise SystemExit("Need artifacts/mock/features_doc.parquet — run features first.")

    df = pd.read_parquet(fdoc)

    # Si 'stance' absente (mock), on la crée : pro (1) si Fc >= Fi
    if "stance" not in df.columns:
        df = df.assign(stance=(df["fc_mean"] >= df["fi_mean"]).astype(int))

    # Vecteurs propres
    y = df["stance"].astype(int).values
    s_tel = df["n_tel"].astype(float).values

    # Proxy style-only très léger : longueur normalisée (bornée [0,1])
    denom = max(10, int(df["len_tokens"].max()))
    s_style = (df["len_tokens"].astype(float) / denom).clip(0, 1).values

    # Retirer lignes non-informatives
    mask = np.isfinite(s_tel) & np.isfinite(s_style)
    y, s_tel, s_style = y[mask], s_tel[mask], s_style[mask]

    if len(np.unique(y)) < 2:
        delta_mean, ci_lo, ci_hi = np.nan, np.nan, np.nan
    else:
        delta_mean, (ci_lo, ci_hi) = bootstrap_ci_delta(
            y, s_tel, s_style, n_resamples=1000, seed=1337
        )

    # =================== H3 : LRT via GLM Binomial (proportions) ===================
    fwin = Path("artifacts/mock/features_win.parquet")
    if not fwin.exists():
        raise SystemExit("Need artifacts/mock/features_win.parquet — run windows first.")

    win = pd.read_parquet(fwin).dropna(subset=["n_tel_mean", "n_docs"]).copy()

    if win.empty:
        stat, p_lrt = np.nan, np.nan
    else:
        # Endog = proportion (succès / essais), avec poids = n_docs
        # n_tel_mean est déjà borné [0,1] ; on clippe légèrement pour stabilité
        eps = 1e-6
        prop = win["n_tel_mean"].clip(eps, 1 - eps).astype(float)
        weights = win["n_docs"].clip(lower=1).astype(float)

        # Modèle nul : intercept seul
        X0 = np.ones((len(win), 1), dtype=float)
        # Modèle plein : intercept + n_tel_mean + has_shock
        X1 = sm.add_constant(
            win[["n_tel_mean", "has_shock"]].astype(float), has_constant="add"
        )

        # Ajustements (GLM binomial avec poids de fréquence)
        m0 = sm.GLM(prop, X0, family=sm.families.Binomial(), freq_weights=weights).fit()
        m1 = sm.GLM(prop, X1, family=sm.families.Binomial(), freq_weights=weights).fit()

        ll0 = float(m0.llf)
        ll1 = float(m1.llf)
        df_added = X1.shape[1] - X0.shape[1]
        stat, p_lrt = lrt_from_ll(ll0, ll1, df_added=df_added)

    # =================== Export commun ===================
    out = {
        "H1_delta_auc_telotopic_minus_style": (
            float(delta_mean) if np.isfinite(delta_mean) else None
        ),
        "H1_delta_auc_ci95": [
            float(ci_lo) if np.isfinite(ci_lo) else None,
            float(ci_hi) if np.isfinite(ci_hi) else None,
        ],
        "H3_lrt_stat": float(stat) if np.isfinite(stat) else None,
        "H3_lrt_p": float(p_lrt) if np.isfinite(p_lrt) else None,
    }

    out_dir = Path("artifacts/mock")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "hypotheses.json"
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
