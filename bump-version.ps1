# Script simple para incrementar versión en archivos
# Uso: .\bump-version.ps1 -NewVersion "2.0.2"

param(
    [Parameter(Mandatory=$true)]
    [string]$NewVersion
)

$ErrorActionPreference = "Stop"

Write-Host "Actualizando versión a: $NewVersion" -ForegroundColor Cyan

# README.md
if (Test-Path "README.md") {
    $content = Get-Content "README.md" -Raw
    $content = $content -replace 'version-\d+\.\d+\.\d+', "version-$NewVersion"
    Set-Content "README.md" $content -NoNewline
    Write-Host "✓ README.md actualizado" -ForegroundColor Green
}

# constants.py
$constFile = "src\config\constants.py"
if (Test-Path $constFile) {
    $content = Get-Content $constFile -Raw
    $content = $content -replace 'VERSION = ".*"', "VERSION = `"$NewVersion`""
    Set-Content $constFile $content -NoNewline
    Write-Host "✓ constants.py actualizado" -ForegroundColor Green
} else {
    Write-Host "! constants.py no existe (se creará en próxima release)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Versión actualizada a $NewVersion" -ForegroundColor Green
Write-Host "No olvides actualizar CHANGELOG.md manualmente" -ForegroundColor Yellow
