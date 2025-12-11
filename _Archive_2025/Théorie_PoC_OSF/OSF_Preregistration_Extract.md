# OSF preregistration — extrait consolidé (PoC “Théorie de l’axiodynamique”)

## 1) Objet scientifique
**But général.** Détecter et mesurer, dans des textes politiques, deux axes conatifs :  
- **Fc (push)** : obligation / incitation / accélération de l’action.  
- **Fi (inhibit)** : blocage / frein / opposition.

**Idée centrale.** Les signatures conatives (Fc/Fi) expliquent mieux certains phénomènes (classement partisan, variation autour d’événements) que des marqueurs de style généraux.

## 2) Hypothèses confirmatoires (PoC)
- **H1 – ΔAUC.** Un classifieur télotopique (features Fc/Fi) surpasse un classifieur “style-only” (ΔAUC > 0).  
  *Évaluation :* AUC_telotopic_linear vs AUC_style_only (+ “party line” baseline) sur documents tenus hors‑échantillon.
- **H3 – Dynamique autour de chocs.** L’intensité conative varie de manière significative dans des fenêtres ±30 jours autour d’événements exogènes (“shocks”).  
  *Évaluation :* GLM + Likelihood Ratio Test (LRT) sur séries temporelles agrégées.

*(H2 était réservé aux comparaisons inter-domaines ; non requis pour le PoC minimal.)*

## 3) Données — contraintes OSF
- **Langue :** FR/EN (ou mixte). Le pipeline gère FR/EN — **lexique bilingue** requis dans la version générale.  
- **Inclusion :** textes longs institutionnels/partisans/ONG ; documents ≥ 800 tokens recommandés pour le PoC (≥ 500 tokens minimum).  
- **Granularité confirmatoire minimale :** par **acteur × domaine × période** : **≥ 8 documents et ≥ 8 000 tokens**.
- **Périodes :** T1 = 2021‑01‑01 → 2022‑12‑31 ; T2 = 2023‑01‑01 → 2024‑06‑30 (réglables).  
- **Shocks (exemples) :** 3/domaines (p.ex. climat : COP26, IRA‑US, Net Zero‑UK).

## 4) Modèle opératoire
- **Lexique conatif** (CSV) : couples *(lemme/locution, type push|inhibit, poids [0..1])* + (optionnel) POS et regexp robustes.  
- **NLP (spaCy)** : `fr_core_news_lg` (FR), `en_core_web_lg` (EN) pour lemmatisation/POS et appariement du lexique.  
- **Features** :  
  - **Fc/Fi v3** (strict, fail‑fast sur dépendances) : somme pondérée des occurrences (et/ou normalisation par longueur).  
  - **θ (style)** : marqueurs stylistiques (baseline).  
  - **Windows** : agrégation ±30j autour des shocks.
- **Évaluation** : AUC (ROC), ΔAUC (H1), GLM/LRT (H3).

## 5) Qualité & gouvernance
- **Fail‑fast** au chargement des dépendances et du lexique (pas de fallback silencieux).  
- **Tolérance par document** : en cas d’échec d’analyse d’un doc, on logue et **le batch continue**.  
- **Outils QA** : `verify_lexicon.py` (validation dure) ; `repair_lexicon.py` (nettoyage lignes vides, BOM, types, bornes).

## 6) Artefacts attendus
- **Parquet features (doc‑level)** : `features_doc.parquet` (inclut Fc, Fi, θ, langue, métadonnées).  
- **Parquet windows** : `features_win.parquet` (agrégations autour de chocs).  
- **Scores baselines** : `scores_baselines.json`.  
- **Résultats hypothèses** : `hypotheses.json`.  
- **Rapport** : `report_poc.md` (résumé H1/H3 + graphiques).

## 7) Décisions pour le PoC
- **PoC EN‑only** possible : conserver le lexique bilingue *ou* dériver un `lexicon_conative_en.csv` allégé pour clarté.  
- Respecter les contraintes OSF (≥ 8 docs / ≥ 8k tokens par cellule).  
- Démarrage rapide recommandé avec un **corpus pré‑structuré EN** (US Congress / UK Hansard) pour éviter les frictions d’API.
