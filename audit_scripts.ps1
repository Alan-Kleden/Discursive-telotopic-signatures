# === audit_scripts.ps1 ===
param([string]$Root="G:\Mon Drive\Signatures_Telotopiques_POC")

$outDir = Join-Path $Root "artifacts\phase1\reports"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
$ts   = Get-Date -Format "yyyyMMdd_HHmmss"
$json = Join-Path $outDir ("py_scripts_{0}.json" -f $ts)
$csv  = [IO.Path]::ChangeExtension($json,".csv")

function Get-FileTextSafe([string]$path){
  try { return Get-Content $path -Raw -ErrorAction Stop } catch { }
  try { return [System.IO.File]::ReadAllText($path,[Text.UTF8Encoding]::new($false)) } catch { }
  try { return [System.IO.File]::ReadAllText($path,[Text.Encoding]::Unicode) } catch { }
  try { return [System.IO.File]::ReadAllText($path,[Text.Encoding]::Default) } catch { }
  return ""
}

$files = Get-ChildItem $Root -Recurse -Include *.py -File | Where-Object {
  $_.FullName -notmatch "\\\.venv|\\envs\\|\\site-packages\\|\\__pycache__\\"
}

$rows = foreach($f in $files){
  $txt = Get-FileTextSafe $f.FullName
  $txt = if ($null -ne $txt) { $txt } else { "" }

  $hasArgparse = ($txt -ne "" -and $txt -match "import\s+argparse")
  $hasClick    = ($txt -ne "" -and $txt -match "import\s+click")
  $hasTyper    = ($txt -ne "" -and $txt -match "import\s+typer")
  $usesReq     = ($txt -ne "" -and $txt -match "import\s+requests")
  $usesBS      = ($txt -ne "" -and ($txt -match "from\s+bs4" -or $txt -match "BeautifulSoup"))
  $usesFeed    = ($txt -ne "" -and $txt -match "feedparser")
  $usesRead    = ($txt -ne "" -and $txt -match "readability")
  $usesNewsp   = ($txt -ne "" -and ($txt -match "newspaper3k" -or $txt -match "from\s+newspaper\s+import"))
  $usesPandas  = ($txt -ne "" -and $txt -match "import\s+pandas")
  $usesCSV     = ($txt -ne "" -and $txt -match "import\s+csv")

  $flags = ""
  if ($txt -ne "") {
    $flagMatches = [regex]::Matches($txt,'--[a-zA-Z0-9_-]+')
    $flags = ($flagMatches | ForEach-Object { $_.Value } | Select-Object -Unique) -join " "
  }

  $funcs = ""
  if ($txt -ne "") {
    $funcMatches = [regex]::Matches($txt,'def\s+([a-zA-Z_][a-zA-Z0-9_]*)\(')
    $funcs = ($funcMatches | ForEach-Object { $_.Groups[1].Value } | Select-Object -Unique) -join " "
  }

  $doc = ""
  if ($txt -ne "") {
    $docMatch = [regex]::Match($txt,'"""(.|\n){0,400}?"""')
    if($docMatch.Success){ $doc = ($docMatch.Value -replace '"""','').Trim() }
  }

  # fallback capacité si fichier illisible: nom du fichier
  $cap = @()
  if ($usesFeed -or ($usesReq -and $usesBS) -or ($f.Name -match '^scrape|^ingest|harvest')) { $cap += "harvest" }
  if ($usesRead -or $usesNewsp -or ($f.Name -match 'extract|article')) { $cap += "article_extraction" }
  if ($usesCSV -or $usesPandas -or ($f.Name -match 'csv|merge|validate|export|report')) { $cap += "csv_io" }
  $capability = ($cap | Select-Object -Unique) -join ";"

  [pscustomobject]@{
    path        = $f.FullName.Substring($Root.Length).TrimStart('\')
    name        = $f.Name
    size        = $f.Length
    argparse    = $hasArgparse
    click       = $hasClick
    typer       = $hasTyper
    requests    = $usesReq
    bs4         = $usesBS
    feedparser  = $usesFeed
    readability = $usesRead
    newspaper3k = $usesNewsp
    pandas      = $usesPandas
    csv_mod     = $usesCSV
    flags       = $flags
    funcs       = $funcs
    doc         = $doc
    capability  = $capability
  }
}

$rows | ConvertTo-Json -Depth 4 | Set-Content $json -Encoding UTF8
$rows | Export-Csv -NoTypeInformation -Encoding UTF8 $csv
Write-Host "Inventaire:" $csv
