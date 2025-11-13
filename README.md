# 🎮 OptiScaler Manager

![Version](https://img.shields.io/badge/version-2.2.0-blue)
![Python](https://img.shields.io/badge/python-3.12-green)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey)
![License](https://img.shields.io/badge/license-MIT-orange)
[![Release](https://github.com/Bigflood92/OptiScaler-Manager/actions/workflows/release.yml/badge.svg)](https://github.com/Bigflood92/OptiScaler-Manager/actions)
[![GitHub release](https://img.shields.io/github/v/release/Bigflood92/OptiScaler-Manager)](https://github.com/Bigflood92/OptiScaler-Manager/releases)
[![GitHub stars](https://img.shields.io/github/stars/Bigflood92/OptiScaler-Manager?style=social)](https://github.com/Bigflood92/OptiScaler-Manager)

**Gestor automatizado de OptiScaler** - Herramienta gráfica avanzada para inyectar FSR 3.1/4.0 (AMD FidelityFX Super Resolution), XeSS y DLSS en juegos compatibles mediante OptiScaler. Ahora con build nativa vía Nuitka + elevación UAC automática.

---

## 📸 Capturas de Pantalla

### Interfaz Principal
<div align="center">
  <img src=".github/images/main-interface.png" alt="Interfaz Principal" width="800"/>
  <p><em>Vista principal con lista de juegos detectados, navegación drag-to-scroll y controles centralizados</em></p>
</div>

### Panel de Ayuda (Controles)
<div align="center">
  <img src=".github/images/help-panel.png" alt="Panel de Ayuda" width="800"/>
  <p><em>Panel desplegable con todos los controles de gamepad y atajos de teclado</em></p>
</div>

### Descarga de Mods
<div align="center">
  <img src=".github/images/mod-downloader.png" alt="Descarga de Mods" width="600"/>
  <p><em>Gestor de versiones de OptiScaler con descarga automática desde GitHub</em></p>
</div>

### Configuración de Juego
<div align="center">
  <img src=".github/images/game-config.png" alt="Configuración de Juego" width="600"/>
  <p><em>Configuración individual por juego con presets y opciones avanzadas</em></p>
</div>

### Configuración General
<div align="center">
  <img src=".github/images/settings.png" alt="Configuración" width="800"/>
  <p><em>Ajustes de la aplicación, carpetas personalizadas y opciones avanzadas</em></p>
</div>

---

## ✨ Características

### 🔄 Auto-Actualización (NUEVO v2.3.0)
- **Chequeo automático** al iniciar la aplicación
- **Notificaciones visuales** cuando hay nuevas versiones disponibles
- **Actualización masiva** de OptiScaler en todos los juegos instalados
- **Badges de versión** por juego (✅ Actualizado | ⚠️ Update disponible | ⚪ Sin mod)
- **Historial de versiones** preservado automáticamente
- Ver guía completa: [`docs/user-guide/auto-update-guide.md`](docs/user-guide/auto-update-guide.md)

### 🎨 Interfaz Moderna
- **Iconos centralizados**: Diseño consistente con iconos PNG personalizados
- **Drag-to-scroll**: Navegación fluida en listas largas de juegos
- **Panel de ayuda integrado**: Muestra todos los controles disponibles (teclado/gamepad)
- **Sistema de progreso avanzado**: Barra animada con porcentajes, tiempo estimado y resumen detallado
- **Interfaz Gaming** (En desarrollo): Navegación optimizada para mandos Xbox/PlayStation

### 🎯 Gestión de Mods
- **Detección automática** de juegos en Steam, Epic Games, Xbox Game Pass, GOG
- **Instalación/desinstalación masiva** con seguimiento en tiempo real
- **Configuración individual** por juego
- **Sistema de caché** para detección rápida de juegos
- **Presets rápidos**: Default, Performance, Balanced, Quality, Custom
- **Vista previa en vivo**: Resaltado visual de juegos mientras se procesan

### ⚙️ Configuración Avanzada
- **GPU**: AMD/Intel o NVIDIA
- **DLL de inyección**: dxgi.dll, d3d11.dll, d3d12.dll, dinput8.dll, winmm.dll
- **Frame Generation**: Automático, Activado, Desactivado
- **Upscaler**: FSR 3.1, FSR 4.0, XeSS, DLSS, Automático
- **Modo de reescalado**: Performance, Balanced, Quality, Ultra Performance, Native AA, Automático
- **Sharpness**: Control deslizante 0.0 - 1.0
- **Extras**: Overlay debug, Motion Blur

### 📦 Gestión de Versiones
- **Auto-actualización inteligente** con detección de nuevas releases (v2.3.0+)
- **Descarga automática** de versiones de OptiScaler desde GitHub
- **Instalación directa** desde el gestor
- **Caché de versiones** para trabajo offline
- **Tracking por juego** con badges visuales de estado
- **Comparación automática** de versiones instaladas vs disponibles

---

## 📥 Instalación

### Ejecutable (Usuario Final)

**[📦 Descargar última versión](https://github.com/Bigflood92/OptiScaler-Manager/releases/latest)**

1. Descarga `Gestor OptiScaler V2.2.exe`
2. Doble clic (Windows solicitará permisos de administrador automáticamente)
3. Se crearán las carpetas en `Config Optiscaler Gestor/` junto al .exe
4. ¡Listo para usar!

> **Nota**: El ejecutable requiere permisos de administrador para funcionar (necesarios para copiar archivos en carpetas de juegos). No está firmado digitalmente - acepta el aviso UAC de Windows.

### Desde Código Fuente (Desarrolladores)

#### Requisitos
- Windows 10/11 x64
- Python 3.12 (recomendado - Python 3.13 tiene bugs conocidos)
- Permisos de administrador

#### Instalación

```powershell
# Clonar repositorio
git clone https://github.com/Bigflood92/OptiScaler-Manager.git
cd OptiScaler-Manager

# Crear entorno virtual con Python 3.12
py -3.12 -m venv .venv312

# Activar entorno
.\.venv312\Scripts\Activate.ps1

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar aplicación
python -m src.main
```

---

## 🚀 Uso

### Primera Ejecución

1. Ejecuta `Gestor OptiScaler V2.2.exe` (solicitará permisos de administrador automáticamente)
2. Aparecerá un tutorial de bienvenida en el primer inicio
3. Ve a **Ajustes de la App** → **Carpetas Personalizadas**
4. Añade rutas donde tienes juegos instalados (ej: `D:\Juegos`)
5. Pulsa **🔍 Escanear** para detectar juegos (con animación y progreso en tiempo real)

### Instalar Mod en Juegos

1. En **Juegos Detectados**, marca los juegos deseados con checkbox
2. Configura opciones en **Configuración del Mod** o usa un **Preset**
3. Pulsa **✅ APLICAR A SELECCIONADOS**
4. Observa el progreso en tiempo real con porcentaje, tiempo estimado y lista actualizada
5. Al finalizar, haz clic en **"Ver detalles"** para ver el resumen completo

### Gestión de Versiones

1. Ve a **Ajustes de la App** → **Descargar Mods**
2. Selecciona la versión de OptiScaler deseada
3. Pulsa **Descargar y Seleccionar**
4. La versión descargada se aplicará a futuros mods

---

## 🔧 Presets Disponibles

| Preset | Upscaler | Frame Gen | Modo Escalado | Nitidez |
|--------|----------|-----------|---------------|---------|
| **Default** | Automático | Automático | Automático | 0.8 |
| **Performance** | FSR 3.1 | Activado | Performance | 0.5 |
| **Balanced** | FSR 3.1 | Activado | Balanced | 0.7 |
| **Quality** | XeSS | Desactivado | Quality | 0.9 |
| **Custom** | - | - | - | - |

---

## 📁 Estructura del Proyecto

```
OptiScaler-Manager/
├── src/                    # Código fuente modular
│   ├── main.py            # Punto de entrada principal
│   ├── core/              # Lógica de negocio
│   │   ├── scanner.py     # Detección de juegos
│   │   ├── installer.py   # Instalación de mods
│   │   ├── config_manager.py  # Gestión de configuración
│   │   └── utils.py       # Utilidades comunes
│   ├── gui/               # Interfaz gráfica
│   │   ├── gaming_app.py  # Interfaz principal de la aplicación
│   │   ├── components/    # Componentes reutilizables (modales, popups)
│   │   └── widgets/       # Widgets personalizados
│   └── config/            # Configuración y constantes
│       └── settings.py
├── Config Optiscaler Gestor/  # Configuración de usuario
│   ├── mod_source/        # Versiones descargadas de OptiScaler
│   ├── games_cache.json   # Caché de juegos detectados
│   └── injector_config.json  # Configuración de la aplicación
├── requirements.txt       # Dependencias Python
├── Gestor optiscaler V2.0.spec  # Configuración PyInstaller
└── run.ps1                # Script de arranque
```

---

## 🛠️ Desarrollo

### Compilar Ejecutable (Nuitka recomendado)

Requiere Python 3.12 y (opcional) Visual Studio Build Tools. Nuitka descargará un toolchain MinGW si no existe MSVC.

```powershell
# Activar entorno virtual
.\.venv312\Scripts\Activate.ps1

# Instalar dependencias de build (una sola vez)
pip install nuitka ordered-set zstandard

# Build con elevación UAC automática
./build_nuitka_admin.ps1

# El ejecutable queda en dist/Gestor OptiScaler V2.2.exe
```

### Alternativa: PyInstaller (obsoleto, no recomendado)

```powershell
# Activar entorno virtual
.\.venv312\Scripts\Activate.ps1

# Puede fallar con ciertos problemas de imágenes en CustomTkinter
pyinstaller --noconfirm "Gestor optiscaler V2.0.spec"

# Ejecutable: dist/Gestor optiscaler V2.0.exe
```

### Ejecutar Tests

```powershell
# Tests unitarios (si existen)
pytest tests/

# Test del auto-updater (seguro, NO modifica archivos)
.\.venv312\Scripts\python.exe test_updater.py

# Test de actualización real (CON confirmación)
.\.venv312\Scripts\python.exe test_updater_real.py
```

---

## 🐛 Solución de Problemas

### Auto-actualización no funciona
1. Verifica tu conexión a internet
2. Comprueba que no haya firewall bloqueando `api.github.com`
3. Consulta la guía detallada: [`docs/user-guide/auto-update-guide.md`](docs/user-guide/auto-update-guide.md)

### No se detectan juegos
1. Verifica que los juegos estén instalados en las rutas estándar
2. Añade carpetas personalizadas en **Configuración de la App**
3. Usa **Ruta Manual** para juegos específicos

### El mod no funciona en un juego
1. Verifica que el juego sea compatible con DLSS/FSR
2. Prueba con diferentes DLLs de inyección
3. Consulta el archivo `gestor_optiscaler_log.txt` para detalles

### Error: "No module named 'customtkinter'"
**Causa**: Dependencias no instaladas en el entorno virtual

**Solución**:
```powershell
.\.venv312\Scripts\pip install -r requirements.txt
```

---

## 📄 Licencia

**MIT License** - © 2025 Jorge Coronas

Se concede permiso para usar, copiar, modificar, fusionar, publicar, distribuir, sublicenciar y/o vender copias del Software, sujeto a las condiciones de la licencia MIT completa.

Ver [LICENSE](LICENSE) para más detalles.

---

## 🙏 Créditos

- **[OptiScaler](https://github.com/cdozdil/OptiScaler)** - Por el increíble mod que hace posible FSR3/XeSS en juegos DLSS
- **[CustomTkinter](https://github.com/TomSchimansky/CustomTkinter)** - Por la moderna biblioteca de UI
- Comunidad de modding de PC Gaming

---

## 🤝 Contribuciones

¡Las contribuciones son bienvenidas! Por favor:

1. Lee la [Guía de Contribución](CONTRIBUTING.md)
2. Fork el proyecto
3. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
4. Commit tus cambios (`git commit -m 'Add: Amazing Feature'`)
5. Push a la rama (`git push origin feature/AmazingFeature`)
6. Abre un Pull Request

Ver [CHANGELOG.md](CHANGELOG.md) para el historial de cambios del proyecto.

---

## 📞 Contacto

**Jorge Coronas** - Creador y mantenedor principal

- GitHub: [@Bigflood92](https://github.com/Bigflood92)
- Repositorio: [OptiScaler-Manager](https://github.com/Bigflood92/OptiScaler-Manager)

---

<p align="center">
  <sub>Hecho con ❤️ para la comunidad de gaming en PC</sub>
</p>
