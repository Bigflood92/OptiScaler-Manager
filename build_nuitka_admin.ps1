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
  --include-package=src `
  --include-data-dir=icons=icons `
  --windows-uac-admin `
  --assume-yes-for-downloads `
  --nofollow-import-to=more_itertools `
  --nofollow-import-to=setuptools `
  --nofollow-import-to=pkg_resources `
  --nofollow-import-to=importlib_metadata `
  --show-progress `
  --show-memory `
  --output-dir=dist `
  --output-filename="Gestor OptiScaler V2.3.1.exe" `
  run.py

if ($LASTEXITCODE -ne 0) {
    Write-Host "Build failed with exit code $LASTEXITCODE" -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host "Build completed: dist\Gestor OptiScaler V2.3.1.exe" -ForegroundColor Green
