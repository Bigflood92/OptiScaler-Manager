# 🎮 OptiScaler Manager v2.3.1

**Fecha de lanzamiento**: 14 de noviembre de 2025

## 🆕 Nuevas Características

### 🖱️ Click-to-Focus Mejorado
- **Click para enfocar widgets**: Ahora puedes hacer clic en cualquier botón, combobox, checkbox o campo para establecer el foco automáticamente
- **Comportamiento inteligente de sliders**: Los sliders requieren activación explícita (Enter/A) antes de poder ajustarlos
  - 🔵 **Borde azul**: Slider enfocado pero inactivo
  - 🟢 **Borde verde brillante**: Slider activo para ajuste
  - Usa **←/→** para ajustar el valor cuando está activo
  - Presiona **A** de nuevo o **B** para desactivar

### 📊 Detalles de Instalación Mejorados
- **Lectura del OptiScaler.ini**: La ventana de detalles ahora muestra la configuración real del juego
- **Información detallada**:
  - ✅ Estado exacto de Frame Generation (OptiFG/Nukem's/Desactivado)
  - 🎮 Upscaler configurado (DX12/DX11)
  - 📐 Modo de escalado activo
  - ✨ Nivel de nitidez (sharpness)
  - 🎯 Configuración de GPU spoofing
- **Verificación precisa**: Ya no solo verifica archivos, sino que lee la configuración activa

## 🐛 Correcciones de Bugs

### Sliders
- ✅ Corregido: Los sliders ahora requieren activación explícita (Enter/A) en lugar de recibir foco directo con clic
- ✅ Corregido: El ajuste de sliders con ←/→ ahora actualiza correctamente el valor visual y el callback
- ✅ Corregido: La variable vinculada del slider se sincroniza perfectamente
- ✅ Corregido: Los labels de sliders (FPS, Sharpness, Mipmap) se actualizan en tiempo real

### Detalles de Instalación
- ✅ Corregido: La ventana de detalles ahora muestra el estado real de Frame Generation leyendo el OptiScaler.ini
- ✅ Corregido: Ya no muestra información genérica basada solo en archivos presentes

## 🔧 Mejoras Técnicas

### Sistema de Foco
- Nueva variable `slider_active` para rastrear estado de sliders
- Función `_adjust_slider()` que maneja el incremento/decremento de valores
- Desactivación automática de sliders al navegar o cambiar de widget
- Actualización de variable vinculada + callback manual para garantizar sincronización perfecta

### Navegación con Gamepad
- Interceptación de ←/→ cuando un slider está activo
- ↑/↓ desactivan automáticamente el slider y continúan la navegación
- Botón B desactiva el slider activo antes de volver al sidebar

### Logs
- Eliminados mensajes DEBUG excesivos para mantener logs limpios
- Solo se muestran errores cuando ocurren

## 📦 Instalación

**Descarga directa**: [Gestor OptiScaler V2.3.1.exe](https://github.com/Bigflood92/OptiScaler-Manager/releases/latest)

### Requisitos
- Windows 10/11 (64-bit)
- Permisos de administrador (UAC automático)
- ~19 MB de espacio en disco

### Pasos
1. Descarga el ejecutable
2. Doble clic → Acepta el UAC
3. ¡Listo para usar!

## 🎮 Controles

### Con Sliders Activos
- **A / Enter**: Activar/Desactivar slider
- **←/→**: Ajustar valor del slider (cuando está activo - borde verde)
- **↑/↓**: Desactivar slider y navegar
- **B**: Desactivar slider

### General
- **Clic en widget**: Establecer foco automáticamente
- **Gamepad completo**: Navegación, activación, y ajustes
- **Teclado**: Todas las funciones accesibles

## 📊 Estadísticas

- **Líneas de código modificadas**: ~150
- **Funciones nuevas**: 3 (`enable_click_to_focus`, `setup_widget_focus`, `_adjust_slider`)
- **Variables nuevas**: 1 (`slider_active`)
- **Tamaño del ejecutable**: ~18.8 MB (sin cambios)
- **Tiempo de compilación**: ~2 minutos (Nuitka)

## 🙏 Créditos

- **OptiScaler**: [cdozdil/OptiScaler](https://github.com/cdozdil/OptiScaler)
- **Nukem's DLSSG-to-FSR3**: [Nukem9/dlssg-to-fsr3](https://github.com/Nukem9/dlssg-to-fsr3)
- **Desarrollador**: Bigflood92

## 📝 Notas de Actualización

### Desde v2.3.0
- Si actualizas desde v2.3.0, no necesitas hacer cambios en tu configuración
- Todas las carpetas de escaneo y configuraciones se mantienen
- Los mods instalados siguen funcionando normalmente
- Nueva funcionalidad de click-to-focus disponible inmediatamente

### Archivos Afectados
- `src/gui/gaming_app.py`: Sistema de foco y navegación mejorado
- `README.md`: Actualizado a v2.3.1
- `CHANGELOG.md`: Nueva entrada para v2.3.1

---

**[⬇️ Descargar v2.3.1](https://github.com/Bigflood92/OptiScaler-Manager/releases/latest)** | **[📖 Documentación](https://github.com/Bigflood92/OptiScaler-Manager)** | **[🐛 Reportar Bug](https://github.com/Bigflood92/OptiScaler-Manager/issues)**
