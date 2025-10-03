# Discursive Telotopic Signatures (Preregistered PoC)

This repository hosts the preregistered proof-of-concept on **discursive telotopic signatures** in public institutional texts.  
The OSF preregistration is finalized; this repo contains the **computational environment** files and (as they become available) the code and configuration to reproduce the pipeline.

## Project status

- ✅ OSF preregistration submitted and frozen
- ✅ Reproducible environment files available
- ⏳ Code and frozen inputs (Appendices, roster, shocks) will be mirrored here as they become public in the OSF project

## Repository layout (relevant here)
/06_Environnement/
requirements.txt # concise, pinned deps for Python 3.11
requirements-lock.txt # pip-compile lock (exact snapshot)
environment.yml # Conda recipe (installs requirements.txt)
README_Environnement.md # step-by-step instructions (Conda & pip-lock)


## How to recreate the environment

**Recommended (Conda):**
```bash
conda env create -f 06_Environnement/environment.yml
conda activate telotopic-311
python -m spacy download fr_core_news_lg
python -m spacy download en_core_web_lg
python -c "import nltk; import nltk; nltk.download('punkt'); nltk.download('stopwords')"
```
**Alternative (pip exact lock, no Conda):**
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

python -m pip install -U pip
python -m pip install -r 06_Environnement/requirements-lock.txt
python -m spacy download fr_core_news_lg
python -m spacy download en_core_web_lg
python -c "import nltk; import nltk; nltk.download('punkt'); nltk.download('stopwords')"

For detailed environment notes and rationale, see
06_Environnement/README_Environnement.md


Reproducibility notes

Python: 3.11

CPU-only baseline (PyTorch CPU wheels). Switch to CUDA if needed by adjusting Torch install.

Exact package set captured in requirements-lock.txt (generated via pip-compile).

Contact

Lead contact: Alan Kleden — ak@alankleden.com
 / alan.kleden@gmail.com

 
