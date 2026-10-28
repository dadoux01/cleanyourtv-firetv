# One-step setup for Windows (PowerShell): prepares the Python environment, then looks for your Fire TV.
# Installation en une étape pour Windows (PowerShell). Usage :  powershell -ExecutionPolicy Bypass -File install.ps1
$here = $PSScriptRoot
$check = 'import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)'
$py = $null; $pyArgs = @()
foreach ($c in @(@('py', '-3'), @('python'))) {
    $exe = $c[0]; $extra = @($c | Select-Object -Skip 1)
    $cmd = Get-Command $exe -ErrorAction SilentlyContinue
    # The Microsoft Store stub (WindowsApps\python.exe) only opens the Store: it fails the version check below.
    if ($cmd) {
        & $exe @extra -c $check 2>$null
        if ($LASTEXITCODE -eq 0) { $py = $exe; $pyArgs = $extra; break }
    }
}
if (-not $py) {
    [Console]::Error.WriteLine('Python 3.8+ is required / Python 3.8+ est requis : https://www.python.org/downloads/ (or: winget install Python.Python.3.12)')
    exit 1
}
& $py @pyArgs (Join-Path $here 'firetv.py') setup
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& $py @pyArgs (Join-Path $here 'firetv.py') discover
exit 0
