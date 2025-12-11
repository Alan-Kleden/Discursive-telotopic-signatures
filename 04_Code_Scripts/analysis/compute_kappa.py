# 04_Code_Scripts/analysis/compute_kappa.py

import pandas as pd
import numpy as np
from sklearn.metrics import cohen_kappa_score
from scipy.stats import spearmanr

# Charger annotations
annotations = pd.read_csv('07_Config/validation/annotation_template_v2.csv')

# Convertir en numérique
annotations['annotator_1_fc'] = pd.to_numeric(annotations['annotator_1_fc'], errors='coerce')
annotations['annotator_1_fi'] = pd.to_numeric(annotations['annotator_1_fi'], errors='coerce')
annotations['annotator_2_fc'] = pd.to_numeric(annotations['annotator_2_fc'], errors='coerce')
annotations['annotator_2_fi'] = pd.to_numeric(annotations['annotator_2_fi'], errors='coerce')

# Supprimer lignes incomplètes
complete = annotations.dropna(subset=['annotator_1_fc', 'annotator_1_fi', 
                                      'annotator_2_fc', 'annotator_2_fi'])

print(f"Documents annotés : {len(complete)}")

# Kappa pour FC
kappa_fc = cohen_kappa_score(
    complete['annotator_1_fc'].round(),  # Arrondi pour kappa
    complete['annotator_2_fc'].round(),
    weights='linear'  # Weighted kappa (mieux pour échelles ordinales)
)

# Kappa pour FI
kappa_fi = cohen_kappa_score(
    complete['annotator_1_fi'].round(),
    complete['annotator_2_fi'].round(),
    weights='linear'
)

# Spearman (corrélation continue)
spearman_fc, p_fc = spearmanr(complete['annotator_1_fc'], complete['annotator_2_fc'])
spearman_fi, p_fi = spearmanr(complete['annotator_1_fi'], complete['annotator_2_fi'])

print("\n" + "="*60)
print("INTER-ANNOTATOR AGREEMENT")
print("="*60)
print(f"Cohen's Kappa (FC) : {kappa_fc:.3f}")
print(f"Cohen's Kappa (FI) : {kappa_fi:.3f}")
print(f"\nSpearman rho (FC)  : {spearman_fc:.3f} (p={p_fc:.4f})")
print(f"Spearman rho (FI)  : {spearman_fi:.3f} (p={p_fi:.4f})")

# Gate ≥ 0.70
print("\n" + "="*60)
print("GATE CHECK (κ ≥ 0.70)")
print("="*60)

if kappa_fc >= 0.70 and kappa_fi >= 0.70:
    print("✅ PASSED - Inter-annotator agreement sufficient")
else:
    print("❌ FAILED - Need reconciliation or additional training")
    if kappa_fc < 0.70:
        print(f"   FC below threshold: {kappa_fc:.3f} < 0.70")
    if kappa_fi < 0.70:
        print(f"   FI below threshold: {kappa_fi:.3f} < 0.70")

# Consensus scores (moyenne)
complete['consensus_fc'] = (complete['annotator_1_fc'] + complete['annotator_2_fc']) / 2
complete['consensus_fi'] = (complete['annotator_1_fi'] + complete['annotator_2_fi']) / 2

# Sauvegarder consensus
complete.to_csv('07_Config/validation/annotations_with_consensus.csv', index=False)
print(f"\n✓ Consensus saved: annotations_with_consensus.csv")