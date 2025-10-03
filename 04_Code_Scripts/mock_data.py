# mock_data.py — génération d’un corpus synthétique cohérent (FR/EN)
from __future__ import annotations
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from utils.seed import seed_all
from utils.io import ensure_dir, write_csv, write_parquet

DOMAINS = ["climate", "security"]
LANGS = {"A": "fr", "B": "en"}  # A* acteurs FR, B* acteurs EN

# Lexiques simples pro/anti par domaine (détectables)
LEXICON = {
    "climate": {
        "pro":  ["transition", "renewables", "green", "énergétique", "solaire", "éolien"],
        "anti": ["coal", "fossil", "subsidies", "charbon", "pétrole", "gaz"]
    },
    "security": {
        "pro":  ["safety", "border", "security", "contrôles", "police", "protéger"],
        "anti": ["crime", "threat", "risque", "violence", "trafic"]
    }
}

def _sample_text(domain: str, pro: bool, lang: str, rng: np.random.Generator) -> str:
    lex = LEXICON[domain]["pro" if pro else "anti"]
    boiler_fr = "Nous " + ("accélérons la " if domain=="climate" else "renforçons la ")
    boiler_en = "We " + ("accelerate the " if domain=="climate" else "strengthen the ")
    boiler = boiler_fr if lang=="fr" else boiler_en
    tokens = rng.choice(lex, size=rng.integers(2, 4), replace=True).tolist()
    filler = " ".join(tokens)
    return f"{boiler}{domain} {filler}."

def generate_mock_corpus(n_actors: int = 6, n_docs: int = 120, seed: int = 1337):
    """
    - Acteurs A1..A{n/2} (FR) et B1..B{n/2} (EN)
    - 2 domaines, 120 docs répartis 60/60, déséquilibres par acteur
    - 10 'shocks' datés répartis, pour fenêtrage
    - Teloi: 1 par acteur et domaine (mots-clés pro)
    """
    seed_all(seed)
    rng = np.random.default_rng(seed)
    # acteurs
    nA = n_actors // 2
    actors = []
    for i in range(1, nA+1):
        actors.append((f"A{i}", f"Actor A{i}", "FR", "fr"))
    for i in range(1, nA+1):
        actors.append((f"B{i}", f"Actor B{i}", "EN", "en"))
    actors_df = pd.DataFrame(actors, columns=["actor_id", "actor_name", "country", "language"])

    # timeline T1/T2
    start = datetime(2024, 1, 1)
    dates = [start + timedelta(days=int(x)) for x in np.linspace(0, 300, n_docs)]
    domains = np.where(rng.random(n_docs) < 0.5, "climate", "security")
    # répartition par acteur
    actor_ids = rng.choice(actors_df["actor_id"], size=n_docs, p=None)
    # stance dominante par acteur/domaine (pour Party-line)
    actor_pref = {a: {d: (rng.random() < 0.6) for d in DOMAINS} for a in actors_df["actor_id"]}

    rows = []
    for i in range(n_docs):
        actor = actor_ids[i]
        lang = "fr" if actor.startswith("A") else "en"
        dom = domains[i]
        pro = actor_pref[actor][dom] if rng.random() < 0.7 else not actor_pref[actor][dom]
        text = _sample_text(dom, pro, lang, rng)
        rows.append((actor, dom, dates[i].date().isoformat(), text, lang))
    docs_df = pd.DataFrame(rows, columns=["actor_id","domain_id","date","text","language"])

    # teloi (mots pro du domaine)
    teloi = {}
    for a in actors_df["actor_id"]:
        teloi[a] = {d: LEXICON[d]["pro"][:3] for d in DOMAINS}

    # shocks (5 par domaine)
    shocks = []
    for d in DOMAINS:
        for k in range(5):
            day = start + timedelta(days=int(rng.uniform(10, 290)))
            shocks.append((f"{d}_S{k+1}", d, day.date().isoformat(), f"{d}_shock_{k+1}", f"Event {k+1} in {d}"))
    shocks_df = pd.DataFrame(shocks, columns=["shock_id","domain_id","date","label","description"])

    return actors_df, docs_df, teloi, shocks_df

def export_mock(root: str = "data/mock"):
    actors_df, docs_df, teloi, shocks_df = generate_mock_corpus()
    ensure_dir(root)
    write_csv(actors_df, f"{root}/actor_roster.csv")
    write_parquet(docs_df, f"{root}/docs.parquet")
    write_csv(shocks_df, f"{root}/shocks.csv")
    # teloi en json simple
    import json, pathlib
    pathlib.Path(root).mkdir(parents=True, exist_ok=True)
    with open(f"{root}/teloi.json","w", encoding="utf-8") as f:
        json.dump(teloi, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    export_mock()
    print("Mock exported to data/mock/")
