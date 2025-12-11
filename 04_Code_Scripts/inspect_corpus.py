import pandas as pd

# Charger corpus
corpus = pd.read_parquet('artifacts/real/corpus_final.parquet')

# 1. Structure générale
print("=" * 60)
print("STRUCTURE DU CORPUS")
print("=" * 60)
print(corpus.info())
print()

# 2. Colonnes disponibles
print("=" * 60)
print("COLONNES")
print("=" * 60)
print(corpus.columns.tolist())
print()

# 3. Exemple d'un document complet
print("=" * 60)
print("EXEMPLE DOCUMENT 0")
print("=" * 60)
doc0 = corpus.iloc[0].to_dict()
for key, value in doc0.items():
    if isinstance(value, str) and len(value) > 200:
        print(f"{key}: {value[:200]}... [truncated, total length: {len(value)}]")
    else:
        print(f"{key}: {value}")
print()

# 4. Statistiques texte
print("=" * 60)
print("STATISTIQUES")
print("=" * 60)
if 'text' in corpus.columns:
    text_col = 'text'
elif 'content' in corpus.columns:
    text_col = 'content'
elif 'full_text' in corpus.columns:
    text_col = 'full_text'
else:
    text_col = [c for c in corpus.columns if 'text' in c.lower()][0]

print(f"Colonne texte détectée: {text_col}")
print(f"Nombre de documents: {len(corpus)}")
print(f"Longueur moyenne (chars): {corpus[text_col].str.len().mean():.0f}")
print(f"Longueur min: {corpus[text_col].str.len().min()}")
print(f"Longueur max: {corpus[text_col].str.len().max()}")

# 5. Distribution par acteur
print()
print("Distribution par acteur:")
if 'actor_id' in corpus.columns:
    print(corpus['actor_id'].value_counts())
elif 'actor_name' in corpus.columns:
    print(corpus['actor_name'].value_counts())
else:
    print("Colonne acteur non trouvée")