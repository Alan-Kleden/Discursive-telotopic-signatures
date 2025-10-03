# Discursive Telotopic Signatures (PoC) â€” Data off-drive (H:)
Data directories live outside the synced drive:
- RAW         : H:\Data\Telotopic\00_Raw
- Intermediate: H:\Data\Telotopic\10_Intermediate
- Processed   : H:\Data\Telotopic\20_Processed

Paths configured in 07_Config\paths.yml. Do not store RAW under the synced drive.

# Tokenize a short sentence (FR/EN)
python -c "import spacy; print(spacy.load('fr_core_news_lg')('La transition climatique avance.')._.has_vector)"
python -c "import spacy; print(spacy.load('en_core_web_lg')('Security policy is evolving.')._.has_vector)"

# Sentence-Transformers round-trip (ensures torch+transformers interplay is OK)
python -c "from sentence_transformers import SentenceTransformer; m=SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2'); import numpy as np; v=m.encode(['hello','world']); print(v.shape, float(np.linalg.norm(v)))"
