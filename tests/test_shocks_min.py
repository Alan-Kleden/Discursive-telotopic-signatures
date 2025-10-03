import sys, pathlib, pandas as pd
sys.path.insert(0, str(pathlib.Path("04_Code_Scripts").resolve()))
from features.shocks import load_shocks, tag_windows_with_shocks
from features.windows import sliding_windows

def test_shocks_alignment_basic():
    docs = pd.read_parquet("data/mock/docs.parquet")
    # fabriquer un n_tel minimal si besoin : ici on vérifie juste la mécanique
    docs = docs.assign(n_tel=0.5, ambivalence_flag=0)
    win = sliding_windows(docs, 30, 7)
    shocks = load_shocks("data/mock/shocks.csv")
    tagged = tag_windows_with_shocks(win, shocks)
    assert {"n_shocks","has_shock"} <= set(tagged.columns)
    # au moins un window par domaine doit toucher un shock
    assert (tagged.groupby("domain_id")["has_shock"].max() >= 1).all()
