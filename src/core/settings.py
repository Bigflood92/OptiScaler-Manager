"""Constantes y configuraciones de la aplicación."""

import os

# Información de la aplicación
APP_VERSION = "2.0"
APP_TITLE = "FSR3 Injector"

# Rutas predeterminadas de Steam
STEAM_COMMON_DIR = "C:\\Program Files (x86)\\Steam\\steamapps\\common"

# Carpetas comunes donde buscar ejecutables
COMMON_EXE_SUBFOLDERS_DIRECT = [
    "bin", "binaries", "Binaries",  # Carpetas bin genéricas
    "bin\\win64", "Binaries\\Win64", "binaries\\win64",  # Subcarpetas x64
    "win64", "Win64", "x64", "64",  # Carpetas x64 genéricas
    "engine\\binaries\\win64", "Engine\\Binaries\\Win64"  # Motor (UE, etc)
]

# Patrones glob para búsqueda recursiva de .exe
RECURSIVE_EXE_PATTERNS = [
    "**/bin/**/*.exe",
    "**/binaries/**/*.exe",
    "**/win64/**/*.exe",
    "**/x64/**/*.exe",
    "**/engine/binaries/**/*.exe"
]

# Palabras clave para la lista negra de ejecutables
EXE_BLACKLIST_KEYWORDS = [
    "unins", "launcher", "crash", "report", "redist", "setup", "config", 
    "update", "install", "vc_redist", "prereq", "steam_api64", "steamwebhelper",
    "dotnet", "bink2w64", "nvngx", "d3dcompiler", "dxil", "UnityCrashHandler",
    "UplayWebCore", "EasyAntiCheat", "BattlEye", "denuvo", "PhysXCore",
    "ASICacheCleaner", "UnityShimLib", "UnityShaderCompiler", "LightingService",
    "UPlayBrowser", "UbisoftGameLauncher", "UplayService", "UbisoftConnect",
    "WebViewHost", "BEService", "EpicGamesLauncher", "EADesktop", "Origin",
    "GalaxyClient", "UnityCrashHandler64", "shadercompiler", "shaderpatch",
    "ffxivshader"
]

# URL de descarga de 7-Zip
SEVEN_ZIP_DOWNLOAD_URL = "https://www.7-zip.org/a/7za920.zip"
SEVEN_ZIP_EXE_NAME = "7z.exe"

# Textos de ayuda para los tabs
HELP_TEXT_GAMES = """
Este tab te permite seleccionar el juego al que quieres inyectar FSR.

Pasos:
1. Selecciona el juego de la lista o agrega manualmente la ruta
2. Verifica que se haya detectado el ejecutable correcto
3. Si todo es correcto, pasa al siguiente tab para gestionar los mods

Notas:
- Se buscan juegos en Steam, Epic y carpetas personalizadas
- La detección automática busca el .exe más probable
- Puedes cambiar manualmente el .exe si la detección falla
"""

HELP_TEXT_MODS = """
En este tab puedes gestionar los mods y archivos DLL para el juego seleccionado.

Pasos:
1. Descarga los archivos necesarios desde los enlaces
2. Verifica que se hayan descargado correctamente
3. Selecciona las opciones deseadas
4. Aplica los cambios al juego

Notas:
- Los archivos se extraen automáticamente
- Se hace backup de los archivos originales
- Puedes revertir los cambios en cualquier momento
"""

HELP_TEXT_SETTINGS = """
Aquí puedes configurar las opciones generales de la aplicación.

Opciones disponibles:
- Tema de la interfaz (claro/oscuro)
- Carpetas de búsqueda personalizadas
- Configuración de respaldos
- Otros ajustes generales

Los cambios se guardan automáticamente.
"""

HELP_TEXT_HELP = """
Esta sección contiene ayuda detallada sobre el uso de la aplicación.

Temas principales:
1. Cómo funciona FSR3 y sus ventajas
2. Guía paso a paso de uso
3. Solución de problemas comunes
4. Preguntas frecuentes
5. Enlaces útiles y recursos

Si necesitas más ayuda, no dudes en consultar los enlaces proporcionados.
"""