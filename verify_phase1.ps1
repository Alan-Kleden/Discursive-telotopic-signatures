# verify_phase1.ps1 — check complet et log
$ErrorActionPreference = "Stop"
Set-Location "G:\Mon Drive\Signatures_Telotopiques_POC"

$inDir = ".\artifacts\phase1\inputs"
$lot   = Join-Path $inDir "lot20_final.csv"
$cand  = Join-Path $inDir "candidates_25.csv"
$raw   = Join-Path $inDir "lot_raw.csv"
$ts    = Get-Date -Format 'yyyyMMdd_HHmm'
$log   = ".\artifacts\phase1\outputs\diag\verify_$ts.log"

$lines = @()

# 1) FICHIERS
$lines += "== 1) FICHIERS =="
$files = Get-Item $raw,$cand,$lot -ErrorAction SilentlyContinue
$lines += ($files | ForEach-Object { "{0}  {1:n0} bytes" -f $_.Name,$_.Length })

# 2) VALIDATE
$lines += ""; $lines += "== 2) VALIDATE =="
$lines += (cmd /c python .\scripts\poc_tools\validate_lot.py 2>&1)

# 3) LONGUEURS & Fc/Fi
$lines += ""; $lines += "== 3) LONGUEURS & Fc/Fi =="
$lotData = Import-Csv $lot
$lenData = $lotData | Select-Object *, @{n='excerpt_len';e={($_.excerpt -split '\s+').Count}}
$lines += ($lenData | Measure-Object -Property excerpt_len -Min -Max | Out-String)
$FcPos = ($lotData | Where-Object { $_.Fc_items -notmatch '0$' -or $_.Fi_items -notmatch '0$' } | Measure-Object).Count
$lines += ("Fc_pos=" + $FcPos)

# 4) RÉPARTITIONS
$lines += ""; $lines += "== 4) RÉPARTITIONS =="
$lines += "TOPICS:"
$lines += ($lotData | Group-Object topic | Sort-Object Count -desc | Format-Table -Auto Name,Count | Out-String)
$lines += "STANCE:"
$lines += ($lotData | Group-Object stance_guess | Sort-Object Count -desc | Format-Table -Auto Name,Count | Out-String)
$lines += "DOMAINES:"
$lines += ($lotData | Group-Object source | Sort-Object Count -desc | Format-Table -Auto Name,Count | Out-String)

# 5) DUPLICATS
$lines += ""; $lines += "== 5) DUPLICATS =="
$lines += "ID dup:";  $lines += ($lotData.id  | Group-Object | Where-Object Count -gt 1 | Format-Table -Auto Name,Count | Out-String)
$lines += "URL dup:"; $lines += ($lotData.url | Group-Object | Where-Object Count -gt 1 | Format-Table -Auto Name,Count | Out-String)

# 6) APERÇU
$lines += ""; $lines += "== 6) APERÇU =="
$lines += ($lotData | Select-Object -First 3 | Format-List id,topic,stance_guess,source,url | Out-String)

$lines -join "`r`n" | Tee-Object -FilePath $log
$log
