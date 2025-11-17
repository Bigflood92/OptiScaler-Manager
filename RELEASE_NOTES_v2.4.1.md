# 🎮 Gestor OptiScaler V2.4.1

## 🐛 Correcciones

### Mejoras de UI/UX para Handheld PC

- **Ventana de Detalles Rediseñada**: La ventana de detalles de instalación ahora utiliza componentes CustomTkinter con estética consistente
- **Soporte de Scroll**: Añadido `CTkScrollableFrame` para visualización completa en pantallas pequeñas (optimizado para 700x600px)
- **Corrección Frame Generation**: El dropdown de FG ahora solo muestra "FSR-FG (Nukem's)" cuando el mod está realmente instalado en el juego

---

## 📋 Características Completas (V2.4.x)

### Configuración del Overlay
- 3 modos de overlay: Desactivado, Básico, Completo
- Control de métricas visibles (FPS, Frame Time, Mensajes)
- 9 posiciones configurables
- Ajuste de escala y tamaño de fuente

### OptiPatcher
- Descarga e instalación automática
- Seguimiento de versiones
- Integración con sistema de plugins ASI

### Auto-Actualización
- Detección automática de nuevas versiones
- Descarga e instalación con un clic
- Verificación SHA256 de integridad
- Ventana modal con barra de progreso

---

## 🔧 Requisitos del Sistema

- **Sistema Operativo**: Windows 10/11 (64-bit)
- **GPU**: AMD, Intel, o NVIDIA
- **Espacio en Disco**: ~50MB para la aplicación + espacio para mods

---

## 📦 Instalación

1. Descarga `Gestor.OptiScaler.V2.4.1.exe`
2. Verifica el checksum SHA256 (opcional pero recomendado)
3. Ejecuta el instalador con permisos de administrador
4. La aplicación se abrirá automáticamente

---

## 🎯 Uso Rápido

### Para Handheld PC (Steam Deck, ROG Ally, etc.)
1. Abre la app en modo Gaming
2. Selecciona tu juego
3. Haz clic en "📋 Ver Detalles" para verificar la instalación (ahora con scroll)
4. Configura FG según los mods instalados en el juego
5. Aplica configuración

---

## 🔍 Cambios Técnicos

### Archivo Nuevo
- `src/gui/components/windows/installation_details_window.py`: Ventana modal CustomTkinter para detalles de instalación

### Archivos Modificados
- `src/gui/gaming_app.py`:
  - Reemplazado `show_installation_details()` con llamada a ventana modal
  - Actualizado `update_fg_options()` para verificar instalación de Nukem en el juego seleccionado
- `src/config/constants.py`: Versión 2.4.1
- `build_nuitka_admin.ps1`: Salida V2.4.1.exe

---

## 🐛 Problemas Conocidos

Ninguno reportado en esta versión.

---

## 📝 Notas

Esta es una versión de corrección enfocada en mejorar la experiencia en dispositivos handheld PC.

Para más información, consulta el [CHANGELOG completo](CHANGELOG.md).
