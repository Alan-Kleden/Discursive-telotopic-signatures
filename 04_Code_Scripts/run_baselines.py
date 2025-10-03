from __future__ import annotations
import json, pandas as pd
from pathlib import Path
from models.h1_h2 import style_only_auc, party_line_auc, telotopic_linear_auc

def main():
    f = Path("artifacts/mock/features_doc.parquet")
    if not f.exists():
        raise SystemExit("Run features first (run_mock_pipeline.py)")
    df = pd.read_parquet(f)

    # fabriquer une 'stance' mock si absente : pro (1) si fc >= fi
    if "stance" not in df.columns:
        df = df.assign(stance=(df["fc_mean"] >= df["fi_mean"]).astype(int))

    scores = {
        "AUC_telotopic_linear": float(telotopic_linear_auc(df)),
        "AUC_style_only": float(style_only_auc(df)),
        "AUC_party_line": float(party_line_auc(df)),
    }
    Path("artifacts/mock").mkdir(parents=True, exist_ok=True)
    out = Path("artifacts/mock/scores_baselines.json")
    out.write_text(json.dumps(scores, indent=2))
    print("Wrote", out)
    print(json.dumps(scores, indent=2))

if __name__ == "__main__":
    main()
