# Changelog

Todos los cambios notables de este proyecto serán documentados en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/lang/es/).

## [No publicado]

## [2.3.1] - 2025-11-14

### Añadido
- **🖱️ Click-to-Focus Completo**
  - Click para enfocar: Botones, comboboxes, checkboxes y campos reciben foco al hacer clic
  - Navegación mouse-gamepad integrada: Cambio fluido entre ambos métodos
  - Función `enable_click_to_focus()`: Binding automático de clic en widgets
  - Función `setup_widget_focus()`: Configura indicador + click-to-focus en un solo paso

- **🎚️ Sistema de Sliders Mejorado**
  - Activación explícita requerida: Presiona Enter/A para activar slider antes de ajustar
  - Indicadores visuales claros:
    - 🔵 Borde azul (2px): Slider enfocado pero inactivo
    - 🟢 Borde verde brillante (3px): Slider activo para ajuste
  - Ajuste con ←/→: Controla el valor solo cuando está activo (verde)
  - Desactivación automática: Al navegar (↑/↓), cambiar widget, o presionar B
  - Función `_adjust_slider()`: Maneja incremento/decremento con step_size correcto

- **📊 Detalles de Instalación Mejorados**
  - Lectura de OptiScaler.ini: Ahora lee la configuración real del juego
  - Sección nueva: "⚙️ CONFIGURACIÓN (OptiScaler.ini)" muestra:
    - Estado exacto de Frame Generation (OptiFG/Nukem's/Desactivado)
    - Upscaler configurado (DX12/DX11)
    - Modo de escalado activo
    - Nivel de nitidez (sharpness)
    - Configuración de GPU spoofing
  - Validación de Nukem's DLL cuando fg_type='nukems'

### Corregido
- Sliders ya no reciben foco directo con clic (requieren activación con Enter/A)
- Actualización del valor del slider ahora funciona correctamente con ←/→
- Variable vinculada del slider se sincroniza perfectamente
- Labels de sliders (FPS, Sharpness, Mipmap) se actualizan en tiempo real
- Ventana de detalles muestra estado real leyendo OptiScaler.ini en lugar de solo verificar archivos

### Mejorado
- Logs más limpios: Eliminados mensajes DEBUG excesivos de click-to-focus y sliders
- Sincronización de sliders: Actualiza variable vinculada + callback manual para garantizar actualización visual
- Sistema de foco unificado: `setup_widget_focus()` aplica todas las configuraciones necesarias

### Técnico
- Nueva variable: `self.slider_active` rastrea estado de sliders
- Navegación mejorada: Intercepta ←/→ cuando slider está activo
- Desactivación inteligente: Múltiples puntos de desactivación automática
- Actualización visual forzada: `update_idletasks()` garantiza renderizado inmediato

## [2.3.0] - 2025-11-14

### Añadido
- **🎮 WideComboBox con Navegación Completa**
  - Controles desplegables personalizados que reemplazan CTkComboBox estándar
  - Autoscroll interno: Los menús largos hacen scroll automático al navegar
  - Navegación unificada: A/Enter abre/selecciona, B/Esc cierra
  - Foco visual mejorado: Borde único sin duplicación
  - Indicador visual: Borde completo en opción activa del desplegable
  - Ancho consistente: El dropdown siempre coincide con el control base
  - Máximo 8 opciones visibles con scroll automático

- **📁 Gestión de Carpetas Personalizadas**
  - Nueva interfaz para añadir carpetas de escaneo personalizadas
  - Persistencia: Las carpetas se guardan entre sesiones en `injector_config.json`
  - Interfaz intuitiva: Botones añadir/eliminar con validación
  - Detección de carpetas duplicadas automática
  - Integración completa: Se escanean junto con Steam, Epic, Xbox

- **🎯 Filtro de Xbox en Detección Automática**
  - Opción "Xbox" añadida al filtro de plataformas
  - Filtra específicamente juegos de Xbox Game Pass y Windows Store
  - Complementa opciones existentes: Steam, Epic Games, Custom

- **🖱️ Drag-to-Scroll Completo**
  - Habilitado en Settings panel (faltaba)
  - Habilitado en Help panel (faltaba)
  - Configuración consistente en todos los paneles scrollables

- **🔍 Autoscroll Inteligente de Ventana**
  - Scroll automático del contenido al navegar con teclado/gamepad
  - Detección recursiva del CTkScrollableFrame en cualquier nivel de jerarquía
  - Margen adaptativo: Mantiene el widget enfocado visible con 100px de margen
  - Búsqueda robusta de canvas con múltiples métodos de acceso
  - Logs de diagnóstico con prefijo `[AUTOSCROLL]` para troubleshooting

### Cambiado
- **Títulos y Versiones**
  - Versión actualizada de 2.2.0 a 2.3.0 en toda la aplicación
  - Introducida constante `APP_VERSION = "2.3.0"`
  - Introducida constante `APP_TITLE = f"GESTOR AUTOMATIZADO DE OPTISCALER V{APP_VERSION}"`
  - Todos los títulos hardcoded ahora usan `APP_TITLE`
  - About text usa f-string dinámico con `APP_VERSION`

- **Documentación Actualizada**
  - Panel de Ayuda: 3 nuevas FAQs sobre carpetas personalizadas, Xbox, WideComboBox
  - Total 9 FAQs cubriendo todas las características de v2.3
  - Controles de gamepad y teclado actualizados
  - About text menciona soporte para Xbox y carpetas personalizadas

### Corregido
- **❌ Instalación en Juegos de Xbox/Windows Store**
  - **ANTES**: Instalación fallaba completamente con "ACCESO DENEGADO" al copiar carpetas opcionales
  - **AHORA**: Carpetas opcionales (`D3D12_Optiscaler`, `DlssOverrides`, `Licenses`) generan WARNING en lugar de ERROR
  - La instalación continúa exitosamente incluso si carpetas opcionales fallan
  - El mod funciona correctamente solo con archivos core (DLL + INI)
  - Mensaje claro: "El mod puede funcionar sin esta carpeta. Si hay problemas, ejecuta como admin."

- **📋 Detalles de Instalación Incorrectos**
  - **ANTES**: Mostraba "OptiScaler.dll - NO ENCONTRADO" aunque el mod estaba instalado
  - **AHORA**: Detecta correctamente las DLLs renombradas (`dxgi.dll`, `d3d11.dll`, `d3d12.dll`, `winmm.dll`)
  - Si encuentra cualquier DLL renombrada + `OptiScaler.ini` → "Archivos core: COMPLETO"
  - Eliminadas DLLs core de sección "Archivos adicionales" para evitar duplicación
  - Mensaje mejorado si falta: "OptiScaler.dll - NO ENCONTRADO (debe estar renombrado...)"

- **🔄 Limpieza de Código Legacy**
  - Eliminado código de parches globales obsoletos para CTkComboBox
  - Removidas funciones helper obsoletas: `_configure_combobox_dropdown_width`, etc.
  - Código simplificado y más mantenible
  - WideComboBox proporciona toda la funcionalidad necesaria

### Técnico
- **WideComboBox** (`src/gui/components/wide_combobox.py`):
  - CTkFrame base con CTkToplevel para dropdown
  - Scroll interno con CTkScrollableFrame (max 8 opciones visibles)
  - Navegación con índice interno (`_current_index`)
  - Método `_scroll_to_current()` para autoscroll del dropdown
  - Prevención de recursión en `configure()`
  - Focus ring en frame interno `_content` para evitar clipping
  - Redirección de foco de hijos (label, arrow) al frame principal

- **Gestión de Carpetas**:
  - Config key: `custom_game_folders` (lista de strings)
  - Inicialización automática como lista vacía si no existe
  - Método `manage_scan_folders()` con UI completa
  - Guardado automático en `save_config()`
  - Paso al scanner via parámetro `custom_folders`

- **Autoscroll de Ventana**:
  - Función `auto_scroll_to_widget()` mejorada
  - Búsqueda recursiva de `CTkScrollableFrame` con función interna `find_scrollable()`
  - Cálculo de posición con `winfo_rooty()` (absoluta)
  - Fallback a método de recorrido jerárquico
  - Actualización forzada con `update_idletasks()`

- **Instalador**:
  - Líneas 518-534: PermissionError en carpetas opcionales cambiado de ERROR a WARNING
  - Handler general de excepciones como fallback
  - Instalación continúa en lugar de abortar

### Estadísticas
- **Archivos modificados**: 3
  - `src/gui/gaming_app.py`
  - `src/gui/components/wide_combobox.py`
  - `src/core/installer.py`
- **Líneas añadidas**: ~800
- **Líneas eliminadas**: ~200
- **Nuevas características**: 5
- **Bugs corregidos**: 3
- **FAQs añadidas**: 3

## [2.3.0-dev-snapshot] - 2025-11-13

### Añadido
- Persistencia del preset **Custom**: snapshot automático de valores modificados (fg_mode, upscale_mode, upscaler, sharpness, fps_limit, dll_name).
- Indicador visual mejorado de preset activo: bordes coloreados por tipo y etiqueta dinámica en esquina.

### Cambiado
- Lógica de trazas (`trace_add`) ahora separada: `mark_preset_custom` solo marca visualmente sin reinstanciar valores.
- Se introduce `_suppress_custom` para evitar que cambios programáticos activen el modo Custom durante aplicación de presets predefinidos.

### Corregido
- Borde de "Custom" permanecía activo al seleccionar otro preset.
- Activación indebida de "Custom" al aplicar un preset estándar (Performance, Balanced, Quality, Default).

### Interno
- Creación de backups locales: `backups/OptiScaler-Manager-full-<timestamp>.zip` y versión fuente reducida.
- Tag Git anotado creado: `v2.3.0-dev-snapshot` como punto de restauración.
- Preparación de base para próximos grupos colapsables en panel de configuración.

### Próximo (plan)
- Secciones colapsables para organización avanzada de parámetros.
- Persistencia de snapshot Custom entre sesiones (guardar en config).
- Utilidades de reset rápido para el estado Custom.

## [2.2.1] - 2025-11-13

### Corregido
- **[CRÍTICO] 🔴 Estados contradictorios en instalaciones de mod**
  - La lista mostraba "instalado" pero la barra de progreso mostraba "falló"
  - Causa: `update_game_status_realtime()` re-detectaba el estado del disco después de errores
  - Solución: Añadido parámetro `force` para preservar mensajes de error
  - Instalaciones exitosas usan `force=False` (re-detecta versión), errores usan `force=True` (preserva mensaje)
  
- **[CRÍTICO] 🔴 Falsos positivos de "instalación incompleta"**
  - Juegos con OptiScaler correctamente instalado mostraban "❌ Instalación incompleta"
  - Causa: `check_installation_complete()` buscaba `OptiScaler.dll` que se renombra a `dxgi.dll`
  - Solución: Modificada detección para buscar tanto DLL original como variantes renombradas
  - Ahora busca: `OptiScaler.dll`, `dxgi.dll`, `nvngx.dll`, `d3d11.dll`, `d3d12.dll`, `winmm.dll`, `version.dll`
  
- **[ALTO] 🎮 Crash del monitor de gamepad en consolas portátiles**
  - Error "main thread is not in main loop" al iniciar en ROG Ally, Steam Deck
  - Movida inicialización de pygame a callback `after(500ms)` para ejecutar después de `mainloop()`
  - 100% estabilidad en dispositivos con gamepad integrado
  
- **[ALTO] 🎯 Detección incorrecta de ejecutables en 3 juegos**
  - Hogwarts Legacy, Lords of the Fallen, DRAGON BALL Sparking detectaban `CrashReportClient.exe`
  - Implementada prioridad por patrones de nombre conocidos (UE5 `-WinGDK-Shipping.exe`, `-Win64-Shipping.exe`)
  - Ahora busca ejecutables reales antes de recurrir a lista negra
  - 0% de falsos positivos en tests con 67 juegos
  
- **[MEDIO] ⚡ Performance lenta en escaneo de juegos grandes**
  - Forza Horizon 5 (120GB) tardaba 1.5s → ahora ~0.5s (66% más rápido)
  - Limitada profundidad recursiva a 4 niveles (suficiente para encontrar todos los .exe)
  - Total scan time reducido de ~15s a ~5s (67 juegos)
  
- **[BAJO] 🛡️ Race condition potencial al spam botón escaneo**
  - Añadido flag `_scan_in_progress` con early return
  - Previene crash si usuario presiona "Escanear" múltiples veces rápidamente

### Mejorado
- **🔍 Detalles de instalación mejorados**
  - Popup de detalles ahora muestra secciones organizadas: Core, Adicionales, Runtime, DLSSG-to-FSR3
  - Diagnóstico detallado con estado de cada componente
  - Mejor visibilidad de qué archivos/carpetas están instalados

### Documentación
- Añadido análisis completo de bugs en `docs/development/bugfix-v2.2.0-rog-ally.md`
- Incluye causa raíz, solución técnica y guías de testing

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

[No publicado]: https://github.com/Bigflood92/OptiScaler-Manager/compare/v2.3.0...HEAD
[2.3.0]: https://github.com/Bigflood92/OptiScaler-Manager/compare/v2.2.1...v2.3.0
[2.3.0-dev-snapshot]: https://github.com/Bigflood92/OptiScaler-Manager/compare/v2.2.1...v2.3.0-dev-snapshot
[2.2.1]: https://github.com/Bigflood92/OptiScaler-Manager/compare/v2.2.0...v2.2.1
[2.2.0]: https://github.com/Bigflood92/OptiScaler-Manager/compare/v2.1.0...v2.2.0
[2.1.0]: https://github.com/Bigflood92/OptiScaler-Manager/compare/v2.0.1...v2.1.0
[2.0.1]: https://github.com/Bigflood92/OptiScaler-Manager/compare/v2.0.0...v2.0.1
[2.0.0]: https://github.com/Bigflood92/OptiScaler-Manager/releases/tag/v2.0.0
[1.0.0]: https://github.com/Bigflood92/OptiScaler-Manager/releases/tag/v1.0.0
