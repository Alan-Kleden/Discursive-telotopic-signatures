param(
  [string]$Python = "python"
)

Write-Host "=== Torch Diagnostic ===" -ForegroundColor Cyan
Write-Host ("Conda env   : {0}" -f $env:CONDA_DEFAULT_ENV)
Write-Host ("PS 64-bit   : {0}" -f [Environment]::Is64BitProcess)
Write-Host ("PS version  : {0}" -f $PSVersionTable.PSVersion.ToString())

# 1) Vérifier Python accessible
try {
  $pyv = & $Python -V
  Write-Host ("Python exec : {0} ({1})" -f $Python, $pyv)
} catch {
  Write-Host "ERROR: Python introuvable. Active 'conda activate telotopic-311' ou passe -Python <chemin>." -ForegroundColor Red
  exit 1
}

# 2) Ecrire un script Python temporaire (pour éviter les pipes)
$pyTemp = Join-Path $env:TEMP "torch_diag_tmp.py"
$pyCode = @"
import sys, platform, os, glob

print("PY_VERSION:", sys.version.split()[0])
print("ARCH      :", platform.architecture()[0])

def find_torch_lib(pattern="*fbgemm*.dll"):
    base = os.path.join(sys.prefix, "Lib", "site-packages", "torch", "lib")
    return [p for p in glob.glob(os.path.join(base, pattern))]

try:
    import torch
    print("TORCH_OK:", torch.__version__)
    print("CUDA_AVAILABLE:", torch.cuda.is_available())
    x = torch.randn(2, 3)
    y = x @ x.T
    print("TEST_OP_OK:", tuple(y.shape))
except Exception as e:
    print("TORCH_ERROR:", type(e).__name__, str(e))
    libs = find_torch_lib()
    print("TORCH_LIB_DIR:", os.path.join(sys.prefix, "Lib", "site-packages", "torch", "lib"))
    print("FbgemmPresent:", bool(libs), libs[:3])
"@

Set-Content -Path $pyTemp -Value $pyCode -Encoding UTF8

# 3) Exécuter le script et capter la sortie
$out = & $Python $pyTemp 2>&1
$out | ForEach-Object { $_ }

# 4) Nettoyage
Remove-Item $pyTemp -Force -ErrorAction SilentlyContinue

# 5) Interprétation rapide
if ($out -match "^TORCH_OK:") {
  Write-Host "`nOK: Torch est operationnel." -ForegroundColor Green
  exit 0
}
if ($out -match "^TORCH_ERROR: ModuleNotFoundError") {
  Write-Host "`nERROR: Torch n'est pas installe dans cet environnement." -ForegroundColor Red
  Write-Host "Solution :"
  Write-Host "  conda install -c pytorch pytorch=2.3  (ou)"
  Write-Host "  pip install --index-url https://download.pytorch.org/whl/cpu torch==2.7.1+cpu"
  exit 2
}
if ( ($out -match "^TORCH_ERROR: OSError") -and ($out -match "fbgemm\.dll") ) {
  Write-Host "`nWARN: Erreur DLL (fbgemm.dll) detectee." -ForegroundColor Yellow
  Write-Host "Etape A : installer 'Microsoft Visual C++ Redistributable 2015-2022 (x64)' puis relancer le test."
  Write-Host "Etape B : si A ne suffit pas, reinstaller un build CPU propre de Torch :"
  Write-Host "   conda remove -y pytorch torchvision torchaudio"
  Write-Host "   pip install --force-reinstall --no-cache-dir --index-url https://download.pytorch.org/whl/cpu torch==2.7.1+cpu"
  exit 3
}
if ($out -match "^TORCH_ERROR:") {
  Write-Host "`nWARN: Torch a echoue a l'import (voir messages ci-dessus)." -ForegroundColor Yellow
  Write-Host "Souvent corrige par VC++ Redistributable x64, ou reinstallation Torch CPU via pip."
  exit 4
}

Write-Host "`nINFO: Resultat inattendu -- copie/colle la sortie ci-dessus pour diagnostic." -ForegroundColor Yellow
exit 5
