# repair_lexicon.py
import sys, csv, re
from pathlib import Path
from datetime import datetime

ALLOWED_LANG = {"EN","FR"}
ALLOWED_TYPE = {"push","inhibit"}
ALLOWED_POS  = {"", None, "VERB","AUX","ADV","ADJ","NOUN","PHRASE"}

src = Path(sys.argv[1]) if len(sys.argv)>1 else Path("07_Config/lexicons/lexicon_conative_v1.csv")
dst = Path(sys.argv[2]) if len(sys.argv)>2 else src.with_name(src.stem + "_clean.csv")

def norm(x): 
    return (x or "").strip()

rows, kept, dropped = [], 0, 0
with src.open("r", encoding="utf-8-sig", newline="") as f:
    rdr = csv.DictReader(f)
    need = ["concept_id","lemma","language","type","pos","pattern_lemma_re","weight","notes"]
    missing = [c for c in need if c not in (rdr.fieldnames or [])]
    if missing:
        print(f"[ERROR] Missing columns: {missing}")
        sys.exit(1)
    for i, row in enumerate(rdr, start=2):  # header = line 1
        # trim
        for k in row:
            row[k] = norm(row[k])
        # drop blank lines (all empty)
        if not any(row.values()):
            dropped += 1
            continue
        # hard validations
        if not row["lemma"]:
            dropped += 1; continue
        if row["language"] not in ALLOWED_LANG:
            dropped += 1; continue
        if row["type"] not in ALLOWED_TYPE:
            dropped += 1; continue
        if row["pos"] not in ALLOWED_POS:
            dropped += 1; continue
        # weight in [0,1]
        try:
            w = float(row["weight"])
            if not (0.0 <= w <= 1.0):
                dropped += 1; continue
            row["weight"] = f"{w:.2f}"
        except:
            dropped += 1; continue
        rows.append(row); kept += 1

if not rows:
    print("[ERROR] No valid rows kept  abort.")
    sys.exit(2)

with dst.open("w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=need)
    w.writeheader(); w.writerows(rows)

print(f"[OK] Cleaned lexicon written: {dst}")
print(f"Kept: {kept}  | Dropped: {dropped}")
