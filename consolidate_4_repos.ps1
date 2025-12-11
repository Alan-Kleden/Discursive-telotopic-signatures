# consolidate_4_repos.ps1
# Script maître pour consolidation des 4 répertoires projet
# Date: 2025-12-09
# Objectif: Unifier vers Signatures_Telotopiques_POC

param(
    [string]$RootPath = "G:\Mon Drive",
    [switch]$DryRun = $false,
    [switch]$SkipBackup = $false
)

$ErrorActionPreference = "Stop"

# Chemins source
$sigPath = Join-Path $RootPath "Signatures_Telotopiques_POC"
$axioPath = Join-Path $RootPath "AxioPoC"
$theorPath = Join-Path $RootPath "Théorie de l'axiodynamique_PoC"
$suiviPath = Join-Path $RootPath "PoC Telotopic Signatures_suivi PoC"

Write-Host "=== CONSOLIDATION 4 RÉPERTOIRES PROJET ===" -ForegroundColor Cyan
Write-Host "Racine: $RootPath" -ForegroundColor Gray
Write-Host "Mode: $(if ($DryRun) {'DRY RUN (simulation)'} else {'PRODUCTION (réel)'})" -ForegroundColor $(if ($DryRun) {'Yellow'} else {'Green'})
Write-Host ""

# Vérifier existence répertoires
$missing = @()
if (-not (Test-Path $sigPath)) { $missing += "Signatures_Telotopiques_POC" }
if (-not (Test-Path $axioPath)) { $missing += "AxioPoC" }
if (-not (Test-Path $theorPath)) { $missing += "Théorie de l'axiodynamique_PoC" }
if (-not (Test-Path $suiviPath)) { $missing += "PoC Telotopic Signatures_suivi PoC" }

if ($missing.Count -gt 0) {
    Write-Host "[ERROR] Répertoires manquants :" -ForegroundColor Red
    $missing | ForEach-Object { Write-Host "  - $_" -ForegroundColor Red }
    exit 1
}

# ==============================================================================
# ÉTAPE 1 : BACKUP COMPLET
# ==============================================================================

if (-not $SkipBackup) {
    Write-Host "[1/7] BACKUP COMPLET" -ForegroundColor Yellow
    
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $backupPath = Join-Path $RootPath "_Backup_Consolidation_$timestamp"
    
    if (-not $DryRun) {
        New-Item -Path $backupPath -ItemType Directory -Force | Out-Null
        
        Write-Host "  Backup Signatures_POC..." -ForegroundColor Gray
        Copy-Item $sigPath -Destination (Join-Path $backupPath "Signatures_POC") -Recurse
        
        Write-Host "  Backup AxioPoC..." -ForegroundColor Gray
        Copy-Item $axioPath -Destination (Join-Path $backupPath "AxioPoC") -Recurse
        
        Write-Host "  Backup Théorie_PoC..." -ForegroundColor Gray
        Copy-Item $theorPath -Destination (Join-Path $backupPath "Théorie_PoC") -Recurse
        
        Write-Host "  Backup Suivi_PoC..." -ForegroundColor Gray
        Copy-Item $suiviPath -Destination (Join-Path $backupPath "Suivi_PoC") -Recurse
        
        Write-Host "  ✅ Backup créé : $backupPath" -ForegroundColor Green
    } else {
        Write-Host "  [DRY RUN] Créerait backup : $backupPath" -ForegroundColor Yellow
    }
} else {
    Write-Host "[1/7] BACKUP SKIPPÉ (--SkipBackup)" -ForegroundColor Yellow
}

Write-Host ""

# ==============================================================================
# ÉTAPE 2 : CRÉER NOUVELLE ARBORESCENCE
# ==============================================================================

Write-Host "[2/7] CRÉER NOUVELLE ARBORESCENCE" -ForegroundColor Yellow

$newDirs = @(
    "01_Framework",
    "01_Framework\References",
    "03_Scripts\features",
    "03_Scripts\hypotheses",
    "03_Scripts\validation",
    "03_Scripts\data_collection",
    "05_Tests",
    "06_Docs\suivi",
    "06_Docs\audit_reports",
    "06_Docs\methodologie",
    "07_Results\hypotheses",
    "07_Results\bootstrap_ci",
    "07_Results\figures",
    "_Archive_2025\AxioPoC_code_merged_2025-12-09",
    "_Archive_2025\Théorie_PoC_OSF",
    "_Archive_2025\Suivi_PoC_notes"
)

foreach ($dir in $newDirs) {
    $fullPath = Join-Path $sigPath $dir
    if (-not (Test-Path $fullPath)) {
        if (-not $DryRun) {
            New-Item -Path $fullPath -ItemType Directory -Force | Out-Null
            Write-Host "  ✅ Créé : $dir" -ForegroundColor Green
        } else {
            Write-Host "  [DRY RUN] Créerait : $dir" -ForegroundColor Yellow
        }
    } else {
        Write-Host "  ⏭ Existe déjà : $dir" -ForegroundColor Gray
    }
}

Write-Host ""

# ==============================================================================
# ÉTAPE 3 : MERGER AXIOPOC
# ==============================================================================

Write-Host "[3/7] MERGER AXIOPOC (code avancé)" -ForegroundColor Yellow

# Fichiers prioritaires à porter
$axioMerge = @{
    "negentropy_telotopic\ntel.py" = "03_Scripts\features\n_tel.py"
    "tests\test_negentropy_telotopic_deg_vec.py" = "05_Tests\test_ntel.py"
    "scripts\bootstrap_axis_stability.py" = "03_Scripts\validation\bootstrap_stability.py"
}

foreach ($src in $axioMerge.Keys) {
    $srcPath = Join-Path $axioPath $src
    $dstPath = Join-Path $sigPath $axioMerge[$src]
    
    if (Test-Path $srcPath) {
        if (-not $DryRun) {
            Copy-Item $srcPath -Destination $dstPath -Force
            Write-Host "  ✅ Porté : $src → $($axioMerge[$src])" -ForegroundColor Green
        } else {
            Write-Host "  [DRY RUN] Porterait : $src → $($axioMerge[$src])" -ForegroundColor Yellow
        }
    } else {
        Write-Host "  ⚠ Source manquante : $src" -ForegroundColor Red
    }
}

# Archiver AxioPoC complet
$archiveDst = Join-Path $sigPath "_Archive_2025\AxioPoC_code_merged_2025-12-09"
if (-not $DryRun) {
    if (Test-Path $archiveDst) {
        Remove-Item $archiveDst -Recurse -Force
    }
    Copy-Item $axioPath -Destination $archiveDst -Recurse
    Write-Host "  ✅ Archivé : AxioPoC complet → _Archive_2025\" -ForegroundColor Green
} else {
    Write-Host "  [DRY RUN] Archiverait : AxioPoC → _Archive_2025\" -ForegroundColor Yellow
}

Write-Host ""

# ==============================================================================
# ÉTAPE 4 : MERGER SUIVI POC
# ==============================================================================

Write-Host "[4/7] MERGER SUIVI POC (notes de suivi)" -ForegroundColor Yellow

$docsDst = Join-Path $sigPath "06_Docs"

# Copier fichiers Markdown
$mdFiles = Get-ChildItem $suiviPath -Filter "*.md" -ErrorAction SilentlyContinue
foreach ($file in $mdFiles) {
    $dstFile = Join-Path $docsDst "suivi\$($file.Name)"
    if (-not $DryRun) {
        Copy-Item $file.FullName -Destination $dstFile -Force
        Write-Host "  ✅ Copié : $($file.Name) → 06_Docs\suivi\" -ForegroundColor Green
    } else {
        Write-Host "  [DRY RUN] Copierait : $($file.Name)" -ForegroundColor Yellow
    }
}

# Copier dossier rapports si existant
$rapportsPath = Join-Path $suiviPath "rapports"
if (Test-Path $rapportsPath) {
    if (-not $DryRun) {
        Copy-Item "$rapportsPath\*" -Destination (Join-Path $docsDst "audit_reports") -Recurse -Force
        Write-Host "  ✅ Copié : rapports\ → 06_Docs\audit_reports\" -ForegroundColor Green
    } else {
        Write-Host "  [DRY RUN] Copierait : rapports\" -ForegroundColor Yellow
    }
}

# Archiver Suivi PoC complet
$suiviArchive = Join-Path $sigPath "_Archive_2025\Suivi_PoC_notes"
if (-not $DryRun) {
    if (Test-Path $suiviArchive) {
        Remove-Item $suiviArchive -Recurse -Force
    }
    Copy-Item $suiviPath -Destination $suiviArchive -Recurse
    Write-Host "  ✅ Archivé : Suivi PoC → _Archive_2025\" -ForegroundColor Green
} else {
    Write-Host "  [DRY RUN] Archiverait : Suivi PoC" -ForegroundColor Yellow
}

Write-Host ""

# ==============================================================================
# ÉTAPE 5 : ANALYSER ET MERGER THÉORIE POC
# ==============================================================================

Write-Host "[5/7] ANALYSER ET MERGER THÉORIE POC" -ForegroundColor Yellow

Write-Host "  [INFO] Recherche docs OSF..." -ForegroundColor Gray
$osfFiles = Get-ChildItem $theorPath -Filter "*OSF*" -Recurse -ErrorAction SilentlyContinue

if ($osfFiles.Count -gt 0) {
    Write-Host "  Trouvé $($osfFiles.Count) fichiers OSF" -ForegroundColor Gray
    foreach ($file in $osfFiles) {
        $dstFile = Join-Path $sigPath "01_Framework\$(Split-Path $file.FullName -Leaf)"
        if (-not $DryRun) {
            Copy-Item $file.FullName -Destination $dstFile -Force
            Write-Host "    ✅ Porté : $($file.Name) → 01_Framework\" -ForegroundColor Green
        } else {
            Write-Host "    [DRY RUN] Porterait : $($file.Name)" -ForegroundColor Yellow
        }
    }
}

Write-Host "  [INFO] Recherche docs méthodologie..." -ForegroundColor Gray
$methodoFiles = Get-ChildItem $theorPath -Filter "*methodo*" -Recurse -ErrorAction SilentlyContinue

if ($methodoFiles.Count -gt 0) {
    Write-Host "  Trouvé $($methodoFiles.Count) fichiers méthodologie" -ForegroundColor Gray
    foreach ($file in $methodoFiles) {
        $dstFile = Join-Path $sigPath "06_Docs\methodologie\$(Split-Path $file.FullName -Leaf)"
        if (-not $DryRun) {
            Copy-Item $file.FullName -Destination $dstFile -Force
            Write-Host "    ✅ Porté : $($file.Name) → 06_Docs\methodologie\" -ForegroundColor Green
        } else {
            Write-Host "    [DRY RUN] Porterait : $($file.Name)" -ForegroundColor Yellow
        }
    }
}

# Archiver Théorie PoC complet
$theorArchive = Join-Path $sigPath "_Archive_2025\Théorie_PoC_OSF"
if (-not $DryRun) {
    if (Test-Path $theorArchive) {
        Remove-Item $theorArchive -Recurse -Force
    }
    Copy-Item $theorPath -Destination $theorArchive -Recurse
    Write-Host "  ✅ Archivé : Théorie PoC → _Archive_2025\" -ForegroundColor Green
} else {
    Write-Host "  [DRY RUN] Archiverait : Théorie PoC" -ForegroundColor Yellow
}

Write-Host ""

# ==============================================================================
# ÉTAPE 6 : NETTOYER GIT
# ==============================================================================

Write-Host "[6/7] NETTOYER GIT" -ForegroundColor Yellow

if (-not $DryRun) {
    Push-Location $sigPath
    
    try {
        # Vérifier si .venv_old existe
        $venvOld = Join-Path $sigPath ".venv_old"
        if (Test-Path $venvOld) {
            Write-Host "  Suppression .venv_old de Git..." -ForegroundColor Gray
            git rm -r --cached .venv_old 2>$null
            
            # Ajouter à .gitignore si pas déjà présent
            $gitignorePath = Join-Path $sigPath ".gitignore"
            $gitignoreContent = if (Test-Path $gitignorePath) { Get-Content $gitignorePath } else { @() }
            if ($gitignoreContent -notcontains ".venv_old/") {
                Add-Content $gitignorePath "`n.venv_old/"
                Write-Host "  ✅ Ajouté .venv_old/ à .gitignore" -ForegroundColor Green
            }
        }
        
        # Commit consolidation
        git add .
        git commit -m @"
chore: consolidate 4 repos into unified architecture

- Merged AxioPoC: ntel.py, tests, bootstrap
- Integrated suivi PoC docs
- Archived legacy repos in _Archive_2025/
- Cleaned .venv_old from tracking
"@
        
        Write-Host "  ✅ Git commit créé" -ForegroundColor Green
        
    } catch {
        Write-Host "  ⚠ Erreur Git (non bloquant) : $_" -ForegroundColor Yellow
    } finally {
        Pop-Location
    }
} else {
    Write-Host "  [DRY RUN] Nettoierait .venv_old et créerait commit" -ForegroundColor Yellow
}

Write-Host ""

# ==============================================================================
# ÉTAPE 7 : CRÉER REQUIREMENTS + LICENSE
# ==============================================================================

Write-Host "[7/7] CRÉER REQUIREMENTS.TXT + LICENSE" -ForegroundColor Yellow

if (-not $DryRun) {
    Push-Location $sigPath
    
    try {
        # Requirements.txt
        $reqPath = Join-Path $sigPath "requirements.txt"
        if (-not (Test-Path $reqPath)) {
            conda list --export > $reqPath 2>$null
            if ($?) {
                Write-Host "  ✅ Créé : requirements.txt (conda)" -ForegroundColor Green
            } else {
                pip freeze > $reqPath
                Write-Host "  ✅ Créé : requirements.txt (pip)" -ForegroundColor Green
            }
        } else {
            Write-Host "  ⏭ Existe déjà : requirements.txt" -ForegroundColor Gray
        }
        
        # LICENSE MIT
        $licensePath = Join-Path $sigPath "LICENSE"
        if (-not (Test-Path $licensePath)) {
            $mitLicense = @"
MIT License

Copyright (c) 2025 Alan Kleden

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"@
            $mitLicense | Out-File -FilePath $licensePath -Encoding UTF8
            Write-Host "  ✅ Créé : LICENSE (MIT)" -ForegroundColor Green
        } else {
            Write-Host "  ⏭ Existe déjà : LICENSE" -ForegroundColor Gray
        }
        
        # Commit requirements + LICENSE
        git add requirements.txt LICENSE
        git commit -m "docs: add requirements.txt and MIT license"
        Write-Host "  ✅ Git commit : requirements + LICENSE" -ForegroundColor Green
        
    } catch {
        Write-Host "  ⚠ Erreur : $_" -ForegroundColor Yellow
    } finally {
        Pop-Location
    }
} else {
    Write-Host "  [DRY RUN] Créerait requirements.txt + LICENSE" -ForegroundColor Yellow
}

Write-Host ""

# ==============================================================================
# VALIDATION POST-CONSOLIDATION
# ==============================================================================

Write-Host "=== VALIDATION POST-CONSOLIDATION ===" -ForegroundColor Cyan

if (-not $DryRun) {
    Push-Location $sigPath
    
    Write-Host "[TEST 1] Vérifier imports Python..." -ForegroundColor Yellow
    try {
        python -c "from n_tel import compute_ntel_cos2; print('✅ n_tel importable')" 2>$null
        if (-not $?) {
            Write-Host "  ⚠ n_tel non importable (normal si pas encore dans PYTHONPATH)" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "  ⚠ Python non disponible ou erreur import" -ForegroundColor Yellow
    }
    
    Write-Host "[TEST 2] Compter scripts Python..." -ForegroundColor Yellow
    $pyCount = (Get-ChildItem -Path "03_Scripts" -Filter "*.py" -Recurse -ErrorAction SilentlyContinue).Count
    Write-Host "  Scripts Python : $pyCount (attendu ~15, pas 855 !)" -ForegroundColor $(if ($pyCount -lt 50) {'Green'} else {'Red'})
    
    Write-Host "[TEST 3] Vérifier données intactes..." -ForegroundColor Yellow
    $corpusPath = "02_Data\artifacts\real\corpus_final.parquet"
    if (Test-Path $corpusPath) {
        Write-Host "  ✅ Corpus présent : $corpusPath" -ForegroundColor Green
    } else {
        Write-Host "  ⚠ Corpus manquant : $corpusPath" -ForegroundColor Red
    }
    
    Write-Host "[TEST 4] Vérifier Git propre..." -ForegroundColor Yellow
    $gitStatus = git status --short
    if ($gitStatus.Count -eq 0) {
        Write-Host "  ✅ Git propre (aucune modification non commitée)" -ForegroundColor Green
    } else {
        Write-Host "  ⚠ Modifications Git en attente :" -ForegroundColor Yellow
        $gitStatus | ForEach-Object { Write-Host "    $_" -ForegroundColor Gray }
    }
    
    Pop-Location
}

Write-Host ""

# ==============================================================================
# RAPPORT FINAL
# ==============================================================================

Write-Host "=== RAPPORT FINAL ===" -ForegroundColor Cyan

$report = @{
    Date = Get-Date
    Mode = if ($DryRun) {"DRY RUN"} else {"PRODUCTION"}
    RepoUnifié = $sigPath
    Archives = @{
        AxioPoC = Join-Path $sigPath "_Archive_2025\AxioPoC_code_merged_2025-12-09"
        ThéoriePoC = Join-Path $sigPath "_Archive_2025\Théorie_PoC_OSF"
        SuiviPoC = Join-Path $sigPath "_Archive_2025\Suivi_PoC_notes"
    }
    FichiersMergés = @{
        ntel_py = "03_Scripts\features\n_tel.py"
        test_ntel = "05_Tests\test_ntel.py"
        bootstrap = "03_Scripts\validation\bootstrap_stability.py"
    }
}

$reportPath = Join-Path $sigPath "consolidation_report_$(Get-Date -Format 'yyyyMMdd_HHmmss').json"
if (-not $DryRun) {
    $report | ConvertTo-Json -Depth 3 | Out-File $reportPath -Encoding UTF8
    Write-Host "✅ Rapport exporté : $reportPath" -ForegroundColor Green
} else {
    Write-Host "[DRY RUN] Rapport serait exporté" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=== CONSOLIDATION TERMINÉE ===" -ForegroundColor Green
Write-Host "Prochaine étape : Validation tests Python" -ForegroundColor Yellow
Write-Host ""
Write-Host "Commandes suivantes :" -ForegroundColor Cyan
Write-Host "  cd `"$sigPath`"" -ForegroundColor Gray
Write-Host "  pytest 05_Tests/test_ntel.py -v" -ForegroundColor Gray
Write-Host "  python -c `"from n_tel import compute_ntel_cos2`"" -ForegroundColor Gray
Write-Host ""
