# 04_Code_Scripts/run_real_features.py
import sys
import pandas as pd
from features.fc_fi_v3 import apply_fc_fi_v3

def main(inp: str, outp: str):
    df = pd.read_parquet(inp)
    # IMPORTANT : apply_fc_fi_v3 ne supporte pas actor_col/domain_col/etc. dans ta version.
    # Utilise simplement les noms par défaut attendus par la fonction : 'text', 'language', 'date'.
    out = apply_fc_fi_v3(df)  # pas de kwargs non prévus
    out.to_parquet(outp, index=False)
    print(f"OK: {outp} ({len(out)} docs)")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python 04_Code_Scripts/run_real_features.py <in_parquet> <out_parquet>", file=sys.stderr)
        sys.exit(2)
    main(sys.argv[1], sys.argv[2])
