# -*- coding: utf-8 -*-
# scripts/generate_validation_sample.py
"""
Génère l'échantillon d'annotation (gold standard) et les fichiers:
- 07_Config/validation_sample_texts.csv (textes à annoter)
- 07_Config/validation_manual_template.csv (gabarit à remplir par les annotateurs)

Spécifications (v2 corrigée):
- N par défaut = 20 (adapté à T1 ~56 docs), avec cap automatique à 50% du corpus.
- Chemins stricts (pas de fallbacks): 
    artifacts/real/corpus_final.parquet
    artifacts/real/features_doc.parquet
- Strates: fc haut, fi haut, "low" (Q1), "ambiv" (Q3∩Q3), puis top-up jusqu’à N.
- Template annotateur complet: annotator, fc_manual, fi_manual, notes.

Paramétrage optionnel:
- --n 30 (CLI) ou variable d’environnement VALIDATION_N=30
  (La valeur finale est capée à 50% du corpus disponible.)
"""

from __future__ import annotations

import os
import sys
import numpy as np
import pandas as pd

CORPUS_PQ   = os.path.join("artifacts", "real", "corpus_final.parquet")
FEATURES_PQ = os.path.join("artifacts", "real", "features_doc.parquet")
OUT_DIR     = os.path.join("07_Config")


def _load_inputs() -> pd.DataFrame:
    if not os.path.exists(CORPUS_PQ):
        raise FileNotFoundError(CORPUS_PQ)
    corpus = pd.read_parquet(CORPUS_PQ)

    if os.path.exists(FEATURES_PQ):
        feats = pd.read_parquet(FEATURES_PQ)
        keep = ["actor_id", "date", "url", "fc", "fi"]
        feats = feats[[c for c in keep if c in feats.columns]].drop_duplicates()
        df = corpus.merge(feats, on=["actor_id", "date", "url"], how="left")
    else:
        df = corpus.copy()
        # Valeurs neutres si features absents
        df["fc"] = 0.0
        df["fi"] = 0.0

    # Nettoyage minimal
    if "text" not in df.columns:
        raise KeyError("Colonne 'text' absente du corpus fusionné.")
    df = df.dropna(subset=["text"])
    df = df.drop_duplicates(subset=["actor_id", "date", "url"]).reset_index(drop=True)
    return df


def _decide_N(df_len: int, n_requested: int | None) -> int:
    # Défaut sobre
    N_default = 20
    # Source 1: CLI/ENV (si présente)
    if n_requested is None:
        env_n = os.getenv("VALIDATION_N")
        n_requested = int(env_n) if env_n and env_n.isdigit() else N_default
    # Cap à 50% du corpus (guardrail) et à df_len
    if df_len <= 1:
        return min(1, df_len)
    cap = max(1, df_len // 2)  # 50% max
    N = max(1, min(n_requested, cap, df_len))
    if N < n_requested:
        print(f"[WARN] N capé de {n_requested} à {N} (50% du corpus ou disponibilité).", file=sys.stderr)
    return N


def main(argv=None) -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Generate validation sample (texts + manual template).")
    parser.add_argument("--n", type=int, default=None, help="Taille cible (défaut 20, cap à 50% du corpus).")
    args = parser.parse_args(argv)

    # Reproductibilité
    np.random.seed(42)

    # Chargement
    df = _load_inputs()
    df_len = len(df)
    if df_len == 0:
        print("[ERR] Corpus vide après fusion.", file=sys.stderr)
        return 3

    # Choix N (défaut 20, cap 50% corpus)
    N = _decide_N(df_len, args.n)

    # --- Strates contrôlées ---
    sample_idx = set()

    # fc élevés: top10 puis sample 5
    if "fc" in df.columns and df["fc"].notna().sum() >= 10:
        top_fc = df.nlargest(10, "fc")
        sample_idx |= set(top_fc.sample(min(5, len(top_fc)), random_state=42).index)

    # fi élevés: top10 puis sample 5
    if "fi" in df.columns and df["fi"].notna().sum() >= 10:
        top_fi = df.nlargest(10, "fi")
        sample_idx |= set(top_fi.sample(min(5, len(top_fi)), random_state=43).index)

    # low: simultanément fc & fi en dessous de Q1
    if "fc" in df.columns and "fi" in df.columns:
        q1_fc = df["fc"].quantile(0.25)
        q1_fi = df["fi"].quantile(0.25)
        low = df[(df["fc"] <= q1_fc) & (df["fi"] <= q1_fi)]
        if len(low) >= 5:
            sample_idx |= set(low.sample(5, random_state=44).index)

    # ambiv: simultanément fc & fi au-dessus de Q3 (intensités hautes conjointes)
    if "fc" in df.columns and "fi" in df.columns:
        q3_fc = df["fc"].quantile(0.75)
        q3_fi = df["fi"].quantile(0.75)
        ambiv = df[(df["fc"] >= q3_fc) & (df["fi"] >= q3_fi)]
        if len(ambiv) >= 5:
            sample_idx |= set(ambiv.sample(5, random_state=45).index)

    # Top-up jusqu'à N (sans doublons)
    need = max(0, N - len(sample_idx))
    if need > 0:
        rest = df.drop(index=list(sample_idx)) if len(sample_idx) > 0 else df
        take = min(need, len(rest))
        if take > 0:
            extra = rest.sample(take, random_state=46).index
            sample_idx |= set(extra)

    # Échantillon final trié + doc_id
    sample = df.loc[list(sample_idx)].copy()
    sample = sample.sort_values(["actor_id", "date"]).reset_index(drop=True)
    sample["doc_id"] = [f"DOC_{i:03d}" for i in range(1, len(sample) + 1)]

    # Sorties
    os.makedirs(OUT_DIR, exist_ok=True)
    texts_path = os.path.join(OUT_DIR, "validation_sample_texts.csv")
    tpl_path   = os.path.join(OUT_DIR, "validation_manual_template.csv")

    # Textes annotables
    sample[["doc_id", "actor_id", "date", "url", "text"]].to_csv(
        texts_path, index=False, encoding="utf-8"
    )

    # Template annotateur — RESTAURÉ (comme ta v1)
    tpl = sample[["doc_id", "actor_id", "date", "url"]].copy()
    tpl["annotator"] = ""
    tpl["fc_manual"] = np.nan
    tpl["fi_manual"] = np.nan
    tpl["notes"]     = ""
    tpl.to_csv(tpl_path, index=False, encoding="utf-8")

    # Logs console
    print(f"[OK] Textes  : {texts_path} (écriture)")
    print(f"[OK] Template: {tpl_path} (écriture)")
    print(f"[INFO] Échantillon: {len(sample)} docs (N demandé/capé = {N}/{len(sample)})")
    print("[HINT] Uploadez ces 2 fichiers sur OSF (A3 et A5) avec le même préfixe de version.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
