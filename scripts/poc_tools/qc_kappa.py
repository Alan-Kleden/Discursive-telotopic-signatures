import csv
from pathlib import Path

def load(path):
    d={}
    with Path(path).open(encoding="utf-8") as f:
        r=csv.DictReader(f)
        for row in r:
            rid=row["id"]
            telos=(row.get("telos_central","") or "").strip().lower()
            fc=1 if (row.get("Fc_items","") or "").strip() else 0
            fi=1 if (row.get("Fi_items","") or "").strip() else 0
            d[rid]=(telos,fc,fi)
    return d

A=load(r".\artifacts\phase1\outputs\qc_A.csv")
B=load(r".\artifacts\phase1\outputs\qc_B.csv")
ids=sorted(set(A)&set(B))

def kappa_binary(xs, ys):
    n=len(xs)
    if n==0: return 0.0
    agree=sum(int(x==y) for x,y in zip(xs,ys))
    p0=agree/n
    px=sum(xs)/n; py=sum(ys)/n
    pe=px*py+(1-px)*(1-py)
    return (p0-pe)/(1-pe) if pe<1 else 1.0

k_fc=kappa_binary([A[i][1] for i in ids],[B[i][1] for i in ids])
k_fi=kappa_binary([A[i][2] for i in ids],[B[i][2] for i in ids])
tel_agree=sum(int(A[i][0]==B[i][0] and A[i][0]!="") for i in ids)/len(ids) if ids else 0.0

print(f"Kappa_Fc={k_fc:.2f} Kappa_Fi={k_fi:.2f} Telos_exact_agree={tel_agree:.2f}")
