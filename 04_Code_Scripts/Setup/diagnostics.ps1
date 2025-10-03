# =========================================================================
# SCRIPT DE DIAGNOSTIC DE L'ENVIRONNEMENT PYTHON
# A exécuter dans le terminal (PowerShell ou Anaconda Prompt) depuis la racine du projet.
# =========================================================================

$ErrorActionPreference = "Continue" # Ne pas stopper au premier échec

Write-Host "================================================================="
Write-Host "      1. VÉRIFICATION DE L'ACCÈS À CONDA"
Write-Host "================================================================="

try {
    # Tente d'appeler conda pour vérifier s'il est dans le PATH
    $condaPath = (Get-Command conda).Path
    Write-Host "✅ Conda est accessible via: $condaPath" -ForegroundColor Green
    $condaAccessible = $true
} catch {
    Write-Host "❌ Commande 'conda' introuvable dans le PATH actuel." -ForegroundColor Red
    Write-Host "   -> Solution: Utilisez l'Anaconda Prompt ou exécutez 'conda init powershell'." -ForegroundColor Yellow
    $condaAccessible = $false
}

Write-Host "`n================================================================="
Write-Host "      2. VÉRIFICATION DE L'ENVIRONNEMENT ACTIF"
Write-Host "================================================================="

# Vérifie si un environnement Conda est actif (recherche le préfixe dans le prompt)
$envPrefix = $env:CONDA_DEFAULT_ENV

if ($envPrefix -like "telotopic-311") {
    Write-Host "✅ Environnement (telotopic-311) est ACTIF." -ForegroundColor Green
} elseif ($envPrefix) {
    Write-Host "⚠️ Un autre environnement Conda est actif: ($envPrefix)" -ForegroundColor Yellow
    Write-Host "   -> Exécutez: 'conda activate telotopic-311'" -ForegroundColor Yellow
} else {
    Write-Host "❌ Aucun environnement Conda n'est actif." -ForegroundColor Red
    Write-Host "   -> Solution: Exécutez: 'conda activate telotopic-311'" -ForegroundColor Yellow
}


Write-Host "`n================================================================="
Write-Host "      3. VÉRIFICATION DES LIBRAIRIES CLÉS"
Write-Host "================================================================="

if ($condaAccessible) {
    # Vérifie la version de Python et les librairies essentielles dans l'environnement actif
    $pythonCheck = "
import sys, importlib

results = []
required_libs = ['torch', 'transformers', 'pandas']

# Vérification de la version Python
results.append(f'PYTHON: {sys.version.split()[0]}')

# Vérification des librairies
for lib in required_libs:
    try:
        module = importlib.import_module(lib)
        version = module.__version__
        results.append(f'✅ {lib.upper()}: {version}')
    except ImportError:
        results.append(f'❌ {lib.upper()}: Non installé')
    except Exception as e:
        results.append(f'⚠️ {lib.upper()}: Erreur de chargement ({e})')

print('\n'.join(results))
"
    # Exécute le code Python
    Write-Host "-> Exécution du diagnostic Python..."
    $result = python -c $pythonCheck 2>&1

    # Affiche le résultat ligne par ligne
    $result -split "`r?`n" | ForEach-Object {
        if ($_ -like "*✅*") {
            Write-Host $_ -ForegroundColor Green
        } elseif ($_ -like "*❌*") {
            Write-Host $_ -ForegroundColor Red
        } else {
            Write-Host $_ -ForegroundColor Cyan
        }
    }

} else {
    Write-Host "Impossible d'exécuter le diagnostic Python car 'conda' ou 'python' n'est pas accessible." -ForegroundColor Red
}

Write-Host "================================================================="
Write-Host "      DIAGNOSTIC TERMINÉ."
Write-Host "================================================================="
