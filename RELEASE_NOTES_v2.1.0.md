# OptiScaler Manager v2.1.0 🎮

## 🚀 Mejoras Principales

### Compilación Nativa con Nuitka
- **Ejecutable optimizado** compilado con Nuitka para máxima compatibilidad y rendimiento
- **Tamaño reducido**: ~20 MB onefile (vs ~40 MB con PyInstaller)
- **Inicio más rápido** y menor uso de recursos
- **Sin falsos positivos** de antivirus comunes

### Elevación de Privilegios Automática
- **UAC prompt integrado** - el ejecutable solicita permisos de administrador automáticamente
- **Fallback inteligente** - si no se compila con UAC, la aplicación se auto-eleva en tiempo de ejecución
- **Sin necesidad de "Run as Administrator"** manualmente

### Gestión de Rutas Mejorada
- **Configuración persistente** - las carpetas de configuración se crean junto al ejecutable, no en carpetas temporales
- **Logs centralizados** en `src/config/paths.py`
- **Compatible con compilados** - funciona correctamente tanto en Python como en .exe

---

## 📦 Instalación

1. Descarga **`Gestor Optiscaler V2.0 ADMIN.exe`**
2. (Opcional) Verifica la integridad con el checksum SHA256
3. Ejecuta el .exe - se solicitarán permisos de administrador automáticamente
4. ¡Listo! La aplicación creará las carpetas necesarias en su primera ejecución

---

## ⚠️ Notas Importantes

- **Requiere permisos de administrador** para instalar mods en carpetas de juegos protegidas
- **Compatible con Windows 10/11** (x64)
- **Primera ejecución**: puede tardar unos segundos mientras se inicializa

---

## 🔧 Cambios Técnicos

### Añadido
- Build nativo con Nuitka (onefile) con `--windows-uac-admin`
- Fallback de auto-elevación en código (relanza si no hay admin)
- Detección de entorno Nuitka usando `NUITKA_ONEFILE_DIRECTORY`

### Cambiado
- Centralización de rutas y logs usando `src/config/paths.py`
- README actualizado con instrucciones de compilación vía Nuitka
- Workflow de GitHub Actions migrado a Nuitka

### Corregido
- Error de rutas en compilados (configuración se creaba en `%TEMP%`)
- Error de logging en compilado (uso incorrecto de `self.log_dir`)
- Crash silencioso en .exe compilado con PyInstaller

---

## 📋 Changelog Completo

Ver [CHANGELOG.md](https://github.com/Bigflood92/OptiScaler-Manager/blob/main/CHANGELOG.md) para la lista completa de cambios.

---

## 🐛 Problemas Conocidos

- Navegación por gamepad puede tener issues menores (se corregirá en v2.2.0)
- Algunos antivirus pueden requerir excepción para ejecutables compilados con Nuitka

---

## 💬 Soporte

¿Problemas? Abre un [issue en GitHub](https://github.com/Bigflood92/OptiScaler-Manager/issues)

---

**Checksums:**
- SHA256: Ver archivo `.sha256` adjunto
