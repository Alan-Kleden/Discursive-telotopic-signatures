# create_data_links.ps1
# Crée 02_Donnees_Corpus + jonctions vers H:\Data\Telotopic\*
# + README + dossier Extracted_Teloi (fichiers "gelés" versionnés)

$ErrorActionPreference = "Stop"

# --- PARAMÈTRES ---
$RepoRoot = "C:\Users\ojahi\Mon Drive\Signatures_Telotopiques_POC"
$DataRoot = "H:\Data\Telotopic"
$RawRoot  = Join-Path $DataRoot "00_Raw"
$IntRoot  = Join-Path $DataRoot "10_Intermediate"
$ProcRoot = Join-Path $DataRoot "20_Processed"

# --- util: créer répertoire s'il manque ---
foreach ($p in @($DataRoot,$RawRoot,$IntRoot,$ProcRoot)) {
  if (!(Test-Path $p)) { New-Item -ItemType Directory -Path $p -Force | Out-Null }
}

# --- util: jonction robuste (+ fallback mklink /J) ---
function New-Or-Replace-Junction {
  param([string]$LinkPath, [string]$TargetPath)

  if (!(Test-Path $TargetPath)) {
    Write-Host "❌ Cible introuvable: $TargetPath" -ForegroundColor Red
    return $false
  }
  if (Test-Path $LinkPath) {
    $item = Get-Item $LinkPath -Force
    $isJunction = ($item.Attributes -band [IO.FileAttributes]::ReparsePoint)
    if ($isJunction) {
      Remove-Item $LinkPath -Force
    } else {
      Write-Host "ℹ️ $LinkPath existe déjà (non-junction). Non modifié." -ForegroundColor Yellow
      return $true
    }
  }
  try {
    New-Item -ItemType Junction -Path $LinkPath -Target $TargetPath | Out-Null
  } catch {
    # fallback (fonctionne quasiment partout)
    cmd /c mklink /J "$LinkPath" "$TargetPath" | Out-Null
  }
  Write-Host "✅ Jonction: $LinkPath  →  $TargetPath" -ForegroundColor Green
  return $true
}

# --- 1) Dossier 02_Donnees_Corpus ---
$Repo02 = Join-Path $RepoRoot "02_Donnees_Corpus"
New-Item -ItemType Directory -Path $Repo02 -Force | Out-Null
Write-Host "📁 $Repo02 créé/présent."

# --- 2) Jonctions vers H: ---
$ok1 = New-Or-Replace-Junction -LinkPath (Join-Path $Repo02 "00_Raw")          -TargetPath $RawRoot
$ok2 = New-Or-Replace-Junction -LinkPath (Join-Path $Repo02 "10_Intermediate") -TargetPath $IntRoot
$ok3 = New-Or-Replace-Junction -LinkPath (Join-Path $Repo02 "20_Processed")    -TargetPath $ProcRoot
if (-not ($ok1 -and $ok2 -and $ok3)) { Write-Host "⚠️ Jonctions incomplètes." -ForegroundColor Yellow }

# --- 3) Sous-dossier Teloi FROZEN (versionné dans Git) ---
$TeloiDir = Join-Path $Repo02 "Extracted_Teloi"
New-Item -ItemType Directory -Path $TeloiDir -Force | Out-Null
Set-Content -Path (Join-Path $TeloiDir ".gitkeep") -Value "" -Encoding UTF8

$teloiCSVHeader = "actor_id,telos_id,telos_canonical_text,date_frozen_yyyy_mm_dd"
$teloiCSVPath   = Join-Path $TeloiDir "teloi_endogenes_V1_FROZEN.csv"
if (!(Test-Path $teloiCSVPath)) {
  Set-Content -Path $teloiCSVPath -Value $teloiCSVHeader -Encoding UTF8
}

# --- 4) README & sentinel ---
$readme = @"
# 02_Donnees_Corpus (links to H:)

Ce dossier contient des **jonctions NTFS** vers les données stockées hors 'Mon Drive' :

- 00_Raw          → $RawRoot
- 10_Intermediate → $IntRoot
- 20_Processed    → $ProcRoot

Le sous-dossier **Extracted_Teloi/** héberge les fichiers **FROZEN** (versionnés) exigés par la prereg OSF.
Ne modifiez pas ces fichiers sans créer une nouvelle version datée.

⚠️ Ne stockez pas de gros fichiers ici : mettez-les sur H: et accédez-y via ces liens.
Voir aussi `07_Config\paths.yml` utilisé par les scripts.
"@
Set-Content -Path (Join-Path $Repo02 "README.md") -Value $readme -Encoding UTF8

$sentinel = "Les données LOURDES vivent sur H:. Ce dépôt ne contient que code, configs, résultats agrégés et fichiers FROZEN (Extracted_Teloi)."
Set-Content -Path (Join-Path $Repo02 "DO_NOT_PUT_DATA_HERE.txt") -Value $sentinel -Encoding UTF8

Write-Host "`n🎉 Terminé. Ouvrez 02_Donnees_Corpus dans VS Code : vous verrez les liens vers H: + Extracted_Teloi." -ForegroundColor Cyan
