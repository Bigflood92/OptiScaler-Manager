# Script para compilar localmente
$ErrorActionPreference = "Stop"

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "  COMPILAR EJECUTABLE LOCAL" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

if (-not (Test-Path ".venv312\Scripts\python.exe")) {
    Write-Host "ERROR: Entorno virtual no encontrado" -ForegroundColor Red
    Write-Host "Ejecuta primero: py -3.12 -m venv .venv312" -ForegroundColor Yellow
    exit 1
}

Write-Host "OK Entorno virtual encontrado" -ForegroundColor Green
Write-Host ""
Write-Host "Activando entorno virtual..." -ForegroundColor Cyan
& .\.venv312\Scripts\Activate.ps1

Write-Host ""
Write-Host "Verificando PyInstaller..." -ForegroundColor Cyan
pip install pyinstaller --quiet --disable-pip-version-check
Write-Host "OK PyInstaller listo" -ForegroundColor Green

Write-Host ""
Write-Host "Limpiando builds anteriores..." -ForegroundColor Cyan
if (Test-Path "build") { Remove-Item -Path "build" -Recurse -Force }
if (Test-Path "dist") { Remove-Item -Path "dist" -Recurse -Force }
Write-Host "OK Directorio limpio" -ForegroundColor Green

Write-Host ""
Write-Host "Compilando con PyInstaller..." -ForegroundColor Cyan
Write-Host "Esto puede tardar 1-2 minutos" -ForegroundColor Yellow
Write-Host ""

pyinstaller --noconfirm "Gestor optiscaler V2.0.spec"

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "ERROR: La compilacion fallo" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "==================================================" -ForegroundColor Green
Write-Host "  COMPILACION EXITOSA" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green
Write-Host ""

$exePath = "dist\Gestor optiscaler V2.0.exe"
if (-not (Test-Path $exePath)) {
    Write-Host "ADVERTENCIA: No se encontro el ejecutable" -ForegroundColor Yellow
    exit 0
}

$size = (Get-Item $exePath).Length / 1MB
Write-Host "Ejecutable creado:" -ForegroundColor White
Write-Host "  Ubicacion: $exePath" -ForegroundColor Yellow
Write-Host "  Tamano: $([math]::Round($size, 2)) MB" -ForegroundColor Yellow
Write-Host ""

$test = Read-Host "Ejecutar el .exe para probar? (s/n)"
if ($test -eq "s" -or $test -eq "S") {
    Write-Host ""
    Write-Host "Ejecutando..." -ForegroundColor Cyan
    Start-Process $exePath
}
