# -*- coding: utf-8 -*-
from __future__ import annotations
import sys, glob, os, logging
import pandas as pd
from .common import df_schema

logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")

def main(out_parquet: str):
    files = sorted(glob.glob("data/raw/*.csv"))
    if not files:
        raise RuntimeError("No input CSVs in data/raw/*.csv")
    logging.info("Merging %d CSV files", len(files))

    dfs = []
    for f in files:
        try:
            df = pd.read_csv(f, encoding="utf-8")
            if df.empty:
                logging.warning("Skip %s: empty", f)
                continue
            # Normalisation colonnes
            need = df_schema()
            for c in need:
                if c not in df.columns:
                    df[c] = ""  # remplir colonnes manquantes
            df = df[need]
            dfs.append(df)
        except Exception as e:
            logging.warning("Skip %s: %s", f, e)

    if not dfs:
        raise RuntimeError("No usable CSVs in data/raw/*.csv")

    full = pd.concat(dfs, ignore_index=True)

    # nettoyage minimal
    full["actor_id"]  = full["actor_id"].fillna("").astype(str)
    full["domain_id"] = full["domain_id"].fillna("").astype(str)
    full["period"]    = full["period"].fillna("").astype(str)
    full["date"]      = full["date"].fillna("").astype(str)
    full["url"]       = full["url"].fillna("").astype(str)
    full["language"]  = full["language"].fillna("en").astype(str)
    full["text"]      = full["text"].fillna("").astype(str)
    full["tokens"]    = pd.to_numeric(full["tokens"], errors="coerce").fillna(0).astype(int)

    # drop lignes clairement invalides
    full = full.dropna(subset=["text", "actor_id", "period", "date", "url"])

    # === DÉDUPLICATION ===
    # 1) sur l’empreinte logique (acteur + date + url)
    before = len(full)
    full = full.drop_duplicates(subset=["actor_id", "date", "url"], keep="first")
    after1 = len(full)
    # 2) filet de sécurité sur doublon exact
    full = full.drop_duplicates(keep="first")
    after2 = len(full)
    logging.info("Dedup: %d → %d (keys) → %d (exact)",
                 before, after1, after2)

    # vérifs schéma
    missing = [c for c in df_schema() if c not in full.columns]
    if missing:
        raise ValueError(f"Missing columns in merged corpus: {missing}")

    # export
    os.makedirs(os.path.dirname(out_parquet), exist_ok=True)
    full.to_parquet(out_parquet, index=False)
    print(f"OK parquet: {out_parquet} ({len(full)} docs)")

if __name__ == "__main__":
    # EX: python -m collect.merge_corpus artifacts/real/corpus_final.parquet
    _, outp = sys.argv
    main(outp)
