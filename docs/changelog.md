# Changelog

Todos los cambios notables de este proyecto serán documentados en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/lang/es/).

## [No publicado]

## [2.3.0-dev-snapshot] - 2025-11-13

### Añadido
- Persistencia inicial del preset Custom (snapshot en memoria de parámetros modificados).
- Bordes coloreados para cada preset y etiqueta de estado activo.

### Cambiado
- Separada la lógica de marcado Custom para evitar sobrescritura de valores al editar.
- Uso de `_suppress_custom` durante aplicación de presets estándar.

### Corregido
- Borde de "Custom" permanecía activo tras cambiar de preset.
- Activación accidental de "Custom" al aplicar otros presets.

### Interno
- Backups locales generados (full y fuente).
- Tag git `v2.3.0-dev-snapshot` creado para referencia de desarrollo.

### Próximo
- Secciones colapsables en panel de configuración.
- Guardar snapshot Custom en archivo de configuración para persistencia entre sesiones.
- Botón de reset rápido para Custom.

### Por añadir
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

[No publicado]: https://github.com/Bigflood92/OptiScaler-Manager/compare/v2.0.1...HEAD
[2.3.0-dev-snapshot]: https://github.com/Bigflood92/OptiScaler-Manager/compare/v2.2.1...v2.3.0-dev-snapshot
[2.2.1]: https://github.com/Bigflood92/OptiScaler-Manager/compare/v2.2.0...v2.2.1
[2.2.0]: https://github.com/Bigflood92/OptiScaler-Manager/compare/v2.1.0...v2.2.0
[2.1.0]: https://github.com/Bigflood92/OptiScaler-Manager/compare/v2.0.1...v2.1.0
[2.0.1]: https://github.com/Bigflood92/OptiScaler-Manager/compare/v2.0.0...v2.0.1
[2.0.0]: https://github.com/Bigflood92/OptiScaler-Manager/releases/tag/v2.0.0
[1.0.0]: https://github.com/Bigflood92/OptiScaler-Manager/releases/tag/v1.0.0
