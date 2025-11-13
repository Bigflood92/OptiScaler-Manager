# Eliminación del Auto-Update en Gaming Mode

## Fecha
13 de noviembre, 2025

## Cambio Realizado
Se ha **eliminado completamente** la funcionalidad de auto-actualización de OptiScaler desde el Gaming Mode.

## Motivo
- El botón "🔄 Buscar actualización" en Gaming Mode presentaba problemas con la descarga y extracción de archivos .7z
- La funcionalidad de descarga ya existe de forma más robusta en el **modo gestor principal**
- El gestor de descargas del modo principal maneja correctamente las dependencias (7z.exe) y tiene mejor control de errores
- Simplifica la experiencia del usuario evitando funcionalidad duplicada y problemática

## Componentes Eliminados

### UI (gaming_app.py)
- ❌ Botón "🔄 Buscar actualización" 
- ❌ Label de estado de actualizaciones (`update_status_label`)
- ❌ Frame contenedor de botones de actualización

### Funciones Eliminadas
1. `background_update_check()` - Chequeo automático al iniciar
2. `check_updates_manual()` - Handler del botón manual
3. `prompt_update_all()` - Diálogo de confirmación
4. `run_full_update()` - Orquestación de la actualización
5. `update_progress_stage()` - Actualización de progreso UI
6. `on_update_success()` - Handler de éxito
7. `on_update_noop()` - Handler de no-actualización
8. `on_update_failed()` - Handler de error

### Variables/Estado Eliminado
- `self.updater` (instancia de OptiScalerUpdater)
- `self.update_check_running` (bandera de estado)
- Import de `OptiScalerUpdater` desde `..core.updater`

### Dependencies
- ❌ Removido `py7zr>=0.21.0` de requirements.txt (ya no necesario)

## Dónde Actualizar OptiScaler Ahora

Los usuarios deben usar el **modo gestor principal** (no gaming mode) para:
1. Descargar nuevas versiones de OptiScaler desde GitHub
2. Gestionar versiones instaladas
3. Actualizar los mods en los juegos

El gestor de descargas del modo principal tiene:
- ✅ Manejo robusto de archivos .7z con 7z.exe
- ✅ Mejor control de errores y feedback
- ✅ UI dedicada para gestión de versiones
- ✅ Funcionalidad de rollback/selección de versiones

## Archivos Modificados
1. `src/gui/gaming_app.py` - Eliminadas ~180 líneas de código de auto-update
2. `requirements.txt` - Removida dependencia py7zr

## Archivos que Permanecen (para uso en modo gestor)
- `src/core/updater.py` - Se mantiene para el modo gestor principal
- Las mejoras de diagnóstico añadidas al updater siguen disponibles para el gestor

## Beneficios
✅ Menos código a mantener en Gaming Mode  
✅ Eliminación de funcionalidad problemática  
✅ UI más simple y enfocada  
✅ Usuarios dirigidos a la herramienta correcta (gestor) para descargas  
✅ Menos dependencias en requirements.txt  

## Impacto en Usuarios
- **Gaming Mode**: Ya no tiene botón de actualización (experiencia más simple)
- **Modo Gestor**: Sin cambios, sigue funcionando normalmente para descargas

---
*Nota: Si en el futuro se desea re-implementar auto-update en Gaming Mode, se recomienda usar la infraestructura robusta del gestor de descargas existente en lugar de duplicar funcionalidad.*
