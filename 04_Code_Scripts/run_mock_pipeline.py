from utils.seed import seed_all
from utils.io import write_parquet
from mock_data import export_mock
from features.fc_fi import apply_fc_fi
from features.theta import apply_theta
from features.n_tel import apply_n_tel
import json, pandas as pd

def main():
    seed_all(1337)
    export_mock()  # data/mock/*
    docs = pd.read_parquet("data/mock/docs.parquet")
    with open("data/mock/teloi.json","r",encoding="utf-8") as f:
        teloi = json.load(f)
    LEXICON = {
        "climate": {"pro":["transition","renewables","green","énergétique","solaire","éolien"],
                    "anti":["coal","fossil","subsidies","charbon","pétrole","gaz"]},
        "security":{"pro":["safety","border","security","contrôles","police","protéger"],
                    "anti":["crime","threat","risque","violence","trafic"]},
    }
    df = apply_fc_fi(docs, LEXICON)
    df = apply_theta(df, teloi)
    df = apply_n_tel(df)
    write_parquet(df, "artifacts/mock/features_doc.parquet")
    print("OK: artifacts/mock/features_doc.parquet")

if __name__ == "__main__":
    main()
