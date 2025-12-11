# coding: utf-8
import csv, sys
from pathlib import Path

# Valide le lot final Phase 1.
# Contraintes:
# - Schéma exact (12 colonnes)
# - Longueur extrait ∈ [120, 250] si non vide
# - country ∈ {UK, US} ou vide
# - topic ∈ ALLOWED_TOPICS (inclut MISC) ou vide

ALLOWED_TOPICS = {
    "IMM", "LIBSEC", "CLIM", "MISC"
}

REQUIRED_SCHEMA = {
    "id","excerpt","telos_central","Fc_items","Fi_items",
    "stance_guess","topic","country","source","url",
    "rationale","notes"
}

p = Path(r".\artifacts\phase1\inputs\lot20_final.csv")
errs = []

with p.open(encoding="utf-8") as f:
    r = csv.DictReader(f)
    if set(r.fieldnames) != REQUIRED_SCHEMA:
        print("SCHEMA_ERROR", r.fieldnames); sys.exit(2)

    for i, row in enumerate(r, start=2):
        ex = (row.get("excerpt","") or "").strip()
        n = len(ex.split())
        if n and (n < 120 or n > 250):
            errs.append((i, row.get("id",""), n))

        country = (row.get("country","") or "").strip().upper()
        if country and country not in {"UK","US"}:
            errs.append((i, row.get("id",""), "COUNTRY"))

        topic = (row.get("topic","") or "").strip().upper()
        if topic and topic not in ALLOWED_TOPICS:
            errs.append((i, row.get("id",""), "TOPIC"))

print("OK" if not errs else f"ERR {errs}")
