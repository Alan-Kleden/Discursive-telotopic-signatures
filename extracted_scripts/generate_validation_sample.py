# scripts/generate_validation_sample.py
# -*- coding: utf-8 -*-
import os, numpy as np, pandas as pd

ROOT = os.getcwd()
CORPUS_PQ   = os.path.join("artifacts","real","corpus_final.parquet")
FEATURES_PQ = os.path.join("artifacts","real","features_doc.parquet")
OUT_DIR     = os.path.join("07_Config")

def main():
    np.random.seed(42)
    if not os.path.exists(CORPUS_PQ):
        raise FileNotFoundError(CORPUS_PQ)
    corpus = pd.read_parquet(CORPUS_PQ)

    if os.path.exists(FEATURES_PQ):
        feats = pd.read_parquet(FEATURES_PQ)
        keep = ["actor_id","date","url","fc","fi"]
        feats = feats[[c for c in keep if c in feats.columns]].drop_duplicates()
        df = corpus.merge(feats, on=["actor_id","date","url"], how="left")
    else:
        df = corpus.copy()
        df["fc"] = 0.0; df["fi"] = 0.0

    sample_idx = set()
    if df["fc"].notna().sum() >= 10:
        sample_idx |= set(df.nlargest(10, 'fc').sample(min(5, len(df)), random_state=42).index)
    if df["fi"].notna().sum() >= 10:
        sample_idx |= set(df.nlargest(10, 'fi').sample(min(5, len(df)), random_state=43).index)
    low_mask = (df["fc"] <= df["fc"].quantile(0.25)) & (df["fi"] <= df["fi"].quantile(0.25))
    low = df[low_mask]
    if len(low) >= 5:
        sample_idx |= set(low.sample(5, random_state=44).index)
    ambiv = df[(df["fc"] >= df["fc"].quantile(0.75)) & (df["fi"] >= df["fi"].quantile(0.75))]
    if len(ambiv) >= 5:
        sample_idx |= set(ambiv.sample(5, random_state=45).index)

    need = 20 - len(sample_idx)
    if need > 0:
        rest = df.drop(index=list(sample_idx))
        sample_idx |= set(rest.sample(min(need, len(rest)), random_state=46).index)

    sample = df.loc[list(sample_idx)].copy()
    sample = sample.sort_values(["actor_id","date"]).reset_index(drop=True)
    sample["doc_id"] = [f"DOC_{i:03d}" for i in range(1, len(sample)+1)]

    os.makedirs(OUT_DIR, exist_ok=True)
    sample[["doc_id","actor_id","date","url","text"]].to_csv(
        os.path.join(OUT_DIR,"validation_sample_texts.csv"), index=False, encoding="utf-8"
    )
    tpl = sample[["doc_id","actor_id","date","url"]].copy()
    tpl["annotator"] = ""
    tpl["fc_manual"] = np.nan
    tpl["fi_manual"] = np.nan
    tpl["notes"] = ""
    tpl.to_csv(os.path.join(OUT_DIR,"validation_manual_template.csv"), index=False, encoding="utf-8")

    print(f"[OK] Template: 07_Config/validation_manual_template.csv (à remplir)")
    print(f"[OK] Textes  : 07_Config/validation_sample_texts.csv (lecture)")
    print(f"[INFO] Échantillon: {len(sample)} docs")

if __name__ == "__main__":
    main()

