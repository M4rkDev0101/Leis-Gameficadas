# Gera instalador\dist\VadeTribunal.exe (Python embutido; o jogo e as leis são baixados ao abrir).
#   powershell -ExecutionPolicy Bypass -File instalador\build.ps1
$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$venv = Join-Path $env:TEMP "vade-build-venv"
if (-not (Test-Path "$venv\Scripts\python.exe")) {
    python -m venv $venv
    & "$venv\Scripts\python.exe" -m pip install -q --disable-pip-version-check pyinstaller
}
& "$venv\Scripts\python.exe" "$here\gerar_icone.py" "$here\vade.ico"
Push-Location $here
try {
    & "$venv\Scripts\python.exe" -m PyInstaller --noconfirm --clean --onefile --windowed `
        --name VadeTribunal --icon vade.ico `
        --distpath dist --workpath build --specpath build vade_launcher.py
} finally { Pop-Location }
Write-Host "Pronto: $here\dist\VadeTribunal.exe"
