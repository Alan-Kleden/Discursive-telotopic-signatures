param(
  [string]$SrcRoot = "G:\Mon Drive\Signatures_Telotopiques_POC",
  [string]$DstRoot = "H:\PoC_OSF",
  [switch]$DryRun
)

function Resolve-And-Copy {
  param(
    [string]$RelPath,
    [string]$DstDir,
    [switch]$DryRun
  )
  $fullPattern = Join-Path $SrcRoot $RelPath

  if ($RelPath -match "[\*\?\[\]]") {
    $items = Get-ChildItem -Path $fullPattern -File -Recurse -ErrorAction SilentlyContinue
    if (-not $items -or $items.Count -eq 0) {
      Write-Warning "Aucun fichier pour le motif: $RelPath"
      return
    }
    foreach ($it in $items) {
      $dst = Join-Path $DstDir (Split-Path $it.FullName -Leaf)
      if ($DryRun) { Write-Host "[DRY] COPY  $($it.FullName)  ->  $dst" }
      else { Copy-Item -Path $it.FullName -Destination $dst -Force -ErrorAction Continue }
    }
  } else {
    if (Test-Path $fullPattern) {
      $isDir = (Get-Item $fullPattern).PSIsContainer
      if ($isDir) {
        if ($DryRun) { Write-Host "[DRY] COPY DIR  $fullPattern  ->  $DstDir" }
        else { Copy-Item -Path (Join-Path $fullPattern '*') -Destination $DstDir -Recurse -Force -ErrorAction Continue }
      } else {
        $dst = Join-Path $DstDir (Split-Path $fullPattern -Leaf)
        if ($DryRun) { Write-Host "[DRY] COPY  $fullPattern  ->  $dst" }
        else { Copy-Item -Path $fullPattern -Destination $dst -Force -ErrorAction Continue }
      }
    } else {
      Write-Warning "Introuvable: $RelPath"
    }
  }
}

$annexMap = [ordered]@{
  '01 Preregistration & Protocol' = @(
    'OSF_Preregistration_Extract.md',
    'artifacts\OSF\README.md'
    # Ajouter ici d’éventuels appendices protocolaires si présents
    # '01_Protocoles\Appendix_A4_beta_modality_clarification_v1.1.md'
  )
  '02 Data & Description' = @(
    'artifacts\real\corpus_final.parquet',
    'artifacts\real\features_doc.parquet',
    '07_Config\actors_and_shocks\actor_roster.csv',
    '07_Config\actors_and_shocks\shocks.csv'
  )
  '03 Lexicons & Validation' = @(
    '07_Config\lexicons\lexicon_conative_v1.clean.csv',
    '07_Config\lexicons\lexicon_conative_v1.mapped.csv',
    '07_Config\lexicons\lexicon_conative_v2_enhanced.csv',
    '07_Config\validation_manual_template.csv',
    '07_Config\validation_manual.csv'
  )
  '04 Scripts & Reproducibility' = @(
    '04_Code_Scripts\**\*.py',
    'tasks.ps1',
    'requirements.txt',
    'LICENSE'
  )
  '05 Analytical Outputs (PoC)' = @(
    'artifacts\real\lexicon_v2_eval\*',
    'artifacts\real\lexicon_comparison\by_actor_v1_vs_v2.csv'
  )
  '06 OSF Bundle (Zip-ready)' = @(
    'artifacts\real\lexicon_v2_eval\*',
    'artifacts\real\lexicon_comparison\by_actor_v1_vs_v2.csv',
    '07_Config\lexicons\*v1*.csv',
    '07_Config\lexicons\lexicon_conative_v2_enhanced.csv',
    'artifacts\OSF\README.md'
  )
}

New-Item -ItemType Directory -Path $DstRoot -Force | Out-Null
$missing = New-Object System.Collections.Generic.List[string]

foreach ($annexName in $annexMap.Keys) {
  $dstDir = Join-Path $DstRoot $annexName
  New-Item -ItemType Directory -Path $dstDir -Force | Out-Null
  Write-Host "`n>> Annex: $annexName" -ForegroundColor Cyan

  foreach ($rel in $annexMap[$annexName]) {
    try { Resolve-And-Copy -RelPath $rel -DstDir $dstDir -DryRun:$DryRun }
    catch {
      $missing.Add($rel) | Out-Null
      Write-Warning "Erreur copie: $rel -> $dstDir : $($_.Exception.Message)"
    }
  }
}

Write-Host "`n=== RÉCAP ===" -ForegroundColor Yellow
Write-Host "Destination : $DstRoot"
Write-Host "Annexes traitées : $($annexMap.Keys.Count)"
if ($missing.Count -gt 0) {
  Write-Host "Éléments en erreur : $($missing.Count)" -ForegroundColor DarkYellow
  ($missing | Sort-Object -Unique) | ForEach-Object { Write-Host " - $_" }
} else {
  Write-Host "Aucune erreur signalée." -ForegroundColor Green
}
