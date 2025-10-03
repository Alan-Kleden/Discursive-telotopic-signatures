from __future__ import annotations
from pathlib import Path
import pandas as pd

from features.windows import sliding_windows
from features.shocks import load_shocks, tag_windows_with_shocks


def main() -> None:
    in_path = Path("artifacts/mock/features_doc.parquet")
    if not in_path.exists():
        raise SystemExit("Run features first (run_mock_pipeline.py)")

    df = pd.read_parquet(in_path)
    win = sliding_windows(df, window_days=30, step_days=7)

    # Tag des chocs (lags 0, 7, 14 jours)
    shocks = load_shocks("data/mock/shocks.csv")
    win = tag_windows_with_shocks(win, shocks, lags=(0, 7, 14))

    out_path = Path("artifacts/mock/features_win.parquet")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    win.to_parquet(out_path, index=False)
    print(f"OK: {out_path.as_posix()}")


if __name__ == "__main__":
    main()
