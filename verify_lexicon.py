#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Vérification structurée du fichier lexicon_conative_v1.csv

- Localisation: lit le chemin depuis l'argument CLI, sinon $CONATIVE_LEXICON_PATH,
  sinon 07_Config/lexicons/lexicon_conative_v1.csv
- Encodage: accepte UTF-8, signale la présence d'un BOM
- Colonnes requises: concept_id, lemma, language, type, pos, pattern_lemma_re, weight, notes
- Valeurs autorisées:
    language ∈ {FR, EN}
    type ∈ {push, inhibit}
    pos ∈ {"", None, VERB, NOUN, ADJ, ADV, AUX, PHRASE}
- weight ∈ [0,1]
- pattern_lemma_re: regex compilable (vide accepté si pos≠PHRASE)
- Doublons (clé): (concept_id) doit être unique
- Avertit si (language, lemma, type, pos, pattern_lemma_re) apparaît plusieurs fois
- Code retour:
    0 si ok ou seulement warnings
    2 si erreurs bloquantes
Options:
    --strict : transforme les warnings en erreurs (retour 2)
"""

from __future__ import annotations
import csv
import os
import re
import sys
from typing import Dict, List, Tuple

REQUIRED_COLS = [
    "concept_id",
    "lemma",
    "language",
    "type",
    "pos",
    "pattern_lemma_re",
    "weight",
    "notes",
]

ALLOWED_LANG = {"FR", "EN"}
ALLOWED_TYPE = {"push", "inhibit"}
ALLOWED_POS  = {None, "", "VERB", "NOUN", "ADJ", "ADV", "AUX", "PHRASE"}

def find_lexicon_path(cli_arg: str | None) -> str:
    if cli_arg:
        return cli_arg
    env = os.environ.get("CONATIVE_LEXICON_PATH")
    if env:
        return env
    return os.path.join("07_Config", "lexicons", "lexicon_conative_v1.csv")

def read_csv_any_utf8(path: str) -> Tuple[List[Dict[str, str]], bool]:
    """
    Lit CSV en UTF-8, détecte BOM (UTF-8-SIG) et le retire si présent.
    Retourne (rows, had_bom).
    """
    had_bom = False
    # Première passe pour détecter BOM
    with open(path, "rb") as f:
        head = f.read(3)
        if head == b"\xef\xbb\xbf":
            had_bom = True
    # Lecture texte (utf-8-sig enlève BOM côté header s'il existe)
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        # Normaliser les noms de colonnes (strip et retrait éventuel du BOM résiduel)
        fieldnames = [c.lstrip("\ufeff").strip() for c in (reader.fieldnames or [])]
        # Re-créer rows avec clés normalisées
        norm_rows = []
        for r in rows:
            norm_rows.append({fieldnames[i]: v for i, v in enumerate(r.values())})
    return norm_rows, had_bom

def check_header(columns: List[str]) -> List[str]:
    missing = [c for c in REQUIRED_COLS if c not in columns]
    return missing

def is_float_in_0_1(x: str) -> bool:
    try:
        v = float(x)
        return 0.0 <= v <= 1.0
    except Exception:
        return False

def compile_regex_safe(pat: str) -> Tuple[bool, str]:
    try:
        re.compile(pat)
        return True, ""
    except re.error as e:
        return False, str(e)

def main(argv: List[str]) -> int:
    strict = "--strict" in argv
    args = [a for a in argv[1:] if not a.startswith("--")]
    path = find_lexicon_path(args[0] if args else None)

    errors: List[str] = []
    warnings: List[str] = []

    if not os.path.isfile(path):
        errors.append(f"[IO] File not found: {path}")
        return end(strict, errors, warnings)

    try:
        rows, had_bom = read_csv_any_utf8(path)
    except Exception as e:
        errors.append(f"[IO] Cannot read CSV as UTF-8/UTF-8-SIG: {e!r}")
        return end(strict, errors, warnings)

    if had_bom:
        warnings.append("[ENCODING] BOM detected. Prefer clean UTF-8 (no BOM).")

    # Vérifier header exact
    # Relecture du header à partir de la première ligne si disponible
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        try:
            header = next(reader)
        except StopIteration:
            errors.append("[CSV] Empty file.")
            return end(strict, errors, warnings)
    header = [h.lstrip("\ufeff").strip() for h in header]
    missing = check_header(header)
    if missing:
        errors.append(f"[CSV] Missing required columns: {missing}")

    # Dictionnaires pour détection de duplications
    seen_concept_id = set()
    seen_signature  = set()  # (language, lemma, type, pos, pattern)

    # Validation ligne à ligne
    for idx, row in enumerate(rows, start=2):  # 2 = compte ligne après header
        def gv(k: str) -> str:
            return (row.get(k, "") or "").strip()

        concept_id       = gv("concept_id")
        lemma            = gv("lemma")
        language         = gv("language").upper()
        type_            = gv("type").lower()
        pos              = gv("pos")
        pattern          = gv("pattern_lemma_re")
        weight           = gv("weight")
        notes            = gv("notes")

        # concept_id
        if not concept_id:
            errors.append(f"[ROW {idx}] Empty concept_id.")
        else:
            if concept_id in seen_concept_id:
                errors.append(f"[ROW {idx}] Duplicate concept_id: {concept_id!r}")
            seen_concept_id.add(concept_id)

        # lemma
        if not lemma:
            errors.append(f"[ROW {idx}] Empty lemma.")
        # language
        if language not in ALLOWED_LANG:
            errors.append(f"[ROW {idx}] Invalid language {language!r}, allowed {sorted(ALLOWED_LANG)}")
        # type
        if type_ not in ALLOWED_TYPE:
            errors.append(f"[ROW {idx}] Invalid type {type_!r}, allowed {sorted(ALLOWED_TYPE)}")
        # pos
        if pos not in ALLOWED_POS:
            errors.append(f"[ROW {idx}] Invalid pos {pos!r}, allowed {sorted([p for p in ALLOWED_POS if p]) + ['(empty)']}")

        # weight
        if not is_float_in_0_1(weight):
            errors.append(f"[ROW {idx}] weight must be float in [0,1], got {weight!r}")

        # pattern_lemma_re et POS
        if pos == "PHRASE":
            if not pattern:
                errors.append(f"[ROW {idx}] pos=PHRASE requires non-empty pattern_lemma_re.")
            else:
                ok, msg = compile_regex_safe(pattern)
                if not ok:
                    errors.append(f"[ROW {idx}] invalid regex pattern_lemma_re={pattern!r}: {msg}")
        else:
            if pattern:
                # pattern optionnel hors PHRASE; si présent, vérifier la compilabilité
                ok, msg = compile_regex_safe(pattern)
                if not ok:
                    errors.append(f"[ROW {idx}] invalid regex pattern_lemma_re={pattern!r}: {msg}")

        sig = (language, lemma, type_, pos or "", pattern or "")
        if sig in seen_signature:
            warnings.append(f"[ROW {idx}] Potential duplicate entry (language,lemma,type,pos,pattern): {sig}")
        seen_signature.add(sig)

    # Récapitulatif
    print(f"\nLexicon check — {path}")
    print(f"Rows: {len(rows)} | Errors: {len(errors)} | Warnings: {len(warnings)}")
    if warnings:
        print("\nWARNINGS:")
        for w in warnings:
            print("  -", w)
    if errors:
        print("\nERRORS:")
        for e in errors:
            print("  -", e)

    return end(strict, errors, warnings)

def end(strict: bool, errors: List[str], warnings: List[str]) -> int:
    if errors:
        return sys.exit(2)
    if strict and warnings:
        return sys.exit(2)
    return sys.exit(0)

if __name__ == "__main__":
    sys.exit(main(sys.argv))
