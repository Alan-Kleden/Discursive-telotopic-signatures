from __future__ import annotations
import pandas as pd
from pathlib import Path
from features.windows import sliding_windows
from features.shocks import load_shocks, tag_windows_with_shocks

def main():
    in_path = Path("artifacts/mock/features_doc.parquet")
    if not in_path.exists():
        raise SystemExit("Run features_doc first (run_mock_pipeline.py)")
    df = pd.read_parquet(in_path)

    win = sliding_windows(df, window_days=30, step_days=7)

    # tag shocks (mock ou réel, même schéma)
    shocks = load_shocks("data/mock/shocks.csv")
    win = tag_windows_with_shocks(win, shocks)

    out_path = Path("artifacts/mock/features_win.parquet")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    win.to_parquet(out_path, index=False)
    print(f"OK: {out_path}")

if __name__ == "__main__":
    main()
