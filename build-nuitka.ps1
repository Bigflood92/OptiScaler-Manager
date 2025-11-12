# Build optimized executable with Nuitka for performance comparison
# Requires: pip install nuitka ordered-set zstandard

$ErrorActionPreference = "Stop"

if (-not (Test-Path ".venv312\Scripts\python.exe")) {
    Write-Host "ERROR: Entorno virtual no encontrado (.venv312)" -ForegroundColor Red
    exit 1
}

& .\.venv312\Scripts\Activate.ps1

python -m pip install --quiet --disable-pip-version-check nuitka ordered-set zstandard
if ($LASTEXITCODE -ne 0) { exit 1 }

Write-Host "Limpiando build_nuitka/ y dist_nuitka/" -ForegroundColor Cyan
if (Test-Path "build_nuitka") { Remove-Item build_nuitka -Recurse -Force }
if (Test-Path "dist_nuitka") { Remove-Item dist_nuitka -Recurse -Force }

Write-Host "Compilando con Nuitka (esto tardará unos minutos)..." -ForegroundColor Cyan
python -m nuitka --onefile --nofollow-import-to=tkinter.test --include-data-dir=icons=icons `
  --output-dir=dist_nuitka --remove-output --standalone --windows-console-mode=disable `
  --enable-plugin=tk-inter --company-name="OptiScaler" --product-name="OptiScaler Manager" `
  --file-version=2.2.0.0 --product-version=2.2.0 `
  --include-package=src --include-package-data=src src/main.py

if ($LASTEXITCODE -ne 0) { exit 1 }

Write-Host "Nuitka build completado. Binarios en dist_nuitka/" -ForegroundColor Green
