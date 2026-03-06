$ErrorActionPreference = "Stop"

$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$venvPython = Join-Path $root ".venv\\Scripts\\python.exe"

if (Test-Path $venvPython) {
  $python = $venvPython
} else {
  $python = "python"
}

$env:PYTHONPATH = (Join-Path $root "src")

try {
  $null = ollama ps 2>$null
} catch {
  Write-Host "Ollama not detected. Start it in another window: ollama serve"
}

& $python (Join-Path $root "src\\Furhat\\main.py")
