# n_tel.py — cohérence pondérée + flag ambivalence
# Revision: March 2026 — Fc⊗Fi orthogonality correction
# Ref: Prolegomena v1.0 (Kleden, 2026) doi:10.5281/zenodo.19003446
# Amendment: OSF_Amendment_PoC_March2026.pdf (osf.io/rm42h)
from __future__ import annotations
import numpy as np
import pandas as pd

# poids figés (pré-enregistrement OSF — inchangés)
ALPHA, BETA, GAMMA, DELTA, EPSILON = 0.30, 0.20, 0.25, 0.15, 0.10


def compute_ambivalence_score(fc: float, fi: float, eps: float = 1e-6) -> float:
    """
    Ratio d'équilibre Fc/Fi dans [0,1].
    1.0 = équilibre parfait (fc == fi)
    0.0 = une force domine complètement l'autre

    Remplace |fc - fi| < 0.1 (logique soustractive incompatible avec Fc⊗Fi).
    Sous ⊗, fc=fi=1 est la tension maximale, non l'ambivalence au sens annulation.
    Ref: OSF Amendment March 2026, §3.3
    """
    return (2.0 * min(fc, fi)) / (fc + fi + eps)


def compute_ambivalence_flag(fc: float, fi: float,
                              tau: float = 0.20,
                              eps: float = 1e-6) -> int:
    """
    Flag ambivalence via ratio d'équilibre.
    tau = ambivalence_tau_abs: 0.20 (préregistré OSF, inchangé)
    """
    return int(compute_ambivalence_score(fc, fi, eps) > tau)


def compute_doclen_norm(n_tokens: int, cap: int = 200) -> float:
    return float(min(max(n_tokens, 0), cap) / cap)


def compute_n_tel_row(fc: float, fi: float,
                       cos_t: float, ambiv: int,
                       n_tokens: int) -> float:
    """
    Calcul N_tel révisé (Fc⊗Fi orthogonality — March 2026).

    Modifications vs version précédente :
    - BETA : (1.0 - fi)  →  sqrt(fc²+fi²)/sqrt(2)
      Fi est contributif (mobilisation totale), non pénalisant.
      Justification : proxy de π absent ; ALPHA·fc compense asymétrie
      d'information (cf. OSF Amendment §3.2, note sur asymétrie).
    - GAMMA : abs(cos_t)  →  cos_t²
      Noyau d'alignement canonique de v5.7 : cos²(θ_k − θ_T).
    - ambiv : calculé via compute_ambivalence_flag (ratio, non différence)

    Poids préregistrés inchangés : ALPHA=0.30, BETA=0.20,
    GAMMA=0.25, DELTA=0.15, EPSILON=0.10
    """
    dl = compute_doclen_norm(n_tokens)

    # Norme euclidienne normalisée sous ⊗
    # max = sqrt(2) quand fc=fi=1 → normalisé à 1.0
    f_ortho_norm = np.sqrt(float(fc)**2 + float(fi)**2) / np.sqrt(2)

    score = (
        (ALPHA   * float(fc))
      + (BETA    * f_ortho_norm)
      + (GAMMA   * float(cos_t)**2)
      + (DELTA   * (1 - ambiv))
      + (EPSILON * dl)
    )
    return float(np.clip(score, 0.0, 1.0))


def apply_n_tel(df: pd.DataFrame) -> pd.DataFrame:
    """
    Applique N_tel révisé sur un DataFrame.
    Colonnes requises : fc_mean, fi_mean, cos_theta, len_tokens
    """
    out = df.copy()

    # Ambivalence via ratio (remplace |fc - fi| < 0.1)
    out["ambivalence_flag"] = [
        compute_ambivalence_flag(f, i)
        for f, i in zip(out["fc_mean"], out["fi_mean"])
    ]

    out["n_tel"] = [
        compute_n_tel_row(f, i, c, a, n)
        for f, i, c, a, n in zip(
            out["fc_mean"],
            out["fi_mean"],
            out["cos_theta"],
            out["ambivalence_flag"],
            out["len_tokens"]
        )
    ]
    return out
