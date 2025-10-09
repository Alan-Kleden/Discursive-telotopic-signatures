# extract_poc_scripts.ps1
# Extrait tous les scripts Python critiques pour finaliser le PoC

param(
    [string]$RootPath = "G:\Mon Drive\Signatures_Telotopiques_POC",
    [string]$OutputDir = ".\extracted_scripts"
)

Write-Host "=== EXTRACTION DES SCRIPTS PoC ===" -ForegroundColor Cyan
Write-Host ""

# Crée le dossier de sortie
New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null

# Liste des scripts critiques à extraire
$criticalScripts = @{
    "Analysis" = @(
        "04_Code_Scripts\analysis\generate_validation_sample.py",
        "04_Code_Scripts\analysis\validate_lexicon_v2.py",
        "04_Code_Scripts\analysis\enrich_lexicon_v2_enhanced.py",
        "04_Code_Scripts\analysis\compare_v1_v2_performance.py",
        "04_Code_Scripts\analysis\map_lexicon_v1.py"
    )
    "Features" = @(
        "04_Code_Scripts\features\fc_fi.py",
        "04_Code_Scripts\features\theta.py",
        "04_Code_Scripts\features\n_tel.py",
        "04_Code_Scripts\features\conative.py",
        "04_Code_Scripts\features\windows.py"
    )
    "Pipelines" = @(
        "04_Code_Scripts\pipelines\axio_features.py",
        "04_Code_Scripts\pipelines\teloi_matcher.py"
    )
    "Utils" = @(
        "04_Code_Scripts\utils\__init__.py",
        "04_Code_Scripts\utils\io.py",
        "04_Code_Scripts\utils\seed.py",
        "04_Code_Scripts\utils\validate_csv.py"
    )
    "Config" = @(
        "07_Config\params.yml",
        "07_Config\paths.yml",
        "07_Config\domain_rules.yml",
        "07_Config\validation_manual_template.csv"
    )
}

# Statistiques
$stats = @{
    Total = 0
    Found = 0
    Missing = 0
    TotalLines = 0
    TotalSize = 0
}

# Fonction pour extraire un fichier
function Extract-Script {
    param(
        [string]$RelativePath,
        [string]$Category
    )
    
    $fullPath = Join-Path $RootPath $RelativePath
    $stats.Total++
    
    if (Test-Path $fullPath) {
        $stats.Found++
        
        # Lit le contenu
        $content = Get-Content $fullPath -Raw -Encoding UTF8
        $lines = ($content -split "`n").Count
        $size = (Get-Item $fullPath).Length
        
        $stats.TotalLines += $lines
        $stats.TotalSize += $size
        
        # Crée la structure de dossiers
        $categoryDir = Join-Path $OutputDir $Category
        New-Item -ItemType Directory -Force -Path $categoryDir | Out-Null
        
        # Nom du fichier de sortie
        $fileName = Split-Path $RelativePath -Leaf
        $outPath = Join-Path $categoryDir $fileName
        
        # Copie avec métadonnées
        $header = @"
# ================================================
# Source: $RelativePath
# Category: $Category
# Lines: $lines
# Size: $([math]::Round($size/1KB, 2)) KB
# Extracted: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
# ================================================

"@
        
        $header + $content | Out-File -FilePath $outPath -Encoding UTF8
        
        Write-Host "  ✓ $fileName" -ForegroundColor Green -NoNewline
        Write-Host " ($lines lines, $([math]::Round($size/1KB, 1)) KB)"
        
        return $true
    }
    else {
        $stats.Missing++
        Write-Host "  ✗ $(Split-Path $RelativePath -Leaf)" -ForegroundColor Red -NoNewline
        Write-Host " (NOT FOUND)"
        return $false
    }
}

# Extraction par catégorie
foreach ($category in $criticalScripts.Keys) {
    Write-Host "`n[$category]" -ForegroundColor Yellow
    
    foreach ($scriptPath in $criticalScripts[$category]) {
        Extract-Script -RelativePath $scriptPath -Category $category
    }
}

# Génère un index Markdown
Write-Host "`n=== GÉNÉRATION INDEX ===" -ForegroundColor Cyan

$indexContent = @"
# Scripts PoC Extraits

**Date:** $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
**Source:** ``$RootPath``

## Statistiques

- **Total scripts:** $($stats.Total)
- **Trouvés:** $($stats.Found) ✓
- **Manquants:** $($stats.Missing) ✗
- **Lignes totales:** $($stats.TotalLines)
- **Taille totale:** $([math]::Round($stats.TotalSize/1KB, 2)) KB

## Contenu par catégorie

"@

foreach ($category in $criticalScripts.Keys) {
    $indexContent += "`n### $category`n`n"
    
    foreach ($scriptPath in $criticalScripts[$category]) {
        $fileName = Split-Path $scriptPath -Leaf
        $fullPath = Join-Path $RootPath $scriptPath
        
        if (Test-Path $fullPath) {
            $lines = (Get-Content $fullPath).Count
            $size = [math]::Round((Get-Item $fullPath).Length/1KB, 1)
            $indexContent += "- ✓ ``$fileName`` ($lines lines, $size KB)`n"
        }
        else {
            $indexContent += "- ✗ ``$fileName`` (MISSING)`n"
        }
    }
}

$indexContent += @"

## Utilisation

1. **Analyser les scripts manuellement** (éditeur de texte)
2. **Fournir à Claude** (copier-coller ou upload)
3. **Intégrer dans le projet** si besoin

## Scripts manquants

"@

if ($stats.Missing -gt 0) {
    $indexContent += "`nLes scripts suivants n'ont pas été trouvés :`n`n"
    
    foreach ($category in $criticalScripts.Keys) {
        foreach ($scriptPath in $criticalScripts[$category]) {
            $fullPath = Join-Path $RootPath $scriptPath
            if (-not (Test-Path $fullPath)) {
                $indexContent += "- ``$scriptPath```n"
            }
        }
    }
}
else {
    $indexContent += "`n✓ Tous les scripts critiques ont été trouvés.`n"
}

# Sauvegarde l'index
$indexPath = Join-Path $OutputDir "README.md"
$indexContent | Out-File -FilePath $indexPath -Encoding UTF8

Write-Host "`n✓ Index créé: $indexPath" -ForegroundColor Green

# Crée un ZIP pour faciliter l'upload
Write-Host "`n=== CRÉATION ARCHIVE ===" -ForegroundColor Cyan

$zipPath = ".\poc_scripts_$(Get-Date -Format 'yyyyMMdd_HHmmss').zip"
Compress-Archive -Force -Path "$OutputDir\*" -DestinationPath $zipPath

$zipSize = [math]::Round((Get-Item $zipPath).Length/1KB, 2)
Write-Host "✓ Archive créée: $zipPath ($zipSize KB)" -ForegroundColor Green

# Résumé final
Write-Host "`n=== RÉSUMÉ ===" -ForegroundColor Cyan
Write-Host "Scripts trouvés  : $($stats.Found)/$($stats.Total)" -ForegroundColor Green
Write-Host "Scripts manquants: $($stats.Missing)" -ForegroundColor $(if ($stats.Missing -eq 0) { "Green" } else { "Red" })
Write-Host "Lignes totales   : $($stats.TotalLines)"
Write-Host "Taille totale    : $([math]::Round($stats.TotalSize/1KB, 2)) KB"
Write-Host ""
Write-Host "Dossier: $OutputDir" -ForegroundColor Yellow
Write-Host "Archive: $zipPath" -ForegroundColor Yellow
Write-Host ""

# Options de partage
Write-Host "=== OPTIONS DE PARTAGE ===" -ForegroundColor Cyan
Write-Host "1. Uploader le ZIP dans le chat Claude"
Write-Host "2. Copier-coller les scripts individuels"
Write-Host "3. Partager via GitHub (si pushé)"
Write-Host ""

# Ouvre le dossier
Start-Process explorer.exe -ArgumentList $OutputDir