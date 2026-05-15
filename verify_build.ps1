#requires -Version 7
# verify_build.ps1 — post-deploy sanity check for the 2026-05-15 fan-out + Box->R2 + Sheets->Airtable batch.
# Runs from any cwd. Reads the snapshot from n8n_backups/ and queries Airtable via Python subprocess (env files denied to Claude directly).

$ErrorActionPreference = 'Continue'
$repo     = 'C:\CONTENT_PIPELINE'
$snapshot = Join-Path $repo 'n8n_backups\GetAutomata_W01-W05_CREDENTIALS_2026-05-15.json'

$pass = 0
$fail = 0
function Mark-Pass($label) { Write-Host "  PASS  $label" -ForegroundColor Green; $script:pass++ }
function Mark-Fail($label) { Write-Host "  FAIL  $label" -ForegroundColor Red;   $script:fail++ }
function Mark-Info($label) { Write-Host "  INFO  $label" -ForegroundColor Yellow }

Write-Host "=== BUILD VERIFICATION  (2026-05-15) ===" -ForegroundColor Cyan

# --- A. git log ---
Write-Host "`n[A] git log --oneline -5  (expecting 51e50a9 and 768d254):" -ForegroundColor Cyan
Push-Location $repo
$gitLog = git log --oneline -5
Pop-Location
$gitLog | ForEach-Object { Write-Host "      $_" }
$hasFirst  = ($gitLog | Select-String -SimpleMatch '51e50a9').Count -gt 0
$hasSecond = ($gitLog | Select-String -SimpleMatch '768d254').Count -gt 0
if ($hasFirst)  { Mark-Pass 'commit 51e50a9 present' } else { Mark-Fail 'commit 51e50a9 missing' }
if ($hasSecond) { Mark-Pass 'commit 768d254 present' } else { Mark-Fail 'commit 768d254 missing' }

# --- B. Snapshot file exists, size ~586KB ---
Write-Host "`n[B] Snapshot file:" -ForegroundColor Cyan
if (Test-Path $snapshot) {
    $bytes = (Get-Item $snapshot).Length
    $kb    = [math]::Round($bytes / 1KB, 1)
    Write-Host "      $snapshot"
    Write-Host "      Size: $kb KB ($bytes bytes)"
    if ($kb -ge 560 -and $kb -le 620) { Mark-Pass "size $kb KB within 560-620" } else { Mark-Fail "size $kb KB outside 560-620" }
} else {
    Mark-Fail "snapshot not found at $snapshot"
}

# --- C. Node count = 465 ---
Write-Host "`n[C] Node count in snapshot  (expected 465):" -ForegroundColor Cyan
try {
    $json = Get-Content $snapshot -Raw | ConvertFrom-Json -Depth 100
    $nodeCount = $json.nodes.Count
    Write-Host "      Nodes: $nodeCount"
    if ($nodeCount -eq 465) { Mark-Pass 'node count = 465' } else { Mark-Fail "node count = $nodeCount (expected 465)" }
} catch {
    Mark-Fail "JSON parse failed: $_"
}

# --- D. Airtable tables exist via API ---
Write-Host "`n[D] Airtable tables in base appC3HqG42ftswOvw  (expecting n16_Data, R39_Data, n19_Data, n21_Data, n3_Data):" -ForegroundColor Cyan
$pyScript = @'
import sys, requests
sys.path.insert(0, r"C:\CONTENT_PIPELINE\R57_content_engine")
from tools import config
url = f"https://api.airtable.com/v0/meta/bases/{config.AIRTABLE_BASE_ID}/tables"
r = requests.get(url, headers={"Authorization": f"Bearer {config.AIRTABLE_API_KEY}"})
if r.status_code != 200:
    print(f"API_ERR {r.status_code} {r.text[:200]}")
    sys.exit(1)
tables = {t["name"]: t["id"] for t in r.json()["tables"]}
for name in ["n16_Data","R39_Data","n19_Data","n21_Data","n3_Data"]:
    if name in tables:
        print(f"OK {name} {tables[name]}")
    else:
        print(f"MISS {name}")
'@
$pyResult = $pyScript | python -
$pyResult | ForEach-Object { Write-Host "      $_" }
$okLines   = @($pyResult | Where-Object { $_ -match '^OK ' })
$missLines = @($pyResult | Where-Object { $_ -match '^MISS ' })
if ($okLines.Count -eq 5 -and $missLines.Count -eq 0) { Mark-Pass 'all 5 Airtable tables exist' } else { Mark-Fail "$($okLines.Count)/5 tables found, $($missLines.Count) missing" }

# --- E. row_number occurrences ---
Write-Host "`n[E] 'row_number' occurrences in snapshot:" -ForegroundColor Cyan
$rnMatches = Select-String -Path $snapshot -Pattern 'row_number' -AllMatches
$rnTotal = ($rnMatches | ForEach-Object { $_.Matches.Count } | Measure-Object -Sum).Sum
if (-not $rnTotal) { $rnTotal = 0 }
Write-Host "      Total occurrences: $rnTotal"
if ($rnTotal -eq 0) {
    Mark-Pass 'zero row_number references (fully cleaned)'
} else {
    Mark-Info "$rnTotal row_number references remain (expected — §H operator-audit follow-up)"
}

# --- F. R2_ENDPOINT presence ---
Write-Host "`n[F] 'R2_ENDPOINT' occurrences in snapshot  (expecting >= 3 — one per ex-Box node):" -ForegroundColor Cyan
$r2Matches = Select-String -Path $snapshot -Pattern 'R2_ENDPOINT' -AllMatches
$r2Total = ($r2Matches | ForEach-Object { $_.Matches.Count } | Measure-Object -Sum).Sum
if (-not $r2Total) { $r2Total = 0 }
Write-Host "      Total occurrences: $r2Total"
if ($r2Total -ge 3) { Mark-Pass "R2_ENDPOINT referenced $r2Total times (>=3)" } else { Mark-Fail "R2_ENDPOINT referenced only $r2Total times (expected >=3)" }

# --- Summary ---
Write-Host "`n=== SUMMARY ===" -ForegroundColor Cyan
Write-Host ("  PASS: {0}" -f $pass) -ForegroundColor Green
$failColor = if ($fail -gt 0) { 'Red' } else { 'Green' }
Write-Host ("  FAIL: {0}" -f $fail) -ForegroundColor $failColor
if ($fail -gt 0) { exit 1 } else { exit 0 }
