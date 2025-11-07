# 📸 Screenshots para el README

Por favor, toma las siguientes capturas de pantalla de la aplicación y guárdalas en esta carpeta con los nombres especificados:

## Capturas Necesarias

### 1. `main-interface.png`
**Dimensiones recomendadas**: 1600x900 o similar (16:9)

**Qué capturar**:
- Ventana completa de la aplicación en modo clásico
- Pestaña "Juegos Detectados" visible
- Lista de juegos con algunos seleccionados (checkbox marcados)
- Panel de configuración del mod visible abajo
- Si es posible, mostrar algunos juegos conocidos en la lista

**Cómo capturar**:
1. Abre la aplicación en modo clásico
2. Escanea juegos para tener la lista poblada
3. Marca algunos juegos con checkbox
4. Usa Alt+PrtScn para capturar solo la ventana
5. Pega en Paint y guarda como `main-interface.png`

---

### 2. `gaming-mode.png`
**Dimensiones recomendadas**: 1600x900 o similar (16:9)

**Qué capturar**:
- Interfaz en modo gaming (presiona el botón 🎮 para cambiar)
- Menú lateral de navegación visible
- Panel de configuración con los controles grandes
- Indicadores de foco visibles (bordes de colores)

**Cómo capturar**:
1. Cambia a modo gaming con el botón 🎮
2. Navega a la sección de configuración
3. Captura con Alt+PrtScn
4. Guarda como `gaming-mode.png`

---

### 3. `mod-downloader.png`
**Dimensiones recomendadas**: 800x600 o el tamaño de la ventana modal

**Qué capturar**:
- Ventana de descarga de mods
- Lista de versiones de OptiScaler disponibles
- Botones de descarga visibles

**Cómo capturar**:
1. Ve a "Ajustes de la App" → "Descargar Mods"
2. Espera a que cargue la lista de versiones
3. Captura la ventana modal con Alt+PrtScn
4. Guarda como `mod-downloader.png`

---

### 4. `game-config.png`
**Dimensiones recomendadas**: 800x600 o el tamaño de la ventana modal

**Qué capturar**:
- Ventana de configuración individual de un juego
- Todos los controles de configuración visibles
- Un preset seleccionado (Performance, Balanced, etc.)

**Cómo capturar**:
1. Selecciona un juego de la lista
2. Haz clic en "Configurar Juego" o similar
3. Captura la ventana de configuración
4. Guarda como `game-config.png`

---

## Consejos para Capturas de Calidad

✅ **Hacer**:
- Capturar en resolución alta (Full HD o superior)
- Asegurarte de que el texto sea legible
- Mostrar la aplicación en un estado "limpio" (sin errores)
- Usar Alt+PrtScn para capturar solo la ventana activa
- Guardar como PNG (mejor calidad que JPG)

❌ **Evitar**:
- Capturas borrosas o de baja resolución
- Ventanas parcialmente fuera de pantalla
- Información personal en las rutas de juegos (si es sensible)
- Capturas con errores o estados inconsistentes

---

## Alternativa: Usar una herramienta de captura

Si prefieres, puedes usar:
- **Snipping Tool** (Windows 10/11): Win + Shift + S
- **ShareX** (gratuito): Más opciones de captura y edición
- **Greenshot** (gratuito): Captura y anotación

---

## Después de tomar las capturas

1. Guarda los 4 archivos PNG en esta carpeta (`.github/images/`)
2. Verifica que los nombres coincidan exactamente:
   - `main-interface.png`
   - `gaming-mode.png`
   - `mod-downloader.png`
   - `game-config.png`
3. Haz commit y push:
   ```powershell
   git add .github/images/*.png
   git commit -m "docs: Add application screenshots"
   git push
   ```

El README ya está preparado para mostrar estas imágenes automáticamente.
