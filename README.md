# 🎮 OptiScaler Manager

![Version](https://img.shields.io/badge/version-2.0.0-blue)
![Python](https://img.shields.io/badge/python-3.12-green)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey)
![License](https://img.shields.io/badge/license-MIT-orange)
[![GitHub release](https://img.shields.io/github/v/release/Bigflood92/OptiScaler-Manager)](https://github.com/Bigflood92/OptiScaler-Manager/releases)
[![GitHub stars](https://img.shields.io/github/stars/Bigflood92/OptiScaler-Manager?style=social)](https://github.com/Bigflood92/OptiScaler-Manager)

**Gestor automatizado de OptiScaler** - Herramienta gráfica avanzada para inyectar FSR3 (AMD FidelityFX Super Resolution 3) en juegos compatibles mediante OptiScaler/DLSS Enabler.




## ✨ Características

### Interfaz Dual
- **Interfaz Clásica**: Vista tradicional de pestañas para configuración detallada
- **Interfaz Gaming**: Diseño optimizado para navegación con mando (Xbox/PlayStation)
  - Navegación completa con D-Pad y botones
  - Indicadores visuales de foco (bordes de colores)
  - Panel lateral de navegación
  - Soporte táctil en dispositivos compatibles

### Gestión de Mods
- **Detección automática** de juegos en múltiples launchers
- **Instalación/desinstalación masiva** en juegos seleccionados
- **Configuración individual** por juego
- **Sistema de caché** para detección rápida de juegos
- **Presets rápidos**: Default, Performance, Balanced, Quality, Custom

### Configuración Avanzada
- **GPU**: AMD/Intel o NVIDIA
- **DLL de inyección**: dxgi.dll, d3d11.dll, d3d12.dll, dinput8.dll, winmm.dll
- **Frame Generation**: Automático, Activado, Desactivado
- **Upscaler**: FSR 3.1, FSR 4.0, XeSS, DLSS, Automático
- **Modo de reescalado**: Performance, Balanced, Quality, Ultra Performance, Native AA, Automático
- **Sharpness**: Control deslizante 0.0 - 1.0
- **Extras**: Overlay debug, Motion Blur

### Gestión de Versiones
- **Descarga automática** de versiones de GitHub
- **Instalación directa** desde el gestor
- **Caché de versiones** para trabajo offline
- **Actualización automática** cada 24h

## 📥 Descarga

**[Descargar última versión](https://github.com/Bigflood92/OptiScaler-Manager/releases/latest)**

El ejecutable es portable, no requiere instalación.




## 🚀 Uso---



### Primera Ejecución1. Clona o descarga este repositorio

1. Ejecutar `Gestor optiscaler V2.0.exe`

2. Ir a **Ajustes de la App** → **Carpetas Personalizadas**## 📋 Requisitos

3. Añadir rutas donde tienes juegos instalados (ej: `D:\Juegos`, Steam, Epic, GOG)

4. Pulsar el botón **🔍 Escanear** para detectar juegos**Opción 2: Desde línea de comandos**2. Instala las dependencias:



### Instalar Mod en Juegos- **Sistema Operativo**: Windows 10/11 x64

1. En **Juegos Detectados**, marcar los juegos deseados

2. Configurar opciones en **Configuración del Mod** (o usar un Preset)- **Python**: 3.12 (recomendado) - *Python 3.13 tiene bugs conocidos*```powershell```bash

3. Pulsar **✅ APLICAR A SELECCIONADOS**

- **Permisos**: Administrador (necesario para modificar archivos de juegos)

### Gestión de Versiones

1. Ir a **Ajustes de la App** → **Descargar Mods**- **Dependencias**: Instaladas automáticamente desde `requirements.txt`.\.venv312\Scripts\python.exe -m src.mainpip install -r requirements.txt

2. Seleccionar versión de OptiScaler

3. Pulsar **Descargar y Seleccionar**

4. La versión descargada se aplicará a futuros mods

---``````

### Navegación con Mando



#### Menú Lateral (NAV)

- **↑↓**: Cambiar entre secciones## 🚀 Inicio Rápido

- **→**: Entrar al panel activo



#### Panel de Configuración

- **↑↓**: Navegar entre filas (Presets → GPU → DLL → Frame Gen → Upscaler → Upscale Mode → Sharpness → Extras)### Ejecutable (Usuario Final)**Opción 3: Desde VS Code**## Uso

- **←→** en **Presets**: Cambiar entre los 5 botones

- **←→** en **GPU**: Cambiar entre AMD/NVIDIA (activa automáticamente)

- **←→** en **Sharpness**: Ajustar valor (±0.05)

- **A/Enter**: Activar desplegables, checkboxes o botones1. Descarga `Gestor optiscaler V2.0.exe` desde [Releases](../../releases)1. Abrir el panel "Run and Debug" (Ctrl+Shift+D)

- **B/Esc**: Cancelar

- **←** (sin opciones horizontales): Volver al menú NAV2. Ejecuta como administrador



#### Panel de Juegos3. ¡Listo para usar!2. Seleccionar "Python: FSR Injector (Normal)"1. Ejecuta el programa como administrador:

- **↑↓**: Navegar entre juegos

- **A**: Seleccionar/deseleccionar juego

- **Botón verde 🎮**: Cambiar a interfaz clásica

### Desde Código Fuente (Desarrollo)3. Presionar F5```bash

## 🔧 Requisitos del Sistema



- **Windows 10/11** (64-bit)

- **7-Zip** (descarga automática disponible en primera ejecución)```powershellpython src/main.py

- **Permisos de administrador** (para inyección de DLLs en carpetas de juegos)

# Clonar repositorio

## 📁 Estructura de Carpetas

git clone https://github.com/TU_USUARIO/gestor-optiscaler.git## 📁 Estructura del Proyecto```

```

Config Optiscaler Gestor/cd gestor-optiscaler

├── mod_source/           # Versiones descargadas de OptiScaler

├── games_cache.json      # Caché de juegos detectados

├── injector_config.json  # Configuración de la aplicación

└── gestor_optiscaler_log.txt  # Registro de operaciones# Crear entorno virtual con Python 3.12

```

py -3.12 -m venv .venv312```2. Selecciona el juego en la primera pestaña

## 🛠️ Desarrollo



### Requisitos

- Python 3.12# Activar entornofsr 3 inyector v2.0/3. Descarga y configura los mods en la segunda pestaña

- Dependencias: `customtkinter`, `pygame`, `pillow`, `requests`, `darkdetect`

.\.venv312\Scripts\Activate.ps1

### Instalación para desarrollo

```bash├── src/                    # Código fuente modular4. Aplica los cambios

# Crear entorno virtual

python -m venv .venv312# Instalar dependencias



# Activar entornopip install -r requirements.txt│   ├── main.py            # Punto de entrada principal5. ¡Disfruta de FSR3!

.venv312\Scripts\activate



# Instalar dependencias

pip install -r requirements.txt# Ejecutar aplicación│   ├── core/              # Lógica de negocio



# Ejecutar aplicaciónpython -m src.main

python -m src.main

``````│   │   ├── scanner.py     # Detección de juegos## Desarrollo



### Compilar ejecutable

```bash

# Activar entorno virtual---│   │   ├── installer.py   # Instalación de mods

.venv312\Scripts\activate



# Compilar con PyInstaller

pyinstaller "Gestor optiscaler V2.0.spec"## 🎯 Uso│   │   ├── config_manager.py  # Gestión de configuraciónPara contribuir al desarrollo:

```



## 📝 Changelog

### Interfaz Gaming (Modo Simplificado)│   │   └── utils.py       # Utilidades comunes

### V2.0.0 (07/11/2025)

- ✨ Interfaz Gaming con navegación completa por mando

- ✨ Sistema bidimensional de navegación en configuración

- ✨ Presets rápidos (Default, Performance, Balanced, Quality, Custom)1. **Configuración del Mod** (⚙️)│   ├── gui/               # Interfaz gráfica1. Crea un entorno virtual:

- ✨ Descarga e instalación de versiones desde GitHub

- ✨ Sistema de caché para detección rápida de juegos   - Selecciona un preset rápido o configura manualmente

- ✨ Configuración individual por juego

- ✨ Soporte para carpetas personalizadas de búsqueda   - Ajusta Frame Generation, Upscaler, DLL de inyección│   │   ├── legacy_app.py  # GUI original migrada```bash

- 🐛 Correcciones de encoding UTF-8 en toda la interfaz

- 🐛 Fix navegación lógica con mando (visual matching)

- 🎨 Tema oscuro consistente en toda la aplicación

- 🎨 Indicadores visuales de foco (bordes verde/azul/gris)2. **Detección Automática** (🎯)│   │   └── legacy_adapter.py  # Adaptador de compatibilidadpython -m venv venv



## 🙏 Créditos   - Lista todos los juegos detectados



- **OptiScaler**: [Proyecto original en GitHub](https://github.com/cdozdil/OptiScaler)   - Selecciona múltiples juegos con checkbox│   └── config/            # Configuración y constantes.\venv\Scripts\activate  # Windows

- **CustomTkinter**: Framework de interfaz moderna

- **PyInstaller**: Empaquetado de ejecutables   - Aplica configuración a todos los seleccionados



## 📄 Licencia│       └── settings.py```



Este proyecto es un gestor/inyector para OptiScaler. Para la licencia de OptiScaler, consulta el [repositorio original](https://github.com/cdozdil/OptiScaler).3. **Ruta Manual** (📁)



## 🐛 Reportar Errores   - Añade juegos manualmente por ruta├── baks/                  # Backups del código original



Si encuentras algún problema, por favor abre un [Issue en GitHub](../../issues).   - Útil para juegos portables o versiones alternativas



## 💡 Contribuciones│   └── fsr_injector_original.py  # Monolito original (backup)2. Instala dependencias de desarrollo:



Las contribuciones son bienvenidas. Por favor abre un Pull Request con tus mejoras.4. **Configuración de la App** (🔧)


   - Añade carpetas de búsqueda personalizadas├── .venv312/             # Entorno virtual Python 3.12```bash

   - Limpia logs antiguos y backups huérfanos

├── run.ps1               # Script de arranquepip install -r requirements-dev.txt

### Navegación por Teclado

└── injector_config.json  # Configuración de la aplicación```

- **Flechas**: Navegar entre opciones

- **Enter**: Activar/seleccionar```

- **Izquierda/Derecha**: Cambiar entre menú y contenido

- **Escape**: Cerrar diálogos3. Ejecuta tests:



---## 🔧 Requisitos```bash



## 🛠️ Desarrollopython -m pytest tests/



### Estructura del Proyecto- **Python 3.12** (requerido - Python 3.13 tiene bugs conocidos)```



```- Windows 10/11

fsr 3 inyector v2.0/

├── src/- Dependencias: customtkinter, pillow, pygame, pywin32, requests## Estructura del proyecto

│   ├── main.py                 # Punto de entrada

│   ├── core/                   # Lógica de negocio

│   │   ├── scanner.py          # Detección de juegos

│   │   ├── installer.py        # Instalación de mods## 📦 Instalación/Configuración del Entorno de Desarrollo```

│   │   └── config_manager.py   # Gestión de configuración

│   └── gui/src/

│       └── legacy_app.py       # Interfaz gráfica principal

├── requirements.txt            # Dependencias PythonSi necesitas reinstalar el entorno virtual:  ├── core/             # Lógica principal

├── Gestor optiscaler V2.0.spec # Configuración PyInstaller

├── version_info.txt            # Información de versión del .exe  │   ├── utils.py     # Funciones auxiliares

└── 7z.exe                      # Extractor de archivos (incluido)

``````powershell  │   └── settings.py  # Configuración



### Compilar Ejecutable# Crear entorno virtual con Python 3.12  │



```powershellpy -3.12 -m venv .venv312  ├── gui/             # Interfaz gráfica

# Activar entorno

.\.venv312\Scripts\Activate.ps1  │   ├── main_window.py  # Ventana principal



# Compilar con PyInstaller# Activar entorno  │   └── widgets/     # Componentes GUI

pyinstaller --noconfirm "Gestor optiscaler V2.0.spec"

.\.venv312\Scripts\Activate.ps1  │       └── tabs.py  # Pestañas

# El ejecutable estará en: dist/Gestor optiscaler V2.0.exe

```  │



### Ejecutar Tests# Instalar dependencias  └── main.py         # Punto de entrada



```powershellpip install customtkinter pillow pygame pywin32 requests

pytest tests/

``````tests/               # Tests unitarios



---docs/                # Documentación



## 🔧 Configuración Avanzada## 🏗️ Arquitecturarequirements.txt     # Dependencias



### Presets Disponibles```



| Preset | Upscaler | Frame Gen | Modo Escalado | Nitidez |### Migración del Monolito (Opción B)

|--------|----------|-----------|---------------|---------|

| **Default** | Automático | Automático | Automático | 0.8 |## Licencia

| **Performance** | FSR 3.1 | Activado | Performance | 0.5 |

| **Balanced** | FSR 3.1 | Activado | Balanced | 0.7 |Este proyecto migró de un archivo monolítico (`fsr_injector.py`) a una arquitectura modular:

| **Quality** | XeSS | Desactivado | Quality | 0.9 |

MIT License - ver [LICENSE](LICENSE) para más detalles.

### Archivos de Configuración- **Core**: Lógica de negocio extraída y modularizada

- **GUI Legacy**: Interfaz original preservada con adaptador

- **injector_config.json**: Configuración de la aplicación (se guarda en `%APPDATA%\Gestor OptiScaler`)- **Adaptador**: Capa de compatibilidad entre GUI y nuevos módulos core

- **nvngx.ini**: Configuración del mod OptiScaler (se copia a cada juego)

El código original se mantiene como backup en `baks/fsr_injector_original.py`.

---

### Componentes Principales

## 🐛 Solución de Problemas

- **Scanner**: Detecta juegos instalados en plataformas (Steam, Epic, Xbox)

### Error: "Editor desconocido" al ejecutar- **Installer**: Maneja la inyección de mods FSR/DLSS

- **Config Manager**: Gestiona configuración y perfiles

**Normal** - El ejecutable no está firmado digitalmente. Es seguro, solo acepta el UAC.- **Legacy App**: GUI original con CTkScrollableFrame patches aplicados



### No se detectan juegos## 🐛 Solución de Problemas



1. Verifica que los juegos estén instalados en las rutas estándar### Error: "attempted relative import with no known parent package"

2. Añade carpetas personalizadas en "Configuración de la App"

3. Usa "Ruta Manual" para juegos específicos**Causa**: Ejecutar `python src/main.py` en lugar de como módulo.



### El mod no funciona en un juego**Solución**: Usar `python -m src.main` o el script `run.ps1`



1. Verifica que el juego sea compatible con DLSS/FSR### Error: "No module named 'customtkinter'"

2. Prueba con diferentes DLLs de inyección (nvngx.dll, dxgi.dll, etc.)

3. Consulta el log de operaciones para detalles**Causa**: Dependencias no instaladas en el entorno virtual.



---**Solución**: 

```powershell

## 📄 Licencia.\.venv312\Scripts\pip install customtkinter pillow pygame pywin32 requests

```

**MIT License** - © 2025 Jorge Coronas

### Error relacionado con traceback.py (Python 3.13)

```

Se concede permiso para usar, copiar, modificar, fusionar, publicar, distribuir,**Causa**: Bug conocido en Python 3.13.7.

sublicenciar y/o vender copias del Software, sujeto a las condiciones de la

licencia MIT completa.**Solución**: Usar Python 3.12 (ya configurado en `.venv312`)

```

## 📝 Notas de Desarrollo

Ver [LICENSE](LICENSE) para más detalles.

- **Imports**: El proyecto usa imports relativos dentro del paquete `src/`

---- **Ejecución**: Siempre ejecutar como módulo: `python -m src.main`

- **Testing**: Los tests deben importar desde `src.core` y ejecutarse desde la raíz

## 🤝 Contribuciones- **VS Code**: Configurado con launch.json para ejecución en módulo



¡Las contribuciones son bienvenidas! Por favor:## 🎮 Uso



1. Fork el proyecto1. Ejecutar `run.ps1`

2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)2. La aplicación detectará automáticamente juegos instalados

3. Commit tus cambios (`git commit -m 'Add: Amazing Feature'`)3. Seleccionar el juego deseado

4. Push a la rama (`git push origin feature/AmazingFeature`)4. Configurar opciones de FSR/DLSS

5. Abre un Pull Request5. Aplicar la inyección



---## 📄 Licencia



## 📞 ContactoProyecto personal - Uso libre


**Jorge Coronas** - Creador y mantenedor principal

- GitHub: [@TU_USUARIO](https://github.com/TU_USUARIO)

---

## 🙏 Agradecimientos

- **OptiScaler** - Por el increíble mod que hace posible FSR3 en juegos DLSS
- **CustomTkinter** - Por la moderna biblioteca de UI
- Comunidad de modding de PC Gaming

---

<p align="center">
  <sub>Hecho con ❤️ para la comunidad de gaming en PC</sub>
</p>
