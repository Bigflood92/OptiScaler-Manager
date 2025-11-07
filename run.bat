@echo off
REM Script de arranque para FSR Injector con Python 3.12
echo Iniciando Gestor OptiScaler V2.0...
echo.

REM Verificar si existe el entorno virtual Python 3.12
if not exist ".venv312\Scripts\python.exe" (
    echo ERROR: No se encontro el entorno virtual Python 3.12
    echo Por favor ejecuta: py -3.12 -m venv .venv312
    echo Luego instala las dependencias: .venv312\Scripts\pip install -r requirements.txt
    pause
    exit /b 1
)

REM Ejecutar la aplicacion
.venv312\Scripts\python.exe -m src.main

if errorlevel 1 (
    echo.
    echo ERROR: La aplicacion termino con errores
    pause
)
