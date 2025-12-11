# === audit_poc.ps1 ===
param(
  [string]$RepoRoot = "G:\Mon Drive\Signatures_Telotopiques_POC"
)

function Test-File { param([string]$p) if (Test-Path $p) { "OK" } else { "MISSING" } }
function Try-Run { param([ScriptBlock]$cmd) try { & $cmd 2>$null } catch { $null } }

$now = Get-Date
$reportDir  = Join-Path $RepoRoot "artifacts\phase1\reports"
New-Item -ItemType Directory -Force -Path $reportDir | Out-Null
$reportPath = Join-Path $reportDir ("audit_{0:yyyyMMdd_HHmmss}.json" -f $now)

# 0) Repo
if (-not (Test-Path $RepoRoot)) { Write-Error "Repo introuvable: $RepoRoot"; exit 1 }
Set-Location $RepoRoot

# 1) Git
$gitInside  = Try-Run { git rev-parse --is-inside-work-tree }
$gitBranch  = Try-Run { git rev-parse --abbrev-ref HEAD }
$gitCommit  = Try-Run { git rev-parse --short HEAD }
$gitStatus  = Try-Run { git status --porcelain=v2 -b }
$gitRemoteV = Try-Run { git remote -v }
$gitLFS     = Try-Run { git lfs env }

# 2) Arborescence
$dirsExpected = @(
  ".\artifacts\phase1\archive",
  ".\artifacts\phase1\inputs",
  ".\artifacts\phase1\outputs",
  ".\artifacts\phase1\reports",
  ".\scripts\poc_tools",
  ".\.vscode"
)
$dirsCheck = foreach ($d in $dirsExpected) {
  [pscustomobject]@{ path = $d; status = if (Test-Path $d) {"OK"} else {"MISSING"} }
}

# 3) Fichiers clés
$filesExpected = @(
  ".\artifacts\phase1\inputs\candidates_25.csv",
  ".\artifacts\phase1\inputs\lot20_final.csv",
  ".\artifacts\phase1\inputs\guide_v1.3_addendum.txt",
  ".\scripts\poc_tools\validate_lot.py",
  ".\scripts\poc_tools\qc_kappa.py",
  ".\.vscode\tasks.json"
)
$filesCheck = foreach ($f in $filesExpected) {
  [pscustomobject]@{ path = $f; status = Test-File $f }
}

# 4) VS Code settings
$vscodeSettingsPath = ".\.vscode\settings.json"
$pyPathFromVSCode = $null
if (Test-Path $vscodeSettingsPath) {
  try {
    $set = Get-Content $vscodeSettingsPath -Raw | ConvertFrom-Json
    $pyPathFromVSCode = $set."python.defaultInterpreterPath"
  } catch { }
}
$pyPathExists = if ($pyPathFromVSCode) { Test-File $pyPathFromVSCode } else { "UNSET" }

# 5) Runtime (pas d'usage de 'py')
$pythonV   = Try-Run { python --version }
$condaInfo = Try-Run { conda info --envs }
$condaEnv  = "MISSING"
if ($condaInfo) {
  $lines = $condaInfo -split "`n"
  $match = $lines | Where-Object { $_ -match "telotopic-311" }
  if ($match) { $condaEnv = "FOUND" }
}

# 6) Issues
$issues = @()
if ($gitInside -ne "true") { $issues += "Git: pas dans un dépôt." }
if (-not $gitBranch)       { $issues += "Git: branche introuvable." }
if (-not $gitCommit)       { $issues += "Git: commit introuvable." }

$missingDirs  = $dirsCheck  | Where-Object {$_.status -eq "MISSING"} | Select-Object -ExpandProperty path
if ($missingDirs) { $issues += ("Dossiers manquants: " + ($missingDirs -join ", ")) }

$missingFiles = $filesCheck | Where-Object {$_.status -eq "MISSING"} | Select-Object -ExpandProperty path
if ($missingFiles) { $issues += ("Fichiers manquants: " + ($missingFiles -join ", ")) }

if ($pyPathFromVSCode -and $pyPathExists -eq "MISSING") { $issues += "VS Code: interpreter path défini mais introuvable." }
if (-not $pythonV)   { $issues += "Python: exécutable non détecté dans le PATH." }
if (-not $condaInfo) { $issues += "Conda: non détecté." }
elseif ($condaEnv -ne "FOUND") { $issues += "Conda: environnement 'telotopic-311' non listé." }

# 7) Normalisation pour JSON
$pythonVersionOut = if ($pythonV -ne $null -and $pythonV -ne "") { $pythonV } else { "N/A" }
$condaEnvOut      = $condaEnv
$condaInfoOut     = $condaInfo

# 8) Rapport JSON
$report = [pscustomobject]@{
  timestamp = $now.ToString("o")
  repo_root = $RepoRoot
  git = [pscustomobject]@{
    inside_repo = $gitInside
    branch      = $gitBranch
    commit      = $gitCommit
    remote_v    = $gitRemoteV
    status_raw  = $gitStatus
    lfs_env     = if ($gitLFS) {"OK"} else {"N/A"}
  }
  structure = [pscustomobject]@{
    directories = $dirsCheck
    files       = $filesCheck
  }
  vscode = [pscustomobject]@{
    settings_path                 = (Test-Path $vscodeSettingsPath)
    python_defaultInterpreterPath = $pyPathFromVSCode
    python_path_exists            = $pyPathExists
  }
  runtime = [pscustomobject]@{
    python_version = $pythonVersionOut
    conda_envs_raw = $condaInfoOut
    telotopic_311  = $condaEnvOut
  }
  issues = $issues
}

$report | ConvertTo-Json -Depth 6 | Out-File -FilePath $reportPath -Encoding utf8 -Force

# 9) Résumé console
Write-Host "=== AUDIT POC ==="
Write-Host ("Repo       : {0}" -f $RepoRoot)
Write-Host ("Git        : branch={0} commit={1}" -f $gitBranch, $gitCommit)

$condaOut = if ($condaInfo) { "OK" } else { "N/A" }
$pyOut    = $pythonVersionOut
$vsPath   = if ($pyPathFromVSCode) { $pyPathFromVSCode } else { "UNSET" }

Write-Host ("Python     : {0}" -f $pyOut)
Write-Host ("Conda envs : {0}" -f $condaOut)
Write-Host ("VSCode Py  : {0} ({1})" -f $vsPath, $pyPathExists)

$dirsOk  = ($dirsCheck  | Where-Object {$_.status -eq "OK"} | Measure-Object).Count
$filesOk = ($filesCheck | Where-Object {$_.status -eq "OK"} | Measure-Object).Count
Write-Host ("Dirs OK    : {0}/{1}" -f $dirsOk,  $dirsCheck.Count)
Write-Host ("Files OK   : {0}/{1}" -f $filesOk, $filesCheck.Count)

if ($issues.Count -gt 0) {
  Write-Warning "Problèmes détectés:"
  $issues | ForEach-Object { Write-Host " - $_" }
} else {
  Write-Host "Aucun problème critique détecté."
}
Write-Host ("Rapport    : {0}" -f $reportPath)
