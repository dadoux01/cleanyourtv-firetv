# One-step setup for Windows (PowerShell): prepares the Python environment and finds your Fire TV.
# Installation en une étape pour Windows (PowerShell). Usage:  powershell -ExecutionPolicy Bypass -File install.ps1
Set-Location $PSScriptRoot
$py = $null
foreach ($c in @('py', 'python')) { if (Get-Command $c -ErrorAction SilentlyContinue) { $py = $c; break } }
if (-not $py) {
    Write-Host 'Python 3.8+ is required / Python 3.8+ est requis : https://www.python.org/downloads/ (or: winget install Python.Python.3.12)'
    exit 1
}
$pyArgs = if ($py -eq 'py') { @('-3') } else { @() }
& $py @pyArgs firetv.py setup
if ($LASTEXITCODE -eq 0) { & $py @pyArgs firetv.py discover }
