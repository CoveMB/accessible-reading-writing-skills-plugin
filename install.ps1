Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

$Python = Get-Command py -ErrorAction SilentlyContinue
if (-not $Python) {
    $Python = Get-Command python3 -ErrorAction SilentlyContinue
}
if (-not $Python) {
    $Python = Get-Command python -ErrorAction SilentlyContinue
}
if (-not $Python) {
    throw "Python is required but was not found."
}

$PythonVersion = & $Python.Source -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
if ($LASTEXITCODE -ne 0) {
    throw "Python 3.10 or newer is required."
}
if ([version]$PythonVersion -lt [version]"3.10") {
    throw "Python 3.10 or newer is required."
}

$env:PYTHONDONTWRITEBYTECODE = "1"

if ($args -notcontains "--dry-run") {
    Write-Host "Tip: run .\install.ps1 --dry-run to preview marketplace registration."
}

& $Python.Source scripts\install_codex_plugin.py @args
if ($LASTEXITCODE -ne 0) {
    throw "Marketplace setup failed with exit code $LASTEXITCODE."
}
