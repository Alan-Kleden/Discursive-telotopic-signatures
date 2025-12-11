# pipeline_phase1.ps1 — Phase 1, sans Python inline
$ErrorActionPreference = "Stop"

# 0) Préambule
Set-Location "G:\Mon Drive\Signatures_Telotopiques_POC"
$ts = Get-Date -Format 'yyyyMMdd_HHmm'

# 1) Dossiers
$inDir  = ".\artifacts\phase1\inputs"
$outDir = ".\artifacts\phase1\outputs\diag\$ts"
New-Item -ItemType Directory -Force -Path $inDir,$outDir | Out-Null

# 2) RSS source — prend le plus récent
$rss = Get-ChildItem "$inDir\rss_items_*.csv" -ErrorAction SilentlyContinue |
       Sort-Object LastWriteTime -desc | Select-Object -First 1
if (-not $rss) {
  Write-Error "Aucun fichier RSS trouvé dans $inDir\rss_items_*.csv"
  exit 1
}
Write-Host "RSS   : $($rss.FullName)"

# 3) ENRICH → lot_raw_$ts.csv
$rawOut = "$inDir\lot_raw_$ts.csv"
python ".\scripts\poc_tools\enrich_from_rss.py" "$($rss.FullName)" "$rawOut"
if (-not (Test-Path $rawOut)) { Write-Error "ENRICH n'a pas produit $rawOut"; exit 1 }
Copy-Item "$rawOut" "$inDir\lot_raw.csv" -Force

# 4) Diagnostic sur RAW
python ".\04_Code_Scripts\analysis\lot20_diagnostic.py" --csv "$rawOut" --outdir "$outDir" --min_words 120

# 5) EXCERPTS → candidates_25_$ts.csv
$candOut = "$inDir\candidates_25_$ts.csv"
python ".\scripts\poc_tools\make_excerpts.py" "$rawOut" "$candOut"
if (-not (Test-Path $candOut)) { Write-Error "EXCERPTS n'a pas produit $candOut"; exit 1 }
Copy-Item "$candOut" "$inDir\candidates_25.csv" -Force

# 6) Sélection 20 → lot20_final_$ts.csv
$lotOut = "$inDir\lot20_final_$ts.csv"
python ".\scripts\poc_tools\select_diverse_20.py" "$candOut" "$lotOut"
if (-not (Test-Path $lotOut)) { Write-Error "SELECT n'a pas produit $lotOut"; exit 1 }
Copy-Item "$lotOut" "$inDir\lot20_final.csv" -Force

# 7) Validation finale
python ".\scripts\poc_tools\validate_lot.py"

# 8) Résumé
Write-Host "RAW   : $rawOut"
Write-Host "CAND  : $candOut"
Write-Host "LOT20 : $lotOut"
