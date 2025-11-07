# Guía Interactiva para Tomar Capturas de Pantalla
# OptiScaler Manager

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "  GUIA PARA CAPTURAS DE PANTALLA" -ForegroundColor Cyan
Write-Host "  OptiScaler Manager" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

$imageFolder = ".github\images"

# Verificar que la aplicación esté ejecutándose
Write-Host "IMPORTANTE:" -ForegroundColor Yellow
Write-Host "- Asegurate de que 'Gestor optiscaler V2.0.exe' este abierto" -ForegroundColor White
Write-Host "- Usa la combinacion Win + Shift + S para capturar" -ForegroundColor White
Write-Host "- O usa Alt + PrtScn para capturar solo la ventana activa" -ForegroundColor White
Write-Host ""

# Captura 1
Write-Host "==================================================" -ForegroundColor Green
Write-Host "CAPTURA 1: main-interface.png" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Que capturar:" -ForegroundColor Yellow
Write-Host "1. Abre la aplicacion en modo clasico (pestañas)" -ForegroundColor White
Write-Host "2. Ve a la pestaña 'Juegos Detectados'" -ForegroundColor White
Write-Host "3. Si no hay juegos, haz clic en 'Escanear' o añade carpetas" -ForegroundColor White
Write-Host "4. Marca algunos juegos con checkbox" -ForegroundColor White
Write-Host "5. Asegurate de ver el panel de configuracion abajo" -ForegroundColor White
Write-Host ""
Write-Host "Presiona Enter cuando estes listo para capturar..." -ForegroundColor Cyan
Read-Host

Write-Host "Ahora:" -ForegroundColor Yellow
Write-Host "1. Haz clic en la ventana de la aplicacion" -ForegroundColor White
Write-Host "2. Presiona Win + Shift + S" -ForegroundColor White
Write-Host "3. Selecciona el area de la ventana" -ForegroundColor White
Write-Host "4. La captura se copiara al portapapeles" -ForegroundColor White
Write-Host "5. Abre Paint (Win + R, escribe 'mspaint', Enter)" -ForegroundColor White
Write-Host "6. Pega (Ctrl + V)" -ForegroundColor White
Write-Host "7. Guarda como: $imageFolder\main-interface.png" -ForegroundColor White
Write-Host ""
Write-Host "Presiona Enter cuando hayas guardado la imagen..." -ForegroundColor Cyan
Read-Host

# Captura 2
Write-Host ""
Write-Host "==================================================" -ForegroundColor Green
Write-Host "CAPTURA 2: gaming-mode.png" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Que hacer:" -ForegroundColor Yellow
Write-Host "1. En la aplicacion, busca el boton 🎮 (Gaming Mode)" -ForegroundColor White
Write-Host "2. Haz clic para cambiar al modo gaming" -ForegroundColor White
Write-Host "3. Navega a la seccion de 'Configuracion'" -ForegroundColor White
Write-Host "4. Asegurate de ver el menu lateral izquierdo" -ForegroundColor White
Write-Host ""
Write-Host "Presiona Enter cuando estes listo..." -ForegroundColor Cyan
Read-Host

Write-Host "Captura con Win + Shift + S y guarda como:" -ForegroundColor White
Write-Host "$imageFolder\gaming-mode.png" -ForegroundColor Yellow
Write-Host ""
Write-Host "Presiona Enter cuando hayas guardado..." -ForegroundColor Cyan
Read-Host

# Captura 3
Write-Host ""
Write-Host "==================================================" -ForegroundColor Green
Write-Host "CAPTURA 3: mod-downloader.png" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Que hacer:" -ForegroundColor Yellow
Write-Host "1. Ve a 'Ajustes de la App' o 'Configuracion'" -ForegroundColor White
Write-Host "2. Busca y haz clic en 'Descargar Mods'" -ForegroundColor White
Write-Host "3. Espera a que cargue la lista de versiones" -ForegroundColor White
Write-Host "4. Captura la ventana emergente" -ForegroundColor White
Write-Host ""
Write-Host "Presiona Enter cuando estes listo..." -ForegroundColor Cyan
Read-Host

Write-Host "Captura la ventana modal y guarda como:" -ForegroundColor White
Write-Host "$imageFolder\mod-downloader.png" -ForegroundColor Yellow
Write-Host ""
Write-Host "Presiona Enter cuando hayas guardado..." -ForegroundColor Cyan
Read-Host

# Captura 4
Write-Host ""
Write-Host "==================================================" -ForegroundColor Green
Write-Host "CAPTURA 4: game-config.png" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Que hacer:" -ForegroundColor Yellow
Write-Host "1. Vuelve a la lista de juegos" -ForegroundColor White
Write-Host "2. Selecciona un juego" -ForegroundColor White
Write-Host "3. Busca y haz clic en 'Configurar Juego' o similar" -ForegroundColor White
Write-Host "4. Captura la ventana de configuracion individual" -ForegroundColor White
Write-Host ""
Write-Host "Presiona Enter cuando estes listo..." -ForegroundColor Cyan
Read-Host

Write-Host "Captura y guarda como:" -ForegroundColor White
Write-Host "$imageFolder\game-config.png" -ForegroundColor Yellow
Write-Host ""
Write-Host "Presiona Enter cuando hayas guardado..." -ForegroundColor Cyan
Read-Host

# Finalizar
Write-Host ""
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "  CAPTURAS COMPLETADAS!" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Verificando archivos..." -ForegroundColor Yellow

$files = @("main-interface.png", "gaming-mode.png", "mod-downloader.png", "game-config.png")
$allFound = $true

foreach ($file in $files) {
    $path = Join-Path $imageFolder $file
    if (Test-Path $path) {
        Write-Host "[✓] $file - ENCONTRADO" -ForegroundColor Green
    } else {
        Write-Host "[✗] $file - FALTA" -ForegroundColor Red
        $allFound = $false
    }
}

Write-Host ""
if ($allFound) {
    Write-Host "Todas las capturas estan listas!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Siguiente paso: Sube las imagenes a GitHub" -ForegroundColor Cyan
    Write-Host "Ejecuta estos comandos:" -ForegroundColor Yellow
    Write-Host "  git add .github/images/*.png" -ForegroundColor White
    Write-Host "  git commit -m 'docs: Add application screenshots'" -ForegroundColor White
    Write-Host "  git push" -ForegroundColor White
} else {
    Write-Host "Faltan algunas capturas. Revisa la carpeta:" -ForegroundColor Yellow
    Write-Host "  $imageFolder" -ForegroundColor White
}

Write-Host ""
Write-Host "Presiona Enter para salir..." -ForegroundColor Cyan
Read-Host
