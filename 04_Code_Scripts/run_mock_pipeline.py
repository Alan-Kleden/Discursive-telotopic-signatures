# 04_Code_Scripts/run_mock_pipeline.py
from __future__ import annotations
import os
from pathlib import Path
import pandas as pd

from features.fc_fi_v3 import apply_fc_fi_v3, _precheck_or_fail

def main():
    _precheck_or_fail()

    in_path = Path("data/mock/docs.parquet")
    if not in_path.exists():
        raise FileNotFoundError(f"Need {in_path} — run mock:gen first.")
    df = pd.read_parquet(in_path)

    # Columns in mock: text lives in 'text'; language optional ('lang')
    text_col = "text" if "text" in df.columns else df.select_dtypes(include="object").columns[0]
    lang_col = "lang" if "lang" in df.columns else None
    # If you have an alignment feature already computed elsewhere, put its column name here
    alignment_col = "alignment" if "alignment" in df.columns else None

    out = apply_fc_fi_v3(
        df,
        text_col=text_col,
        lang_col=lang_col,
        alignment_col=alignment_col,
        lexicon_path=os.environ.get("CONATIVE_LEXICON_PATH") or "01_Protocoles/lexicon_conative_v1.csv",
    )

    # For compatibility with downstream windows/baselines, keep a simple n_tel placeholder
    # (you can later plug the full N_tel formula if needed)
    if "len_tokens" not in out.columns:
        out["len_tokens"] = out[text_col].fillna("").str.split().map(len)
    out["n_tel"] = out["beta"]  # simple stand-in so windows can aggregate

    out_path = Path("artifacts/mock/features_doc.parquet")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out.to_parquet(out_path, index=False)
    print(f"OK: {out_path} (mode=v2+v3)")

if __name__ == "__main__":
    main()
