# scripts/enrich_lexicon_v2.py
# -*- coding: utf-8 -*-
import os, re, csv
import pandas as pd
from datetime import datetime

ROOT = os.getcwd()
V1_PATH_DEFAULT = os.path.join("07_Config","lexicons","lexicon_conative_v1.clean.csv")
V2_PATH_DEFAULT = os.path.join("07_Config","lexicons","lexicon_conative_v2.clean.csv")
CHANGELOG_PATH  = os.path.join("07_Config","lexicons","lexicon_conative_v2.changelog.md")

def load_v1(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Lexicon v1 not found: {path}")
    df = pd.read_csv(path)
    # colonne lexicale
    lex_col = next((c for c in ["term","lemma","token"] if c in df.columns), None)
    if lex_col is None:
        raise ValueError("Missing lexical column in v1 (expected one of: term|lemma|token)")
    # colonne classe
    cls_col = "class" if "class" in df.columns else ("type" if "type" in df.columns else None)
    if cls_col is None:
        raise ValueError("Missing class/type column in v1 (expected: class or type with values in {fc,fi})")
    # poids optionnel
    w_col = "weight" if "weight" in df.columns else None

    keep = df[[lex_col, cls_col] + ([w_col] if w_col else [])].copy()
    keep.rename(columns={lex_col:"_lex", cls_col:"_class"}, inplace=True)
    if w_col:
        keep.rename(columns={w_col:"_weight"}, inplace=True)
    else:
        keep["_weight"] = 1.0

    # nettoyage
    keep["_lex"]   = keep["_lex"].astype(str).str.strip()
    keep["_class"] = keep["_class"].str.lower().str.strip()
    keep = keep[keep["_class"].isin(["fc","fi"])]
    keep = keep.dropna(subset=["_lex"]).drop_duplicates()
    return keep

def to_v2_rows(df_v1):
    rows = []
    # 1) Reprendre v1 sous forme de token exact (\b...\b), insensible casse
    for r in df_v1.itertuples(index=False):
        pat = r._lex
        if not pat: 
            continue
        # échappe les métacaractères pour un token exact
        escaped = re.escape(pat)
        pattern = rf"\b{escaped}\b"
        rows.append({
            "pattern": pattern,
            "kind": "regex",     # on encode en regex pour uniformiser, même si c'est un token exact
            "class": r._class,
            "weight": float(r._weight) if pd.notna(r._weight) else 1.0,
            "note": "from_v1_token_exact",
            "source": "v1"
        })

    # 2) Motifs contextuels (will/must + verbe d’action)
    ctx_fc = [
        r"\bwe\s+will\s+(act|move|proceed|deliver|ensure|implement)\b",
        r"\bwe\s+must\s+(act|move|protect|secure|invest|advance|strengthen)\b",
        r"\bwill\s+(take|implement|ensure|deliver|enforce)\b",
        r"\bmust\s+(invest|protect|strengthen|advance|enforce)\b",
        r"\burge\s+my\s+colleagues\b",
        r"\bcannot\s+stand\s+by\b",
    ]
    ctx_fi = [
        r"\bwill\s+(harm|undermine|weaken)\b",
        r"\bmust\s+(prevent|avoid|stop|halt)\b",
        r"\brise\s+in\s+opposition\b",
    ]

    for pat in ctx_fc:
        rows.append({
            "pattern": pat,
            "kind": "regex",
            "class": "fc",
            "weight": 1.25,  # léger boost d’intensité sur les contextes d’engagement
            "note": "context_pattern",
            "source": "add_ctx"
        })
    for pat in ctx_fi:
        rows.append({
            "pattern": pat,
            "kind": "regex",
            "class": "fi",
            "weight": 1.15,  # léger boost informatif (atténué)
            "note": "context_pattern",
            "source": "add_ctx"
        })

    v2 = pd.DataFrame(rows, columns=["pattern","kind","class","weight","note","source"]).drop_duplicates()
    return v2

def find_ambiguous_terms(df_v1):
    # termes présents dans les deux classes (fc & fi) -> signaler (on n’impose pas d’exclusion automatique)
    g = df_v1.groupby(["_lex"])["_class"].nunique()
    amb = g[g>1]
    if len(amb)==0:
        return []
    terms = sorted(amb.index.tolist())
    return terms

def main(v1_path=V1_PATH_DEFAULT, v2_path=V2_PATH_DEFAULT, changelog_path=CHANGELOG_PATH):
    v1 = load_v1(v1_path)
    v2 = to_v2_rows(v1)
    # changelog
    amb = find_ambiguous_terms(v1)

    os.makedirs(os.path.dirname(v2_path), exist_ok=True)
    v2.to_csv(v2_path, index=False, quoting=csv.QUOTE_MINIMAL)

    lines = []
    lines.append(f"# Lexicon v2 changelog — {datetime.now().isoformat(timespec='seconds')}")
    lines.append("")
    lines.append(f"- Input (v1): {v1_path}")
    lines.append(f"- Output (v2): {v2_path}")
    lines.append(f"- Total v1 entries: {len(v1)}")
    lines.append(f"- Total v2 entries: {len(v2)}  (includes contextual regex)")
    lines.append(f"- Ambiguous terms (present in fc & fi in v1): {len(amb)}")
    if amb:
        preview = ", ".join(amb[:20]) + ("…" if len(amb)>20 else "")
        lines.append(f"  - Examples: {preview}")
    lines.append("")
    lines.append("## Notes")
    lines.append("- v2 keeps exact tokens from v1 as word-boundary regexes (case-insensitive).")
    lines.append("- Adds contextual patterns for commitments (fc) and opposition/constraint (fi).")
    lines.append("- Ambiguities are **reported** here; disambiguation by context happens via added patterns.")
    lines.append("- Weights: token=1.0; contextual patterns: fc=1.25 / fi=1.15 (tunable).")
    os.makedirs(os.path.dirname(changelog_path), exist_ok=True)
    with open(changelog_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"OK → {v2_path}")
    print(f"Changelog → {changelog_path}")

if __name__ == "__main__":
    main()
