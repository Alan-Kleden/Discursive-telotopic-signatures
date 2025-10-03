# Politique d’usage des données lourdes (Colab & Desktop)

## Objectif
Permettre l’exécution de notebooks Colab avec des **données lourdes** sans polluer le dépôt Git, via un **parking temporaire sur Google Drive**.

## Emplacements
- **Parking Colab (hors Git)** : `Mon Drive/02_Donnees_Corpus_LOURD/`
  - Arborescence : `00_Raw/`, `10_Intermediate/`, `20_Processed/`
  - Contient un `README.md` opérationnel (règles & statut de run)
- **Repo Git (léger)** : `Signatures_Telotopiques_POC/02_Donnees_Corpus/`
  - Ne contient **pas** de lourds : uniquement échantillons, `Extracted_Teloi/` (gelés), et ce document.

## Résolution de chemins dans les notebooks
Le code doit :
1. Pointer par défaut sur les chemins du repo (échantillons) ;
2. **Basculer automatiquement** vers `02_Donnees_Corpus_LOURD` s’il existe sur Drive :

```python
import os

PROJECT_NAME = "Signatures_Telotopiques_POC"
DRIVE_ROOT = "/content/drive/MyDrive"
PROJECT_ROOT = f"{DRIVE_ROOT}/{PROJECT_NAME}"
HEAVY_ROOT = f"{DRIVE_ROOT}/02_Donnees_Corpus_LOURD"

paths = {
    "raw_dir":         os.path.join(PROJECT_ROOT, "02_Donnees_Corpus", "00_Raw"),
    "intermediate_dir":os.path.join(PROJECT_ROOT, "02_Donnees_Corpus", "10_Intermediate"),
    "processed_dir":   os.path.join(PROJECT_ROOT, "02_Donnees_Corpus", "20_Processed"),
    "results_dir":     os.path.join(PROJECT_ROOT, "05_Resultats"),
}

if os.path.isdir(HEAVY_ROOT):
    for key, sub in {
        "raw_dir": "00_Raw",
        "intermediate_dir": "10_Intermediate",
        "processed_dir": "20_Processed",
    }.items():
        candidate = os.path.join(HEAVY_ROOT, sub)
        if os.path.isdir(candidate):
            paths[key] = candidate

print("Chemins actifs:", paths)
