#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
make_excerpts.py — fabrique candidates_25.csv depuis lot_raw.csv
Colonnes requises par la suite : id, excerpt, Fc_items, Fi_items, source, country, url
Colonnes utiles annotateurs : telos_central, annotator_X_fc, annotator_X_fi, annotator_X_notes, flag_incertain
Reste neutre sur topic/stance (valeurs par défaut).
"""

import csv, re, sys, time
from pathlib import Path
from urllib.parse import urlparse

# Heuristiques simples pour Fc/Fi auto (motion lexicon minimal)
AUTO_FC_TERMS = [
    r"\bprotect(ion|)\b", r"\bfreedom\b", r"\bgrowth\b", r"\bprosper(ity|ous)\b",
    r"\bsecurity\b", r"\bopportunit(y|ies)\b", r"\binnovation\b", r"\bjobs?\b",
]
AUTO_FI_TERMS = [
    r"\brisk(s|y)?\b", r"\bthreat(s)?\b", r"\bcrisis(es)?\b", r"\bharm(s|ful)?\b",
    r"\bcost(s|ly)?\b", r"\bban(ned|s|ning)?\b", r"\bfailed?|failure\b", r"\bdecline\b",
]

RX_FC = re.compile("|".join(AUTO_FC_TERMS), re.I)
RX_FI = re.compile("|".join(AUTO_FI_TERMS), re.I)

LEGAL_BANNERS = [
    r"^this material may not be published.*?lipper\s*\.\s*$",
    r"^©\d{4} .*? all rights reserved\.\s*$",
    r"^legal statement\s*\.\s*$",
    r"^powered and implemented by .*?\.\s*$",
    r"^quotes displayed in real\-time.*?\.\s*$",
]
RX_LEGAL = re.compile("|".join(LEGAL_BANNERS), re.I | re.S)

def clean_excerpt(txt: str, max_words=250) -> str:
    if not txt:
        return ""
    t = txt.strip()
    # retire bannière légale en tête éventuelle
    t = RX_LEGAL.sub("", t).strip()
    # condense espaces
    t = re.sub(r"\s+", " ", t).strip()
    # tronque à N mots
    words = t.split()
    if len(words) > max_words:
        t = " ".join(words[:max_words])
    return t

def count_fc_fi(txt: str):
    fc = len(RX_FC.findall(txt))
    fi = len(RX_FI.findall(txt))
    return fc, fi

def read_rows(src: Path):
    # attend un lot_raw CSV avec colonnes: id, text, url[, source, country]
    with src.open("r", encoding="utf-8", newline="") as f:
        rdr = csv.DictReader(f)
        for r in rdr:
            yield r

def main():
    if len(sys.argv) != 5 or sys.argv[1] != "--in" or sys.argv[3] != "--out":
        print("Usage: python make_excerpts.py --in <lot_raw.csv> --out <candidates_25.csv>")
        sys.exit(2)

    src = Path(sys.argv[2])
    dst = Path(sys.argv[4])
    dst.parent.mkdir(parents=True, exist_ok=True)

    t0 = time.time()
    n_in, n_out = 0, 0

    with src.open("r", encoding="utf-8", newline="") as f_in, \
         dst.open("w", encoding="utf-8", newline="") as f_out:

        rdr = csv.DictReader(f_in)
        fieldnames = [
            "id","excerpt","excerpt_120_250w",
            "telos_central","Fc_items","Fi_items","stance_guess","topic",
            "country","source","url","rationale","notes",
            "annotator_X_fc","annotator_X_fi","annotator_X_notes","flag_incertain"
        ]
        wr = csv.DictWriter(f_out, fieldnames=fieldnames)
        wr.writeheader()

        for r in rdr:
            n_in += 1
            raw_txt = (r.get("text") or "").strip()
            if not raw_txt:
                continue

            excerpt = clean_excerpt(raw_txt, max_words=250)
            if not excerpt:
                continue

            fc, fi = count_fc_fi(excerpt)

            url = (r.get("url") or "").strip()
            dom = ""
            if url:
                try:
                    dom = urlparse(url).hostname or ""
                except Exception:
                    dom = ""
            source = (r.get("source") or dom or "").strip()
            country = (r.get("country") or "").strip()

            out_row = {
                "id": (r.get("id") or f"C{n_in:03d}"),
                "excerpt": excerpt,
                "excerpt_120_250w": excerpt,
                "telos_central": "",
                "Fc_items": f"auto_fc_hits={fc}",
                "Fi_items": f"auto_fi_hits={fi}",
                "stance_guess": "Inter",
                "topic": "MISC",
                "country": country,
                "source": source,
                "url": url,
                "rationale": "auto: legal-banner removed + 250w excerpt",
                "notes": "",
                "annotator_X_fc": "",
                "annotator_X_fi": "",
                "annotator_X_notes": "",
                "flag_incertain": "",
            }
            wr.writerow(out_row)
            n_out += 1

            # progress toutes les 100 lignes
            if n_out % 100 == 0:
                print(f"[make_excerpts] wrote {n_out} rows…", flush=True)

    dt = time.time() - t0
    print(f"[make_excerpts] DONE -> {dst} ({n_out} rows) in {dt:.2f}s")

if __name__ == "__main__":
    main()
