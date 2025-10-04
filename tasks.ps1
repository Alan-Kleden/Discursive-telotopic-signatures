# tasks.ps1  — reset version
# Usage: .\tasks.ps1 [task]
# Examples:
#   .\tasks.ps1
#   .\tasks.ps1 help
#   .\tasks.ps1 all:v2

[CmdletBinding()]
param(
  [Parameter(Position=0,Mandatory=$false)]
  [string]$Task = "help"
)

$ErrorActionPreference = "Stop"

# -- Root folder & env ---------------------------------------------------------
$ROOT = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ROOT

# PYTHONPATH : racine + 04_Code_Scripts
$env:PYTHONPATH = ".;$(Resolve-Path 04_Code_Scripts)"

function Show-Tasks {
  @"
Tasks:
  mock:gen        -> export data/mock/*
  features:doc    -> artifacts/mock/features_doc.parquet (Fc/Fi v1)
  features:doc:v2 -> artifacts/mock/features_doc.parquet (Fc/Fi v2+v3 spaCy)
  features:win    -> artifacts/mock/features_win.parquet (+shocks lags 0/7/14)
  baselines       -> artifacts/mock/scores_baselines.json
  hypotheses      -> artifacts/mock/hypotheses.json
  report          -> artifacts/mock/report_poc.md
  all             -> mock → features v1 → win → baselines → hypotheses → report
  all:v2          -> mock → features v2 → win → baselines → hypotheses → report
  test            -> pytest (short suite)
"@ | Write-Host
}

function RunPy([string]$script) {
  Write-Host $script -ForegroundColor DarkCyan
  & python $script
  if ($LASTEXITCODE -ne 0) {
    throw "Python exited with code $LASTEXITCODE for $script"
  }
}


switch ($Task) {
  "help" { Show-Tasks; break }

  "mock:gen" {
    # si tu as un script dédié; sinon retire cette ligne
    RunPy "04_Code_Scripts/export_mock.py"
    break
  }

  "features:doc" {
    RunPy "04_Code_Scripts/run_mock_pipeline.py"
    break
  }

  "features:doc:v2" {
    # Le script interne détecte v2+v3 et affiche (mode=v2+v3)
    RunPy "04_Code_Scripts/run_mock_pipeline.py"
    break
  }

  "features:win" {
    RunPy "04_Code_Scripts/run_windows.py"
    break
  }

  "baselines" {
    RunPy "04_Code_Scripts/run_baselines.py"
    break
  }

  "hypotheses" {
    RunPy "04_Code_Scripts/run_hypotheses.py"
    break
  }

  "report" {
    RunPy "04_Code_Scripts/report_poc.py"
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
    Write-Host "pytest -q" -ForegroundColor DarkCyan
    & python -m pytest -q
    break
  }

  default {
    Write-Warning "Unknown task: $Task"
    Show-Tasks
  }
}
