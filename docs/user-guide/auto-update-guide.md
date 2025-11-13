# 🔄 Auto-Actualización de OptiScaler - Guía de Usuario

**Versión**: v2.3.0  
**Última actualización**: 13 de Noviembre de 2025

---

## 📋 Descripción General

El sistema de auto-actualización permite mantener OptiScaler siempre actualizado de forma automática, descargando las últimas versiones desde GitHub y aplicándolas tanto al repositorio local como a todos los juegos instalados.

### ✨ Características Principales

- ✅ **Chequeo automático** al iniciar la aplicación
- ✅ **Notificación visual** cuando hay nuevas versiones
- ✅ **Descarga en segundo plano** con barra de progreso
- ✅ **Actualización masiva** de todos los juegos instalados
- ✅ **Historial de versiones** preservado en carpetas separadas
- ✅ **Detección de versión por juego** con badges visuales
- ✅ **Soporte para archivos .7z** (formato nativo de OptiScaler)

---

## 🚀 Uso Básico

### Método 1: Chequeo Automático (Recomendado)

1. **Inicia la aplicación** normalmente
2. **Espera 2 segundos** → el sistema verifica automáticamente
3. Si hay actualización disponible, verás una **notificación azul** en la barra de progreso:
   ```
   🆕 OptiScaler 0.8.0 disponible (clic para actualizar)
   ```
4. **Haz clic** en la notificación → aparece diálogo de confirmación
5. Confirma → descarga e instalación automática

### Método 2: Chequeo Manual

1. Ve a **⚙️ Ajustes** (panel lateral)
2. Busca la sección **"📥 Gestión de Mods"**
3. Haz clic en **"🔄 Buscar actualización"**
4. El sistema consulta GitHub y muestra el resultado:
   - ✅ **"Nueva versión: X.X.X"** → botón de actualización disponible
   - ℹ️ **"Ya tienes la última versión"** → no hay nada que hacer

---

## 🎮 Badges de Versión en Juegos

Cada juego en la lista muestra un **badge de estado** que indica:

| Badge | Significado | Acción Recomendada |
|-------|-------------|-------------------|
| **⚪ Sin mod** | OptiScaler no instalado | Instalar desde panel Auto |
| **✅ OptiScaler v0.7.9** | Instalado y actualizado | Ninguna |
| **⚠️ Actualización disponible (v0.7.9 → v0.8.0)** | Versión desactualizada | Usar "Buscar actualización" |
| **❌ Instalación incompleta** | Archivos faltantes | Re-instalar |

### ¿Cómo se detecta la versión?

1. Al **instalar** OptiScaler en un juego, se crea `version.json` con metadata:
   ```json
   {
     "version": "0.7.9",
     "tag": "v0.7.9",
     "installed_at": "2025-11-13T10:30:00",
     "source_url": "https://github.com/optiscaler/OptiScaler/releases/tag/v0.7.9"
   }
   ```

2. Al **escanear juegos**, el sistema lee este archivo y compara con la versión global

3. El **badge se actualiza** automáticamente tras instalar/actualizar

---

## 📁 Estructura de Archivos

### Ubicación de Versiones

```
Config Optiscaler Gestor/
  mod_source/
    OptiScaler/
      version.json              ← Versión global (última descargada)
      OptiScaler_0.7.9/         ← Versión 0.7.9
        OptiScaler.dll
        OptiScaler.ini
        ...
      OptiScaler_0.8.0/         ← Versión 0.8.0 (nueva)
        OptiScaler.dll
        OptiScaler.ini
        ...
```

### Versionado por Juego

```
C:/Games/Cyberpunk 2077/bin/x64/
  OptiScaler.dll
  OptiScaler.ini
  nvngx.dll                    ← DLL spoofed
  version.json                 ← Metadata de versión instalada
```

---

## ⚙️ Proceso de Actualización Detallado

### Fase 1: Detección (2-5 segundos)

1. Consulta GitHub API: `https://api.github.com/repos/optiscaler/OptiScaler/releases`
2. Obtiene última versión publicada (ej: `0.8.0`)
3. Lee versión local desde `mod_source/OptiScaler/version.json`
4. Compara versiones usando semver (ej: `0.8.0 > 0.7.9`)

### Fase 2: Descarga (30-90 segundos según conexión)

1. Descarga asset `.7z` desde GitHub Releases
2. Muestra progreso en barra: `[████████░░] 80%`
3. Guarda temporalmente en `_download_0.8.0.7z`

### Fase 3: Extracción (10-20 segundos)

1. Usa `7z.exe` para extraer contenido
2. Crea carpeta `OptiScaler_0.8.0/`
3. Preserva versiones anteriores (no se eliminan)

### Fase 4: Actualización de Metadatos (< 1 segundo)

1. Escribe `version.json` global con nueva versión
2. Marca la nueva carpeta como versión activa

### Fase 5: Actualización de Juegos (5-30 segundos por juego)

1. **Detecta** juegos con OptiScaler instalado (busca `version.json` en cada juego)
2. **Copia** archivos esenciales desde `OptiScaler_0.8.0/`:
   - `OptiScaler.dll`
   - `OptiScaler.ini`
   - `amd_fidelityfx_*.dll`
   - `libxess*.dll`
3. **Actualiza** `version.json` en cada juego con nueva versión
4. **Muestra** progreso: `Actualizando juego 3/5...`

---

## 🛡️ Seguridad y Backup

### Backup Automático

- ✅ **Versiones anteriores se preservan** en carpetas separadas (`OptiScaler_0.7.9/`, `OptiScaler_0.8.0/`)
- ✅ **Archivos .bak** creados al instalar (ej: `dxgi.dll.bak`)
- ⚠️ **NO se hace backup de juegos** antes de actualizar (se sobrescribe directamente)

### Rollback Manual

Si necesitas volver a una versión anterior:

1. Ve a **⚙️ Ajustes** → **"📥 Gestión de Mods"**
2. En **"Versión activa"**, selecciona `OptiScaler_0.7.9` del dropdown
3. Haz clic en **"✓ APLICAR"** en los juegos que desees revertir

---

## 🔧 Solución de Problemas

### Problema: "No se pudo obtener releases de GitHub"

**Causas posibles**:
- Sin conexión a internet
- GitHub API temporalmente inaccesible
- Firewall bloqueando acceso a `api.github.com`

**Solución**:
1. Verifica tu conexión a internet
2. Intenta de nuevo en 5 minutos
3. Si persiste, descarga manualmente desde: https://github.com/optiscaler/OptiScaler/releases

---

### Problema: "Error al extraer archivo .7z"

**Causas posibles**:
- `7z.exe` no encontrado en `mod_source/`
- Archivo `.7z` corrupto (descarga interrumpida)

**Solución**:
1. Verifica que existe `Config Optiscaler Gestor/mod_source/7z.exe`
2. Elimina archivo temporal `_download_*.7z`
3. Intenta de nuevo

---

### Problema: Badge muestra "⚠️ Actualización disponible" pero ya actualicé

**Causa**: El `version.json` del juego no se actualizó

**Solución**:
1. Ve al juego en panel **🎮 Detección Automática**
2. Haz clic en **"Quitar"**
3. Luego **"✓ APLICAR"** de nuevo
4. Esto recreará el `version.json` con versión correcta

---

## 🎯 Testing del Sistema

### Para Desarrolladores

Se incluyen dos scripts de prueba:

#### 1. `test_updater.py` (Seguro - NO modifica archivos)

```powershell
.\.venv312\Scripts\python.exe test_updater.py
```

**Verifica**:
- ✅ Conexión a GitHub API
- ✅ Detección de versión instalada
- ✅ Comparación de versiones
- ✅ URLs de descarga válidas

#### 2. `test_updater_real.py` (Actualización real con confirmación)

```powershell
.\.venv312\Scripts\python.exe test_updater_real.py
```

**Ejecuta**:
- ⚠️ Descarga real desde GitHub
- ⚠️ Extracción de archivos
- ⚠️ Actualización de `mod_source/`
- ✅ Pide confirmación antes de proceder

---

## 📊 Métricas de Rendimiento

| Operación | Tiempo Promedio | Nota |
|-----------|----------------|------|
| Chequeo GitHub | 2-5 segundos | Depende de latencia |
| Descarga .7z (30MB) | 30-90 segundos | Depende de velocidad de internet |
| Extracción | 10-20 segundos | Archivo .7z comprimido |
| Actualización por juego | 2-5 segundos | Copia de ~8 archivos |
| **Total (3 juegos)** | **1-2 minutos** | Vs 5-10 minutos manual |

**Ahorro de tiempo**: ~70% comparado con actualización manual

---

## 🔮 Roadmap Futuro

Mejoras planificadas para futuras versiones:

- [ ] **Rollback automático** si falla actualización de juegos
- [ ] **Hash verification** de archivos descargados (SHA256)
- [ ] **Delta updates** (solo archivos modificados)
- [ ] **Changelog modal** mostrando notas de release antes de actualizar
- [ ] **Programación de chequeos** (diario, semanal, manual)
- [ ] **Notificaciones de escritorio** Windows cuando hay updates

---

## 📞 Soporte

- **GitHub Issues**: https://github.com/Bigflood92/OptiScaler-Manager/issues
- **Documentación**: `docs/development/v2.3.0-plan.md`
- **Logs**: `gestor_optiscaler_log.txt`

---

**Última revisión**: 13 de Noviembre de 2025  
**Autor**: Jorge + GitHub Copilot  
**Versión del documento**: 1.0
