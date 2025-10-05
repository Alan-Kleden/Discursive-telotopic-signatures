Param(
  [Parameter(Position=0)]
  [string]$Task = "help"
)

# --- util ---
function Invoke-Step {
  param(
    [string]$Title,
    [scriptblock]$Action
  )
  Write-Host $Title
  & $Action
  if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

# S'assure que PYTHONPATH pointe sur 04_Code_Scripts (utile partout)
try {
  $global:PYTHONPATH = ".;$(Resolve-Path 04_Code_Scripts)"
} catch {
  $global:PYTHONPATH = "."
}
$env:PYTHONPATH = $global:PYTHONPATH

switch ($Task) {

  # =======================
  # AIDE
  # =======================
  "help" {
    Write-Host "Tasks:"
    Write-Host "  mock:gen                        -> export data/mock/*"
    Write-Host "  features:doc                    -> artifacts/mock/features_doc.parquet (Fc/Fi v1)"
    Write-Host "  features:doc:v2                 -> artifacts/mock/features_doc.parquet (Fc/Fi v2+v3 spaCy)"
    Write-Host "  features:win                    -> artifacts/mock/features_win.parquet (+shocks lags 0/7/14)"
    Write-Host "  baselines                       -> artifacts/mock/scores_baselines.json"
    Write-Host "  hypotheses                      -> artifacts/mock/hypotheses.json"
    Write-Host "  report                          -> artifacts/mock/report_poc.md"
    Write-Host "  all                             -> mock → features v1 → win → baselines → hypotheses → report"
    Write-Host "  all:v2                          -> mock → features v2 → win → baselines → hypotheses → report"
    Write-Host "  test                            -> pytest (short suite)"
    Write-Host ""
    Write-Host "  real:collect:govuk:homeoffice:T1 -> GOV.UK Home Office (2021-01-01..2022-12-31)"
    Write-Host "  real:collect:govuk:homeoffice:T2 -> GOV.UK Home Office (2023-01-01..2024-06-30)"
    Write-Host "  real:collect:govuk:mod:T1        -> GOV.UK Ministry of Defence (2021-01-01..2022-12-31)"
    Write-Host "  real:collect:govuk:mod:T2        -> GOV.UK Ministry of Defence (2023-01-01..2024-06-30)"
    Write-Host "  real:collect:congress:dems:T1    -> US House Democrats (Congress.gov) T1"
    Write-Host "  real:collect:congress:dems:T2    -> US House Democrats (Congress.gov) T2"
    Write-Host "  real:collect:congress:reps:T1    -> US House Republicans (Congress.gov) T1"
    Write-Host "  real:collect:congress:reps:T2    -> US House Republicans (Congress.gov) T2"
    Write-Host "  real:corpus:merge                -> data/raw/*.csv → artifacts/real/corpus_final.parquet"
    Write-Host "  real:features:doc:v2             -> features v2+v3 sur corpus réel"
    Write-Host "  real:all                         -> enchaîne collecte → merge → features"
    break
  }

  # =======================
  # MOCK / POC
  # =======================
  "mock:gen" {
    if (Test-Path "04_Code_Scripts/export_mock.py") {
      Invoke-Step "04_Code_Scripts/export_mock.py" { python 04_Code_Scripts/export_mock.py }
    } else {
      Write-Warning "export_mock.py introuvable — on continue (les étapes suivantes peuvent générer leurs propres données mock)."
    }
    break
  }

  "features:doc" {
    Invoke-Step "04_Code_Scripts/run_mock_pipeline.py (v1)" { python 04_Code_Scripts/run_mock_pipeline.py --mode v1 }
    break
  }

  "features:doc:v2" {
    Invoke-Step "04_Code_Scripts/run_mock_pipeline.py (v2+v3 spaCy)" { python 04_Code_Scripts/run_mock_pipeline.py --mode v2 }
    break
  }

  "features:win" {
    Invoke-Step "04_Code_Scripts/run_windows.py" { python 04_Code_Scripts/run_windows.py }
    break
  }

  "baselines" {
    Invoke-Step "04_Code_Scripts/run_baselines.py" { python 04_Code_Scripts/run_baselines.py }
    break
  }

  "hypotheses" {
    Invoke-Step "04_Code_Scripts/run_hypotheses.py" { python 04_Code_Scripts/run_hypotheses.py }
    break
  }

  "report" {
    if (Test-Path "04_Code_Scripts/report_poc.py") {
      Invoke-Step "04_Code_Scripts/report_poc.py" { python 04_Code_Scripts/report_poc.py }
    } else {
      Write-Warning "report_poc.py introuvable — étape ignorée."
    }
    break
  }

  "all" {
    .\tasks.ps1 mock:gen
    .\tasks.ps1 features:doc
    .\tasks.ps1 features:win
    .\tasks.ps1 baselines
    .\tasks.ps1 hypotheses
    .\tasks.ps1 report
    break
  }

  "all:v2" {
    .\tasks.ps1 mock:gen
    .\tasks.ps1 features:doc:v2
    .\tasks.ps1 features:win
    .\tasks.ps1 baselines
    .\tasks.ps1 hypotheses
    .\tasks.ps1 report
    break
  }

  "test" {
    if (Test-Path ".\.venv\Scripts\pytest.exe") {
      Invoke-Step "pytest (venv)" { .\.venv\Scripts\pytest.exe -q tests -k "smoke or quick" }
    } else {
      Invoke-Step "pytest (global)" { pytest -q tests -k "smoke or quick" }
    }
    break
  }

  # =======================
  # REAL / COLLECTE
  # =======================

  # GOV.UK — Home Office
  "real:collect:govuk:homeoffice:T1" {
    New-Item -ItemType Directory -Force -Path data\raw | Out-Null
    Invoke-Step "collect.scrape_govuk HomeOffice T1" {
      python -m collect.scrape_govuk UK_HomeOffice UK home-office T1 2021-01-01 2022-12-31 60
    }
    break
  }
  "real:collect:govuk:homeoffice:T2" {
    New-Item -ItemType Directory -Force -Path data\raw | Out-Null
    Invoke-Step "collect.scrape_govuk HomeOffice T2" {
      python -m collect.scrape_govuk UK_HomeOffice UK home-office T2 2023-01-01 2024-06-30 60
    }
    break
  }

  # GOV.UK — Ministry of Defence
  "real:collect:govuk:mod:T1" {
    New-Item -ItemType Directory -Force -Path data\raw | Out-Null
    Invoke-Step "collect.scrape_govuk MoD T1" {
      python -m collect.scrape_govuk UK_MoD UK ministry-of-defence T1 2021-01-01 2022-12-31 60
    }
    break
  }
  "real:collect:govuk:mod:T2" {
    New-Item -ItemType Directory -Force -Path data\raw | Out-Null
    Invoke-Step "collect.scrape_govuk MoD T2" {
      python -m collect.scrape_govuk UK_MoD UK ministry-of-defence T2 2023-01-01 2024-06-30 60
    }
    break
  }

  # Congress.gov — DEMS / REPS (House)
  "real:collect:congress:dems:T1" {
    if (-not $env:CONGRESS_API_KEY) { Write-Error 'CONGRESS_API_KEY non défini. Exemple: $env:CONGRESS_API_KEY = "VOTRE_CLE"'; exit 1 }
    New-Item -ItemType Directory -Force -Path data\raw | Out-Null
    Invoke-Step "collect.fetch_congress DEMS T1" {
      python -m collect.fetch_congress house Democratic 2021-01-01 2022-12-31 120 T1 data/raw/US_Dems_House_T1.csv
    }
    break
  }
  "real:collect:congress:dems:T2" {
    if (-not $env:CONGRESS_API_KEY) { Write-Error 'CONGRESS_API_KEY non défini. Exemple: $env:CONGRESS_API_KEY = "VOTRE_CLE"'; exit 1 }
    New-Item -ItemType Directory -Force -Path data\raw | Out-Null
    Invoke-Step "collect.fetch_congress DEMS T2" {
      python -m collect.fetch_congress house Democratic 2023-01-01 2024-06-30 120 T2 data/raw/US_Dems_House_T2.csv
    }
    break
  }
  "real:collect:congress:reps:T1" {
    if (-not $env:CONGRESS_API_KEY) { Write-Error 'CONGRESS_API_KEY non défini. Exemple: $env:CONGRESS_API_KEY = "VOTRE_CLE"'; exit 1 }
    New-Item -ItemType Directory -Force -Path data\raw | Out-Null
    Invoke-Step "collect.fetch_congress REPS T1" {
      python -m collect.fetch_congress house Republican 2021-01-01 2022-12-31 120 T1 data/raw/US_Reps_House_T1.csv
    }
    break
  }
  "real:collect:congress:reps:T2" {
    if (-not $env:CONGRESS_API_KEY) { Write-Error 'CONGRESS_API_KEY non défini. Exemple: $env:CONGRESS_API_KEY = "VOTRE_CLE"'; exit 1 }
    New-Item -ItemType Directory -Force -Path data\raw | Out-Null
    Invoke-Step "collect.fetch_congress REPS T2" {
      python -m collect.fetch_congress house Republican 2023-01-01 2024-06-30 120 T2 data/raw/US_Reps_House_T2.csv
    }
    break
  }

  # Fusion CSV -> Parquet
  "real:corpus:merge" {
    New-Item -ItemType Directory -Force -Path artifacts\real | Out-Null
    Invoke-Step "04_Code_Scripts/collect/merge_corpus.py" {
      python -m collect.merge_corpus artifacts/real/corpus_final.parquet
    }
    break
  }

  # Features v2+v3 sur corpus réel
  "real:features:doc:v2" {
    if (-not (Test-Path "artifacts/real/corpus_final.parquet")) {
      Write-Host "Need artifacts/real/corpus_final.parquet — run: real:corpus:merge"
      break
    }
    if (-not $env:CONATIVE_LEXICON_PATH) {
      Write-Warning 'CONATIVE_LEXICON_PATH non défini. Exemple : $env:CONATIVE_LEXICON_PATH = "07_Config\lexicons\lexicon_conative_v1.clean.csv"'
    }
    Invoke-Step "04_Code_Scripts/run_real_features.py" {
      python 04_Code_Scripts/run_real_features.py artifacts/real/corpus_final.parquet artifacts/real/features_doc.parquet
    }
    break
  }

  # Enchaînement complet réel
  "real:all" {
    .\tasks.ps1 real:collect:govuk:homeoffice:T1
    .\tasks.ps1 real:collect:govuk:homeoffice:T2
    .\tasks.ps1 real:collect:govuk:mod:T1
    .\tasks.ps1 real:collect:govuk:mod:T2
    .\tasks.ps1 real:collect:congress:dems:T1
    .\tasks.ps1 real:collect:congress:dems:T2
    .\tasks.ps1 real:collect:congress:reps:T1
    .\tasks.ps1 real:collect:congress:reps:T2
    .\tasks.ps1 real:corpus:merge
    .\tasks.ps1 real:features:doc:v2
    break
  }

  default {
    Write-Warning "Unknown task: $Task"
    .\tasks.ps1 help
    break
  }
}
