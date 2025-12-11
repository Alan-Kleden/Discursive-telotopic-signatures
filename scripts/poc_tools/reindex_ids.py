import sys, pandas as pd

inp, outp = sys.argv[1], sys.argv[2]
df = pd.read_csv(inp, dtype=str).fillna("")
df["id"] = [f"C{i:03d}" for i in range(1, len(df)+1)]
df.to_csv(outp, index=False, encoding="utf-8")
print(f"OK -> {outp} ({len(df)} rows, ids C001..C{len(df):03d})")
