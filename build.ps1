$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$buildPython = Join-Path $PSScriptRoot '.venv312\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $buildPython)) {
    $buildPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
}
& $buildPython scripts\generate_icon.py
if ($LASTEXITCODE -ne 0) { throw 'Icon generation failed' }
& $buildPython -m PyInstaller --noconfirm SystemMonitor.spec
if ($LASTEXITCODE -ne 0) { throw 'Executable build failed' }
Write-Output 'Built dist\SystemMonitor.exe'
