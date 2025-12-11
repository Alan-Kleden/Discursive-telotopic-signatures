# Data Collection Playbook (EN-first, pragmatique)

## 1) Choix stratégique (PoC)
- **EN‑only** pour livrer vite ; FR gardé comme extension ultérieure.  
- **Option A (recommandée)** : démarrer avec un **corpus pré‑structuré** (US Congress / UK Hansard) pour éviter les erreurs d’API.  
- **Option B** : scraping léger sites officiels (GOV.UK, partis UK, White House/Agences US).

## 2) Schéma cible (CSV/Parquet)
Colonnes cibles (à produire avant features) :
```
actor_id | country | domain_id | period | date | url | language | text | tokens
```
- `language` = "EN" (PoC).  
- `tokens` = longueur (pré‑filtre : ≥ 800 tokens recommandé).

## 3) Option A — Datasets prêts à l’emploi
- **US Congress speeches** (archives publiques académiques/Kaggle/OTA).  
- **UK Hansard** (Oxford Text Archive / API Hansard).  
Procédure :
1) Télécharger CSV/JSON, conserver champs (date, speaker, party, text, url).  
2) **Affecter `actor_id` et `domain_id`** via règles de mots‑clés (ex. climate, immigration, security, health).  
3) Filtrer longueur, puis **exporter vers `data/raw/*.csv`** → `merge_corpus.py`.

## 4) Option B — Scraping léger (pistes robustes)
### 4.1 GOV.UK (finder HTML ou Search API)
- L’API JSON peut renvoyer **422** selon les paramètres ; deux solutions :
  - **Finder HTML :** paginer l’archive (plus tolérant) et extraire titres/liens/dates/texte.
  - **Search API (vérifiée)** : paramétrer prudemment, puis élargir si 0 résultat.
- **Conseils** :
  - User‑Agent explicite (`requests` headers) ;  
  - Réduire *content types* puis élargir ;  
  - Tester d’abord **sur 12 mois** entiers (ex. 2021‑01‑01 → 2021‑12‑31).

### 4.2 Parties UK / White House (HTML simple)
- **Labour** (`/press/`), **Conservatives** (`/news`) : pages structurées, pagination simple.
- **White House** (briefing‑room) : structure stable, article full‑text disponible.

## 5) Gouvernance collecte
- **Journaliser** le nombre d’items vus/filtrés/sauvegardés.  
- **Interdits** : réseaux sociaux, blogs personnels, contenus payants/ToS restrictives.  
- **Conformité PoC** : viser **≥ 8 docs & ≥ 8k tokens** par cellule (acteur×domaine×période).

## 6) Débogage rapide — cas connus
- **GOV.UK 422** : revoir paramètres (organisation slug, content types, dates), ajouter `User-Agent`, ou basculer en **finder HTML**.  
- **Congress.gov 403** : clé absente/quotas ; sinon choisir un **dataset alternatif**.  
- **CSV vides** : vérifier filtres (dates, longueur ≥ 800), puis élargir **période** et **limit**.

## 7) Commandes utiles (PowerShell)
```powershell
# Préparer env
$env:PYTHONPATH = ".;$(Resolve-Path 04_Code_Scripts)"
$env:CONATIVE_LEXICON_PATH = "07_Config\lexicons\lexicon_conative_v1.clean.csv"

# (Option) Clé API
$env:CONGRESS_API_KEY = "<VOTRE_CLE_API>"

# Merger tous les CSV valides présents dans data/raw/
python -m collect.merge_corpus artifacts/real/corpus_final.parquet

# Lancer features doc sur corpus réel
.	asks.ps1 real:features:doc:v2
```

## 8) After‑merge sanity check
Après `merge_corpus.py` :
- Vérifier **nb docs** et **répartition** par acteur/domaine/période.  
- Si une cellule < 8 docs, compléter ou ajuster affectation de domaine (mots‑clés).

## 9) Étapes suivantes (quand le corpus tient)
1) `all:v2` (ou séquence `features → baselines → hypotheses → report`) sur *corpus_final*.  
2) Inspecter **ΔAUC (H1)** et **GLM/LRT (H3)**.  
3) Affiner lexique (poids/patterns), puis relancer.
