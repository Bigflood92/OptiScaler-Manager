# Script para limpiar el historial de Git eliminando artefactos de build pesados
# Usa BFG Repo-Cleaner para purgar run.dist/, run.build/, etc. del historial completo
# ADVERTENCIA: Este script reescribe el historial de Git. Haz backup antes.

param(
    [switch]$DryRun = $false,
    [switch]$SkipBackup = $false
)

$ErrorActionPreference = "Stop"

Write-Host "===============================================================" -ForegroundColor Cyan
Write-Host "  LIMPIEZA DE HISTORIAL GIT - BFG Repo-Cleaner" -ForegroundColor Cyan
Write-Host "===============================================================" -ForegroundColor Cyan
Write-Host ""

if ($DryRun) {
    Write-Host "MODO DRY-RUN: Solo se mostrara lo que se haria" -ForegroundColor Yellow
    Write-Host ""
}

# 1. Verificar que estamos en un repositorio git
Write-Host "[1/8] Verificando repositorio Git..." -ForegroundColor Cyan
if (-not (Test-Path ".git")) {
    Write-Host "ERROR: No estas en la raiz de un repositorio Git" -ForegroundColor Red
    exit 1
}
Write-Host "OK Repositorio Git detectado" -ForegroundColor Green
Write-Host ""

# 2. Verificar que no hay cambios sin commitear
Write-Host "[2/8] Verificando estado del repositorio..." -ForegroundColor Cyan
$status = git status --porcelain
if ($status -and -not $DryRun) {
    Write-Host "ERROR: Hay cambios sin commitear:" -ForegroundColor Red
    Write-Host $status -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Commitea o stash los cambios antes de continuar." -ForegroundColor Yellow
    exit 1
}
Write-Host "OK No hay cambios pendientes" -ForegroundColor Green
Write-Host ""

# 3. Crear backup del repositorio
if (-not $SkipBackup -and -not $DryRun) {
    Write-Host "[3/8] Creando backup del repositorio..." -ForegroundColor Cyan
    $backupPath = "..\OptiScaler-Manager-backup-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
    
    Write-Host "  Copiando a: $backupPath" -ForegroundColor White
    Copy-Item -Path "." -Destination $backupPath -Recurse -Force
    Write-Host "OK Backup creado en: $backupPath" -ForegroundColor Green
    Write-Host ""
} else {
    Write-Host "[3/8] Saltando backup (-SkipBackup o -DryRun)" -ForegroundColor Yellow
    Write-Host ""
}

# 4. Verificar/instalar Java (necesario para BFG)
Write-Host "[4/8] Verificando Java..." -ForegroundColor Cyan

# Refresh PATH para detectar Java recién instalado
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

try {
    $javaVersion = java -version 2>&1 | Select-Object -First 1
    Write-Host "OK Java instalado: $javaVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Java no esta instalado" -ForegroundColor Red
    Write-Host ""
    Write-Host "Instala Java con:" -ForegroundColor Yellow
    Write-Host "  winget install -e --id Oracle.JavaRuntimeEnvironment" -ForegroundColor White
    Write-Host "O descarga desde: https://www.java.com/download/" -ForegroundColor White
    exit 1
}
Write-Host ""

# 5. Descargar BFG si no existe
Write-Host "[5/8] Verificando BFG Repo-Cleaner..." -ForegroundColor Cyan
$bfgJar = "bfg-1.14.0.jar"
$bfgUrl = "https://repo1.maven.org/maven2/com/madgag/bfg/1.14.0/bfg-1.14.0.jar"

if (-not (Test-Path $bfgJar)) {
    Write-Host "  Descargando BFG desde Maven..." -ForegroundColor White
    if (-not $DryRun) {
        Invoke-WebRequest -Uri $bfgUrl -OutFile $bfgJar
    }
    Write-Host "OK BFG descargado" -ForegroundColor Green
} else {
    Write-Host "OK BFG ya existe localmente" -ForegroundColor Green
}
Write-Host ""

# 6. Mostrar tamaño actual del repositorio
Write-Host "[6/8] Tamaño actual del repositorio..." -ForegroundColor Cyan
$repoSize = (Get-ChildItem -Path ".git" -Recurse -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum / 1MB
Write-Host "  Tamaño .git/: $([math]::Round($repoSize, 2)) MB" -ForegroundColor White
Write-Host ""

# 7. Ejecutar BFG para eliminar carpetas del historial
Write-Host "[7/8] Ejecutando BFG Repo-Cleaner..." -ForegroundColor Cyan
Write-Host "  Carpetas a purgar del historial:" -ForegroundColor White
Write-Host "    - run.dist/" -ForegroundColor Yellow
Write-Host "    - run.build/" -ForegroundColor Yellow
Write-Host "    - run.onefile-build/" -ForegroundColor Yellow
Write-Host "    - dist_nuitka/" -ForegroundColor Yellow
Write-Host "    - build_nuitka/" -ForegroundColor Yellow
Write-Host ""

if ($DryRun) {
    Write-Host "  [DRY-RUN] Se ejecutaria:" -ForegroundColor Yellow
    Write-Host "    java -jar $bfgJar --delete-folders '{run.dist,run.build,run.onefile-build,dist_nuitka,build_nuitka}' --no-blob-protection ." -ForegroundColor White
} else {
    Write-Host "  Ejecutando BFG (esto puede tardar unos minutos)..." -ForegroundColor White
    
    # BFG elimina las carpetas del historial completo
    java -jar $bfgJar --delete-folders '{run.dist,run.build,run.onefile-build,dist_nuitka,build_nuitka}' --no-blob-protection .
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: BFG fallo con codigo $LASTEXITCODE" -ForegroundColor Red
        exit $LASTEXITCODE
    }
    
    Write-Host "OK BFG completado" -ForegroundColor Green
    Write-Host ""
    
    # Limpiar refs y objetos huérfanos
    Write-Host "  Limpiando referencias y ejecutando garbage collection..." -ForegroundColor White
    git reflog expire --expire=now --all
    git gc --prune=now --aggressive
    
    Write-Host "OK Git GC completado" -ForegroundColor Green
}
Write-Host ""

# 8. Mostrar nuevo tamaño
Write-Host "[8/8] Resumen final..." -ForegroundColor Cyan
if (-not $DryRun) {
    $newRepoSize = (Get-ChildItem -Path ".git" -Recurse -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum / 1MB
    $saved = $repoSize - $newRepoSize
    
    Write-Host "  Tamaño anterior: $([math]::Round($repoSize, 2)) MB" -ForegroundColor White
    Write-Host "  Tamaño nuevo:    $([math]::Round($newRepoSize, 2)) MB" -ForegroundColor Green
    Write-Host "  Ahorrado:        $([math]::Round($saved, 2)) MB ($([math]::Round(($saved/$repoSize)*100, 1))%)" -ForegroundColor Cyan
}
Write-Host ""

# Instrucciones finales
Write-Host "===============================================================" -ForegroundColor Cyan
Write-Host "  SIGUIENTE PASO: FORCE PUSH" -ForegroundColor Cyan
Write-Host "===============================================================" -ForegroundColor Cyan
Write-Host ""

if ($DryRun) {
    Write-Host "[DRY-RUN] Para ejecutar la limpieza real:" -ForegroundColor Yellow
    Write-Host "  .\cleanup-git-history.ps1" -ForegroundColor White
} else {
    Write-Host "IMPORTANTE: El historial ha sido reescrito localmente." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Para aplicar los cambios en GitHub:" -ForegroundColor White
    Write-Host "  1. Verifica que todo funciona:" -ForegroundColor White
    Write-Host "     git log --oneline --graph --all" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  2. Haz force push (DESTRUCTIVO para colaboradores):" -ForegroundColor White
    Write-Host "     git push origin main --force" -ForegroundColor Red
    Write-Host ""
    Write-Host "  3. Si tienes otras ramas, actualizalas tambien:" -ForegroundColor White
    Write-Host "     git push origin --force --all" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Nota: Si trabajas con mas personas, coordinalos primero." -ForegroundColor Yellow
    Write-Host "   Tendran que hacer: git fetch origin ; git reset --hard origin/main" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Para restaurar el backup si algo falla:" -ForegroundColor White
    Write-Host "   Copia de vuelta desde: $backupPath" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "===============================================================" -ForegroundColor Green
Write-Host "  SCRIPT COMPLETADO" -ForegroundColor Green
Write-Host "===============================================================" -ForegroundColor Green
