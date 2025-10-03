param([string]$Task="help")
$env:PYTHONPATH = "."

switch ($Task) {
  # ================= MOCK =================
  "mock:gen"        { python .\04_Code_Scripts\mock_data.py }
  "features:doc"    { Remove-Item -ErrorAction SilentlyContinue .\artifacts\mock\features_doc.parquet; $env:FCFI_MODE="v1"; python .\04_Code_Scripts\run_mock_pipeline.py }
  "features:doc:v2" { Remove-Item -ErrorAction SilentlyContinue .\artifacts\mock\features_doc.parquet; $env:FCFI_MODE="v2"; python .\04_Code_Scripts\run_mock_pipeline.py }
  "features:win"    { python .\04_Code_Scripts\run_windows.py }
  "baselines"       { python .\04_Code_Scripts\run_baselines.py }
  "hypotheses"      { python .\04_Code_Scripts\run_hypotheses.py }
  "report"          { python .\04_Code_Scripts\report_poc.py }

  "all" {
    .\tasks.ps1 mock:gen
    .\tasks.ps1 features:doc
    .\tasks.ps1 features:win
    .\tasks.ps1 baselines
    .\tasks.ps1 hypotheses
    .\tasks.ps1 report
  }

  "all:v2" {
    .\tasks.ps1 mock:gen
    .\tasks.ps1 features:doc:v2
    .\tasks.ps1 features:win
    .\tasks.ps1 baselines
    .\tasks.ps1 hypotheses
    .\tasks.ps1 report
  }

  "features:doc:v3" {
    $env:PYTHONPATH="."
    $env:FCFI_MODE="v3"
    python .\04_Code_Scripts\run_mock_pipeline.py
  }


  # ================= REAL (optionnel, si tu l'as) =================
  "real:features:doc"    { Remove-Item -ErrorAction SilentlyContinue .\artifacts\real\features_doc.parquet; $env:FCFI_MODE="v1"; python .\04_Code_Scripts\run_real_etl_to_features.py }
  "real:features:doc:v2" { Remove-Item -ErrorAction SilentlyContinue .\artifacts\real\features_doc.parquet; $env:FCFI_MODE="v2"; python .\04_Code_Scripts\run_real_etl_to_features.py }

  default {
    Write-Host "Tasks:" -ForegroundColor Cyan
    "  mock:gen        -> export data/mock/*"
    "  features:doc    -> artifacts/mock/features_doc.parquet (Fc/Fi v1)"
    "  features:doc:v2 -> artifacts/mock/features_doc.parquet (Fc/Fi v2 spaCy+TF-IDF)"
    "  features:win    -> artifacts/mock/features_win.parquet (+shocks lags 0/7/14)"
    "  baselines       -> artifacts/mock/scores_baselines.json"
    "  hypotheses      -> artifacts/mock/hypotheses.json"
    "  report          -> artifacts/mock/report_poc.md"
    "  all             -> mock → features v1 → win → baselines → hypotheses → report"
    "  all:v2          -> mock → features v2 → win → baselines → hypotheses → report"
    "  real:features:doc     -> ETL réel → artifacts/real/features_doc.parquet (v1)"
    "  real:features:doc:v2  -> ETL réel → artifacts/real/features_doc.parquet (v2)"
  }
}
