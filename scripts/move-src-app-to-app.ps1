Param(
  [string]$FrontendRoot = "frontend",
  [switch]$DryRun
)

$ErrorActionPreference = "Stop"
function Timestamp { Get-Date -Format "yyyyMMdd-HHmmss" }

$root   = (Resolve-Path $FrontendRoot).Path
$srcApp = Join-Path $root "src\app"
$dstApp = Join-Path $root "app"

if (-not (Test-Path $srcApp)) {
  Write-Host "[INFO] Nothing to do: '$srcApp' does not exist." -ForegroundColor Yellow
  exit 0
}

if (-not (Test-Path $dstApp)) {
  Write-Host "[INFO] Creating destination app dir: $dstApp"
  New-Item -ItemType Directory -Path $dstApp | Out-Null
}

Write-Host "=== Merge 'src/app' into 'app' (Next.js single app dir) ===" -ForegroundColor Cyan
Write-Host "Root:    $root"
Write-Host "Source:  $srcApp"
Write-Host "Dest:    $dstApp"
Write-Host "DryRun:  $DryRun"

$files = Get-ChildItem $srcApp -Recurse -File
Write-Host ("[INFO] {0} files found under src/app" -f $files.Count)
if ($DryRun) {
  $files | ForEach-Object { Write-Host ("DRYRUN -> {0}" -f $_.FullName.Replace($root, ".")) }
  exit 0
}

$backupDir = "$dstApp.__premerge__$(Timestamp)"
Write-Host "[INFO] Backing up current '$dstApp' to '$backupDir'"
Copy-Item -Recurse -Force $dstApp $backupDir

Write-Host "[INFO] Copying files from src/app to app (overwrite existing)"
robocopy $srcApp $dstApp /E /NP /NFL /NDL /NJH /NJS > $null
if ($LASTEXITCODE -ge 8) { throw "robocopy failed with code $LASTEXITCODE" }

Write-Host "[INFO] Removing '$srcApp'"
Remove-Item -Recurse -Force $srcApp

Write-Host "[DONE] Merge complete."
Write-Host "A backup of the old 'app' exists at: $backupDir"
Write-Host "Next:"
Write-Host "  1) git add -A && git commit -m 'Merge src/app into app; remove duplicate tree'"
Write-Host "  2) Rebuild frontend image and redeploy"
