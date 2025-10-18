<#
.\runserver-local.ps1
Starts the Django development server bound to 127.0.0.1:8000 using the virtualenv python
so you don't accidentally expose the dev server on all interfaces (0.0.0.0) and see
TLS/HTTPS handshake noise in the logs. No external packages required.

Usage:
  Right-click -> Run with PowerShell, or from PowerShell:
    .\runserver-local.ps1
#>

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition
$venvPython = Join-Path $projectRoot 'env\Scripts\python.exe'

if (Test-Path $venvPython) {
    Write-Host "Using virtualenv python: $venvPython"
    & $venvPython manage.py runserver 127.0.0.1:8000
} else {
    Write-Host "Virtualenv python not found, falling back to system python"
    python manage.py runserver 127.0.0.1:8000
}
