import sys, pathlib, json, pandas as pd
sys.path.insert(0, str(pathlib.Path("04_Code_Scripts").resolve()))

from features.fc_fi import apply_fc_fi
from features.theta import apply_theta
from features.n_tel import apply_n_tel
from features.windows import sliding_windows

LEXICON = {
    "climate": {"pro":["transition","renewables","green","énergétique","solaire","éolien"],
                "anti":["coal","fossil","subsidies","charbon","pétrole","gaz"]},
    "security":{"pro":["safety","border","security","contrôles","police","protéger"],
                "anti":["crime","threat","risque","violence","trafic"]},
}

def test_windows_ok():
    docs = pd.read_parquet("data/mock/docs.parquet")
    with open("data/mock/teloi.json","r",encoding="utf-8") as f:
        teloi = json.load(f)

    df = apply_fc_fi(docs, LEXICON)
    df = apply_theta(df, teloi)
    df = apply_n_tel(df)

    win = sliding_windows(df, window_days=30, step_days=7)
    assert {"actor_id","domain_id","win_start","win_end","n_docs","n_tel_mean","ambivalence_rate","Delta_n_tel"} <= set(win.columns)
    assert not win.empty
    assert win.duplicated(subset=["actor_id","domain_id","win_start"]).sum() == 0
