# scripts/Inventory-Workspace.ps1
# Inventaire exhaustif de l'espace de travail (fichiers, résumés, arborescence)
# Usage simple :
#   & "scripts/Inventory-Workspace.ps1" -Root "C:\Users\ojahi\Mon Drive\Signatures_Telotopiques_POC"
# Options :
#   -Mode quick|deep (deep calcule des hashes SHA256)
#   -MaxHashMB 25   (seuil de hash en Mo si Mode=deep)
#   -ExcludeDirs ... (liste de dossiers à exclure)
#   -OutDir "REPORTS\inventory"

param(
  [string]$Root = "C:\Users\ojahi\Mon Drive\Signatures_Telotopiques_POC",
  [ValidateSet("quick","deep")]
  [string]$Mode = "quick",
  [int]$MaxHashMB = 25,
  [string[]]$ExcludeDirs = @(".git",".venv","venv","node_modules","__pycache__",".ipynb_checkpoints",".pytest_cache",".mypy_cache",".vs",".vscode\.history","artifacts_xfer"),
  [string]$OutDir = "REPORTS\inventory"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $Root)) {
  Write-Host "[ERR] Root not found: $Root" -ForegroundColor Red
  exit 2
}

# Normalisation chemins
$rootFull = (Resolve-Path -LiteralPath $Root).Path
$ts = Get-Date -Format "yyyyMMdd_HHmmss"
$invDir = Join-Path -Path $Root -ChildPath $OutDir
$invDirTS = Join-Path -Path $invDir -ChildPath $ts
New-Item -ItemType Directory -Force -Path $invDirTS | Out-Null

Write-Host "[OK] Root: $rootFull"
Write-Host "[OK] Out : $invDirTS"

# Regex d'exclusion sur FullName
# (match si un segment de chemin correspond à un des dossiers exclus)
$exRe = ('\\(' + (($ExcludeDirs | ForEach-Object {
    [Regex]::Escape($_).Replace('\.', '\.').Replace('\\','\\')
  }) -join '|') + ')(\\|$)').Replace('\\\\','\\')

# Récupération exhaustive des fichiers (hors exclusions)
Write-Host "[..] Scanning files..." -ForegroundColor Cyan
$files = Get-ChildItem -LiteralPath $rootFull -Recurse -File -Force -ErrorAction SilentlyContinue |
  Where-Object { $_.FullName -notmatch $exRe }

# Construction objets d'inventaire
function Get-RelPath([string]$full, [string]$root) {
  return $full.Substring($root.Length).TrimStart('\','/')
}

$records = foreach ($f in $files) {
  [pscustomobject]@{
    Name          = $f.Name
    Extension     = $f.Extension.ToLower()
    Length        = $f.Length
    LengthKB      = [math]::Round($f.Length/1KB,2)
    LengthMB      = [math]::Round($f.Length/1MB,2)
    LastWriteTime = $f.LastWriteTime
    FullName      = $f.FullName
    RelPath       = Get-RelPath $f.FullName $rootFull
    TopFolder     = ($rp = Get-RelPath $f.FullName $rootFull; ($rp -split '[\\/]')[0])
  }
}

# Si deep, calcul de hash pour les fichiers < MaxHashMB
if ($Mode -eq "deep") {
  Write-Host "[..] Computing SHA256 for files <= $MaxHashMB MB..." -ForegroundColor Cyan
  $limit = $MaxHashMB * 1MB
  $hashDict = @{}
  foreach ($f in $files) {
    if ($f.Length -le $limit) {
      try {
        $h = Get-FileHash -LiteralPath $f.FullName -Algorithm SHA256
        $hashDict[$f.FullName] = $h.Hash
      } catch {
        $hashDict[$f.FullName] = $null
      }
    } else {
      $hashDict[$f.FullName] = $null
    }
  }
  # enrichit $records
  $records = $records | ForEach-Object {
    $_ | Add-Member -NotePropertyName "SHA256" -NotePropertyValue ($hashDict[$_.FullName]) -PassThru
  }
}

# Exports
$filesCsv = Join-Path $invDirTS "files_all.csv"
$codeCsv  = Join-Path $invDirTS "files_code.csv"
$extCsv   = Join-Path $invDirTS "summary_by_ext.csv"
$topCsv   = Join-Path $invDirTS "summary_by_topfolder.csv"
$treeTxt  = Join-Path $invDirTS "tree.txt"

# Fichiers code : extensions les plus utiles à l'audit
$codeExt = @(".py",".ps1",".psm1",".psd1",".bat",".sh",".ipynb",".json",".yml",".yaml",".md",".rst",".tex",".csv",".tsv",".ini",".toml",".cfg",".txt",".ps1xml",".xml")

# Exports CSV
$records | Sort-Object RelPath | Export-Csv -NoTypeInformation -Encoding UTF8 -Path $filesCsv

$records |
  Where-Object { $codeExt -contains $_.Extension } |
  Sort-Object RelPath |
  Export-Csv -NoTypeInformation -Encoding UTF8 -Path $codeCsv

$records |
  Group-Object Extension |
  ForEach-Object {
    [pscustomobject]@{
      Extension = $_.Name
      Count     = $_.Count
      TotalMB   = [math]::Round(($_.Group | Measure-Object -Property Length -Sum).Sum / 1MB, 2)
    }
  } |
  Sort-Object -Property TotalMB -Descending |
  Export-Csv -NoTypeInformation -Encoding UTF8 -Path $extCsv

$records |
  Group-Object TopFolder |
  ForEach-Object {
    [pscustomobject]@{
      TopFolder = $_.Name
      Count     = $_.Count
      TotalMB   = [math]::Round(($_.Group | Measure-Object -Property Length -Sum).Sum / 1MB, 2)
    }
  } |
  Sort-Object -Property TotalMB -Descending |
  Export-Csv -NoTypeInformation -Encoding UTF8 -Path $topCsv

# Arborescence "tree"
try {
  cmd.exe /c "tree /F /A `"$rootFull`"" | Out-File -FilePath $treeTxt -Encoding utf8
} catch {
  # fallback PowerShell
  Get-ChildItem -LiteralPath $rootFull -Recurse |
    ForEach-Object { $_.FullName.Substring($rootFull.Length).TrimStart('\','/') } |
    Out-File -FilePath $treeTxt -Encoding utf8
}

# Échos finaux
Write-Host ""
Write-Host "=== INVENTORY COMPLETE ===" -ForegroundColor Green
Write-Host ("All files  : " + $filesCsv)
Write-Host ("Code files : " + $codeCsv)
Write-Host ("By ext     : " + $extCsv)
Write-Host ("By folder  : " + $topCsv)
Write-Host ("Tree       : " + $treeTxt)
Write-Host ""
Write-Host "Astuces d'affichage UTF-8 :" -ForegroundColor Yellow
Write-Host '  chcp 65001 > $null; $OutputEncoding = [Console]::OutputEncoding = New-Object System.Text.UTF8Encoding'
