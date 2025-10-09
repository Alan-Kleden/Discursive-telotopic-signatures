# 04_Code_Scripts/analysis/audit_lexicon_v1.py
# -*- coding: utf-8 -*-
import os, sys, csv, pandas as pd

def main():
    if len(sys.argv) != 2:
        print("Usage: python audit_lexicon_v1.py 07_Config\\lexicons\\lexicon_conative_v1.clean.csv")
        sys.exit(1)
    src = sys.argv[1]
    if not os.path.exists(src):
        print(f"[ERR] Not found: {src}")
        sys.exit(2)

    # Compte brut de lignes (CSV “physique”)
    with open(src, 'r', encoding='utf-8', errors='ignore') as f:
        n_lines = sum(1 for _ in f)
    print(f"[FILE] {src}  raw_lines={n_lines}")

    # Lecture stricte (pour voir si ça casse)
    try:
        df_raw = pd.read_csv(src, encoding="utf-8")
        strict_ok = True
    except Exception as e:
        print("[WARN] strict read failed ->", repr(e))
        strict_ok = False

    # Lecture tolérante
    df = pd.read_csv(src, encoding="utf-8", on_bad_lines="skip")
    print(f"[PANDAS] parsed_rows={len(df)}  columns={list(df.columns)}")

    # Colonnes attendues
    needed = ["lemma","concept_id","type","pattern_lemma_re","weight","language","pos","notes"]
    exist = {c: (c in df.columns) for c in needed}
    print("[COLUMNS presence]", exist)

    # Valeurs de type
    if "type" in df.columns:
        tcounts = df["type"].astype(str).str.strip().str.lower().value_counts().to_dict()
        print("[type value_counts]", tcounts)
    else:
        print("[WARN] no 'type' column")

    # Lignes problématiques (absences)
    missing_type = df[df.get("type").isna()] if "type" in df.columns else pd.DataFrame()
    missing_lemma = df[df.get("lemma").isna()] if "lemma" in df.columns else pd.DataFrame()
    print(f"[MISSING] type={len(missing_type)}  lemma={len(missing_lemma)}")

    # Aperçu
    print("\n[HEAD]")
    print(df.head(5).to_string(index=False))
    print("\n[TAIL]")
    print(df.tail(5).to_string(index=False))

    # Heuristique : delimiteurs
    with open(src, 'r', encoding='utf-8', errors='ignore') as f:
        sample = [next(f) for _ in range(min(10, n_lines))]
    semi = sum(1 for ln in sample if ';' in ln)
    comma = sum(1 for ln in sample if ',' in ln)
    print(f"[DELIMS] first10: has_semicolon_lines={semi}  has_comma_lines={comma}")

    # Ligne orpheline style “74” ?
    orphan_numeric = 0
    for ln in sample:
        s = ln.strip()
        if s.isdigit():
            orphan_numeric += 1
    print(f"[ODD] numeric_only_lines_in_first10={orphan_numeric}")

if __name__ == "__main__":
    main()
