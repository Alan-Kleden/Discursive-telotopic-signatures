param(
  [string]$ProjectRoot = "G:\Mon Drive\Signatures_Telotopiques_POC",
  [string]$OsfRoot     = "H:\PoC_OSF"
)

# ---------- helpers ----------
function Test-BOM {
  param([string]$Path)
  try {
    $fs = [System.IO.File]::OpenRead($Path)
    try {
      $b = New-Object byte[] 3
      $null = $fs.Read($b, 0, 3)
      return ($b[0] -eq 0xEF -and $b[1] -eq 0xBB -and $b[2] -eq 0xBF)
    } finally { $fs.Close() }
  } catch { return $false }
}

function Get-LineEnding {
  param([string]$Path)
  try {
    $raw = Get-Content -Path $Path -Raw -ErrorAction Stop
    if ($raw -match "`r`n") { "CRLF" }
    elseif ($raw -match "`n") { "LF" }
    else { "Unknown" }
  } catch { "Unknown" }
}

function Get-TitleH1 {
  param([string]$Path)
  try {
    $content = Get-Content -Path $Path -TotalCount 200 -ErrorAction Stop
    foreach ($line in $content) {
      if ($line -match '^\s*#\s+(.+?)\s*$') { return $matches[1].Trim() }
    }
    return ""
  } catch { return "" }
}

# ---------- collecte ----------
$roots = @()
if (Test-Path $ProjectRoot) { $roots += @{Root=$ProjectRoot; Label="PROJECT"} }
if (Test-Path $OsfRoot)     { $roots += @{Root=$OsfRoot;     Label="OSF"} }

if ($roots.Count -eq 0) {
  Write-Error "Aucune racine valide. Vérifie ProjectRoot / OsfRoot."
  exit 1
}

$inventory = New-Object System.Collections.Generic.List[psobject]
$excludeDirs = @("\.git", "\.venv", "\.venv_old", "node_modules", "dist", "build", "\.tox")

foreach ($r in $roots) {
  $root = $r.Root
  $label = $r.Label
  Write-Host "Scan: $label -> $root" -ForegroundColor Cyan

  $files = Get-ChildItem -Path $root -Recurse -Filter *.md -File -ErrorAction SilentlyContinue
  foreach ($f in $files) {
    $rel = $f.FullName.Substring($root.Length).TrimStart('\','/')
    # exclusions simples
    if ($excludeDirs | ForEach-Object { if ($rel -match $_) { $true } } | Where-Object { $_ } ) { continue }

    $inventory.Add([pscustomobject]@{
      RootLabel   = $label
      RootPath    = $root
      Relative    = $rel
      FileName    = $f.Name
      TitleH1     = Get-TitleH1 $f.FullName
      SizeKB      = [math]::Round($f.Length/1KB,2)
      Modified    = $f.LastWriteTime.ToString("yyyy-MM-dd HH:mm:ss")
      HasBOM      = Test-BOM $f.FullName
      LineEnding  = Get-LineEnding $f.FullName
      SHA256      = (Get-FileHash -Path $f.FullName -Algorithm SHA256).Hash
      FullPath    = $f.FullName
    }) | Out-Null
  }
}

# ---------- sorties ----------
$outRoot = if (Test-Path $OsfRoot) { Join-Path $OsfRoot "_audit" } else { Join-Path $ProjectRoot "_audit" }
New-Item -ItemType Directory -Path $outRoot -Force | Out-Null

$invCsv  = Join-Path $outRoot "md_inventory.csv"
$inventory | Sort-Object RootLabel, Relative | Export-Csv -Path $invCsv -NoTypeInformation -Encoding UTF8
Write-Host "Inventaire : $invCsv" -ForegroundColor Yellow

# Doublons par nom
$dupName = $inventory | Group-Object FileName | Where-Object { $_.Count -gt 1 } |
  ForEach-Object {
    $_.Group | Select-Object FileName, RootLabel, Relative, SizeKB, Modified, SHA256
  }
$dupNameCsv = Join-Path $outRoot "dup_by_name.csv"
$dupName | Export-Csv -Path $dupNameCsv -NoTypeInformation -Encoding UTF8
Write-Host "Doublons (nom) : $dupNameCsv" -ForegroundColor Yellow

# Doublons par contenu (hash)
$dupHash = $inventory | Group-Object SHA256 | Where-Object { $_.Count -gt 1 } |
  ForEach-Object {
    $_.Group | Select-Object SHA256, FileName, RootLabel, Relative, SizeKB, Modified
  }
$dupHashCsv = Join-Path $outRoot "dup_by_hash.csv"
$dupHash | Export-Csv -Path $dupHashCsv -NoTypeInformation -Encoding UTF8
Write-Host "Doublons (hash) : $dupHashCsv" -ForegroundColor Yellow

# Petit résumé à l'écran
$summary = $inventory | Group-Object RootLabel | ForEach-Object { [pscustomobject]@{Root=$_.Name; Count=$_.Count} }
$summary | Format-Table -AutoSize
