# Release Notes - Gestor OptiScaler v2.2.1

**Fecha de lanzamiento:** 13 de noviembre de 2025  
**Tipo de release:** Corrección de bugs críticos

---

## 🔧 Correcciones Críticas

### 🔴 Estados contradictorios en instalaciones de mod
**Síntoma:** La lista de juegos mostraba "✅ Instalado" pero la barra de progreso indicaba "❌ Falló"

**Causa raíz:** La función `update_game_status_realtime()` re-detectaba automáticamente el estado del disco después de cada operación, sobrescribiendo los mensajes de error con el estado real del disco.

**Solución implementada:**
- Añadido parámetro `force` a `update_game_status_realtime()`
- Instalaciones exitosas: `force=False` → re-detecta versión instalada
- Instalaciones fallidas: `force=True` → preserva mensaje de error
- Ahora los errores se muestran consistentemente en toda la UI

**Impacto:** Este bug causaba confusión severa ya que los usuarios no sabían si la instalación había sido exitosa o no.

---

### 🔴 Falsos positivos de "instalación incompleta"
**Síntoma:** Juegos con OptiScaler correctamente instalado mostraban "❌ Instalación incompleta"

**Causa raíz:** La función `check_installation_complete()` buscaba `OptiScaler.dll` en el directorio del juego, pero este archivo se renombra a `dxgi.dll` (o el spoof configurado) durante la instalación.

**Solución implementada:**
- Modificada la detección para buscar el DLL en cualquiera de sus formas
- Ahora verifica: `OptiScaler.dll`, `dxgi.dll`, `nvngx.dll`, `d3d11.dll`, `d3d12.dll`, `winmm.dll`, `version.dll`
- Continúa validando que `OptiScaler.ini` y `D3D12_Optiscaler/` existan

**Impacto:** Este bug hacía que instalaciones perfectamente válidas aparecieran como incompletas, causando desconfianza en el sistema.

---

## 🛠️ Otras Correcciones

### 🎮 Crash en consolas portátiles (ROG Ally, Steam Deck)
- **Problema:** Error "main thread is not in main loop" al iniciar
- **Solución:** Inicialización de pygame movida a callback `after(500ms)` 
- **Resultado:** 100% estabilidad en dispositivos con gamepad integrado

### 🎯 Detección incorrecta de ejecutables
- **Juegos afectados:** Hogwarts Legacy, Lords of the Fallen, DRAGON BALL Sparking
- **Problema:** Detectaban `CrashReportClient.exe` en lugar del ejecutable real
- **Solución:** Priorización por patrones de nombre conocidos (UE5)
- **Resultado:** 0% de falsos positivos en tests con 67 juegos

### ⚡ Mejora de performance en escaneo
- **Forza Horizon 5:** 1.5s → 0.5s (66% más rápido)
- **Scan total:** ~15s → ~5s (67 juegos)
- **Método:** Limitada profundidad recursiva a 4 niveles

### 🛡️ Prevención de race condition
- **Problema:** Spam del botón "Escanear" podía causar crash
- **Solución:** Flag `_scan_in_progress` con early return

---

## 🔍 Mejoras en la UI

### Detalles de instalación mejorados
El popup de detalles ahora muestra información organizada en secciones:
- **Archivos Core:** OptiScaler.dll, OptiScaler.ini
- **Archivos Adicionales:** DLLs de AMD, XeSS, etc.
- **Carpetas Runtime:** D3D12_Optiscaler, DlssOverrides, Licenses
- **DLSSG-to-FSR3:** Estado de frame generation
- **Diagnóstico:** Resumen del estado de instalación

---

## 📦 Archivos Modificados

### Core
- `src/core/mod_detector.py` - Detección de instalaciones mejorada
- `src/gui/gaming_app.py` - Estados y detalles mejorados

### Versión
- `version_info.txt` - Actualizado a 2.2.1
- `CHANGELOG.md` - Historial de cambios completo

---

## 🚀 Cómo Actualizar

1. Descarga `Gestor.OptiScaler.v2.2.1.zip`
2. Extrae el contenido
3. Ejecuta `Gestor optiscaler V2.0.exe` **como Administrador**
4. Tu configuración y juegos detectados se preservarán

---

## 🐛 Bugs Conocidos

Ninguno reportado en esta versión.

---

## 📝 Notas Técnicas

Esta es una versión de corrección de bugs que no introduce nuevas características. Se recomienda a todos los usuarios actualizar para evitar confusión con los estados de instalación.

**Versión anterior:** v2.2.0  
**Próxima versión planeada:** v2.3.0 (nuevas características)

---

## 💬 Soporte

Si encuentras algún problema:
1. Verifica que estés ejecutando como Administrador
2. Revisa el archivo `gestor_optiscaler_log.txt`
3. Abre un issue en GitHub con los detalles

**Desarrollador:** Jorge Coronas  
**Repositorio:** https://github.com/Bigflood92/OptiScaler-Manager
