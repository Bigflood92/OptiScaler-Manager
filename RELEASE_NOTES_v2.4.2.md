# 🚀 OptiScaler Manager v2.4.2

**Fecha de lanzamiento:** 18 de Noviembre, 2025

## 🛠️ Correcciones y Mejoras

### ✅ **Problemas Resueltos en Ejecutables**
- **🖼️ Íconos**: Mejorado el sistema de detección de rutas de iconos para PyInstaller y Nuitka
- **📝 Tutorial de Bienvenida**: Arreglado el problema de persistencia del checkbox "No volver a mostrar"
- **🎮 Gamepad**: Resuelto el error "video system not initialized" con fallback automático a display oculto

### 🔧 **Mejoras Técnicas**
- **📁 Configuración**: Directorio de configuración ahora usa ubicación escribible (fallback a %APPDATA% si es necesario)
- **🗂️ Rutas de Archivos**: Mejorada la detección de recursos en ejecutables compilados
- **🎯 Interfaz**: Corregido el ícono de descarga (⬇️) en la ventana de OptiScaler

### 🧪 **Robustez**
- **💾 JSON**: Manejo más robusto de archivos de configuración corruptos
- **🔍 Diagnósticos**: Logs mejorados para debugging en ejecutables
- **⚙️ Inicialización**: Inicialización más segura del subsistema de gamepad

## 📝 **Notas Técnicas**

### Para Desarrolladores
- Mejorado `IconManager` con detección múltiple de rutas de iconos
- `APP_DIR` ahora detecta automáticamente ubicaciones escribibles
- Gamepad inicializa solo el subsistema joystick para evitar dependencias de video

### Archivos Modificados
- `src/config/constants.py` - Versión actualizada a 2.4.2
- `src/config/paths.py` - Lógica de directorio escribible
- `src/gui/icon_manager.py` - Detección mejorada de rutas
- `src/gui/gaming_app.py` - Inicialización gamepad + logs diagnósticos
- `build_nuitka_admin.ps1` - Actualizado nombre de salida

## 🔗 **Enlaces**

- [Repositorio GitHub](https://github.com/Bigflood92/OptiScaler-Manager)
- [Documentación](https://github.com/Bigflood92/OptiScaler-Manager/tree/main/docs)
- [Reportar Issues](https://github.com/Bigflood92/OptiScaler-Manager/issues)

---

**Compatibilidad:** Windows 10/11 x64
**Tamaño aproximado:** ~25MB (ejecutable standalone)