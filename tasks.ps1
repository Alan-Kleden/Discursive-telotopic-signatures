param([string]$Task="help")
$env:PYTHONPATH = "."

switch ($Task) {
  "mock:gen"     { python .\04_Code_Scripts\mock_data.py }
  "features:doc" { python .\04_Code_Scripts\run_mock_pipeline.py }
  "features:win" { python .\04_Code_Scripts\run_windows.py }
  "test"         { python -m pytest -q }
  "baselines"    { python .\04_Code_Scripts\run_baselines.py }
  "hypotheses"   { python .\04_Code_Scripts\run_hypotheses.py }

  default {
    Write-Host "Tasks:" -ForegroundColor Cyan
    "  mock:gen      -> export data/mock/*"
    "  features:doc  -> artifacts/mock/features_doc.parquet"
    "  features:win  -> artifacts/mock/features_win.parquet"
    "  test          -> run pytest"
  }
}
