# Build OptiScaler Manager with Nuitka (Admin UAC prompt)
# Usage: run from repo root: .\build_nuitka_admin.ps1

$ErrorActionPreference = "Stop"

# Use venv Python if exists, otherwise system Python
if (Test-Path ".\.venv312\Scripts\python.exe") {
    $python = ".\.venv312\Scripts\python.exe"
} else {
    $python = "python"
}

# Ensure output directory exists
if (-not (Test-Path -Path "dist")) {
    New-Item -ItemType Directory -Path "dist" | Out-Null
}

# Compile with admin prompt by default
& $python -m nuitka `
  --standalone `
  --onefile `
  --windows-console-mode=disable `
  --enable-plugin=tk-inter `
  --include-data-dir=icons=icons `
  --windows-uac-admin `
  --assume-yes-for-downloads `
  --output-dir=dist `
  --output-filename="Gestor Optiscaler V2.0 ADMIN.exe" `
  src/main.py

if ($LASTEXITCODE -ne 0) {
    Write-Host "Build failed with exit code $LASTEXITCODE" -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host "Build completed: dist\\Gestor Optiscaler V2.0 ADMIN.exe" -ForegroundColor Green
