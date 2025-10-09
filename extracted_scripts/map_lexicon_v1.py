# 04_Code_Scripts/analysis/map_lexicon_v1.py
# -*- coding: utf-8 -*-
import os, re, argparse, pandas as pd

def coerce_class(x: str):
    if not isinstance(x, str):
        return None
    s = x.strip().lower()
    if s in ("push", "forward", "fc", "pro"):
        return "fc"
    if s in ("inhibit", "pull", "oppose", "fi", "contra", "critic", "against"):
        return "fi"
    # mapping tolérant
    if any(k in s for k in ("push","forward"," fc","pro","commit")):
        return "fc"
    if any(k in s for k in ("inhibit","pull","oppose"," fi","contra","critic","against")):
        return "fi"
    return None

def main():
    ap = argparse.ArgumentParser(description="Map v1 → v1.mapped (pattern, class)")
    ap.add_argument("--in",  dest="src", required=True)
    ap.add_argument("--out", dest="dst", required=True)
    ap.add_argument("--lang", default="EN", help="Ne garder que cette langue (par défaut: EN)")
    args = ap.parse_args()

    if not os.path.exists(args.src):
        raise SystemExit(f"Input not found: {args.src}")

    df = pd.read_csv(args.src, encoding="utf-8", on_bad_lines="skip")

    # Filtre langue (si colonne présente)
    if "language" in df.columns:
        df = df[df["language"].astype(str).str.upper().eq(args.lang.upper())].copy()

    # Classe
    if "type" not in df.columns:
        raise SystemExit("Missing 'type' column in v1.")
    df["class"] = df["type"].apply(coerce_class)

    keep = df[df["class"].isin(["fc","fi"])].copy()

    # Pattern : priorité à pattern_lemma_re s’il existe et non vide, sinon \b{lemma}\b
    if "pattern_lemma_re" in keep.columns:
        pl = keep["pattern_lemma_re"].fillna("").astype(str).str.strip()
        use_pl = pl.ne("")
        keep["pattern"] = None
        keep.loc[use_pl, "pattern"] = pl[use_pl]
        base_col = "lemma" if "lemma" in keep.columns else ("concept_id" if "concept_id" in keep.columns else None)
        if base_col is None:
            raise SystemExit("No lemma/concept_id to fallback.")
        keep.loc[~use_pl, "pattern"] = keep[base_col].astype(str).str.strip().apply(lambda t: rf"\b{re.escape(t)}\b")
    else:
        base_col = "lemma" if "lemma" in keep.columns else ("concept_id" if "concept_id" in keep.columns else None)
        if base_col is None:
            raise SystemExit("No lemma/concept_id to build patterns.")
        keep["pattern"] = keep[base_col].astype(str).str.strip().apply(lambda t: rf"\b{re.escape(t)}\b")

    out = keep[["pattern","class"]].dropna().drop_duplicates()
    os.makedirs(os.path.dirname(args.dst), exist_ok=True)
    out.to_csv(args.dst, index=False)

    fc = (out["class"]=="fc").sum()
    fi = (out["class"]=="fi").sum()
    print(f"OK -> {args.dst}  rows={len(out)}  fc={fc}  fi={fi}")

if __name__ == "__main__":
    main()

