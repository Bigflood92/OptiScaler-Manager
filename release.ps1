# Script para crear una nueva release
# Uso: .\release.ps1 -Version "2.0.2" -Type "patch"

param(
    [Parameter(Mandatory=$true)]
    [string]$Version,
    
    [Parameter(Mandatory=$true)]
    [ValidateSet("major", "minor", "patch")]
    [string]$Type,
    
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "  CREAR NUEVA RELEASE v$Version" -ForegroundColor Cyan
Write-Host "  Tipo: $Type" -ForegroundColor Cyan
if ($DryRun) {
    Write-Host "  MODO: DRY RUN (no se ejecutarán cambios)" -ForegroundColor Yellow
}
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

# Validar formato de versión
if ($Version -notmatch '^\d+\.\d+\.\d+$') {
    Write-Host "ERROR: Formato de versión inválido. Usa MAJOR.MINOR.PATCH (ej: 2.0.2)" -ForegroundColor Red
    exit 1
}

# Verificar que no hay cambios sin commit
$status = git status --porcelain
if ($status -and -not $DryRun) {
    Write-Host "ERROR: Hay cambios sin commitear:" -ForegroundColor Red
    Write-Host $status -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Por favor, commit o stash los cambios primero." -ForegroundColor Yellow
    exit 1
}

Write-Host "✓ No hay cambios sin commitear" -ForegroundColor Green

# Actualizar archivos de versión
Write-Host ""
Write-Host "Actualizando archivos de versión..." -ForegroundColor Cyan

$files = @(
    "README.md",
    "mkdocs.yml"
)

foreach ($file in $files) {
    if (Test-Path $file) {
        Write-Host "  - Actualizando $file" -ForegroundColor White
        if (-not $DryRun) {
            $content = Get-Content $file -Raw
            
            # Actualizar versión en README badges
            if ($file -eq "README.md") {
                $content = $content -replace 'version-\d+\.\d+\.\d+', "version-$Version"
            }
            
            # Actualizar versión en mkdocs
            if ($file -eq "mkdocs.yml") {
                $content = $content -replace 'site_url:.*', "site_url: https://bigflood92.github.io/OptiScaler-Manager/"
            }
            
            Set-Content $file $content -NoNewline
        }
    }
}

# Crear constantes de versión si no existe
$constFile = "src\config\constants.py"
if (-not (Test-Path $constFile)) {
    Write-Host "  - Creando $constFile" -ForegroundColor White
    if (-not $DryRun) {
        $constContent = @"
"""
Constantes de configuración de la aplicación.
"""

VERSION = "$Version"
APP_NAME = "OptiScaler Manager"
AUTHOR = "Jorge Coronas"
"@
        New-Item -Path "src\config" -Name "constants.py" -ItemType File -Value $constContent -Force | Out-Null
    }
} else {
    Write-Host "  - Actualizando $constFile" -ForegroundColor White
    if (-not $DryRun) {
        $content = Get-Content $constFile -Raw
        $content = $content -replace 'VERSION = ".*"', "VERSION = `"$Version`""
        Set-Content $constFile $content -NoNewline
    }
}

Write-Host "✓ Archivos actualizados" -ForegroundColor Green

# Commit cambios de versión
if (-not $DryRun) {
    Write-Host ""
    Write-Host "Commiteando cambios de versión..." -ForegroundColor Cyan
    git add README.md mkdocs.yml src/config/constants.py 2>$null
    git commit -m "chore: bump version to $Version" 2>$null
    Write-Host "✓ Commit creado" -ForegroundColor Green
}

# Crear tag
Write-Host ""
Write-Host "Creando tag v$Version..." -ForegroundColor Cyan
if (-not $DryRun) {
    $tagMessage = "Release v$Version - OptiScaler Manager"
    git tag -a "v$Version" -m $tagMessage
    Write-Host "✓ Tag creado localmente" -ForegroundColor Green
} else {
    Write-Host "[DRY RUN] Se crearía el tag v$Version" -ForegroundColor Yellow
}

# Push cambios y tag
Write-Host ""
Write-Host "Subiendo cambios a GitHub..." -ForegroundColor Cyan
if (-not $DryRun) {
    git push origin main
    git push origin "v$Version"
    Write-Host "✓ Cambios y tag subidos" -ForegroundColor Green
} else {
    Write-Host "[DRY RUN] Se subirían los cambios y el tag" -ForegroundColor Yellow
}

# Resumen
Write-Host ""
Write-Host "==================================================" -ForegroundColor Green
Write-Host "  RELEASE v$Version CREADA EXITOSAMENTE" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green
Write-Host ""

if (-not $DryRun) {
    Write-Host "GitHub Actions está compilando el ejecutable..." -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Puedes ver el progreso en:" -ForegroundColor White
    Write-Host "  https://github.com/Bigflood92/OptiScaler-Manager/actions" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "En unos minutos estará disponible en:" -ForegroundColor White
    Write-Host "  https://github.com/Bigflood92/OptiScaler-Manager/releases/tag/v$Version" -ForegroundColor Yellow
    Write-Host ""
    
    $openActions = Read-Host "¿Abrir GitHub Actions ahora? (s/n)"
    if ($openActions -eq "s" -or $openActions -eq "S") {
        start "https://github.com/Bigflood92/OptiScaler-Manager/actions"
    }
} else {
    Write-Host "[DRY RUN] No se ejecutaron cambios reales" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Siguiente paso: Actualiza CHANGELOG.md con los cambios de esta versión" -ForegroundColor Cyan
