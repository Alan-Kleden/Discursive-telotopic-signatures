# 04_Code_Scripts/utils/validate_csv.py
# -*- coding: utf-8 -*-
# Valide un CSV de collecte (schéma PoC) :
#  - Fichier existe et non vide
#  - En-tête attendu
#  - ≥ 2 lignes (header + ≥1 data)
#
# Usage:
#   python -m utils.validate_csv data/raw/UK_HomeOffice_T1.csv
#   python 04_Code_Scripts/utils/validate_csv.py data/raw/UK_HomeOffice_T1.csv

from __future__ import annotations
import sys, csv
from pathlib import Path

EXPECTED_HEADER = ["actor_id","country","domain_id","period","date","url","language","text","tokens"]

def main():
    if len(sys.argv) != 2:
        print("Usage: python -m utils.validate_csv <csv_path>")
        sys.exit(2)

    path = Path(sys.argv[1])
    if not path.exists():
        print(f"[FAIL] File not found: {path}")
        sys.exit(1)
    if path.stat().st_size == 0:
        print(f"[FAIL] Empty file: {path}")
        sys.exit(1)

    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        rows = list(reader)

    if not rows:
        print(f"[FAIL] No rows in: {path}")
        sys.exit(1)

    header = rows[0]
    if header != EXPECTED_HEADER:
        print(f"[FAIL] Header mismatch.\nExpected: {EXPECTED_HEADER}\nFound   : {header}")
        sys.exit(1)

    if len(rows) < 2:
        print(f"[FAIL] No data rows in: {path}")
        sys.exit(1)

    print(f"[OK] {path}  rows={len(rows)}")
    for i, r in enumerate(rows[:3]):
        print(f"[{i}] {r}")

if __name__ == "__main__":
    main()
