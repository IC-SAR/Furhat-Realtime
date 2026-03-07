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
  $provider = & $python -c "from Furhat import settings_store; print(settings_store.load_settings().provider)"
  if ($provider.Trim() -eq "ollama") {
    try {
      $null = ollama ps 2>$null
    } catch {
      Write-Host "Ollama not detected. Start it in another window: ollama serve"
    }
  }
} catch {
}

& $python -m Furhat.main
