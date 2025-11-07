# Instrucciones para Completar la Configuración

## ✅ A) Añadir Topics al Repositorio

1. Ve a: https://github.com/Bigflood92/OptiScaler-Manager
2. Haz clic en el ícono de engranaje ⚙️ al lado de "About" (arriba a la derecha)
3. En "Topics", añade estos (separados por comas):
   ```
   fsr, dlss, xess, upscaling, gaming, mod-manager, python, customtkinter, optiscaler, game-mods, fsr3, frame-generation, windows, modding-tools
   ```
4. Click en "Save changes"

---

## ✅ B) Habilitar GitHub Pages

### Paso 1: Configurar Pages

1. Ve a: https://github.com/Bigflood92/OptiScaler-Manager/settings/pages
2. En "Build and deployment":
   - Source: **Deploy from a branch**
   - Branch: **gh-pages** (se creará automáticamente)
   - Folder: **/ (root)**
3. Click en "Save"

### Paso 2: Esperar el Deploy

El workflow `docs.yml` se ejecutará automáticamente y creará la rama `gh-pages`.

Espera 2-3 minutos y luego tu documentación estará en:
**https://bigflood92.github.io/OptiScaler-Manager/**

---

## ✅ C) Dependabot

✅ **Ya configurado** - Se activará automáticamente con el archivo `.github/dependabot.yml`

Dependabot creará PRs automáticos cada lunes para actualizar:
- Dependencias de Python
- GitHub Actions

---

## ✅ D) Habilitar y Configurar GitHub Wiki

### Paso 1: Habilitar Wiki

1. Ve a: https://github.com/Bigflood92/OptiScaler-Manager/settings
2. Baja a la sección "Features"
3. Marca el checkbox "Wikis"
4. Click en "Save changes"

### Paso 2: Crear Páginas de Wiki

Ve a: https://github.com/Bigflood92/OptiScaler-Manager/wiki

Crea estas páginas (usa el botón "Create the first page" y luego "New Page"):

#### 1. Home (Página Principal)

```markdown
# Bienvenido a OptiScaler Manager Wiki

![OptiScaler Manager](https://raw.githubusercontent.com/Bigflood92/OptiScaler-Manager/main/.github/images/main-interface.png)

## 📚 Índice de Contenidos

- [Instalación](Installation)
- [Guía de Inicio Rápido](Quick-Start)
- [Configuración Avanzada](Advanced-Configuration)
- [Modo Gaming](Gaming-Mode)
- [Juegos Probados](Tested-Games)
- [Solución de Problemas](Troubleshooting)
- [FAQ](FAQ)

## 🎮 ¿Qué es OptiScaler Manager?

OptiScaler Manager es una herramienta gráfica avanzada para inyectar FSR 3.1/4.0 (AMD FidelityFX Super Resolution), XeSS y DLSS en juegos compatibles mediante OptiScaler.

## 🚀 Enlaces Rápidos

- [📦 Descargar última versión](https://github.com/Bigflood92/OptiScaler-Manager/releases/latest)
- [📖 Documentación completa](https://bigflood92.github.io/OptiScaler-Manager/)
- [🐛 Reportar bug](https://github.com/Bigflood92/OptiScaler-Manager/issues/new?template=bug_report.md)
- [✨ Sugerir feature](https://github.com/Bigflood92/OptiScaler-Manager/issues/new?template=feature_request.md)

## ✨ Características Principales

### 🎨 Interfaz Dual
- **Modo Clásico**: Vista tradicional con pestañas
- **Modo Gaming**: Optimizado para mandos (Steam Deck, ROG Ally, etc.)

### 🎯 Gestión Inteligente
- Detección automática de juegos (Steam, Epic, Xbox, GOG)
- Instalación masiva con un clic
- Configuración individual por juego

### ⚙️ Configuración Avanzada
- Presets rápidos (Default, Performance, Balanced, Quality)
- Control de Frame Generation
- Múltiples opciones de upscaling
```

#### 2. Tested-Games (Juegos Probados)

```markdown
# Juegos Probados

Lista de juegos verificados que funcionan con OptiScaler Manager.

## ✅ Funcionando Perfectamente

| Juego | Versión OptiScaler | DLL | Notas |
|-------|-------------------|-----|-------|
| Cyberpunk 2077 | 0.7.9 | nvngx.dll | Frame Gen funciona |
| Starfield | 0.7.9 | dxgi.dll | Usar preset Balanced |
| Alan Wake 2 | 0.7.9 | nvngx.dll | Excelente rendimiento |
| Spider-Man Remastered | 0.7.9 | nvngx.dll | Sin problemas |
| Red Dead Redemption 2 | 0.7.9 | dxgi.dll | Mejora notable |

## ⚠️ Funciona con Ajustes

| Juego | Problema | Solución |
|-------|----------|----------|
| Hogwarts Legacy | Crash al inicio | Usar d3d12.dll en lugar de nvngx.dll |
| Forza Horizon 5 | Frame Gen inestable | Desactivar Frame Generation |

## ❌ Problemas Conocidos

| Juego | Problema | Estado |
|-------|----------|--------|
| Call of Duty MW3 | Anticheat incompatible | No soportado |
| Valorant | Anticheat incompatible | No soportado |

## 🤝 Contribuir

¿Probaste un juego? [Reporta tus resultados](https://github.com/Bigflood92/OptiScaler-Manager/issues/new?template=feature_request.md)

Incluye:
- Nombre del juego
- Versión de OptiScaler usada
- DLL de inyección
- Configuración (preset)
- GPU utilizada
- Resultado (funciona/no funciona/parcial)
```

#### 3. Troubleshooting

```markdown
# Solución de Problemas

Guía completa para resolver problemas comunes.

## 🎮 Problemas con la Aplicación

### La aplicación no inicia

**Síntomas**: Nada sucede al hacer doble clic

**Soluciones**:
1. Ejecuta como administrador (click derecho → "Ejecutar como administrador")
2. Verifica que tienes Windows 10/11 64-bit
3. Revisa `gestor_optiscaler_log.txt` en la carpeta de la aplicación

### No se detectan juegos

**Soluciones**:
1. Ve a **Ajustes → Carpetas Personalizadas**
2. Añade las rutas donde tienes juegos instalados
3. Usa **Ruta Manual** para añadir juegos específicos
4. Presiona **Escanear** después de añadir carpetas

### Windows Defender bloquea el ejecutable

**Causa**: Ejecutable no firmado digitalmente

**Solución**:
1. Click en "Más información"
2. Click en "Ejecutar de todas formas"
3. (Opcional) Añade excepción en Windows Defender

## 🎯 Problemas con Mods

### El mod no funciona en el juego

**Pasos de diagnóstico**:

1. **Verifica compatibilidad**: El juego debe soportar DLSS nativo
2. **Prueba diferentes DLLs**:
   - Empieza con `nvngx.dll`
   - Si no funciona, prueba `dxgi.dll`
   - Luego `d3d11.dll` o `d3d12.dll`
3. **Revisa configuración**:
   - Prueba preset **Default** primero
   - Desactiva Frame Generation
4. **Verifica instalación**:
   - Revisa `gestor_optiscaler_log.txt`
   - Verifica que los archivos se copiaron al juego

### El juego crashea después de instalar

**Solución inmediata**:
1. Desinstala el mod desde OptiScaler Manager
2. Verifica integridad de archivos (Steam/Epic)
3. Reinicia el juego

**Si el problema persiste**:
1. Actualiza drivers de GPU
2. Prueba con preset más conservador (Quality sin Frame Gen)
3. Verifica que tu GPU sea compatible

### Frame Generation no funciona

**Requisitos**:
- GPU: AMD RX 5000+, NVIDIA GTX 10XX+, Intel Arc
- OptiScaler 0.7.0 o superior
- Juego compatible con DLSS 3

**Soluciones**:
1. Activa DLSS/FSR en el juego primero
2. Selecciona modo Performance o Balanced
3. Verifica en overlay (Insert) que Frame Gen está activo

## 📊 Problemas de Rendimiento

### FPS más bajos después del mod

**Causas posibles**:
1. Frame Generation no está activado en el juego
2. Configuración muy alta (Ultra Quality)
3. GPU no soporta Frame Gen eficientemente

**Soluciones**:
1. Activa DLSS/FSR en opciones del juego
2. Usa preset Performance o Balanced
3. Verifica que Frame Generation esté activado

### Stuttering o micro-parones

**Soluciones**:
1. Desactiva Frame Generation
2. Usa modo Quality en lugar de Performance
3. Actualiza drivers de GPU
4. Cierra aplicaciones en segundo plano

## 🔧 Otros Problemas

### No puedo descargar nuevas versiones de OptiScaler

**Soluciones**:
1. Verifica conexión a internet
2. Desactiva temporalmente firewall/antivirus
3. Descarga manualmente desde [OptiScaler GitHub](https://github.com/cdozdil/OptiScaler/releases)

### Configuración no se guarda

**Soluciones**:
1. Ejecuta como administrador
2. Verifica permisos en carpeta `%APPDATA%\Gestor OptiScaler`
3. Reinstala la aplicación

## 📝 Reportar Problemas

Si ninguna solución funciona:

1. Ve a [GitHub Issues](https://github.com/Bigflood92/OptiScaler-Manager/issues)
2. Usa el template de bug report
3. Incluye:
   - `gestor_optiscaler_log.txt`
   - Versión de Windows
   - Modelo de GPU
   - Juego afectado
   - Pasos para reproducir

[🐛 Reportar Bug](https://github.com/Bigflood92/OptiScaler-Manager/issues/new?template=bug_report.md){ .md-button }
```

---

## 🎉 Resumen Final

Una vez completes todos los pasos:

✅ **Topics añadidos** → Mejor descubribilidad en GitHub
✅ **GitHub Pages activo** → https://bigflood92.github.io/OptiScaler-Manager/
✅ **Dependabot configurado** → PRs automáticos cada lunes
✅ **Wiki creada** → Documentación extendida accesible

Tu repositorio estará al nivel de proyectos profesionales open-source! 🚀
