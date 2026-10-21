# Gera instalador\dist\VadeTribunal.exe (Python embutido; o jogo e as leis são baixados ao abrir).
#   powershell -ExecutionPolicy Bypass -File instalador\build.ps1
# Dica: rode de uma pasta com caminho curto (ex.: C:\vade). O Windows limita caminhos a 260 caracteres.
$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$venv = Join-Path $env:TEMP "vade-build-venv"
if (-not (Test-Path "$venv\Scripts\python.exe")) {
    python -m venv $venv
    & "$venv\Scripts\python.exe" -m pip install -q --disable-pip-version-check pyinstaller
}
$icon = Join-Path $here "vade.ico"
& "$venv\Scripts\python.exe" (Join-Path $here "gerar_icone.py") $icon
Push-Location $here
try {
    # --icon com caminho absoluto: o PyInstaller resolve caminhos relativos a partir do --specpath
    & "$venv\Scripts\python.exe" -m PyInstaller --noconfirm --clean --onefile --windowed `
        --name VadeTribunal --icon $icon `
        --distpath dist --workpath build --specpath build vade_launcher.py
} finally { Pop-Location }
Write-Host "Pronto: $here\dist\VadeTribunal.exe"
