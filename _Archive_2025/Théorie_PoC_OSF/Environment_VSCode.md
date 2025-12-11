# Environnement VS Code — organisation & exécution (PoC)

## 1) Arborescence minimale
```
Signatures_Telotopiques_POC/
├── 01_Protocoles/
│   └── Appendix_A4_beta_modality_clarification_v1.1.md
├── 04_Code_Scripts/
│   ├── features/
│   │   ├── conative.py
│   │   ├── fc_fi_v3.py
│   │   ├── theta.py
│   │   ├── windows.py
│   │   └── shocks.py
│   ├── collect/
│   │   ├── scrape_govuk.py
│   │   ├── fetch_congress.py
│   │   └── merge_corpus.py
│   ├── run_mock_pipeline.py
│   ├── run_baselines.py
│   ├── run_hypotheses.py
│   ├── run_windows.py
│   └── report_poc.py
├── 06_Environnement/
│   └── requirements.in
├── 07_Config/
│   └── lexicons/
│       ├── lexicon_conative_v1.csv
│       └── lexicon_conative_v1.clean.csv   # (validé)
├── artifacts/
│   ├── mock/
│   └── real/
├── data/
│   └── raw/
├── tasks.ps1
└── verify_lexicon.py / repair_lexicon.py
```

## 2) Environnement Python
- **Python** : 3.11 (env `telotopic-311`), VS Code + extension Python.
- **Dépendances clés** : `spacy`, `fr_core_news_lg`, `en_core_web_lg`, `pandas`, `numpy`, `pyarrow`, `scikit-learn`,
  `statsmodels`, `transformers`, `requests`, `beautifulsoup4`.
- **Installation modèles spaCy** :
  ```powershell
  python -m spacy download fr_core_news_lg
  python -m spacy download en_core_web_lg
  ```

## 3) Variables d’environnement (PowerShell)
```powershell
$env:PYTHONPATH = ".;$(Resolve-Path 04_Code_Scripts)"
$env:CONATIVE_LEXICON_PATH = "07_Config\lexicons\lexicon_conative_v1.clean.csv"
# (Optionnel) pour Congress.gov si utilisé
$env:CONGRESS_API_KEY = "<VOTRE_CLE_API>"
```

## 4) Tâches (tasks.ps1)
```text
help                              # liste
all:v2                            # mock: gen → features v2+v3 → baselines → hypotheses → report
features:doc:v2                   # features doc (mock)
baselines | hypotheses | report   # étapes unitaires
real:collect:...                  # collecteurs (si utilisés)
real:corpus:merge                 # fusion data/raw/*.csv → artifacts/real/corpus_final.parquet
real:features:doc:v2              # features sur corpus réel (parquet)
test                              # mini-suite pytest (si présente)
```
> Astuce : `.	asks.ps1 help` doit s’exécuter sans erreur.

## 5) Lancement — Mock (de bout en bout)
```powershell
$env:PYTHONPATH = ".;$(Resolve-Path 04_Code_Scripts)"
$env:CONATIVE_LEXICON_PATH = "07_Config\lexicons\lexicon_conative_v1.clean.csv"
.	asks.ps1 all:v2
.	asks.ps1 test
```
Sorties : `artifacts/mock/*.parquet`, `scores_baselines.json`, `hypotheses.json`, `report_poc.md`.

## 6) Lancement — Réel (quand des CSV existent)
```powershell
# prérequis : des CSV non vides dans data/raw/
.	asks.ps1 real:corpus:merge
.	asks.ps1 real:features:doc:v2
```
Sorties : `artifacts/real/features_doc.parquet` (puis baselines/hypotheses/report si nécessaire).

## 7) Lexique — hygiène & validation
```powershell
python verify_lexicon.py "07_Config\lexicons\lexicon_conative_v1.clean.csv" --strict
```
Règles : pas de lignes vides, en‑tête conforme, langue ∈ {EN,FR}, type ∈ {push,inhibit}, poids ∈ [0,1].

## 8) Fichiers critiques (à emporter vers le nouveau repo)
- `04_Code_Scripts/features/*.py` (surtout `conative.py`, `fc_fi_v3.py`)
- `04_Code_Scripts/run_*` (+ `report_poc.py`)
- `verify_lexicon.py`, `repair_lexicon.py`
- `tasks.ps1` (version stable)
- `07_Config/lexicons/lexicon_conative_v1.clean.csv`
- `01_Protocoles/Appendix_A4_beta_modality_clarification_v1.1.md`
