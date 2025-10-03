# fc_fi.py — Fc/Fi simples, déterministes
from __future__ import annotations
import re
import numpy as np
import pandas as pd
from typing import Sequence, Dict, List

def _tok(s: str) -> List[str]:
    return re.findall(r"[a-zàâäéèêëîïôöùûüç'-]+", s.lower(), flags=re.I)

def fc_fi_for_doc(text: str, domain_id: str, lexicon: Dict[str, Dict[str, Sequence[str]]]) -> tuple[float,float,int]:
    toks = _tok(text)
    if not toks:
        return 0.0, 0.0, 0
    pro = set(lexicon.get(domain_id,{}).get("pro",[]))
    anti= set(lexicon.get(domain_id,{}).get("anti",[]))
    n_pro = sum(t in pro for t in toks)
    n_anti= sum(t in anti for t in toks)
    n = len(toks)
    # normalisation simple par longueur (plafonnée)
    fc = n_pro / max(5, n)
    fi = n_anti / max(5, n)
    fc = float(np.clip(fc, 0.0, 1.0))
    fi = float(np.clip(fi, 0.0, 1.0))
    return fc, fi, n

def apply_fc_fi(df: pd.DataFrame, lexicon: Dict, text_col="text") -> pd.DataFrame:
    out = df.copy()
    vals = [fc_fi_for_doc(t, d, lexicon) for t,d in zip(out[text_col], out["domain_id"])]
    out["fc_mean"] = [v[0] for v in vals]
    out["fi_mean"] = [v[1] for v in vals]
    out["len_tokens"] = [v[2] for v in vals]
    return out
