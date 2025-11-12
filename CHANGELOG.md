# Changelog

Todos los cambios notables de este proyecto serán documentados en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/lang/es/).

## [No publicado]

## [2.2.0] - 2025-11-12

### Añadido
- **🎯 Barra de progreso integrada mejorada** en panel de Detección Automática
  - Reemplaza ventanas emergentes molestas con feedback visual continuo
  - Aparece/desaparece dinámicamente según sea necesario
  - Muestra el estado de la última operación permanentemente
  
- **📊 Indicadores de progreso avanzados**:
  - Porcentaje visual durante operaciones: `"Instalando 2/5 (40%)"`
  - Tiempo estimado restante basado en velocidad real: `"~15s restantes"`
  - Truncado inteligente de nombres largos (30 caracteres)
  
- **🌈 Colores dinámicos según estado**:
  - 🔵 Azul (#00BFFF): Operación en progreso
  - 🟢 Verde (#00FF88): Completado exitosamente
  - 🟠 Naranja (#FFA500): Advertencias o errores parciales
  - 🔴 Rojo (#FF4444): Errores críticos
  
- **📋 Resumen detallado expandible**:
  - Clic en la barra completada abre ventana modal con detalles
  - Lista de juegos exitosos con fondo verde
  - Lista de juegos fallidos con razón del error y fondo rojo
  - Cursor cambia a "mano" para indicar que es clicable
  
- **🎬 Preview en tiempo real**:
  - Estado del juego se actualiza EN LA LISTA mientras se procesa
  - Efecto de resaltado temporal (1 segundo) al completar
  - No espera al escaneo final para mostrar cambios
  
- **🔄 Animación del botón de escaneo**:
  - Emojis rotatorios mientras escanea: 🔄 → 🔃 → ⟳ → ⟲
  - Animación cada 200ms con detención automática
  
- **📏 Modo compacto dinámico**:
  - Barra expandida (12px padding) durante operaciones
  - Barra compacta (6px padding) 1.5s después de completar
  - Transición suave automática para ahorrar espacio
  
- **✕ Botón para ocultar manualmente**:
  - Pequeño botón "X" en esquina superior derecha
  - Color rojo al pasar el mouse
  - Control total del usuario sobre el espacio visual

### Cambiado
- **Eliminadas ventanas emergentes** (messageboxes) durante operaciones:
  - ~~Error de escaneo~~ → Mensaje en barra roja
  - ~~Resultado de instalación~~ → Mensaje en barra verde/naranja
  - ~~Resultado de desinstalación~~ → Mensaje en barra verde/naranja
  - **Mantenidos**: Diálogos de confirmación (askyesno)
  
- **Escaneo silencioso** después de instalar/desinstalar:
  - Actualiza lista en segundo plano sin modificar la barra
  - Mantiene visible el mensaje de operación completada
  
- **Mejora de UX general**:
  - Feedback visual continuo sin interrupciones
  - Información detallada en tiempo real
  - Progreso visible con porcentajes exactos

### Corregido
- Barra de progreso quedaba parcialmente llena al terminar escaneo
- Ventanas emergentes bloqueaban la interfaz durante operaciones largas
- Falta de feedback visual durante procesamiento de múltiples juegos

## [2.1.0] - 2025-11-12

### Añadido
- **Tutorial de bienvenida interactivo**: 6 páginas con guía completa para nuevos usuarios
  - Auto-muestra en primer inicio con opción "No volver a mostrar"
  - Navegación intuitiva con emojis grandes y contenido claro
- Build nativo con Nuitka (onefile) para máxima compatibilidad
- Ejecutable con elevación UAC automática (`--windows-uac-admin`)
- Fallback de auto-elevación en código (relanza si no hay admin)
- **Panel de ayuda integrado**: Muestra controles de gamepad/teclado al presionar botón "?"
- **Iconos centralizados**: Sistema de gestión de iconos PNG consistente en toda la UI
- **Drag-to-scroll**: Navegación fluida en listas largas arrastrando con el ratón
- Detección de entorno Nuitka usando `NUITKA_ONEFILE_DIRECTORY`

### Cambiado
- **Nombre del ejecutable simplificado**: `Gestor OptiScaler V2.1.exe` (elimina sufijo "ADMIN")
  - El permiso de administrador es obligatorio y se solicita automáticamente
- **Código base limpio**: Eliminados 10,004 líneas de código legacy obsoleto
  - Eliminadas interfaces antiguas (legacy_app.py, main_window.py)
  - Una única interfaz moderna (gaming_app.py)
- Centralización de rutas y logs usando `src/config/paths.py`
- README actualizado con nuevas capturas de pantalla (5 imágenes)
- README actualizado con instrucciones de compilación vía Nuitka
- Interfaz simplificada (eliminada información de GPU en settings)
- Iconos de botones de gamepad corregidos (Xbox/PlayStation)

### Corregido
- Error de rutas en compilados Nuitka (configuración se creaba en `%TEMP%`)
- Error de logging en compilado (uso de `self.log_dir`)
- Crash silencioso en .exe compilado con PyInstaller (migración a Nuitka)
- Iconos de gamepad mostrando teclas incorrectas


### Por añadir
- Arreglar navegación por gamepad
- Sistema de actualización automática de la aplicación
- Soporte para más launchers (Ubisoft Connect, Battle.net)
- Perfiles de configuración guardados
- Modo oscuro/claro personalizable

## [2.0.1] - 2025-11-07

### Añadido
- Screenshots de la aplicación en el README
- Documentación mejorada con ejemplos visuales
- GitHub Actions para builds automáticos
- Release automática al crear tags

### Cambiado
- README reorganizado y limpiado
- Badges profesionales añadidos

## [2.0.0] - 2025-11-07

### Añadido
- ✨ Interfaz Gaming con navegación completa por mando (Xbox/PlayStation)
- ✨ Sistema bidimensional de navegación en configuración
- ✨ Presets rápidos (Default, Performance, Balanced, Quality, Custom)
- ✨ Descarga e instalación de versiones de OptiScaler desde GitHub
- ✨ Sistema de caché para detección rápida de juegos
- ✨ Configuración individual por juego
- ✨ Soporte para carpetas personalizadas de búsqueda
- 📦 Gestión de versiones con descarga automática
- 🎮 Soporte completo para navegación con mando
- 🎨 Indicadores visuales de foco (bordes de colores)

### Cambiado
- 🔄 Migración de arquitectura monolítica a modular
- 🎨 Tema oscuro consistente en toda la aplicación
- 🎨 Interfaz dual: Modo clásico y modo gaming

### Corregido
- 🐛 Correcciones de encoding UTF-8 en toda la interfaz
- 🐛 Fix navegación lógica con mando (visual matching)
- 🐛 Detección mejorada de juegos en múltiples plataformas

### Técnico
- Refactorización completa del código
- Separación de lógica de negocio (core) y GUI
- Mejora en gestión de configuración
- Sistema de logging mejorado

## [1.0.0] - 2024-XX-XX

### Añadido
- Primera versión funcional del gestor
- Detección básica de juegos
- Instalación manual de OptiScaler
- Interfaz gráfica simple con CustomTkinter

---

## Tipos de cambios

- **Añadido** para funcionalidades nuevas.
- **Cambiado** para cambios en funcionalidades existentes.
- **Obsoleto** para funcionalidades que serán eliminadas.
- **Eliminado** para funcionalidades eliminadas.
- **Corregido** para corrección de errores.
- **Seguridad** para vulnerabilidades.

---

[No publicado]: https://github.com/Bigflood92/OptiScaler-Manager/compare/v2.1.0...HEAD
[2.1.0]: https://github.com/Bigflood92/OptiScaler-Manager/compare/v2.0.1...v2.1.0
[2.0.1]: https://github.com/Bigflood92/OptiScaler-Manager/compare/v2.0.0...v2.0.1
[2.0.0]: https://github.com/Bigflood92/OptiScaler-Manager/releases/tag/v2.0.0
[1.0.0]: https://github.com/Bigflood92/OptiScaler-Manager/releases/tag/v1.0.0
