# Script para compilar localmente (testing antes de release)
# Uso: .\build-local.ps1

$ErrorActionPreference = "Stop"

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "  COMPILAR EJECUTABLE LOCAL" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

# Verificar entorno virtual
if (-not (Test-Path ".venv312\Scripts\python.exe")) {
    Write-Host "ERROR: Entorno virtual no encontrado" -ForegroundColor Red
    Write-Host "Ejecuta primero: py -3.12 -m venv .venv312" -ForegroundColor Yellow
    exit 1
}

Write-Host "✓ Entorno virtual encontrado" -ForegroundColor Green

# Activar entorno virtual
Write-Host ""
Write-Host "Activando entorno virtual..." -ForegroundColor Cyan
& .\.venv312\Scripts\Activate.ps1

# Instalar/actualizar PyInstaller
Write-Host ""
Write-Host "Verificando PyInstaller..." -ForegroundColor Cyan
pip install pyinstaller --quiet --disable-pip-version-check
Write-Host "✓ PyInstaller listo" -ForegroundColor Green

# Limpiar builds anteriores
Write-Host ""
Write-Host "Limpiando builds anteriores..." -ForegroundColor Cyan
if (Test-Path "build") { Remove-Item -Path "build" -Recurse -Force }
if (Test-Path "dist") { Remove-Item -Path "dist" -Recurse -Force }
Write-Host "✓ Directorio limpio" -ForegroundColor Green

# Compilar con PyInstaller
Write-Host ""
Write-Host "Compilando con PyInstaller..." -ForegroundColor Cyan
Write-Host "(Esto puede tardar 1-2 minutos)" -ForegroundColor Yellow
Write-Host ""

pyinstaller --noconfirm "Gestor optiscaler V2.0.spec"

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "==================================================" -ForegroundColor Green
    Write-Host "  COMPILACIÓN EXITOSA" -ForegroundColor Green
    Write-Host "==================================================" -ForegroundColor Green
    Write-Host ""
    
    $exePath = "dist\Gestor optiscaler V2.0.exe"
    if (Test-Path $exePath) {
        $size = (Get-Item $exePath).Length / 1MB
        Write-Host "Ejecutable creado:" -ForegroundColor White
        Write-Host "  Ubicación: $exePath" -ForegroundColor Yellow
        Write-Host "  Tamaño: $([math]::Round($size, 2)) MB" -ForegroundColor Yellow
        Write-Host ""
        
        $test = Read-Host "¿Ejecutar el .exe para probar? (s/n)"
        if ($test -eq "s" -or $test -eq "S") {
            Write-Host ""
            Write-Host "Ejecutando..." -ForegroundColor Cyan
            Start-Process $exePath -Verb RunAs
        }
    }
} else {
    Write-Host ""
    Write-Host "ERROR: La compilación falló" -ForegroundColor Red
    Write-Host "Revisa los mensajes de error arriba" -ForegroundColor Yellow
    exit 1
}
