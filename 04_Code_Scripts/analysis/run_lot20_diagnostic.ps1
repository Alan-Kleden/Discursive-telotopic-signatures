param(
  [string]$Csv      = "07_Config/validation_sample_texts.csv",
  [string]$OutDir   = "artifacts/diagnostics/lot20",
  [int]   $MinWords = 120,
  [string]$CondaEnv = "telotopic-311"
)

# --- Paths ---
# $scriptDir = ...\04_Code_Scripts\analysis
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
# $codeDir   = ...\04_Code_Scripts
$codeDir   = Split-Path -Parent $scriptDir
# $repoRoot  = repo root
$repoRoot  = Split-Path -Parent $codeDir

Set-Location $repoRoot
$env:PYTHONPATH = (Resolve-Path ".\04_Code_Scripts")

# (optionnel) activer conda si nécessaire
try { conda activate $CondaEnv | Out-Null } catch {}

Write-Host "Repo root  : $repoRoot"
Write-Host "PYTHONPATH : $env:PYTHONPATH"
Write-Host "Running diagnostic on $Csv ..."

$py = Join-Path $repoRoot "04_Code_Scripts\analysis\lot20_diagnostic.py"
if (-not (Test-Path $py)) {
  Write-Error "Introuvable: $py"
  exit 2
}

python $py --csv $Csv --outdir $OutDir --min_words $MinWords
