# 04_Code_Scripts/features/conative.py
from __future__ import annotations
from typing import Dict, Any, Tuple
import re
import pandas as pd

# -- Lexiques initiaux (évolutifs) --
VERB_PUSH = {
    # modaux/impératifs d’action (poussée)
    "devoir": 0.9, "falloir": 0.8, "exiger": 0.85,
    "accélérer": 0.7, "renforcer": 0.6, "agir": 0.6, "engager": 0.55,
}
VERB_INHIBIT = {
    # blocage/ralentissement
    "empêcher": 0.9, "bloquer": 0.85, "freiner": 0.7, "ralentir": 0.6,
    "s_opposer": 0.85, "refuser": 0.75, "abstenir": 0.6,
}
# Locutions utiles (push / inhibit)
LOC_PUSH = [
    "il est temps", "sans délai", "immédiatement", "au plus vite",
    "afin de", "dans le but de",
]
LOC_INHIBIT = [
    "ne pas", "s_abstenir de", "refus de", "mettre fin à", "cesser de",
    "il conviendrait", "on pourrait envisager",
]

_WORD = re.compile(r"[^\W_]+", re.UNICODE)

def _simple_lemmas(text: str):
    # fallback simple si spaCy indisponible
    return [t.lower() for t in _WORD.findall(text or "")]

def conative_counts(text: str, nlp=None) -> Tuple[float, float]:
    """
    Renvoie (push_score, inhibit_score) indépendamment de la valence affective.
    spaCy si dispo (lemmes/POS, négation), sinon regex simple.
    """
    push, inhibit = 0.0, 0.0
    text = text or ""

    # locutions (score additif léger)
    low = " ".join(_simple_lemmas(text))
    for loc in LOC_PUSH:
        if loc in low:
            push += 0.3
    for loc in LOC_INHIBIT:
        if loc in low:
            inhibit += 0.3

    if nlp is None:
        # fallback: lemmes naïfs ≈ tokens
        toks = _simple_lemmas(text)
        for tok in toks:
            push += VERB_PUSH.get(tok, 0.0)
            inhibit += VERB_INHIBIT.get(tok, 0.0)
        # gestion “ne pas X” simple
        if "ne" in toks and "pas" in toks:
            inhibit += 0.3
        return push, inhibit

    # voie spaCy
    doc = nlp(text)
    # détection verbes + négations
    negated_heads = set()
    for t in doc:
        if t.dep_.lower() in ("neg", "advmod") and t.head is not None:
            negated_heads.add(t.head.i)

    for t in doc:
        lem = t.lemma_.lower()
        if t.pos_ == "VERB":
            push += VERB_PUSH.get(lem, 0.0)
            inhibit += VERB_INHIBIT.get(lem, 0.0)
            # si verbe d'action est nié → inhibition légère
            if t.i in negated_heads and lem in VERB_PUSH:
                inhibit += 0.3

    return float(push), float(inhibit)

def add_conative(df: pd.DataFrame, text_col: str = "text", mode: str = "v2") -> pd.DataFrame:
    nlp = None
    if mode.lower() == "v2":
        try:
            import spacy
            nlp = spacy.load("fr_core_news_lg")
        except Exception:
            nlp = None
    out = df.copy()
    vals = out[text_col].apply(lambda s: conative_counts(str(s), nlp))
    out["push_raw"] = vals.apply(lambda x: x[0])
    out["inhibit_raw"] = vals.apply(lambda x: x[1])
    return out
