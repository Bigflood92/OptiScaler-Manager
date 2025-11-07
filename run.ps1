# Script de arranque para FSR Injector con Python 3.12
Write-Host "Iniciando Gestor OptiScaler V2.0..." -ForegroundColor Green
Write-Host ""

# Verificar si existe el entorno virtual Python 3.12
if (-not (Test-Path ".venv312\Scripts\python.exe")) {
    Write-Host "ERROR: No se encontro el entorno virtual Python 3.12" -ForegroundColor Red
    Write-Host "Por favor ejecuta: py -3.12 -m venv .venv312" -ForegroundColor Yellow
    Write-Host "Luego instala las dependencias: .venv312\Scripts\pip install -r requirements.txt" -ForegroundColor Yellow
    Read-Host "Presiona Enter para salir"
    exit 1
}

# Ejecutar la aplicacion desde la estructura modular
& .venv312\Scripts\python.exe -m src.main

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "ERROR: La aplicacion termino con errores" -ForegroundColor Red
    Read-Host "Presiona Enter para salir"
}
