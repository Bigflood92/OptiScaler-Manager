# 🎉 Release v2.4.0 - Overlay Settings + OptiPatcher + Auto-Update

**Fecha de lanzamiento**: 17 de noviembre de 2025

---

## 🌟 Novedades Principales

### 🔄 Auto-Actualización de la Aplicación

¡La aplicación ahora se actualiza automáticamente!

#### Funcionamiento:
1. **Verificación automática**: Al iniciar, busca nuevas versiones en GitHub
2. **Notificación visual**: Ventana modal con información del release
3. **Un clic para actualizar**: Descarga, instala y reinicia automáticamente
4. **Sin intervención manual**: Todo el proceso es automatizado

#### Características:
- **Ventana de Actualización**:
  - Muestra versión actual vs nueva versión
  - Notas del release (changelog completo)
  - 3 botones: "Ver en GitHub", "Cerrar", "Descargar y Actualizar"
  
- **Proceso Inteligente**:
  - Crea backup del ejecutable actual (*.exe_old)
  - Descarga la nueva versión desde GitHub
  - Reemplaza automáticamente el ejecutable
  - Reinicia la aplicación con la nueva versión
  - Limpia backups antiguos

- **Seguridad**:
  - Comparación semver de versiones
  - Verificación de integridad del archivo descargado
  - Rollback automático si falla la actualización (mantiene backup)

#### Ubicación:
Se ejecuta automáticamente 1.5 segundos después del inicio

---

### 📊 Overlay Settings - Monitorización en Tiempo Real

¡Ahora puedes ver FPS, Frame Time y mensajes de depuración directamente en el juego!

#### Características:
- **3 Modos de Visualización**:
  - **Desactivado**: Sin overlay
  - **Básico**: Solo muestra FPS
  - **Completo**: FPS + Frame Time + Mensajes de depuración

- **Personalización Completa**:
  - **Posición**: 8 ubicaciones (Esquinas + Centros de bordes)
  - **Escala**: De 100% a 200% en incrementos de 10%
  - **Tamaño de Fuente**: Pequeña (12px), Media (16px), Grande (20px)

- **Integración con Presets**: Cada preset (Default, Performance, Balanced, Quality) incluye configuración de overlay predefinida

#### Ubicación:
`Configuración del Mod` → **📊 Overlay Settings (Monitorización)**

---

### 🔧 OptiPatcher Plugin - Mejor Compatibilidad para 171+ Juegos

OptiPatcher es un plugin ASI que mejora la compatibilidad de OptiScaler mediante parches en memoria.

#### Beneficios:
- **171+ juegos soportados**: Black Myth: Wukong, Stalker 2, Hogwarts Legacy, Final Fantasy VII Rebirth, Indiana Jones, Alan Wake 2, y muchos más
- **Elimina errores D3D12** en GPUs Intel Arc
- **Sin spoofing necesario**: Expone DLSS/DLSS-FG nativamente
- **No modifica archivos del juego**: Los parches se aplican en memoria

#### Sistema de Descarga y Actualización:
1. **Estado en tiempo real**: Muestra versión instalada con fecha
2. **Búsqueda de actualizaciones**: Compara con la última versión en GitHub
3. **Descarga con un clic**: Botón dinámico que cambia según el estado
4. **Acceso directo a GitHub**: Consulta cambios y release notes

#### Instalación Automática:
- Se instala automáticamente con OptiScaler si está habilitado
- Se desinstala al eliminar OptiScaler
- Visible en "Ver detalles de instalación"

#### Ubicación:
`Ajustes de la App` → **🔧 OptiPatcher (Plugin ASI)**

---

## 🎨 Mejoras de UI

### WideComboBox Optimizado
- Parámetro `max_visible_items` para controlar altura de dropdowns
- Renderizado adaptativo: Sin scroll innecesario cuando hay pocas opciones
- Overlay dropdown: Muestra máximo 3 opciones visibles
- Debug dropdown: Muestra máximo 6 opciones visibles

---

## 🐛 Correcciones

### Cache Directory Duplicada
- **Problema**: Se creaban dos carpetas `.cache` (una correcta, otra en raíz del proyecto)
- **Solución**: Ahora solo se crea en `Config Optiscaler Gestor/.cache`

### Estilo UI Inconsistente
- Overlay y Debug dropdowns ahora usan el mismo estilo que el resto de la app
- Eliminados colores personalizados en botones de OptiPatcher

---

## 📦 Descarga

**[⬇️ Descargar Gestor OptiScaler V2.4.0.exe](https://github.com/Bigflood92/OptiScaler-Manager/releases/tag/v2.4.0)**

### Requisitos:
- Windows 10/11 x64
- Permisos de administrador (solicitados automáticamente)

### Instalación:
1. Descargar el ejecutable
2. Doble clic (acepta el UAC de Windows)
3. ¡Listo para usar!

---

## 🔄 Actualización desde v2.3.x

Si ya tienes instalada una versión anterior:

1. **Opción 1 - Reemplazar ejecutable**:
   - Cierra la aplicación actual
   - Descarga `Gestor OptiScaler V2.4.0.exe`
   - Reemplaza el antiguo ejecutable
   - Tu configuración se mantiene automáticamente

2. **Opción 2 - Instalación limpia**:
   - Descarga el nuevo ejecutable en otra carpeta
   - Al ejecutar, detectará tu configuración existente en `Config Optiscaler Gestor/`

---

## 📝 Notas Técnicas

### Archivos Modificados:
- `src/gui/gaming_app.py`: +400 líneas (Overlay UI + OptiPatcher UI)
- `src/core/installer.py`: +200 líneas (install/uninstall OptiPatcher)
- `src/core/github.py`: +100 líneas (download_optipatcher)
- `src/config/constants.py`: Constantes OptiPatcher
- `src/config/paths.py`: CACHE_DIR centralizado

### Nuevas Dependencias:
- Ninguna (usa las mismas que v2.3.x)

### Compatibilidad:
- ✅ Windows 10/11 x64
- ✅ Python 3.12
- ✅ Compilación con Nuitka
- ✅ Compatible con configuraciones existentes

---

## 🙏 Créditos

- **[OptiScaler](https://github.com/cdozdil/OptiScaler)** - Por el mod base
- **[OptiPatcher](https://github.com/optiscaler/OptiPatcher)** - Por el plugin de compatibilidad
- **Comunidad de testers** - Por reportar issues y sugerencias

---

## 📞 Soporte

¿Problemas o sugerencias?
- **Issues**: [GitHub Issues](https://github.com/Bigflood92/OptiScaler-Manager/issues)
- **Documentación**: [Guías de usuario](docs/user-guide/)

---

<p align="center">
  <sub>Hecho con ❤️ para la comunidad de gaming en PC</sub>
</p>
