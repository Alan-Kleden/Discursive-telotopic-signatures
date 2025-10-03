This document explains how to recreate the software environment for the project Discursive Telotopic Signatures so results are reproducible.

1) Recommended layout
/Signatures_Telotopiques_POC
├─ 06_Environnement/
│  ├─ requirements.txt
│  ├─ requirements-lock.txt
│  ├─ environment.yml
│  └─ README_Environnement.md   ← ce fichier
└─ ...
2) Two reproducible paths

A. Conda-based (recommended: simple & robust)

1) Create the environment
    conda env create -f 06_Environnement\environment.yml
    conda activate telotopic-311

2) Download language resources (spaCy + NLTK)
    python -m spacy download fr_core_news_lg
    python -m spacy download en_core_web_lg
    python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"

Notes

environment.yml pins Python 3.11 and installs packages from requirements.txt.

This setup is CPU-only (PyTorch from the CPU wheel index). If you need CUDA, adjust PyTorch separately.

B. Pip “lock” (exact snapshot, for CI/servers without Conda)

1. Create a clean virtual environment
python -m venv .venv
.\.venv\Scripts\activate
python -m pip install --upgrade pip

2. Install from the lock file
pip install -r 06_Environnement\requirements-lock.txt

3. Download language resources (same as above)

3) Quick verification
python -c "import importlib.metadata as m; \
print('torch',m.version('torch'), \
'| transformers',m.version('transformers'), \
'| tokenizers',m.version('tokenizers'), \
'| sentence-transformers',m.version('sentence-transformers'), \
'| spacy-transformers',m.version('spacy-transformers'))"

python -c "import spacy; spacy.load('fr_core_news_lg'); print('spaCy FR OK')"
python -c "import spacy; spacy.load('en_core_web_lg'); print('spaCy EN OK')"

python -c "import torch; print('torch cuda available:', torch.cuda.is_available())"
Expected (example)
transformers 4.35.2, tokenizers 0.15.2, spacy-transformers 1.3.5, and torch cuda available: False (CPU-only default).

4) Updating the lock (optional, controlled)

requirements-lock.txt is produced with pip-tools and freezes all transitive dependencies.

Regenerate from requirements.txt:
# backup (optional)
Copy-Item 06_Environnement\requirements-lock.txt 06_Environnement\requirements-lock.backup.txt -ErrorAction SilentlyContinue

# install pip-tools
python -m pip install -U pip-tools

# compile the lock file
Copy-Item 06_Environnement\requirements.txt 06_Environnement\requirements.in -Force
pip-compile 06_Environnement\requirements.in --output-file 06_Environnement\requirements-lock.txt
Run these commands inside the active project environment (e.g., conda activate telotopic-311).
Avoid having another venv active at the same time (no (.venv_old) in your shell prompt).

5) Tips & common gotchas

Always install using the Python from the active environment:
python -m pip install -r 06_Environnement\requirements.txt
* If spacy_transformers raises ModuleNotFoundError: spacy_alignments, install:
python -m pip install spacy-alignments==0.9.0
* FutureWarning about torch.utils._pytree is harmless for this workflow.

* For Jupyter, launch from the active env:
jupyter lab

6) PyTorch variants (optional)

CPU (default in requirements.txt)

--extra-index-url https://download.pytorch.org/whl/cpu
torch==2.7.1+cpu
CUDA GPU (if needed; outside the CPU replication scope)

Replace the torch==... line with a CUDA build that matches your driver.

Remove the CPU --extra-index-url line if pointing to CUDA wheels.