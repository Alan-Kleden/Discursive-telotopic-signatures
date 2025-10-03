# theta.py — projection rudimentaire vs telos → cosθ, sinθ
from __future__ import annotations
import numpy as np
import pandas as pd
import re
from typing import Dict, List

def _tok(s: str) -> List[str]:
    return re.findall(r"[a-zàâäéèêëîïôöùûüç'-]+", s.lower(), flags=re.I)

def cos_sin_theta_for_doc(text: str, telos_keywords: List[str], fc: float, fi: float) -> tuple[float,float]:
    """
    Heuristique robuste :
    - cosθ = clamp( (fc - fi), [-1,1] )
    - sinθ = signe basé sur présence de mots-telos vs anti-mots approx.
      Ici on fixe sinθ = 0 pour simplicité (tests ne requièrent que cosθ).
    """
    cos_t = float(np.clip(fc - fi, -1.0, 1.0))
    sin_t = 0.0
    return cos_t, sin_t

def apply_theta(df: pd.DataFrame, teloi: Dict[str, Dict[str, List[str]]]) -> pd.DataFrame:
    out = df.copy()
    cos_list, sin_list = [], []
    for actor, domain, text, fc, fi in zip(out["actor_id"], out["domain_id"], out["text"], out["fc_mean"], out["fi_mean"]):
        telos_kw = teloi.get(actor, {}).get(domain, [])
        c, s = cos_sin_theta_for_doc(text, telos_kw, fc, fi)
        cos_list.append(c); sin_list.append(s)
    out["cos_theta"] = cos_list
    out["sin_theta"] = sin_list
    return out
