import json, pandas as pd
from pathlib import Path

def test_mock_files_exist():
    root = Path("data/mock")
    assert (root / "actor_roster.csv").exists()
    assert (root / "docs.parquet").exists()
    assert (root / "shocks.csv").exists()
    assert (root / "teloi.json").exists()

def test_mock_schemas():
    actors = pd.read_csv("data/mock/actor_roster.csv")
    docs   = pd.read_parquet("data/mock/docs.parquet")
    shocks = pd.read_csv("data/mock/shocks.csv")
    with open("data/mock/teloi.json","r",encoding="utf-8") as f:
        teloi = json.load(f)

    assert {"actor_id","actor_name","country","language"} <= set(actors.columns)
    assert {"actor_id","domain_id","date","text","language"} <= set(docs.columns)
    assert {"shock_id","domain_id","date","label","description"} <= set(shocks.columns)
    any_actor = next(iter(teloi))
    assert isinstance(teloi[any_actor], dict)
