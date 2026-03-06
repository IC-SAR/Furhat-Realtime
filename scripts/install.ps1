$ErrorActionPreference = "Stop"

$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$venv = Join-Path $root ".venv"
$requirements = Join-Path $root "requirements.txt"

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
  Write-Error "Python not found. Install Python 3.10+ and try again."
  exit 1
}

$pyver = python - <<'PY'
import sys
print(f"{sys.version_info.major}.{sys.version_info.minor}")
PY

$major, $minor = $pyver.Trim().Split(".") | ForEach-Object { [int]$_ }
if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 10)) {
  Write-Error "Python 3.10+ is required. Detected $pyver."
  exit 1
}

if (-not (Test-Path $venv)) {
  python -m venv $venv
}

$python = Join-Path $venv "Scripts\python.exe"
& $python -m pip install --upgrade pip
& $python -m pip install -r $requirements

Write-Host "Install complete."
Write-Host "Next: run .\\scripts\\run.ps1"
