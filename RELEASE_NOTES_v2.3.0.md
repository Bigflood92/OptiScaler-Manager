# 🎉 OptiScaler Manager v2.3.0 - Release Notes

## 📅 Fecha de lanzamiento
14 de Noviembre de 2025

## 🎯 Resumen
Esta versión trae mejoras significativas en la experiencia de usuario para dispositivos handheld, con controles personalizados optimizados, autoscroll inteligente, gestión de carpetas personalizadas y mejor soporte para juegos de Xbox/Windows Store.

---

## ✨ Nuevas Características

### 🎮 WideComboBox con Navegación Completa
- **Controles desplegables personalizados** reemplazan los CTkComboBox estándar
- **Autoscroll interno**: Los menús desplegables largos hacen scroll automático al navegar con teclado/gamepad
- **Navegación unificada**: A/Enter para abrir/seleccionar, B/Esc para cerrar
- **Foco visual mejorado**: Borde único y claro sin duplicación
- **Indicador visual**: Borde completo en la opción activa del desplegable
- **Ancho consistente**: El dropdown siempre tiene el mismo ancho que el control

### 📁 Gestión de Carpetas Personalizadas
- **Nueva interfaz** para añadir carpetas de escaneo personalizadas
- **Persistencia**: Las carpetas se guardan entre sesiones
- **Interfaz intuitiva**: Añadir/eliminar carpetas con un click
- **Validación**: Detecta carpetas duplicadas automáticamente
- **Integración completa**: Las carpetas se escanean junto con Steam, Epic y Xbox

### 🔍 Autoscroll Inteligente de Ventana
- **Scroll automático del contenido** cuando navegas con teclado/gamepad
- **Detección recursiva** del CTkScrollableFrame en cualquier nivel
- **Margen adaptativo**: Mantiene el widget enfocado visible con 100px de margen
- **Búsqueda robusta de canvas**: Múltiples métodos de acceso al canvas interno
- **Logs de diagnóstico**: Mensajes DEBUG para troubleshooting

### 🎮 Filtro de Xbox en Detección Automática
- **Opción "Xbox"** añadida al filtro de plataformas
- Filtra específicamente juegos de Xbox Game Pass y Windows Store
- Complementa las opciones existentes: Steam, Epic Games, Custom

### 🖱️ Drag-to-Scroll Completo
- **Drag-to-scroll** habilitado en **todos los paneles scrollables**:
  - Config panel ✅
  - Auto panel ✅
  - Settings panel ✅ (nuevo)
  - Help panel ✅ (nuevo)
- **Configuración consistente** en toda la aplicación

---

## 🐛 Correcciones de Bugs

### ❌ Instalación en Juegos de Xbox/Windows Store
**Problema**: La instalación fallaba completamente con error "ACCESO DENEGADO" al intentar copiar carpetas opcionales.

**Solución**:
- Las carpetas opcionales (`D3D12_Optiscaler`, `DlssOverrides`, `Licenses`) ahora generan **WARNING** en lugar de **ERROR**
- La instalación **continúa** incluso si estas carpetas no se pueden copiar
- El mod funciona correctamente solo con los archivos DLL e INI (archivos core)
- Mensaje claro: "El mod puede funcionar sin esta carpeta. Si hay problemas, ejecuta como admin."

### 📋 Detalles de Instalación Incorrectos
**Problema**: El mensaje de "Detalles de instalación" mostraba "OptiScaler.dll - NO ENCONTRADO" y "Archivos core: INCOMPLETO" aunque el mod estaba instalado correctamente.

**Solución**:
- Ahora detecta correctamente las **DLLs renombradas** (`dxgi.dll`, `d3d11.dll`, `d3d12.dll`, `winmm.dll`)
- Si encuentra **cualquiera** de las DLLs renombradas + `OptiScaler.ini` → **"Archivos core: COMPLETO"**
- Eliminadas las DLLs core de la sección "Archivos adicionales" para evitar duplicación
- Mensaje mejorado si falta: "OptiScaler.dll - NO ENCONTRADO (debe estar renombrado como dxgi/d3d11/d3d12/winmm)"

### 🔄 Limpieza de Código Legacy
**Antes**: Existía código de parches globales obsoletos para CTkComboBox que causaban fragilidad.

**Después**:
- Eliminado el parche global de CTkComboBox
- Removidas funciones helper obsoletas: `_configure_combobox_dropdown_width`, `_ensure_combobox_patched`, `_configure_and_resize_dropdown`, `_force_resize_combobox_dropdown`
- Código simplificado y más mantenible
- WideComboBox proporciona toda la funcionalidad necesaria

---

## 🎨 Mejoras de Interfaz

### Gestionar Carpetas de Escaneo (Ajustes)
- **Botón "➕ Añadir Carpeta"**: Gris oscuro (#3a3a3a)
- **Botón "✓ Guardar y Cerrar"**: Azul cian (COLOR_PRIMARY)
- **Botón "✕ Cancelar"**: Gris secundario (COLOR_SECONDARY)
- **Botón eliminar "✕"**: Símbolo X en lugar de emoji 🗑️
- **Paleta de colores consistente** con el resto de la aplicación

### Títulos y Versiones
- **Título de la ventana**: Usa constante `APP_TITLE` dinámica
- **Versión actualizada** a 2.3.0 en toda la aplicación
- **About text**: Menciona soporte para Xbox y carpetas personalizadas
- **Versión dinámica**: Se actualiza automáticamente desde `APP_VERSION`

---

## 📖 Documentación Actualizada

### Panel de Ayuda
- **3 nuevas FAQs**:
  - "¿Cómo añado carpetas personalizadas para escanear?"
  - "¿Funciona con juegos de Xbox/Windows Store?"
  - "¿Qué son los WideComboBox con autoscroll?"
- Controles de gamepad y teclado actualizados
- Información sobre las nuevas características

---

## 🔧 Cambios Técnicos

### Arquitectura
- **WideComboBox** (`src/gui/components/wide_combobox.py`):
  - CTkFrame base con CTkToplevel para dropdown
  - Scroll interno con CTkScrollableFrame (max 8 opciones visibles)
  - Navegación con índice interno (`_current_index`)
  - Método `_scroll_to_current()` para autoscroll
  - Prevención de recursión en `configure()`
  - Focus ring en frame interno `_content` para evitar clipping

### Gestión de Carpetas
- Config key: `custom_game_folders` (lista de strings)
- Inicialización automática como lista vacía si no existe
- Guardado automático en `on_closing()`
- Paso al scanner via parámetro `custom_folders`

### Autoscroll de Ventana
- Función `auto_scroll_to_widget()` mejorada
- Búsqueda recursiva de `CTkScrollableFrame`
- Cálculo de posición con `winfo_rooty()` (absoluta)
- Fallback a método de recorrido jerárquico
- Actualización forzada con `update_idletasks()`

---

## 📊 Estadísticas

- **Archivos modificados**: 3
  - `src/gui/gaming_app.py`
  - `src/gui/components/wide_combobox.py`
  - `src/core/installer.py`
- **Líneas añadidas**: ~800
- **Líneas eliminadas**: ~200
- **Nuevas características**: 5
- **Bugs corregidos**: 3
- **FAQs añadidas**: 3

---

## 🚀 Instrucciones de Compilación

### Con Nuitka (Recomendado)
```powershell
.\build_nuitka_admin.ps1
```

### Con PyInstaller
```powershell
pyinstaller --noconfirm "Gestor optiscaler V2.0.spec"
```

---

## 📝 Notas de Actualización

### Para usuarios que vienen de v2.2.x
1. **Configuración preservada**: Todos tus ajustes se mantienen
2. **Nuevos controles**: Los combobox ahora son WideComboBox con mejor UX
3. **Carpetas personalizadas**: Ve a Ajustes para añadir tus carpetas de juegos
4. **Xbox compatible**: Los juegos de Xbox Game Pass ahora se instalan correctamente

### Para desarrolladores
1. **API de WideComboBox**: Compatible con CTkComboBox (`.get()`, `.set()`, `.variable`, `.values`)
2. **Config extendido**: Nueva key `custom_game_folders` en `injector_config.json`
3. **Logs mejorados**: Más mensajes DEBUG para autoscroll y navegación

---

## 🙏 Agradecimientos

- **cdozdil** - OptiScaler mod
- **Nukem9** - dlssg-to-fsr3 mod
- **Comunidad** - Feedback y testing en handheld devices

---

## 🔗 Enlaces

- [OptiScaler GitHub](https://github.com/cdozdil/OptiScaler)
- [dlssg-to-fsr3 GitHub](https://github.com/Nukem9/dlssg-to-fsr3)
- [Documentación completa](docs/)

---

## 📄 Licencia

Open Source - Ver [LICENSE](LICENSE) para más detalles.
