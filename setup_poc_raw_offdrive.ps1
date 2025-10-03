# ===========================
# Setup POC : 00_Raw, 10_Intermediate, 20_Processed sur H:
# Repo : C:\Users\ojahi\Mon Drive\Signatures_Telotopiques_POC
# ===========================

$RepoRoot = "C:\Users\ojahi\Mon Drive\Signatures_Telotopiques_POC"
$DataRoot = "H:\Data\Telotopic"  # base data folder on H:
$RawRoot  = Join-Path $DataRoot "00_Raw"
$IntRoot  = Join-Path $DataRoot "10_Intermediate"
$ProcRoot = Join-Path $DataRoot "20_Processed"

# -- Vérifs & création des dossiers H: --
foreach ($p in @($DataRoot, $RawRoot, $IntRoot, $ProcRoot)) {
  New-Item -ItemType Directory -Path $p -Force | Out-Null
  New-Item -ItemType File -Path (Join-Path $p ".gitkeep") -Force | Out-Null
}

# -- Dossiers du repo (sans 00_Raw / 10_Intermediate / 20_Processed) --
$Dirs = @(
  "$RepoRoot\01_Protocoles",
  "$RepoRoot\03_Notebooks_Colab",
  "$RepoRoot\04_Code_Scripts\pipelines",
  "$RepoRoot\04_Code_Scripts\baselines",
  "$RepoRoot\04_Code_Scripts\metrics",
  "$RepoRoot\05_Resultats\Tables",
  "$RepoRoot\05_Resultats\Visualisations",
  "$RepoRoot\06_Environnement",
  "$RepoRoot\07_Config\actors_and_shocks",
  "$RepoRoot\tests"
)
foreach ($d in $Dirs) { New-Item -ItemType Directory -Path $d -Force | Out-Null }

# -- README --
$readme = @"
# Discursive Telotopic Signatures (PoC) — Data off-drive (H:)
Data directories live outside the synced drive:
- RAW         : H:\Data\Telotopic\00_Raw
- Intermediate: H:\Data\Telotopic\10_Intermediate
- Processed   : H:\Data\Telotopic\20_Processed

Paths configured in 07_Config\paths.yml. Do not store RAW under the synced drive.
"@
Set-Content -Path "$RepoRoot\README.md" -Value $readme -Encoding UTF8

# -- .gitignore --
$gitignore = @"
# data (generated / heavy)
02_Donnees_Corpus/
*.zip
*.7z

# models & caches
**/checkpoints/
**/cache/
**/.cache/
**/__pycache__/
**/.ipynb_checkpoints/

# environments
.venv/
.env/
conda_env.yml.lock
pip-wheel-metadata/

# OS
.DS_Store
Thumbs.db
"@
Set-Content -Path "$RepoRoot\.gitignore" -Value $gitignore -Encoding UTF8

# -- Placeholders protocole --
Set-Content -Path "$RepoRoot\01_Protocoles\Hypotheses.md" -Value "See OSF preregistration. All hypotheses are directional." -Encoding UTF8
Set-Content -Path "$RepoRoot\01_Protocoles\Log_Decisions.txt" -Value "YYYY-MM-DD | DECISION | Confirmatory vs Exploratory | Rationale" -Encoding UTF8

# -- Config YAMLs : chemins vers H: --
$pathsYml = @"
raw_dir: H:/Data/Telotopic/00_Raw
intermediate_dir: H:/Data/Telotopic/10_Intermediate
processed_dir: H:/Data/Telotopic/20_Processed
results_dir: ../05_Resultats
"@
Set-Content -Path "$RepoRoot\07_Config\paths.yml" -Value $pathsYml -Encoding UTF8

$paramsYml = @"
# Fixed prereg thresholds/weights
similarity_telos_min: 0.65
ambivalence_percentile: 0.70
ambivalence_tau_abs: 0.20
weights_ntel:
  alpha_intensifiers: 0.30
  beta_modality: 0.20
  gamma_tfidf: 0.25
  delta_rhetorical: 0.15
  epsilon_length: 0.10
window_days: 30
window_step_days: 7
"@
Set-Content -Path "$RepoRoot\07_Config\params.yml" -Value $paramsYml -Encoding UTF8

# -- CSV modèles (acteurs & chocs) --
$actorCSV = "actor_id,actor_name,actor_type,domain,has_endogenous_telos,telos_similarity,tokens_T1,docs_T1,months_active_T1,tokens_T2,docs_T2,months_active_T2,include_confirmatory,notes"
Set-Content -Path "$RepoRoot\07_Config\actors_and_shocks\actor_roster.csv" -Value $actorCSV -Encoding UTF8

$shocksCSV = "domain,shock_id,shock_name,shock_date,media_count_7d,inst_action_window_start,inst_action_window_end,qualifies_as_shock,description,source_urls"
Set-Content -Path "$RepoRoot\07_Config\actors_and_shocks\shocks.csv" -Value $shocksCSV -Encoding UTF8

# -- Environnement (templates) --
$reqTxt = @"
python==3.10.*
numpy==1.26.4
pandas==2.2.2
scipy==1.13.1
scikit-learn==1.4.2
statsmodels==0.14.2
matplotlib==3.8.4
tqdm==4.66.4
torch==2.3.0
transformers==4.41.2
sentence-transformers==2.7.0
tokenizers==0.15.2
spacy==3.7.4
spacy-transformers==1.3.5
nltk==3.8.1
emoji==2.12.1
beautifulsoup4==4.12.3
lxml==5.2.1
requests==2.31.0
ruptures==1.1.9
seaborn==0.13.2
jupyterlab==4.2.1
"@
Set-Content -Path "$RepoRoot\06_Environnement\requirements.txt" -Value $reqTxt -Encoding UTF8

$condaYml = @"
name: telotopic-signatures
channels:
  - conda-forge
dependencies:
  - python=3.10
  - pip=24.0
  - numpy=1.26.4
  - pandas=2.2.2
  - scipy=1.13.1
  - scikit-learn=1.4.2
  - statsmodels=0.14.2
  - matplotlib=3.8.4
  - tqdm=4.66.4
  - beautifulsoup4=4.12.3
  - lxml=5.2.1
  - requests=2.31.0
  - ruamel.yaml=0.18.6
  - pip:
      - torch==2.3.0
      - transformers==4.41.2
      - sentence-transformers==2.7.0
      - tokenizers==0.15.2
      - spacy==3.7.4
      - spacy-transformers==1.3.5
      - nltk==3.8.1
      - emoji==2.12.1
      - ruptures==1.1.9
      - seaborn==0.13.2
      - jupyterlab==4.2.1
"@
Set-Content -Path "$RepoRoot\06_Environnement\conda_env.yml" -Value $condaYml -Encoding UTF8

# -- Squelettes code & tests --
Set-Content -Path "$RepoRoot\04_Code_Scripts\pipelines\teloi_matcher.py" -Value "# teloi_matcher: compute theta/N_tel from endogenous telos" -Encoding UTF8
Set-Content -Path "$RepoRoot\04_Code_Scripts\pipelines\axio_features.py" -Value "# axio_features: extract values and Fc/Fi signals" -Encoding UTF8
Set-Content -Path "$RepoRoot\04_Code_Scripts\baselines\bert_stance_model.py" -Value "# baseline: fine-tuned BERT stance classifier" -Encoding UTF8
Set-Content -Path "$RepoRoot\04_Code_Scripts\metrics\dynamics.py" -Value "# metrics for ambivalence & hysteresis" -Encoding UTF8

Set-Content -Path "$RepoRoot\tests\test_teloi_matcher.py" -Value "def test_placeholder(): assert True" -Encoding UTF8
Set-Content -Path "$RepoRoot\tests\test_axio_features.py" -Value "def test_placeholder(): assert True" -Encoding UTF8
Set-Content -Path "$RepoRoot\tests\test_metrics.py" -Value "def test_placeholder(): assert True" -Encoding UTF8

Write-Host "✅ Création terminée."
Write-Host "   Repo       : $RepoRoot"
Write-Host "   RAW        : $RawRoot"
Write-Host "   Intermediate: $IntRoot"
Write-Host "   Processed  : $ProcRoot"
