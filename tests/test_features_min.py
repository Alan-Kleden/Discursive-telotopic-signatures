import sys, pathlib, json, pandas as pd
# rendre 04_Code_Scripts importable
sys.path.insert(0, str(pathlib.Path("04_Code_Scripts").resolve()))

from features.fc_fi import apply_fc_fi
from features.theta import apply_theta
from features.n_tel import apply_n_tel

LEXICON = {
    "climate": {"pro":["transition","renewables","green","énergétique","solaire","éolien"],
                "anti":["coal","fossil","subsidies","charbon","pétrole","gaz"]},
    "security":{"pro":["safety","border","security","contrôles","police","protéger"],
                "anti":["crime","threat","risque","violence","trafic"]},
}

def test_fc_fi_theta_n_tel_basic():
    docs = pd.read_parquet("data/mock/docs.parquet")
    with open("data/mock/teloi.json","r",encoding="utf-8") as f:
        teloi = json.load(f)

    df = apply_fc_fi(docs, LEXICON)
    df = apply_theta(df, teloi)
    df = apply_n_tel(df)

    assert df["fc_mean"].between(0,1).all()
    assert df["fi_mean"].between(0,1).all()
    assert df["cos_theta"].between(-1,1).all()
    assert df["n_tel"].between(0,1).all()

    probe = df.head(10)
    assert ((probe["fc_mean"] >= probe["fi_mean"]) == (probe["cos_theta"] >= 0)).all()
