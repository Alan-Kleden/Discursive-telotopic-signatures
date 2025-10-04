# 04_Code_Scripts/features/conative.py
from __future__ import annotations
import csv, io, re
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# --- spaCy loader (demandé par fc_fi_v3._precheck_or_fail) -------------------
def _load_spacy_or_fail(lang: str):
    """
    Charge et retourne le pipeline spaCy pour 'FR' ou 'EN'.
    Échec immédiat si indisponible.
    """
    import spacy
    lang = lang.upper()
    model_by_lang = {
        "FR": "fr_core_news_lg",
        "EN": "en_core_web_lg",
    }
    if lang not in model_by_lang:
        raise ValueError(f"[conative] unknown language {lang!r} (expected FR or EN)")
    model = model_by_lang[lang]
    try:
        return spacy.load(model)
    except Exception as e:
        raise RuntimeError(
            f"[conative] spaCy model '{model}' not available. "
            f"Install it, e.g.:\n  python -m spacy download {model}\nOriginal error: {e}"
        )

# --- Types & constantes -------------------------------------------------------
Entry = Dict[str, str]

REQUIRED_MIN = {"lemma", "language", "type", "weight"}
ALLOWED_TYPES = {"push", "inhibit"}
ALLOWED_POS = {None, "", "VERB", "AUX", "ADV", "NOUN", "ADJ", "PHRASE"}

# --- Utils --------------------------------------------------------------------
def _norm_txt(s: str) -> str:
    return s.lower()

def _read_utf8_no_bom(path: Path) -> str:
    raw = path.read_bytes()
    # strip UTF-8 BOM if present
    if raw.startswith(b"\xef\xbb\xbf"):
        raw = raw[3:]
    return raw.decode("utf-8")

def _parse_float(x: str) -> float:
    try:
        v = float(x)
    except Exception:
        raise ValueError(f"[conative] weight is not a float: {x!r}")
    if not (0.0 <= v <= 1.0):
        raise ValueError(f"[conative] weight must be in [0,1], got {v}")
    return v

# --- Structure du lexique -----------------------------------------------------
class ConativeLexicon:
    """Structure bilingue + règles regex optionnelles."""
    def __init__(self) -> None:
        # lemmas[lang][type][lemma] = (weight, concept_id)
        self.lemmas: Dict[str, Dict[str, Dict[str, Tuple[float, Optional[str]]]]] = {}
        # patterns[lang][type] = List[(compiled_re, weight, concept_id)]
        self.patterns: Dict[str, Dict[str, List[Tuple[re.Pattern, float, Optional[str]]]]] = {}

    def add_lemma(self, lang: str, tp: str, lemma: str, weight: float, concept_id: Optional[str]) -> None:
        self.lemmas.setdefault(lang, {}).setdefault(tp, {})
        prev = self.lemmas[lang][tp].get(lemma)
        if prev is None or weight > prev[0]:
            self.lemmas[lang][tp][lemma] = (weight, concept_id)

    def add_pattern(self, lang: str, tp: str, pattern: str, weight: float, concept_id: Optional[str]) -> None:
        try:
            rx = re.compile(pattern, re.IGNORECASE | re.UNICODE)
        except re.error as e:
            raise ValueError(f"[conative] invalid regex for {lang}/{tp}: {pattern!r} ({e})")
        self.patterns.setdefault(lang, {}).setdefault(tp, []).append((rx, weight, concept_id))

def load_conative_lexicon(csv_path: Optional[str|Path] = None) -> ConativeLexicon:
    """Charge un CSV riche ou minimal. Échec immédiat si problème."""
    # Emplacements possibles
    candidates = []
    if csv_path:
        candidates.append(Path(csv_path))
    candidates += [Path("01_Protocoles/lexicon_conative_v1.csv"),
                   Path("01_Protocoles/lexicon_conative.csv")]

    found: Optional[Path] = None
    for p in candidates:
        if p.exists():
            found = p
            break
    if not found:
        raise FileNotFoundError("[conative] lexicon CSV not found in 01_Protocoles (expected lexicon_conative_v1.csv)")

    text = _read_utf8_no_bom(found)
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        raise ValueError("[conative] CSV has no header")

    # Normalise en-têtes
    hdr = [h.strip() for h in reader.fieldnames]
    field_map = {h.lower(): h for h in hdr}

    if not REQUIRED_MIN.issubset(set(field_map.keys())):
        raise ValueError(f"[conative] CSV header must contain {REQUIRED_MIN}, got {set(field_map.keys())}")

    # Champs optionnels
    f_concept = field_map.get("concept_id")
    f_pos     = field_map.get("pos")
    f_re      = field_map.get("pattern_lemma_re")

    lex = ConativeLexicon()
    n_rows = 0
    for row in reader:
        n_rows += 1
        lemma    = row[field_map["lemma"]].strip()
        lang     = row[field_map["language"]].strip().upper()
        tp       = row[field_map["type"]].strip().lower()
        weight   = _parse_float(row[field_map["weight"]].strip())
        concept  = row[f_concept].strip() if f_concept and row.get(f_concept) else None
        pos      = row[f_pos].strip().upper() if f_pos and row.get(f_pos) else None
        patt_re  = row[f_re].strip() if f_re and row.get(f_re) else None

        if not lemma or not lang or not tp:
            raise ValueError(f"[conative] empty lemma/lang/type at row {n_rows}")
        if tp not in ALLOWED_TYPES:
            raise ValueError(f"[conative] invalid type {tp!r} at row {n_rows}, must be in {ALLOWED_TYPES}")
        if pos not in ALLOWED_POS:
            raise ValueError(f"[conative] invalid pos {pos!r} at row {n_rows}, allowed {ALLOWED_POS}")

        lex.add_lemma(lang, tp, lemma, weight, concept)
        if patt_re:
            lex.add_pattern(lang, tp, patt_re, weight, concept)

    if n_rows == 0:
        raise ValueError("[conative] CSV is empty")

    return lex

# --- API principale -----------------------------------------------------------
def conative_from_text(text: str, lang: str, nlp=None, lex: Optional[ConativeLexicon]=None) -> Tuple[float, float, Dict]:
    """
    Retourne (push, inhibit, debug) pour un texte/lang.
    - utilise spaCy (nlp) pour lemmes
    - applique en plus les regex pattern_lemma_re s'il y en a
    - dé-double par concept_id si présent (max des signaux lemma/pattern)
    """
    if lex is None:
        lex = load_conative_lexicon()

    lang = lang.upper()
    push_lem = lex.lemmas.get(lang, {}).get("push", {})
    inh_lem  = lex.lemmas.get(lang, {}).get("inhibit", {})
    push_rx  = lex.patterns.get(lang, {}).get("push", [])
    inh_rx   = lex.patterns.get(lang, {}).get("inhibit", [])

    if nlp is None:
        raise RuntimeError("[conative] spaCy nlp pipeline is required (no fallback in production)")

    doc = nlp(text)
    # 1) signaux par lemme
    concept_score_push: Dict[Optional[str], float] = {}
    concept_score_inh: Dict[Optional[str], float]  = {}

    for tok in doc:
        lem = tok.lemma_.lower()
        if lem in push_lem:
            w, cid = push_lem[lem]
            concept_score_push[cid] = max(concept_score_push.get(cid, 0.0), w)
        if lem in inh_lem:
            w, cid = inh_lem[lem]
            concept_score_inh[cid] = max(concept_score_inh.get(cid, 0.0), w)

    # 2) signaux par pattern (regex sur texte normalisé)
    raw = _norm_txt(text)
    for rx, w, cid in push_rx:
        if rx.search(raw):
            concept_score_push[cid] = max(concept_score_push.get(cid, 0.0), w)
    for rx, w, cid in inh_rx:
        if rx.search(raw):
            concept_score_inh[cid] = max(concept_score_inh.get(cid, 0.0), w)

    # 3) agrégation (somme bornée à 1.0 par canal)
    push_score = min(1.0, sum(concept_score_push.values()))
    inh_score  = min(1.0, sum(concept_score_inh.values()))

    debug = {
        "lang": lang,
        "push_matched": concept_score_push,
        "inhibit_matched": concept_score_inh,
        "n_tokens": len(doc),
    }
    return push_score, inh_score, debug
