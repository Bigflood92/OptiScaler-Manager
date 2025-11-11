# -*- coding: utf-8 -*-
import os
import sys
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox
import platform
import webbrowser
import winreg
import re # Para parsear el VDF de Steam
import configparser # Para leer/escribir INI
import glob # Para búsqueda de .exe
import ctypes # Para la elevación de privilegios
import json # Para guardar/cargar config
import customtkinter as ctk
import traceback # Para mejor manejo de errores
import threading # Para descargas en segundo plano
import subprocess # Para llamar a 7z.exe
import urllib.request # Para descargar 7z.exe

# Importar el gestor de iconos
from src.gui.icon_manager import get_icon_manager

# --- NUEVAS DEPENDENCIAS V2.0 ---
# Se necesita 'requests' - LAZY LOADING (solo cuando se necesita)
# pip install requests
REQUESTS_AVAILABLE = None  # Se verificará cuando se necesite

def ensure_requests_available():
    """Importa requests solo cuando se necesita (lazy loading)."""
    global REQUESTS_AVAILABLE, requests
    if REQUESTS_AVAILABLE is None:
        try:
            import requests
            REQUESTS_AVAILABLE = True
        except ImportError:
            REQUESTS_AVAILABLE = False
            print("WARNING: 'requests' no estú instalado. El auto-descargador no funcionará.")
            print("Instale con: pip install requests")
    return REQUESTS_AVAILABLE

# py7zr se ha eliminado por ser incompatible con los filtros BCJ2

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    print("Pygame no encontrado. El soporte para mando de Xbox estará desactivado.")
    print("Para habilitarlo, instale pygame: pip install pygame")

# ==============================================================================
# 1. Constantes y Variables Globales
# ==============================================================================

# --- NOTA: APP_DATA_DIR se define después de get_script_base_path() ---

CONFIG_FILE = None  # Se inicializará después
CUSTOM_SEARCH_FOLDERS_CONFIG_KEY = "custom_search_folders"
# --- CORREGIDO: URL de compatibilidad ---
COMPATIBILITY_URL = "https://github.com/optiscaler/OptiScaler/wiki/FSR4-Compatibility-List"

# --- NUEVAS CONSTANTES V2.0 ---
# --- CORREGIDO: URL de API de GitHub ---
GITHUB_API_URL = "https://api.github.com/repos/optiscaler/OptiScaler/releases"
MOD_SOURCE_DIR = None  # Se inicializará después
# --- CORREGIDO: URL de 7z ---
SEVEN_ZIP_DOWNLOAD_URL = "https://www.7-zip.org/a/7zr.exe" # V2.0 Mejora D
SEVEN_ZIP_EXE_NAME = "7z.exe"


# --- Rutas Comunes (Usadas como fallback) ---
XBOX_GAMES_DIR = r"C:\XboxGames"
STEAM_COMMON_DIR = r"C:\Program Files (x86)\Steam\steamapps\common"
EPIC_COMMON_DIR = r"C:\Program Files\Epic Games"
NVIDIA_CHECK_FILE = r"C:\Windows\system32\nvapi64.dll"

# --- Subcarpetas comunes DIRECTAS ---
COMMON_EXE_SUBFOLDERS_DIRECT = [
    'Binaries/Win64', 'Binaries/WinGDK', 'bin/x64', 'Engine/Binaries/Win64',
    'Engine/Binaries/ThirdParty', 'x64', 'Binaries', 'bin'
]
# --- Patrones GLOB para búsqueda recursiva ---
RECURSIVE_EXE_PATTERNS = [
    '**/Binaries/Win64/*.exe', '**/Binaries/WinGDK/*.exe', '**/*Game/Binaries/Win64/*.exe',
    '**/*Shipping.exe', '**/bin/x64/*.exe', '**/x64/*.exe'
]

# --- NUEVO (V2.0 Corrección): Lista negra de EXEs (Fix 1) ---
EXE_BLACKLIST_KEYWORDS = [
    'crash', 'report', 'unins', 'setup', 'redist', 'dxsetup', 'vcredist', 
    'dotnet', 'eac', 'battleye', 'cef', 'plugin', 'werfault', 'overlay', 
    'uótility', 'launcher' # Añadimos launcher como genérico, si no hay más remedio se usarú
]


# --- Archivos del Mod ---
MOD_CHECK_FILES = ['OptiScaler.dll', 'dlssg_to_fsr3_amd_is_better.dll']
# --- Opciones de Spoofing (DLLs de inyección) ---
SPOOFING_OPTIONS = {
    1: 'dxgi.dll', 2: 'winmm.dll', 3: 'version.dll', 4: 'dbghelp.dll',
    5: 'd3d12.dll', 6: 'wininet.dll', 7: 'winhttp.dll', 8: 'OptiScaler.asi'
}
SPOOFING_DLL_NAMES = list(SPOOFING_OPTIONS.values())

TARGET_MOD_FILES = [
    'dlssg_to_fsr3_amd_is_better.dll', 'version.dll', 'nvngx_dlss.dll', 'fsr3_config.json',
    'OptiScaler.dll', 'OptiScaler.ini', 'OptiScaler.log',
    'amd_fidelityfx_framegeneration_dx12.dll', 'amd_fidelityfx_upscaler_dx12.dll',
    'amd_fidelityfx_vk.dll', 'amd_fidelityfx_dx12.dll', 'libxess.dll', 'libxess_dx11.dll',
    'nvngx.dll', 'libxess_fg.dll', 'libxell.dll', 'fakenvapi.dll', 'fakenvapi.ini',
    # --- AÑADIDOS: Asegurarnos que la desinstalación los pille todos ---
    'dxgi.dll', 'd3d12.dll', 'winmm.dll', 'dinput8.dll', 'dbghelp.dll', 'wininet.dll', 'winhttp.dll'
]
TARGET_MOD_DIRS = ['D3D12_Optiscaler', 'DlssOverrides', 'Licenses']

# --- Archivos de Spoofing (a eliminar en desinstalación) ---
GENERIC_SPOOF_FILES = ['dxgi.dll', 'd3d12.dll', 'winmm.dll', 'dinput8.dll']


# --- Opciones de Frame Generation ---
FG_OPTIONS = ["Automático", "FSR 4.0", "FSR 3.1", "FSR 3.0", "XeSS", "Desactivada"]
FG_MODE_MAP = {
    "Automático": "auto", "FSR 4.0": "fsr40", "FSR 3.1": "fsr31", "FSR 3.0": "fsr30",
    "XeSS": "xess", "Desactivada": "off"
}
# --- INVERSO: Para leer el INI (Mejora 1) ---
FG_MODE_MAP_INVERSE = {v: k for k, v in FG_MODE_MAP.items()}


# --- Opciones de Reescalador (Upscaler Backend) ---
UPSCALER_OPTIONS = ["Automático", "FSR 4.0", "FSR 3.1", "FSR 2.2", "XeSS", "DLSS"]
UPSCALER_MAP = {
    "Automático": "auto", "FSR 4.0": "fsr40", "FSR 3.1": "fsr31", "FSR 2.2": "fsr22",
    "XeSS": "xess", "DLSS": "dlss"
}
# --- INVERSO: Para leer el INI ---
UPSCALER_MAP_INVERSE = {v: k for k, v in UPSCALER_MAP.items()}

# --- Opciones de Upscaling ---
UPSCALE_OPTIONS = ["Automático", "Calidad", "Equilibrado", "Rendimiento", "Ultra Rendimiento"]
UPSCALE_MODE_MAP = {
    "Automático": "auto", "Calidad": "quality", "Equilibrado": "balanced",
    "Rendimiento": "performance", "Ultra Rendimiento": "ultra_performance"
}
# --- INVERSO: Para leer el INI (Mejora 1) ---
UPSCALE_MODE_MAP_INVERSE = {v: k for k, v in UPSCALE_MODE_MAP.items()}


# --- TEXTOS DE AYUDA ---
# ... (GPU_HELP_TEXT, DLL_HELP_TEXT, etc. sin cambios) ...

GPU_HELP_TEXT = """
[Ayuda: Tipo de GPU]

Esta opción es CRÍTICA para usuarios de AMD e Intel.

- NVIDIA:
  Opción por defecto. No activa el 'spoofing' de GPU.
  Déjalo así si tienes una tarjeta NVIDIA.

- AMD / Intel:
  ¡DEBES SELECCIONAR ESTO si tienes una GPU AMD o Intel!
  Activa el 'spoofing' para simular una GPU NVIDIA. Esto
  engaña al juego para que muestre la opción "NVIDIA DLSS",
  que OptiScaler interceptará y reemplazará por FSR.
"""

DLL_HELP_TEXT = """
[Guía de DLL de Inyección (Spoofing)]

OptiScaler necesita reemplazar un archivo DLL que el juego
cargue al inicio.

- dxgi.dll (Recomenódado):
  Biblioteca de DirectX. La opción más universal para
  juegos DX11/DX12. Pruébala primero!

- d3d12.dll:
  Librería nativa de Direct3D 12. Útil si el juego
  es D3D12 puro y 'dxgi.dll' no funciona.

- version.dll:
  Funciones de versión de Windows. Un 'fallback' muy
  común si las opciones de DirectX fallan.

- winmm.dll:
  Windows Multimedia API. Para títulos antiguos o
  engines especúficos.

- dbghelp.dll:
  Librería de ayuda para depuración/crash dumps.

- wininet.dll / winhttp.dll:
  APIs de red. Para juegos con fuerte componente online.

- OptiScaler.asi:
  Formato de plugin. Solo para juegos que soportan
  ASI-Loaders (ej. juegos de Rockstar).
"""

FG_HELP_TEXT = """
[Ayuda: Modo Frame Generation]

Controla la generación de fotogramas interpolados.

- Automático (Recomenódado):
  Deja que OptiScaler elija la mejor versión de FG
  disponible (prioriza FSR 3.1 si el juego lo soporta).

- FSR 3.1 / 3.0:
  Fuerza una versión especúfica. Útil si 'Automático'
  causa problemas o artefactos visuales.

- XeSS:
  Fuerza el uso de Intel XeSS (si estú disponible).

- Desactivada:
  Desactiva *solo* el Frame Generation (interpolación).
  El Reescalado (Upscaling) seguirú funcionando.
"""

UPSCALER_HELP_TEXT = """
[Ayuda: Reescalador (Upscaler Backend)]

Controla quú tecnologúa de reescalado usar.

- Automático (Recomenódado):
  Deja que OptiScaler elija la mejor tecnologúa
  disponible según tu hardware.

- FSR 2.2 / FSR 3.1:
  Fuerza el uso de AMD FidelityFX Super Resolution.
  Compatible con TODAS las GPUs (AMD, NVIDIA, Intel).

- XeSS:
  Fuerza el uso de Intel XeSS. Funciona mejor en
  GPUs Intel Arc, pero compatible con otras.

- DLSS:
  Usa NVIDIA Deep Learning Super Sampling nativo.
  Solo disponible en GPUs NVIDIA RTX.
"""

UPSCALE_HELP_TEXT = """
[Ayuda: Modo de Reescalado (Upscaling)]

Controla la resolución interna a la que el juego renderiza
antes de reescalar a la resolución de tu monitor.

- Automático (Recomenódado):
  Usarú el modo que tengas seleccionado DENTRO del
  menóú de opciones gráficas del juego (Calidad,
  Rendimiento, etc.).

- Calidad / Equilibrado / Rendimiento / Ultra:
  Fuerza un modo de reescalado especúfico, ignorando
  la configuración del juego. Útil si el juego no
  ofrece selector de DLSS.
  
  (Calidad = Mejor imagen, Ultra = Mús FPS)
"""

SHARPNESS_HELP_TEXT = """
[Ayuda: Nitidez (Sharpness)]

Controla el filtro de nitidez que se aplica a la imagen
final reescalada.

- Valor por defecto: 0.80
- '0.0' = Sin nitidez (imagen más suave).
- '2.0' = Máxima nitidez (imagen más definida).

Ajusta esto a tu gusto personal.
"""

TOGGLES_HELP_TEXT = """
[Ayuda: Opciones Adicionales]

- Mostrar Overlay (Debug):
  Muestra un pequeúo panel en la esquina del juego con
  información de OptiScaler (FPS, modo, etc.).
  úMuy Útil para verificar que el mod estú funcionando!

- Forzar Desactivación Motion Blur:
  Intenta desactivar el desenfoque de movimiento del
  juego. El Motion Blur suele causar artefactos
  visuales (ghosting) con el Frame Generation.
  Activa esto si ves estelas raras.
"""

# --- MODIFICADO: Texto de Ayuda de la App (V2.0 Refactor) ---
APP_HELP_TEXT = """
[Guía Rápida: GESTOR DE OPTISCALER - INTERFAZ CLÁSICA]

Este gestor te permite instalar, desinstalar y
configurar OptiScaler (FSR 3/4) en todos tus juegos.

--- INTERFAZ GAMING 🎮 ---
Pulsa el botón verde 🎮 (esquina superior derecha)
para cambiar a la INTERFAZ GAMING, optimizada
para mandos y pantallas táctiles.

--- FLUJO DE TRABAJO RECOMENDADO ---

1. PESTAÑA 1 (CONFIGURACIÓN DEL MOD):
   ⚡ PRESETS RÁPIDOS:
   - Default: Todo automático (recomendado)
   - Performance: Máximo rendimiento (~+80% FPS)
   - Balanced: Equilibrio calidad/rendimiento
   - Quality: Máxima calidad visual
   - Custom: Se activa al cambiar opciones manualmente
   
   ⬇️ DESCARGA:
   - Pulsa '⬇️ Descargar / Gestionar Mod' para obtener
     la última versión de OptiScaler.
   - Usa el desplegable para cambiar entre versiones.
   
   ⚙️ CONFIGURACIÓN GLOBAL:
   - Aquí configuras los ajustes que se usarán por
     defecto en todas las instalaciones.
   - GPU: Selecciona tu tipo de tarjeta gráfica
   - DLL: Cambia solo si tienes conflictos
   - Frame Gen: Genera frames adicionales (~+80% FPS)
   - Upscaler: Tecnología de reescalado (FSR 3.1/4.0)
   - Modo Reescalado: Rendimiento (+60%) vs Quality (+20%)
   - Sharpness: Nitidez de la imagen (0.0 - 2.0)

2. PESTAÑA 2 (GESTIÓN AUTOMÁTICA):
   🔍 FILTROS:
   - Usa los checkboxes (Steam, Xbox, Epic, Custom)
     para filtrar juegos por plataforma.
   - Búsqueda: Escribe para encontrar juegos rápido.
   
   ⚙️ OPERACIONES:
   - Selecciona juegos con checkbox o 'A' en gamepad
   - INICIAR INYECCIÓN (X): Instala el mod
   - DESINSTALAR (Y): Elimina el mod
   - START: Abre config individual del juego
   - ⚙️ Aplicar Config Global (Select): Actualiza
     configuración de juegos seleccionados

3. PESTAÑA 3 (GESTIúN MANUAL):
   - Úsala si el modo AUTO no encuentra tu juego.
   - Selecciona la carpeta del .exe del juego.
   - Pulsa 'INYECCIÓN MANUAL' (X).
   - También puedes restaurar DLLs originales (.bak).

4. PESTAÑA 4 (CONFIGURACIÓN APP):
   📁 CARPETAS PERSONALIZADAS:
   - Si tienes juegos en GOG, Ubisoft o carpetas
     personalizadas (ej. D:\\Juegos), añádelas aquú.
   - Pulsa '🔄 Re-escanear' para que aparezcan
     en la Pestaña 2.
   
   🎨 APARIENCIA:
   - Tema: Claro / Oscuro / Sistema
   - Escala UI: 80% - 120% (para diferentes pantallas)
   
   🗑️ LIMPIEZA:
   - Limpiar logs y backups antiguos.

5. PESTAÑA 5 (LOG DE OPERACIONES):
   - Aquí puedes ver todo lo que hace la app.
   - Auto-scroll: Desplazamiento automático.
   - Si tienes un error, pulsa '?? Guardar Log'
     para compartirlo.

--- CONTROLES DE MANDO ---

NAVEGACIÓN:
- LB / RB: Cambiar de Pestaña.
- Cruceta ⬆️⬇️: Moverse entre opciones.
- Cruceta ⬅️➡️: Navegar dentro de una fila
  (ej: botón ayuda ? → control).
- A (Botón 0): Seleccionar / Activar / Enter.
- B (Botón 1): Cerrar ventanas / Cancelar.

ACCIONES RÁPIDAS:
- X (Botón 2): Inyectar / Guardar / Refrescar.
- Y (Botón 3): Desinstalar.
- SELECT (Botón 6): Aplicar Config. Global (Pestaña 2).
- START (Botón 7): Abrir ⚙️ Config Individual
  (en la lista de la Pestaña 2).

--- BADGES DE ESTADO ---
? APLICADO: Mod instalado correctamente.
❌ NO APLICADO: Mod no instalado.
? DESCONOCIDO: No se puede determinar el estado.

--- INDICADORES DE RENDIMIENTO ---
? ~+80% FPS: Frame Generation activo
?? +60% / +20%: Impacto del modo de reescalado
    • Performance: +60% FPS (menor calidad)
    • Quality: +20% FPS (mayor calidad)
"""

GAMING_HELP_TEXT = """
[Guía Rápida: GESTOR DE OPTISCALER - INTERFAZ GAMING 🎮]

Interfaz optimizada para mandos, pantallas táctiles
y Steam Deck / ROG Ally.

--- INTERFAZ CLÁSICA ?? ---
Pulsa el botón verde 🎮 (panel izquierdo) para
volver a la INTERFAZ CLÁSICA con todas las opciones
avanzadas.

--- NAVEGACIúN ---

PANEL IZQUIERDO:
⚙️ Configuración del Mod
🎮 Juegos Detectados (Principal)
📁 Ruta Manual
🔧 Ajustes de la App
? Ayuda

Usa la CRUCETA o TÁCTIL para seleccionar.
El panel activo tiene BORDE VERDE.

--- SECCIONES ---

⚙️ CONFIGURACIÓN DEL MOD:

  ⚡ PRESETS RÁPIDOS:
  - 🎯 Default: Todo automático (recomendado)
  - ⚡ Performance: Máximo rendimiento
  - ⚖️ Balanced: Equilibrio
  - 💎 Quality: Máxima calidad
  - 🔧 Custom: Personalizado (auto-detecta cambios)
  
  El preset activo tiene BORDE VERDE.
  
  OPCIONES MANUALES:
  - GPU: AMD/Intel o NVIDIA
  - DLL: Archivo de inyección (dxgi.dll por defecto)
  - Frame Gen: ~+80% FPS extra
  - Upscaler: FSR 3.1, FSR 4.0, XeSS, DLSS
  - Modo Reescalado:
      • Rendimiento: +60% FPS
      • Equilibrado: Balance
      • Calidad: +20% FPS (mejor imagen)
  - Sharpness: Nitidez (0.0 - 1.0)
  - Extras: Overlay debug, Motion Blur

🎮 JUEGOS DETECTADOS:

  CONTADOR: Muestra X/Y juegos
      • X = Juegos seleccionados
      • Y = Total de juegos detectados
  
  LISTA DE JUEGOS:
  - Checkbox: Seleccionar múltiples juegos
  - Badges de estado:
    ✓ APLICADO: Mod instalado
    ❌ NO APLICADO: Sin mod
    ❓ DESCONOCIDO: Estado desconocido
  - Botón ⚙️: Config individual del juego
  
  BOTONES:
  - ✅ APLICAR A SELECCIONADOS: Instala el mod
  - ❌ ELIMINAR DE SELECCIONADOS: Desinstala el mod
  - 🔄 ACTUALIZAR LISTA: Refresca la lista

📁 RUTA MANUAL:

  Usa esta sección si tus juegos no aparecen
  en la detección automática.
  
  1. Pulsa 'SELECCIONAR CARPETA'
  2. Busca la carpeta del .exe del juego
  3. Pulsa 'APLICAR MOD'
  
  También puedes eliminar el mod desde aquí.

🔧 AJUSTES DE LA APP:

  📁 CARPETAS PERSONALIZADAS:
  - Añade rutas donde tienes juegos instalados
    (ej: D:\\Juegos, GOG, Ubisoft)
  - Pulsa ➕ para añadir
  - Pulsa 🔍 para re-escanear después
  
  🎨 APARIENCIA:
  - Tema: Claro / Oscuro / Sistema
  - Escala UI: 80% - 120%
  
  🗑️ LIMPIEZA:
  - Limpiar logs antiguos
  - Eliminar backups huérfanos
  
  📋 LOG:
  - Ver todas las operaciones
  - Guardar log para compartir

? AYUDA:

  Muestra esta ventana de ayuda.

--- CONTROLES ---

NAVEGACIÓN:
- Cruceta / Stick: Moverse por la interfaz
- A / Táctil: Seleccionar / Activar
- B: Volver / Cancelar
- Botón 🎮 verde: Cambiar a Interfaz Clásica

PRESETS:
- Los botones tienen BORDE DE COLOR cuando están activos
- Se auto-detecta Custom al cambiar opciones manualmente

VENTANA CONFIG INDIVIDUAL:
- Cancelar: Cierra sin guardar
- ✅ Aplicar y Cerrar: Guarda y cierra

--- CARACTERÍSTICAS ESPECIALES ---

🔄 AUTO-REFRESH: La lista se actualiza automáticamente
   después de aplicar o eliminar mods.

💬 FEEDBACK VISUAL: Mensajes popup confirman operaciones
   exitosas o errores.

💾 PERSISTENCIA: La app recuerda si estabas en modo
   Gaming y vuelve a abrirse en ese modo.

📶 OFFLINE MODE: Funciona sin internet, con caché de
   versiones disponibles (actualización cada 24h).
"""

# ==============================================================================
# 2. Funciones de Administraciún y Detecciún de Rutas
# ==============================================================================

def is_admin():
    """Verifica si el script se ejecuta con permisos de administrador en Windows."""
    try:
        if platform.system() == "Windows":
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        return True
    except Exception:
        return False

def run_as_admin():
    """(Funciún desactivada) - PyInstaller --uac-admin se encarga."""
    pass

# --- NUEVO (V2.0 Mejora D): Auto-descarga de 7-Zip ---
def get_script_base_path():
    """Obtiene la ruta base del script o del .exe compilado."""
    try:
        if getattr(sys, 'frozen', False):
            # Estamos ejecutando en un .exe compilado
            return os.path.dirname(sys.executable)
        else:
            # Estamos ejecutando como un .py normal
            # Si estú en src/gui/, subir a la raúz del proyecto
            current_dir = os.path.dirname(os.path.abspath(__file__))
            if current_dir.endswith(os.path.join('src', 'gui')):
                return os.path.dirname(os.path.dirname(current_dir))  # Subir 2 niveles
            return current_dir
    except Exception:
        return os.path.abspath(".")

# --- INICIALIZACIúN DE RUTAS CENTRALIZADAS (V2.1) ---
# Esto debe ir después de get_script_base_path()
APP_DATA_DIR = os.path.join(get_script_base_path(), "Config Optiscaler Gestor")
CONFIG_FILE = os.path.join(APP_DATA_DIR, "injector_config.json")
MOD_SOURCE_DIR = os.path.join(APP_DATA_DIR, "mod_source")
GAMES_caché_FILE = os.path.join(APP_DATA_DIR, "games_caché.json")  # V2.1 Performance

# --- MODIFICADO (V2.0 Pulida): Se llama solo al pulsar 'Descargar' ---
def check_and_download_7zip(log_func, master_widget=None):
    """
    Verifica si 7z.exe existe y, si no, lo descarga.
    Devuelve True si 7z.exe estú listo, False si no.
    """
    # Crear carpeta APP_DATA_DIR si no existe
    if not os.path.exists(APP_DATA_DIR):
        os.makedirs(APP_DATA_DIR)
        log_func('INFO', f"Carpeta de configuración creada: {APP_DATA_DIR}")
    
    seven_zip_exe_path = os.path.join(APP_DATA_DIR, SEVEN_ZIP_EXE_NAME)

    if os.path.exists(seven_zip_exe_path):
        log_func('INFO', f"{SEVEN_ZIP_EXE_NAME} encontrado. Extracciún habilitada.")
        return True

    log_func('ERROR', f"úNo se encontrú {SEVEN_ZIP_EXE_NAME}!")
    
    # Usar Tkinter base para este popup, ya que CustomTkinter puede no estar listo
    root = tk.Tk()
    root.withdraw()
    
    # Hacer que el popup sea modal a la ventana principal si es posible
    transient_target = master_widget if master_widget and master_widget.winfo_exists() else None
    
    if messagebox.askyesno("Dependencia Faltante",
                           f"¡No se encontró {SEVEN_ZIP_EXE_NAME}!\n\n"
                           f"Es necesario para descomprimir las descargas de mods (.7z).\n\n"
                           f"¿Quieres que lo descargue automáticamente por ti? (Aprox. 600 KB)",
                           parent=transient_target): # Aúadido 'parent'
        root.destroy()
        log_func('TITLE', f"Descargando {SEVEN_ZIP_EXE_NAME}...")
        try:
            # 7zr.exe es el que se descarga, lo renombramos a 7z.exe
            with urllib.request.urlopen(SEVEN_ZIP_DOWNLOAD_URL) as response, open(seven_zip_exe_path, 'wb') as out_file:
                data = response.read() # Descarga en memoria
                out_file.write(data)
            
            log_func('OK', f"{SEVEN_ZIP_EXE_NAME} descargado con éxito en {seven_zip_exe_path}")
            messagebox.showinfo("Descarga Completa",
                                f"{SEVEN_ZIP_EXE_NAME} se ha descargado con éxito.\n"
                                "La función de descarga de mods ya está disponible.", # menósaje modificado
                                parent=transient_target) # Aúadido 'parent'
            return True # Devolver True en lugar de sys.exit(0)
            
        except Exception as e:
            log_func('ERROR', f"Fallo al descargar {SEVEN_ZIP_EXE_NAME}: {e}")
            messagebox.showerror("Error de Descarga",
                                 f"No se pudo descargar {SEVEN_ZIP_EXE_NAME}.\n"
                                 f"Por favor, descárguelo manualmente desde 7-zip.org ('7zr.exe') "
                                 f"y cámbielo el nombre a '7z.exe' en la carpeta del gestor.\n\nDetalle: {e}",
                                 parent=transient_target) # Aúadido 'parent'
            return False
    else:
        root.destroy()
        log_func('ERROR', "Descarga de 7z.exe cancelada por el usuario.")
        return False


def get_dynamic_steam_paths(log_func):
    """Encuentra todas las bibliotecas de Steam (principal y secundarias)."""
    paths = {STEAM_COMMON_DIR}
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam")
        steam_path = winreg.QueryValueEx(key, "InstallPath")[0]
        winreg.CloseKey(key)

        main_common = os.path.join(steam_path, "steamapps", "common")
        if os.path.isdir(main_common):
            paths.add(main_common)
            log_func('INFO', f"Ruta de Steam (Principal) detectada: {main_common}")

        vdf_path = os.path.join(steam_path, "steamapps", "libraryfolders.vdf")
        if os.path.exists(vdf_path):
            with open(vdf_path, 'r', encoding='utf-8') as f:
                content = f.read()
            lib_paths = re.findall(r'"path"\s+"([^"]+)"', content)
            for lib_path in lib_paths:
                lib_path = lib_path.replace('\\\\', '\\')
                lib_common = os.path.join(lib_path, "steamapps", "common")
                if os.path.isdir(lib_common):
                    paths.add(lib_common)
                    log_func('INFO', f"Ruta de Steam (Biblioteca) detectada: {lib_common}")

    except FileNotFoundError:
        log_func('WARN', "No se encontrú la instalaciún de Steam en el registro. Usando fallback.")
    except Exception as e:
        log_func('ERROR', f"Error al buscar rutas de Steam: {e}")
    return list(paths)


def get_dynamic_epic_paths(log_func):
    """Encuentra juegos de Epic Games iterando las claves de desinstalación en el registro."""
    paths = {EPIC_COMMON_DIR}
    try:
        uninstall_key_path = r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"
        uninstall_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, uninstall_key_path)
        
        i = 0
        while True:
            try:
                subkey_name = winreg.EnumKey(uninstall_key, i)
                subkey_path = os.path.join(uninstall_key_path, subkey_name)
                
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, subkey_path) as subkey:
                    try:
                        publisher = str(winreg.QueryValueEx(subkey, "Publisher")[0])
                        if "Epic Games" in publisher:
                            install_loc = str(winreg.QueryValueEx(subkey, "InstallLocation")[0])
                            if os.path.isfile(install_loc):
                                install_loc = os.path.dirname(install_loc)
                            if os.path.isdir(install_loc) and install_loc not in paths:
                                paths.add(install_loc)
                                log_func('INFO', f"Ruta de Epic (Juego) detectada: {install_loc}")
                    except FileNotFoundError:
                        pass
                    except Exception as e:
                        log_func('WARN', f"Error menor al leer subclave de registro: {e}")
                i += 1
            except OSError:
                break
        winreg.CloseKey(uninstall_key)

    except FileNotFoundError:
        log_func('WARN', "No se encontrú la clave de desinstalación de Epic. Usando fallback.")
    except Exception as e:
        log_func('ERROR', f"Error al buscar rutas de Epic: {e}")
    return list(paths)
# ==============================================================================
# 3. Funciones Principales del Mod
# ==============================================================================

def open_optiscaler_download():
    """Abre la URL de GitHub de OptiScaler en el navegador por defecto."""
    url = "https://github.com/optiscaler/OptiScaler/releases"
    webbrowser.open_new_tab(url)

def open_compatibility_list():
    """Abre la URL de la lista de compatibilidad."""
    webbrowser.open_new_tab(COMPATIBILITY_URL)


# --- MODIFICADO (V2.0 Corrección): Lúgica "Smart EXE" (Fix 1) ---
def find_executable_path(base_game_path, log_func):
    """
    Busca la carpeta de ejecutables más probable y el nombre del .exe.
    Prioriza el .exe más grande e ignora la lista negra (crashreport, etc.).
    """
    
    def get_best_exe_in_folder(folder_path):
        """
        Analiza una carpeta, filtra la lista negra y devuelve el .exe más grande.
        Retorna (nombre_exe, tamaño_exe)
        """
        all_exes = glob.glob(os.path.join(folder_path, '*.exe'))
        if not all_exes:
            return None, 0

        good_candidates = []
        bad_candidates = []

        for exe_path in all_exes:
            exe_name_lower = os.path.basename(exe_path).lower()
            is_blacklisted = any(keyword in exe_name_lower for keyword in EXE_BLACKLIST_KEYWORDS)
            
            try:
                size = os.path.getsize(exe_path)
            except Exception:
                size = 0
            
            if not is_blacklisted:
                good_candidates.append((exe_path, size))
            else:
                bad_candidates.append((exe_path, size))
        
        # 1. Priorizar el .exe más grande de los "buenos" candidatos
        if good_candidates:
            good_candidates.sort(key=lambda x: x[1], reverse=True) # Ordenar por tamaño
            best_exe_path, best_size = good_candidates[0]
            return os.path.basename(best_exe_path), best_size

        # 2. Si NO hay buenos candidatos, usar el .exe más grande de los "malos" (ej. un "launcher.exe")
        if bad_candidates:
            bad_candidates.sort(key=lambda x: x[1], reverse=True) # Ordenar por tamaño
            best_bad_exe_path, best_bad_size = bad_candidates[0]
            log_func('WARN', f"  -> No se encontraron .exes 'buenos', usando el mejor de la lista negra: {os.path.basename(best_bad_exe_path)}")
            return os.path.basename(best_bad_exe_path), best_bad_size
            
        return None, 0

    try:
        # 1. Buscar en subcarpetas comunes DIRECTAS primero
        for subfolder in COMMON_EXE_SUBFOLDERS_DIRECT:
            potential_path = os.path.normpath(os.path.join(base_game_path, subfolder))
            if os.path.isdir(potential_path):
                exe_name, size = get_best_exe_in_folder(potential_path)
                if exe_name:
                    log_func('INFO', f"  -> Ruta inteligente (directa) encontrada: {potential_path} (Exe: {exe_name}, {size//(1024*1024)}MB)")
                    return potential_path, exe_name
        
        # 2. Si no, buscar RECURSIVAmenóTE con patrones glob
        log_func('INFO', f"  -> Buscando recursivamenóte ejecutables en: {base_game_path}")
        best_recursive_exe = None
        best_recursive_size = 0
        best_recursive_dir = None
        
        for pattern in RECURSIVE_EXE_PATTERNS:
            search_pattern = os.path.join(base_game_path, pattern)
            found_exes_paths = glob.glob(search_pattern, recursive=True)
            
            for exe_path in found_exes_paths:
                exe_name_lower = os.path.basename(exe_path).lower()
                is_blacklisted = any(keyword in exe_name_lower for keyword in EXE_BLACKLIST_KEYWORDS)
                if is_blacklisted:
                    continue
                
                try:
                    size = os.path.getsize(exe_path)
                    if size > best_recursive_size:
                        best_recursive_size = size
                        best_recursive_exe = os.path.basename(exe_path)
                        best_recursive_dir = os.path.dirname(exe_path)
                except Exception:
                    pass

        if best_recursive_exe:
            log_func('INFO', f"  -> Ruta inteligente (recursiva) encontrada: {best_recursive_dir} (Exe: {best_recursive_exe}, {best_recursive_size//(1024*1024)}MB)")
            return best_recursive_dir, best_recursive_exe
                    
        # 3. Si no se encuentra nada recursivamenóte, comprobar la RAúZ
        exe_name_root, size_root = get_best_exe_in_folder(base_game_path)
        if exe_name_root:
            log_func('INFO', f"  -> No se encontraron subcarpetas, usando la raúz: {base_game_path} (Exe: {exe_name_root}, {size_root//(1024*1024)}MB)")
            return base_game_path, exe_name_root
        
        # 4. Si no hay .exe en ningún lado, devolver la base como fallback
        log_func('WARN', f"  -> No se encontrú .exe en {base_game_path} o subcarpetas. Usando la raúz por defecto.")
        return base_game_path, None
        
    except Exception as e:
        log_func('ERROR', f"  -> Error en búsqueda inteligente: {e}. Usando raúz: {base_game_path}")
        return base_game_path, None

def get_game_name(folder_name):
    """Limpia el nombre de la carpeta de Game Pass para obtener un nombre legible."""
    name_parts = folder_name.split(' - ')
    if len(name_parts) > 1 and len(name_parts[0]) > 0:
        return name_parts[0]
    return folder_name

# --- MEJORA 2: ESTADO DE DETECCIúN MEJORADO ---
def check_mod_status(game_target_dir):
    """Verifica si el mod estú instalado e informa QUú DLL de inyección se estú usando."""
    if not os.path.isdir(game_target_dir):
        return "ERROR: Carpeta no vúlida"

    # 1. Comprobar los DLL de inyección (los más importantes)
    for dll_name in SPOOFING_DLL_NAMES:
        if os.path.exists(os.path.join(game_target_dir, dll_name)):
            # Comprobar si es OptiScaler.dll renombrado (por tamaño > 1MB)
            try:
                size_mb = os.path.getsize(os.path.join(game_target_dir, dll_name)) / (1024*1024)
                if size_mb > 0.5: # OptiScaler.dll es > 1MB, los .dll reales son < 1MB
                    return f"✓ INSTALADO (usando {dll_name})"
            except Exception:
                 return f"✓ INSTALADO (usando {dll_name})" # Fallback si falla el tamaño

    # 2. Comprobar archivos base del mod si no se encontrú DLL de inyección
    if any(os.path.exists(os.path.join(game_target_dir, f)) for f in MOD_CHECK_FILES):
        return "✓ INSTALADO (OptiScaler.dll)" # Instalado pero no renombrado/inyectado

    # 3. Si no hay nada
    return "❌ AUSENTE"

# --- MODIFICADO (V2.0 Refactor): Almacena nombre de .exe y platform_tag (Fix 8) ---
def scan_games(log_func, custom_folders=None):
    """Escanea carpetas comunes, dinúmicas y personalizadas para encontrar juegos."""
    if custom_folders is None:
        custom_folders = []
    all_games = []
    processed_paths = set()
    
    # Helper para aúadir juego
    def add_game_entry(path, name, status, exe_name, platform_tag):
        # path, display_name, mod_status, exe_name, platform_tag
        all_games.append((path, name, status, exe_name, platform_tag))

    # 1. Escaneo de XBOX (Game Pass)
    if os.path.exists(XBOX_GAMES_DIR):
        log_func('INFO', f"Escaneando Xbox: {XBOX_GAMES_DIR}")
        try:
            for folder_name in os.listdir(XBOX_GAMES_DIR):
                base_folder_path = os.path.normpath(os.path.join(XBOX_GAMES_DIR, folder_name))
                if os.path.isdir(base_folder_path):
                    injection_path_base = os.path.normpath(os.path.join(base_folder_path, 'Content'))
                    if not os.path.isdir(injection_path_base):
                        injection_path_base = base_folder_path
                    
                    final_injection_path, exe_name = find_executable_path(injection_path_base, log_func)
                    
                    # --- NUEVO (Fix 8): No listar si no hay .exe ---
                    if not exe_name:
                        log_func('WARN', f"  -> Omitiendo {folder_name}: No se encontrú .exe vúlido.")
                        continue
                        
                    if final_injection_path in processed_paths: continue
                    processed_paths.add(final_injection_path)

                    mod_status = check_mod_status(final_injection_path)
                    clean_name = get_game_name(folder_name)
                    add_game_entry(final_injection_path, f"[XBOX] {clean_name}", mod_status, exe_name, "Xbox")
        except Exception as e:
            log_func('ERROR', f"Error al escanear {XBOX_GAMES_DIR}: {e}")

    # 2. Escaneo de STEAM (Dinámico)
    steam_dirs = get_dynamic_steam_paths(log_func)
    for base_dir in steam_dirs:
         base_dir = os.path.normpath(base_dir)
         if os.path.exists(base_dir):
            log_func('INFO', f"Escaneando Steam: {base_dir}")
            try:
                for folder_name in os.listdir(base_dir):
                    game_path = os.path.normpath(os.path.join(base_dir, folder_name))
                    if os.path.isdir(game_path):
                        final_injection_path, exe_name = find_executable_path(game_path, log_func)
                        
                        # --- NUEVO (Fix 8): No listar si no hay .exe ---
                        if not exe_name:
                            log_func('WARN', f"  -> Omitiendo {folder_name}: No se encontrú .exe vúlido.")
                            continue

                        if final_injection_path in processed_paths: continue
                        processed_paths.add(final_injection_path)
                        mod_status = check_mod_status(final_injection_path)
                        add_game_entry(final_injection_path, f"[STEAM] {folder_name}", mod_status, exe_name, "Steam")
            except Exception as e:
                log_func('ERROR', f"Error al escanear {base_dir}: {e}")

    # 3. Escaneo de EPIC (Dinámico)
    epic_dirs = get_dynamic_epic_paths(log_func)
    for game_path in epic_dirs:
         game_path = os.path.normpath(game_path)
         if os.path.exists(game_path):
             final_injection_path, exe_name = find_executable_path(game_path, log_func)
             
             # --- NUEVO (Fix 8): No listar si no hay .exe ---
             if not exe_name:
                log_func('WARN', f"  -> Omitiendo {os.path.basename(game_path)}: No se encontrú .exe vúlido.")
                continue

             if final_injection_path in processed_paths: continue
             processed_paths.add(final_injection_path)
             folder_name = os.path.basename(game_path)
             mod_status = check_mod_status(final_injection_path)
             add_game_entry(final_injection_path, f"[EPIC] {folder_name}", mod_status, exe_name, "Epic")

    # --- NUEVO: 4. Escaneo de Carpetas Personalizadas ---
    for base_dir in custom_folders:
        base_dir = os.path.normpath(base_dir)
        if os.path.exists(base_dir):
            log_func('INFO', f"Escaneando Carpeta Personalizada: {base_dir}")
            try:
                for folder_name in os.listdir(base_dir):
                    game_path = os.path.normpath(os.path.join(base_dir, folder_name))
                    if os.path.isdir(game_path) and not folder_name.startswith('$'): # Ignorar carpetas del sistema
                        final_injection_path, exe_name = find_executable_path(game_path, log_func)
                        
                        # --- NUEVO (Fix 8): No listar si no hay .exe ---
                        if not exe_name:
                            log_func('WARN', f"  -> Omitiendo {folder_name}: No se encontrú .exe vúlido.")
                            continue

                        if final_injection_path in processed_paths: continue
                        processed_paths.add(final_injection_path)
                        mod_status = check_mod_status(final_injection_path)
                        add_game_entry(final_injection_path, f"[CUSTOM] {folder_name}", mod_status, exe_name, "Custom")
            except Exception as e:
                log_func('ERROR', f"Error al escanear carpeta personalizada {base_dir}: {e}")


    all_games.sort(key=lambda x: x[1])
    log_func('INFO', f"Escaneo completado. {len(all_games)} juegos encontrados.")
    return all_games

# ==============================================================================
# NUEVO (V2.1 Performance): Sistema de cachéú de Juegos
# ==============================================================================

def save_games_caché(games_data, log_func=None):
    """Guarda la lista de juegos escaneados en un archivo JSON con timestamp."""
    try:
        import datetime
        caché_data = {
            "timestamp": datetime.datetime.now().isoformat(),
            "games_count": len(games_data),
            "games": games_data  # Lista de tuplas: (path, name, status, exe, platform)
        }
        
        # Crear carpeta si no existe
        if not os.path.exists(APP_DATA_DIR):
            os.makedirs(APP_DATA_DIR)
        
        with open(GAMES_caché_FILE, 'w', encoding='utf-8') as f:
            json.dump(caché_data, f, indent=2, ensure_ascii=False)
        
        if log_func:
            log_func('OK', f"cachéú de juegos guardada: {len(games_data)} juegos.")
    except Exception as e:
        if log_func:
            log_func('ERROR', f"Error al guardar cachéú de juegos: {e}")

def load_games_caché(log_func=None):
    """Carga la lista de juegos desde el cachéú JSON. Retorna lista vacía si no existe."""
    try:
        if not os.path.exists(GAMES_caché_FILE):
            if log_func:
                log_func('INFO', "No se encontrú cachéú de juegos. Use el botón '?? Escanear Juegos'.")
            return []
        
        with open(GAMES_caché_FILE, 'r', encoding='utf-8') as f:
            caché_data = json.load(f)
        
        games_list = caché_data.get("games", [])
        timestamp = caché_data.get("timestamp", "desconocido")
        
        if log_func:
            log_func('OK', f"cachéú cargada: {len(games_list)} juegos (último escaneo: {timestamp}).")
        
        # Convertir listas a tuplas (JSON guarda tuplas como listas)
        return [tuple(game) for game in games_list]
    except Exception as e:
        if log_func:
            log_func('WARN', f"Error al cargar cachéú de juegos: {e}")
        return []

def check_registry_override(log_func):
    """Verifica si el DLSS signature check override estú activo."""
    if platform.system() != "Windows":
        return True
    try:
        key_path = r"SOFTWARE\NVIDIA Corporation\Global\NVAPI\Render\Software\NVAPI"
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_READ)
        value, _ = winreg.QueryValueEx(key, "DisableSignatureChecks")
        winreg.CloseKey(key)

        if value == 1:
            log_func('INFO', "VERIFICACIúN REGISTRO: ? Firma de DLSS deshabilitada (OK).")
            return True
        else:
            log_func('WARN', "VERIFICACIúN REGISTRO: ? Comprobaciún de firma ACTIVA (Valor = 0).")
            log_func('WARN', "úMOD BLOQUEADO! Ejecute el archivo 'DISABLE...' REG si el mod no funciona.")
            return False
    except FileNotFoundError:
        log_func('WARN', "VERIFICACIúN REGISTRO: ? Clave de 'DisableSignatureChecks' NO encontrada.")
        log_func('WARN', "úMOD BLOQUEADO! Ejecute el archivo 'DISABLE...' REG si el mod no funciona.")
        return False
    except Exception as e:
        log_func('ERROR', f"VERIFICACIúN REGISTRO: Fallo al leer el Registro: {e}")
        return False

# --- MODIFICADO (V2.0): Busca en la carpeta MOD_SOURCE_DIR ---
def check_mod_source_files(mod_source_dir, log_func):
    """Verifica y retorna la subcarpeta correcta del mod extraúdo."""
    target_files_check = ['dlssg_to_fsr3_amd_is_better.dll', 'OptiScaler.dll']
    source_dir = mod_source_dir
    dll_found = False
    
    # Si el path es vacúo, buscar en la carpeta de auto-descarga
    if not source_dir or not os.path.isdir(source_dir):
        if not os.path.isdir(MOD_SOURCE_DIR):
            log_func('ERROR', "La carpeta de origen del Mod no estú seleccionada.")
            log_func('ERROR', "Use el botón 'Descargar/Gestionar Mod' o seleccione una carpeta manualmente.")
            return None, False
        
        log_func('WARN', "Usando la carpeta de auto-descarga. Buscando la última versión...")
        subdirs = sorted(
            [d for d in os.listdir(MOD_SOURCE_DIR) if os.path.isdir(os.path.join(MOD_SOURCE_DIR, d))],
            reverse=True
        )
        if not subdirs:
            log_func('ERROR', "La carpeta 'mod_source' estú vacía. Por favor, descargue el mod.")
            return None, False
        
        source_dir = os.path.join(MOD_SOURCE_DIR, subdirs[0]) # Usar la más reciente
        log_func('INFO', f"Carpeta de Mod detectada: {source_dir}")

    try:
        for root, _, files in os.walk(source_dir):
            if any(f in files for f in target_files_check):
                source_dir = root
                dll_found = True
                break
    except Exception as e:
        log_func('ERROR', f"Error al escanear la carpeta de origen del mod: {e}")
        return None, False

    if not dll_found:
         log_func('ERROR', "La carpeta de origen NO contiene los archivos clave del mod. Asegúrese de haber EXTRAúDO la carpeta.")
         return None, False
    log_func('INFO', f"Archivos clave del Mod encontrados en: {source_dir}")
    return source_dir, True


def configure_and_rename_dll(target_dir, spoof_dll_name, log_func):
    """Realiza SOLO el renombrado de OptiScaler.dll."""
    original_dll = os.path.join(target_dir, 'OptiScaler.dll')
    selected_filename = spoof_dll_name
    if not selected_filename:
        log_func('ERROR', "Nombre de DLL de inyección no vúlido.")
        return False

    new_dll_path = os.path.join(target_dir, selected_filename)
    backup_path = new_dll_path + ".bak"

    if os.path.exists(new_dll_path):
        try:
            if os.path.exists(backup_path): os.remove(backup_path)
            os.rename(new_dll_path, backup_path)
            log_func('WARN', f"Archivo existente {selected_filename} renombrado a {os.path.basename(backup_path)}")
        except Exception as e:
            log_func('ERROR', f"No se pudo crear backup de {selected_filename}: {e}")

    if not os.path.exists(original_dll):
        if os.path.exists(new_dll_path):
             log_func('WARN', f"OptiScaler.dll no encontrado, pero {selected_filename} ya existe. Asumiendo renombrado previo.")
             return True
        else:
            log_func('ERROR', f"OptiScaler.dll no fue copiado al destino y {selected_filename} no existe. Fallo crútico.")
            return False

    try:
        os.rename(original_dll, new_dll_path)
        log_func('INFO', f"OptiScaler.dll renombrado a {selected_filename}.")
        return True
    except Exception as e:
        log_func('ERROR', f"Fallo al renombrar DLL: {e}. úEstú el juego abierto?")
        if 'backup_path' in locals() and os.path.exists(backup_path):
            try:
                if os.path.exists(new_dll_path): os.remove(new_dll_path)
                os.rename(backup_path, new_dll_path)
                log_func('INFO', f"Backup {os.path.basename(backup_path)} restaurado.")
            except Exception as e_restore:
                 log_func('ERROR', f"Fallo al restaurar backup: {e_restore}")
        return False


def update_optiscaler_ini(target_dir, gpu_choice, fg_mode_selected, upscaler_selected, upscale_mode_selected, sharpness_selected, overlay_selected, mb_selected, log_func):
    """Modifica todas las opciones de configuración en OptiScaler.ini."""
    ini_path = os.path.join(target_dir, 'OptiScaler.ini')
    if not os.path.exists(ini_path):
        log_func('WARN', "OptiScaler.ini no encontrado en el destino. No se pueden aplicar configuraciones.")
        return False

    try:
        config = configparser.ConfigParser(commenót_prefixes=';', allow_no_value=True)
        from io import StringIO
        ini_content = ""
        with open(ini_path, 'r', encoding='utf-8') as f:
            ini_content = f.read()
        
        stringio_content = StringIO(ini_content)
        config.read_file(stringio_content)
        changes_made = False

        # 1. Configurar [Dxgi]
        dxgi_value = 'true' if gpu_choice == 1 else 'auto' # 'true' para AMD/Intel, 'auto' para Nvidia
        if not config.has_section('Dxgi'): config.add_section('Dxgi')
        if config.get('Dxgi', 'Dxgi', fallback='auto') != dxgi_value:
            config.set('Dxgi', 'Dxgi', dxgi_value)
            log_func('INFO', f"OptiScaler.ini: [Dxgi] Dxgi cambiado a '{dxgi_value}'.")
            changes_made = True

        # 2. Configurar [FrameGeneration]
        fg_mode_ini_value = FG_MODE_MAP.get(fg_mode_selected, 'auto')
        if not config.has_section('FrameGeneration'): config.add_section('FrameGeneration')
        if config.get('FrameGeneration', 'Mode', fallback='auto') != fg_mode_ini_value:
             config.set('FrameGeneration', 'Mode', fg_mode_ini_value)
             log_func('INFO', f"OptiScaler.ini: [FrameGeneration] Mode cambiado a '{fg_mode_ini_value}'.")
             changes_made = True

        # 2.5 Configurar [Upscaler] (Backend) - NUEVO
        upscaler_ini_value = UPSCALER_MAP.get(upscaler_selected, 'auto')
        if not config.has_section('Upscaler'): config.add_section('Upscaler')
        if config.get('Upscaler', 'Backend', fallback='auto') != upscaler_ini_value:
             config.set('Upscaler', 'Backend', upscaler_ini_value)
             log_func('INFO', f"OptiScaler.ini: [Upscaler] Backend cambiado a '{upscaler_ini_value}'.")
             changes_made = True

        # 3. Configurar [Upscale] (Modo y Nitidez)
        upscale_mode_ini_value = UPSCALE_MODE_MAP.get(upscale_mode_selected, 'auto')
        sharpness_ini_value = f"{sharpness_selected:.2f}"
        if not config.has_section('Upscale'): config.add_section('Upscale')
        
        if config.get('Upscale', 'Mode', fallback='auto') != upscale_mode_ini_value:
            config.set('Upscale', 'Mode', upscale_mode_ini_value)
            log_func('INFO', f"OptiScaler.ini: [Upscale] Mode cambiado a '{upscale_mode_ini_value}'.")
            changes_made = True
            
        if config.get('Upscale', 'Sharpness', fallback='0.80') != sharpness_ini_value:
             config.set('Upscale', 'Sharpness', sharpness_ini_value)
             log_func('INFO', f"OptiScaler.ini: [Upscale] Sharpness cambiado a '{sharpness_ini_value}'.")
             changes_made = True

        # 4. Configurar [Overlay]
        overlay_ini_value = "basic" if overlay_selected else "off"
        if not config.has_section('Overlay'): config.add_section('Overlay')
        if config.get('Overlay', 'Mode', fallback='off') != overlay_ini_value:
            config.set('Overlay', 'Mode', overlay_ini_value)
            log_func('INFO', f"OptiScaler.ini: [Overlay] Mode cambiado a '{overlay_ini_value}'.")
            changes_made = True

        # 5. Configurar [MotionBlur]
        mb_ini_value = "true" if mb_selected else "false"
        if not config.has_section('MotionBlur'): config.add_section('MotionBlur')
        if config.get('MotionBlur', 'Disable', fallback='false') != mb_ini_value:
            config.set('MotionBlur', 'Disable', mb_ini_value)
            log_func('INFO', f"OptiScaler.ini: [MotionBlur] Disable cambiado a '{mb_ini_value}'.")
            changes_made = True

        if changes_made:
             with open(ini_path, 'w', encoding='utf-8') as f:
                 config.write(f, space_around_delimiters=False)
             log_func('OK', "OptiScaler.ini actualizado con Éxito.")
        
        return True

    except configparser.Error as e:
         log_func('ERROR', f"Error al parsear OptiScaler.ini: {e}")
         return False
    except Exception as e:
        log_func('ERROR', f"Error al actualizar OptiScaler.ini: {e}")
        return False

# --- NUEVA FUNCIúN (MEJORA 1): Leer INI especúfico de un juego ---
def read_optiscaler_ini(target_dir, log_func):
    """Lee la configuración actual de un OptiScaler.ini especúfico."""
    ini_path = os.path.join(target_dir, 'OptiScaler.ini')
    defaults = {
        "gpu_choice": 2, # Nvidia (auto)
        "fg_mode": "Automático",
        "upscaler": "Automático",
        "upscale_mode": "Automático",
        "sharpness": 0.8,
        "overlay": False,
        "motion_blur": True
    }
    
    if not os.path.exists(ini_path):
        log_func('WARN', f"No se encontrú OptiScaler.ini en {target_dir}. Devolviendo valores por defecto.")
        return defaults

    try:
        config = configparser.ConfigParser(commenót_prefixes=';', allow_no_value=True)
        config.read(ini_path)
        
        # Leer valores (con fallbacks por si el INI estú incompleto)
        
        # 1. GPU (Dxgi)
        dxgi_value = config.get('Dxgi', 'Dxgi', fallback='auto')
        gpu_choice = 1 if dxgi_value == 'true' else 2 # 1 = AMD, 2 = Nvidia

        # 2. Frame Generation
        fg_mode_ini = config.get('FrameGeneration', 'Mode', fallback='auto')
        fg_mode = FG_MODE_MAP_INVERSE.get(fg_mode_ini, "Automático")
        
        # 3. Upscaler (Backend)
        upscaler_ini = config.get('Upscale', 'Backend', fallback='fsr31')
        upscaler = UPSCALER_MAP_INVERSE.get(upscaler_ini, "Automático")
        
        # 4. Upscale Mode
        upscale_mode_ini = config.get('Upscale', 'Mode', fallback='auto')
        upscale_mode = UPSCALE_MODE_MAP_INVERSE.get(upscale_mode_ini, "Automático")
        
        # 5. Sharpness
        sharpness = config.getfloat('Upscale', 'Sharpness', fallback=0.8)

        # 6. Overlay
        overlay_ini = config.get('Overlay', 'Mode', fallback='off')
        overlay = (overlay_ini != 'off')

        # 7. Motion Blur
        mb_ini = config.get('MotionBlur', 'Disable', fallback='false')
        motion_blur = (mb_ini == 'true')
        
        log_func('INFO', f"Lectura de {ini_path} exitosa.")
        
        return {
            "gpu_choice": gpu_choice,
            "fg_mode": fg_mode,
            "upscaler": upscaler,
            "upscale_mode": upscale_mode,
            "sharpness": sharpness,
            "overlay": overlay,
            "motion_blur": motion_blur
        }

    except Exception as e:
        log_func('ERROR', f"Error al leer OptiScaler.ini: {e}. Devolviendo valores por defecto.")
        return defaults


def inject_fsr_mod(mod_source_dir, target_dir, log_func, spoof_dll_name="dxgi.dll", gpu_choice=2, fg_mode_selected="Automático",
                   upscaler_selected="Automático", upscale_mode_selected="Automático", sharpness_selected=0.8, overlay_selected=False, mb_selected=True):
    """Copia, renombra y configura el mod FSR 3/4."""
    # --- MODIFICADO (V2.0): Llama a check_mod_source_files con la lógica de auto-detección
    source_dir, source_ok = check_mod_source_files(mod_source_dir, log_func)
    if not source_ok:
        return False

    try:
        log_func('TITLE', "Iniciando proceso de COPIA, RENOMBRADO y CONFIGURACIÓN...")
        copied_files = 0
        created_backups = []

        mod_extensions = ('.dll', '.json', '.ini', '.bat', '.asi', '.cfg', '.txt', '.log', '.dat', '.sh', '.bin', '.reg')

        for item_name in os.listdir(source_dir):
            source_item_path = os.path.join(source_dir, item_name)
            target_item_path = os.path.join(target_dir, item_name)
            is_mod_file = os.path.isfile(source_item_path) and (item_name.lower().endswith(mod_extensions) or item_name in TARGET_MOD_FILES)

            if is_mod_file:
                if os.path.exists(target_item_path):
                    backup_path = target_item_path + ".bak"
                    try:
                        if os.path.exists(backup_path): os.remove(backup_path)
                        os.rename(target_item_path, backup_path)
                        log_func('WARN', f"Archivo existente {item_name} renombrado a {item_name}.bak")
                        created_backups.append(backup_path)
                    except Exception as e:
                        log_func('ERROR', f"No se pudo crear backup de {item_name}: {e}. Se intentarú sobrescribir.")
                
                shutil.copy2(source_item_path, target_dir)
                copied_files += 1
                log_func('INFO', f"  -> Copiando archivo: {item_name}")

        for dir_name in TARGET_MOD_DIRS:
            source_path = os.path.join(source_dir, dir_name)
            target_path = os.path.join(target_dir, dir_name)
            if os.path.isdir(source_path):
                if os.path.exists(target_path):
                    shutil.rmtree(target_path)
                    log_func('WARN', f"  -> Eliminando carpeta existente: {dir_name}")
                shutil.copytree(source_path, target_path)
                log_func('INFO', f"  -> Copiando carpeta recursiva: {dir_name}")

        if copied_files == 0 and not os.path.exists(os.path.join(target_dir, 'OptiScaler.dll')):
             log_func('WARN', "No se encontraron archivos relevantes para copiar.")
             return False

        if not configure_and_rename_dll(target_dir, spoof_dll_name, log_func):
             log_func('ERROR', "Fallo al renombrar DLL principal. Intentando restaurar backups de copia...")
             restored_count = 0
             for bak_file in created_backups:
                 original_file = bak_file[:-4]
                 try:
                     if os.path.exists(original_file): os.remove(original_file)
                     os.rename(bak_file, original_file)
                     log_func('INFO', f"Backup de copia {os.path.basename(bak_file)} restaurado.")
                     restored_count += 1
                 except Exception as e_restore:
                     log_func('ERROR', f"Fallo al restaurar backup de copia {os.path.basename(bak_file)}: {e_restore}")
             if restored_count > 0:
                 log_func('WARN', f"Se restauraron {restored_count} archivos copiados desde backup.")
             return False

        if not update_optiscaler_ini(target_dir, gpu_choice, fg_mode_selected, upscaler_selected, upscale_mode_selected, sharpness_selected, overlay_selected, mb_selected, log_func):
             log_func('ERROR', "Fallo al configurar OptiScaler.ini. La inyección puede no funcionar como se espera.")

        setup_bat_path = os.path.join(target_dir, 'setup_windows.bat')
        if os.path.exists(setup_bat_path): os.remove(setup_bat_path)

        reg_files = [f for f in os.listdir(target_dir) if f.lower().endswith('.reg')]
        if reg_files:
            log_func('WARN', '-------------------------------------------------------')
            log_func('WARN', f"úACCIúN MANUAL! Ejecute el archivo REG que DESHABILITA la firma ({reg_files[0]}) si el juego falla al iniciar.")
            log_func('WARN', '-------------------------------------------------------')

        spoof_name = spoof_dll_name
        log_func('INFO', "-------------------------------------------------------")
        log_func('INFO', "VERIFICACIúN MANUAL REQUERIDA:")
        log_func('INFO', f"1. DLL RENOMBRADO: Compruebe la existencia de '{spoof_name}'.")
        log_func('INFO', f"2. CONFIG. INI: Compruebe OptiScaler.ini para Dxgi, FrameGeneration, etc.")
        log_func('INFO', "-------------------------------------------------------")

        log_func('OK', f"Inyecciún completa y configurada. Total de archivos copiados: {copied_files}")
        return True

    except PermissionError:
        log_func('ERROR', "ACCESO DENEGADO. Asegúrese de que el juego o su launcher estún CERRADOS.")
        return False
    except Exception as e:
        log_func('ERROR', f"Ocurriú un error desconocido al inyectar: {e}")
        return False

# --- MEJORA 4: GESTIúN DE BACKUPS ---
def restore_original_dll(target_dir, log_func):
    """Restaura los .bak de los DLL de inyección, eliminando la versión del mod."""
    if not target_dir or not os.path.isdir(target_dir):
        log_func('ERROR', "La Carpeta de Destino del Juego no es vúlida.")
        return False
        
    restored_count = 0
    known_dll_bases = [name.replace('.dll', '').replace('.asi', '') for name in SPOOFING_DLL_NAMES]
    
    try:
        for filename in os.listdir(target_dir):
            if filename.lower().endswith('.bak'):
                # Es un backup. úEs de un DLL que conocemos?
                original_name = filename[:-4] # Quita ".bak"
                
                # Comprobar si el nombre original estú en nuestra lista de DLLs
                if original_name in SPOOFING_DLL_NAMES:
                    bak_path = os.path.join(target_dir, filename)
                    original_path = os.path.join(target_dir, original_name)
                    
                    try:
                        # 1. Borrar el DLL del mod (si existe)
                        if os.path.exists(original_path):
                            os.remove(original_path)
                            log_func('INFO', f"Restaurando .bak: Se eliminú el DLL activo '{original_name}'.")
                        
                        # 2. Renombrar el .bak a su nombre original
                        os.rename(bak_path, original_path)
                        log_func('OK', f"úúXITO! Se restaurú '{original_name}' desde '{filename}'.")
                        restored_count += 1
                        
                    except PermissionError:
                         log_func('ERROR', f"Fallo al restaurar {filename}. úEstú el juego abierto?")
                    except Exception as e_restore:
                         log_func('ERROR', f"Error al restaurar {filename}: {e_restore}")

        if restored_count > 0:
            log_func('OK', f"Restauraciún de {restored_count} archivo(s) .bak completada.")
            return True
        else:
            log_func('WARN', "No se encontraron archivos .bak relevantes (ej. dxgi.dll.bak) para restaurar.")
            return False
            
    except Exception as e:
        log_func('ERROR', f"Error durante la búsqueda de backups: {e}")
        return False


def uninstall_fsr_mod(target_dir, log_func):
    """Elimina todos los archivos y carpetas del mod. Retorna lista de backups encontrados."""
    if not target_dir or not os.path.isdir(target_dir):
        log_func('ERROR', "La Carpeta de Destino del Juego no es vúlida.")
        return False, []

    files_to_try_to_remove = set(
        TARGET_MOD_FILES + GENERIC_SPOOF_FILES + list(SPOOFING_OPTIONS.values()) +
        ['nvngx.dll', 'libxess_fg.dll', 'libxell.dll', 'fakenvapi.dll', 'fakenvapi.ini']
    )
    dirs_to_remove = TARGET_MOD_DIRS
    found_backups = []

    log_func('WARN', f"Intentando ELIMINAR OptiScaler y archivos relacionados de: {target_dir}")

    try:
        removed_files = 0
        removed_dirs = 0
        
        # 1. Eliminar Archivos especúficos (úignora los .bak!)
        for filename in files_to_try_to_remove:
            if filename.lower().endswith('.bak'): continue # No borrar backups
            
            file_path = os.path.join(target_dir, filename)
            if os.path.exists(file_path) and os.path.isfile(file_path):
                try:
                    os.remove(file_path)
                    removed_files += 1
                    log_func('INFO', f"  -> Eliminado archivo especúfico: {filename}")
                except PermissionError:
                     log_func('ERROR', f"Fallo al eliminar {filename}. úEstú el juego abierto?")
                except Exception as e_rem:
                     log_func('ERROR', f"Error al eliminar {filename}: {e_rem}")

        # 2. Eliminar Carpetas Recursivamenóte
        for dirname in dirs_to_remove:
            dir_path = os.path.join(target_dir, dirname)
            if os.path.isdir(dir_path):
                try:
                    shutil.rmtree(dir_path)
                    removed_dirs += 1
                    log_func('INFO', f"  -> Eliminada carpeta recursiva: {dirname}")
                except PermissionError:
                     log_func('ERROR', f"Fallo al eliminar carpeta {dirname}. úHay archivos en uso?")
                except Exception as e_rem_dir:
                     log_func('ERROR', f"Error al eliminar carpeta {dirname}: {e_rem_dir}")

        # 3. Eliminar archivos genéricos (logs) y BUSCAR .bak
        current_files = os.listdir(target_dir)
        for filename in current_files:
            file_path = os.path.join(target_dir, filename)
            if not os.path.isfile(file_path): continue

            # --- MEJORA 4: Detectar backups en lugar de borrarlos ---
            if filename.lower().endswith('.bak'):
                 original_name = filename[:-4]
                 # Solo nos importan los backups de los DLL que inyectamos
                 if original_name in SPOOFING_DLL_NAMES or original_name == 'OptiScaler.dll':
                     found_backups.append((file_path, original_name))
                     log_func('INFO', f"  -> Encontrado archivo backup: {filename}")
            
            # Borrar logs y .reg
            elif any(filename.lower().endswith(ext) for ext in ['.log', '.reg']):
                 try:
                     os.remove(file_path)
                     removed_files += 1
                     log_func('INFO', f"  -> Eliminado archivo genérico/reg: {filename}")
                 except Exception as e_rem_gen:
                     log_func('ERROR', f"Error al eliminar {filename}: {e_rem_gen}")

        if removed_files > 0 or removed_dirs > 0:
            log_func('OK', f"Desinstalación completada. Se eliminaron {removed_files} archivos y {removed_dirs} carpetas.")
            return True, found_backups
        else:
            log_func('WARN', "No se encontraron archivos principales del mod OptiScaler en esta carpeta.")
            return False, found_backups

    except PermissionError as e:
        log_func('ERROR', f"FALLO AL ACCEDER A LA CARPETA DURANTE LA DESINSTALACIÓN. úJUEGO CERRADO? Detalle: {e}")
        return False, []
    except Exception as e:
        log_func('ERROR', f"Ocurriú un error desconocido al eliminar archivos: {e}.")
        return False, []
# ==============================================================================
# 4. NUEVAS FUNCIONES DE LúGICA V2.0
# ==============================================================================

# --- Mejora 1: Auto-Descargador ---

def fetch_github_releases(log_func):
    """Descarga la lista de releases de la API de GitHub con sistema de cachéú."""
    # Ruta del archivo de cachéú
    caché_file = os.path.join(APP_DATA_DIR, "releases_caché.json")
    caché_expiry_hours = 24
    
    # Intentar cargar desde cachéú
    if os.path.exists(caché_file):
        try:
            with open(caché_file, 'r', encoding='utf-8') as f:
                caché_data = json.load(f)
                caché_time = caché_data.get('timestamp', 0)
                caché_releases = caché_data.get('releases', [])
                
                # Verificar si la cachéú es reciente (< 24 horas)
                import time
                age_hours = (time.time() - caché_time) / 3600
                
                if age_hours < caché_expiry_hours and caché_releases:
                    log_func('INFO', f"Usando cachéú de releases (edad: {age_hours:.1f}h)")
                    return caché_releases
                else:
                    log_func('INFO', f"cachéú expirada (edad: {age_hours:.1f}h), consultando GitHub...")
        except Exception as e:
            log_func('WARN', f"Error al leer cachéú: {e}")
    
    # Si no hay cachéú vúlida, consultar GitHub (lazy load requests)
    if not ensure_requests_available():
        log_func('ERROR', "'requests' no estú instalado. No se pueden buscar versiones.")
        # Intentar usar cachéú aunque estú expirada
        if os.path.exists(caché_file):
            try:
                with open(caché_file, 'r', encoding='utf-8') as f:
                    caché_data = json.load(f)
                    return caché_data.get('releases', [])
            except:
                pass
        return None
    
    try:
        import requests  # Import local después de ensure
        log_func('INFO', "Consultando versiones del mod en GitHub...")
        response = requests.get(GITHUB_API_URL, timeout=10)
        response.raise_for_status()
        releases = response.json()
        log_func('INFO', f"Se encontraron {len(releases)} versiones.")
        
        # Guardar en cachéú
        try:
            import time
            caché_data = {
                'timestamp': time.time(),
                'releases': releases
            }
            with open(caché_file, 'w', encoding='utf-8') as f:
                json.dump(caché_data, f, indent=2)
            log_func('INFO', "cachéú de releases actualizada.")
        except Exception as e:
            log_func('WARN', f"No se pudo guardar cachéú: {e}")
        
        return releases
    except Exception as e:
        log_func('ERROR', f"Error al buscar versiones en GitHub: {e}")
        # Intentar usar cachéú aunque estú expirada como fallback
        if os.path.exists(caché_file):
            try:
                log_func('INFO', "Usando cachéú expirada como fallback...")
                with open(caché_file, 'r', encoding='utf-8') as f:
                    caché_data = json.load(f)
                    return caché_data.get('releases', [])
            except:
                pass
        return None

def download_mod_release(release_info, progress_callback, log_func):
    """Descarga un asset de release (el .7z) en un hilo separado."""
    try:
        if not ensure_requests_available():
             log_func('ERROR', "Faltan 'requests'. Abortando descarga.")
             progress_callback(0, 0, True, "Error: Faltan dependencias.")
             return

        import requests  # Import local después de ensure
        
        asset = next((a for a in release_info['assets'] if a['name'].endswith('.7z')), None)
        if not asset:
            log_func('ERROR', "Esta release no tiene un archivo .7z")
            progress_callback(0, 0, True, "Error: No se encontrú .7z")
            return

        download_url = asset['browser_download_url']
        file_name = asset['name']
        total_size = asset['size']
        download_path = os.path.join(MOD_SOURCE_DIR, file_name)
        
        if not os.path.exists(MOD_SOURCE_DIR):
            os.makedirs(MOD_SOURCE_DIR)
            
        log_func('TITLE', f"Descargando {file_name}...")
        
        with requests.get(download_url, stream=True) as r:
            r.raise_for_status()
            downloaded_size = 0
            with open(download_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
                    downloaded_size += len(chunk)
                    progress_callback(downloaded_size, total_size, False, None)
        
        log_func('OK', f"Descarga completada: {file_name}")
        
        # Pequeúo delay para asegurar que Windows libere el archivo
        import time
        time.sleep(0.5)
        
        # Ahora extraer
        extract_path = os.path.join(MOD_SOURCE_DIR, file_name.replace('.7z', ''))
        
        # --- CORREGIDO: Llama a la nueva funciún de extracciún ---
        if extract_mod_archive(download_path, extract_path, log_func):
            log_func('OK', f"Extracciún completada en: {extract_path}")
            # Limpiar el .7z con retry
            try:
                time.sleep(0.3)
                os.remove(download_path)
            except PermissionError:
                log_func('WARN', f"No se pudo eliminar {file_name} (en uso). Se eliminarú más tarde.")
            except Exception:
                pass
            progress_callback(total_size, total_size, True, f"úCompletado! Listo para usar: {file_name.replace('.7z', '')}")
        else:
            raise Exception("Fallo en la extracciún. Revise el log.") # Error más especúfico

    except Exception as e:
        log_func('ERROR', f"Fallo en la descarga/extracciún: {e}")
        progress_callback(0, 0, True, f"Error: {e}")

# --- CORREGIDO (V2.0 Fix 2): Reemplaza py7zr con subprocess y 7z.exe ---
def extract_mod_archive(archive_path, extract_path, log_func):
    """Extrae un archivo .7z usando 7z.exe externo."""
    
    # --- MODIFICADO (V2.1): Usar carpeta centralizada APP_DATA_DIR ---
    seven_zip_exe = os.path.join(APP_DATA_DIR, SEVEN_ZIP_EXE_NAME)

    if not os.path.exists(seven_zip_exe):
        log_func('ERROR', f"úNo se encontrú {SEVEN_ZIP_EXE_NAME}! El archivo {SEVEN_ZIP_EXE_NAME} debe estar en la")
        log_func('ERROR', f"carpeta '{APP_DATA_DIR}' para poder extraer.")
        # No llamamos a check_and_download_7zip aquú, porque ya se debiú llamar ANTES de entrar al downloader.
        return False
    
    # Verificar que 7z.exe sea ejecutable
    if not os.access(seven_zip_exe, os.X_OK):
        log_func('ERROR', f"{SEVEN_ZIP_EXE_NAME} no tiene permisos de ejecuciún.")
        log_func('WARN', "Intente ejecutar el archivo manualmente una vez para desbloquearlo.")
        log_func('WARN', "En Windows: Clic derecho > Propiedades > Desbloquear > Aplicar")
        return False

    try:
        log_func('INFO', f"Extrayendo {os.path.basename(archive_path)} usando {SEVEN_ZIP_EXE_NAME}...")
        
        # Verificar que el archivo no estú en uso
        import time
        max_retries = 3
        for retry in range(max_retries):
            try:
                # Intentar abrir el archivo para verificar acceso
                with open(archive_path, 'rb') as test_file:
                    test_file.read(1)
                break
            except PermissionError:
                if retry < max_retries - 1:
                    log_func('WARN', f"Archivo en uso, esperando... (intento {retry + 1}/{max_retries})")
                    time.sleep(1)
                else:
                    raise PermissionError(f"No se puede acceder a {archive_path} después de {max_retries} intentos")
        
        if os.path.isdir(extract_path):
            shutil.rmtree(extract_path)

        # Preparar el comando de subprocess
        command = [
            seven_zip_exe,
            'x',             # Comando de extracciún (con rutas completas)
            archive_path,    # Archivo a extraer
            f'-o{extract_path}', # Directorio de salida (sin espacio)
            '-y'             # Sú a todo (sobrescribir)
        ]

        # Ocultar la ventana de la consola de 7z.exe
        startupinfo = None
        if platform.system() == "Windows":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE

        # Usar encoding 'latin-1' para evitar errores de decodificaciún en la salida de 7z.exe
        result = subprocess.run(command, capture_output=True, text=True, startupinfo=startupinfo, encoding='latin-1')
        
        if result.returncode != 0:
            log_func('ERROR', f"{SEVEN_ZIP_EXE_NAME} fallú con el cúdigo {result.returncode}")
            log_func('ERROR', f"Salida: {result.stdout}")
            log_func('ERROR', f"Error: {result.stderr}")
            return False

        log_func('OK', f"Extracciún con {SEVEN_ZIP_EXE_NAME} completada.")

        # OptiScaler a veces estú en una subcarpeta, vamos a moverlo
        subfolders = [d for d in os.listdir(extract_path) if os.path.isdir(os.path.join(extract_path, d))]
        if len(subfolders) == 1:
            subfolder_path = os.path.join(extract_path, subfolders[0])
            # Comprobar si es el dir correcto
            if any(f in os.listdir(subfolder_path) for f in MOD_CHECK_FILES):
                log_func('WARN', "Mod detectado en subcarpeta, moviendo archivos...")
                # Mover todo de la subcarpeta al directorio de extracciún
                for item in os.listdir(subfolder_path):
                    shutil.move(os.path.join(subfolder_path, item), extract_path)
                shutil.rmtree(subfolder_path)
        
        return True
    except PermissionError as e:
        log_func('ERROR', f"Acceso denegado al ejecutar {SEVEN_ZIP_EXE_NAME}: {e}")
        log_func('WARN', f"Soluciones posibles:")
        log_func('WARN', f"1. Ejecute esta aplicaciún como administrador")
        log_func('WARN', f"2. Clic derecho en {SEVEN_ZIP_EXE_NAME} > Propiedades > Desbloquear")
        log_func('WARN', f"3. Verifique que su antivirus no estú bloqueando {SEVEN_ZIP_EXE_NAME}")
        return False
    except Exception as e:
        log_func('ERROR', f"Fallo al ejecutar {SEVEN_ZIP_EXE_NAME}: {e}")
        log_func('ERROR', f"Tipo de error: {type(e).__name__}")
        return False

# --- ELIMINADO (V2.0 Refactor): Funciones de Presets ---

# --- Mejora 4: Limpieza ---

def clean_logs(game_folders, log_func):
    """Elimina OptiScaler.log de todas las carpetas de juegos."""
    cleaned_count = 0
    for game_path in game_folders:
        log_file = os.path.join(game_path, "OptiScaler.log")
        if os.path.exists(log_file):
            try:
                os.remove(log_file)
                log_func('INFO', f"Log eliminado de: {os.path.basename(game_path)}")
                cleaned_count += 1
            except Exception as e:
                log_func('ERROR', f"No se pudo eliminar el log de {os.path.basename(game_path)}: {e}")
    
    log_func('OK', f"Limpieza de {cleaned_count} logs completada.")
    return cleaned_count

def clean_orphan_backups(all_games_data, log_func):
    """Elimina .bak de carpetas de juegos donde el mod estú "AUSENTE"."""
    cleaned_count = 0
    # --- MODIFICADO (V2.0 Refactor): Ajustado a 5 elemenótos de tupla ---
    for game_path, _, mod_status, _, _ in all_games_data: 
        if "AUSENTE" in mod_status:
            try:
                for filename in os.listdir(game_path):
                    if filename.lower().endswith('.bak'):
                        original_name = filename[:-4]
                        if original_name in SPOOFING_DLL_NAMES or original_name == 'OptiScaler.dll':
                            bak_path = os.path.join(game_path, filename)
                            os.remove(bak_path)
                            log_func('INFO', f"Backup huúrfano '{filename}' eliminado de: {os.path.basename(game_path)}")
                            cleaned_count += 1
            except Exception as e:
                log_func('ERROR', f"No se pudo limpiar backups de {os.path.basename(game_path)}: {e}")
    
    log_func('OK', f"Limpieza de {cleaned_count} backups huérfanos completada.")
    return cleaned_count
# ==============================================================================
# 5. Interfaz Grúfica (GUI) - V2.0
# ==============================================================================

# --- ELIMINADO (V2.0 Pulida): Clase Tooltip ---
# La clase Tooltip ha sido eliminada.


class FSRInjectorApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        try:
            # --- NUEVO (V2.1): Crear carpeta de configuración centralizada ---
            if not os.path.exists(APP_DATA_DIR):
                os.makedirs(APP_DATA_DIR)
            
            # --- NUEVO (V2.1): Migrar config antigua si existe ---
            old_config = os.path.join(os.path.dirname(os.path.abspath(__file__)), "injector_config.json")
            if os.path.exists(old_config) and not os.path.exists(CONFIG_FILE):
                import shutil
                shutil.copy2(old_config, CONFIG_FILE)
                print(f"Config migrado de {old_config} a {CONFIG_FILE}")
            
            # --- MODIFICADO (V2.0 Pulida): 7z.exe ya NO se comprueba aquú ---
            # check_and_download_7zip(print) # <--- ELIMINADO DE AQUú

            ctk.set_appearance_mode("dark")
            ctk.set_default_color_theme("blue")

            # --- TúTULO ACTUALIZADO ---
            self.title("GESTOR AUTOMATIZADO DE OPTISCALER V2.0")
            self.geometry("1000x850") # Un poco más alto
            self.minsize(950, 800)
            
            # --- Variables de Estado ---
            self.all_games_data = [] # (path, display_name, mod_status, exe_name, platform_tag)
            self.filtered_game_indices = []
            self.game_checkbox_vars = {}
            self.mod_source_dir = ctk.StringVar()
            self.manual_game_path = ctk.StringVar()
            self.mod_status_manual = ctk.StringVar(value="[Estado: N/A]")
            self.game_filter_var = ctk.StringVar()
            self.fg_mode_var = ctk.StringVar(value="Automático") 
            self.spoof_dll_name_var = ctk.StringVar(value="dxgi.dll")
            self.upscaler_var = ctk.StringVar(value="Automático")
            self.upscale_mode_var = ctk.StringVar(value="Automático")
            self.sharpness_var = ctk.DoubleVar(value=0.8)
            self.overlay_var = ctk.BooleanVar(value=False)
            self.motion_blur_var = ctk.BooleanVar(value=True)
            self.sharpness_label_var = ctk.StringVar(value="0.80")
            
            self.custom_search_folders = []
            self.active_popup = None 
            
            # --- NUEVO (V2.0) ---
            self.github_releases = [] # caché de releases
            self.log_auto_scroll_var = ctk.BooleanVar(value=True) # Mejora C
            self.mod_version_list = ctk.StringVar() # Mejora V2.1 (Selector)
            
            # --- NUEVO: Control de presets ---
            self._applying_preset = False  # Flag para evitar marcar como Custom durante apply_preset
            
            # --- NUEVO (V2.1 Handheld): Modo Gaming ---
            self.gaming_mode_var = ctk.BooleanVar(value=False)
            self.gaming_game_checkboxes = {}  # Diccionario para checkboxes de juegos en modo gaming
            
            # --- NUEVO (V2.1): Sistema de gestiún de iconos ---
            # use_custom_icons=False por defecto (usa emojis)
            # Cambiar a True cuando se aúadan archivos PNG en carpeta icons/
            self.icons = get_icon_manager(use_custom_icons=False)
            
            # --- NUEVO (V2.0 Refactor): Filtros de plataforma (Mejora 3) ---
            self.filter_steam_var = ctk.BooleanVar(value=True)
            self.filter_xbox_var = ctk.BooleanVar(value=True)
            self.filter_epic_var = ctk.BooleanVar(value=True)
            self.filter_custom_var = ctk.BooleanVar(value=True)
            
            self.is_nvidia = os.path.exists(NVIDIA_CHECK_FILE)
            default_gpu_choice = 2 if self.is_nvidia else 1
            self.gpu_choice = ctk.IntVar(value=default_gpu_choice)
            
            # --- Variables del Mando ---
            self.controller = None
            # --- MODIFICADO (V2.0 Refactor): 5 Pestañas ---
            self.tab_names = [
                ' 1. CONFIGURACIÓN DEL MOD ', ' 2. AUTO (Xbox/Steam/Epic) ', 
                ' 3. MANUAL ', ' 4. CONFIGURACIÓN APP ', ' 5. LOG DE OPERACIONES '
            ]
            self.current_tab_index = 0
            
            # --- Gestiún de Foco (REFACTORIZADA V5) ---
            self.focus_location = 'global' # 'global', 'tabs', 'content'
            self.global_navigable_widgets = []
            self.global_focused_index = -1
            
            # Listas de widgets navegables por pestaña (listas de listas, para 2D)
            self.navigable_widgets = { 0: [], 1: [], 2: [], 3: [], 4: [] } # 5 Pestañas
            # índices de foco por pestaña [fila, col]
            self.focused_indices = {
                0: [0, 0], 1: [0, 0], 2: [0, 0], 3: [0, 0], 4: [0, 0]
            }
            
            # --- Variables de Navegaciún Gaming ---
            self.gaming_focus_location = 'nav'  # 'nav' (menóú lateral), 'content' (panel derecho)
            self.gaming_nav_focused_index = 0  # índice en el menóú lateral (0-4)
            self.gaming_content_widgets = []  # Lista plana de widgets navegables en el panel activo
            self.gaming_content_focused_index = 0  # índice en content_widgets
            self.gaming_active_nav_key = 'auto'  # Quú panel estú abierto actualmenóte
            
            # --- Colores ---
            self.default_frame_border_color = None
            self.default_frame_border_width = 0
            self.focus_color = ("#CCCCCC", "#999999")
            # Modo ediciún para sliders (Enter para editar, Izq/Der para ajustar, Enter para confirmar)
            self.slider_edit_mode = False
            
            self.create_widgets()
            
            # --- Tareas Post-Creaciún ---
            self.after(50, self._get_default_border_color)
            self.after(100, self._bind_click_to_navigables)  # Aúadir bindings de click
            self.log_message('INFO', "Permisos de Administrador Verificados.")
            
            self.load_config() # <-- Modificada para cargar carpetas custom
            self.show_recommended_settings()
            
            # --- MODIFICADO (V2.1 Performance): No escanear al inicio ---
            # El escaneo ahora es manual vúa botón "?? Escanear Juegos"
            # Se carga la cachéú si existe
            self.load_games_caché()
            self.filtered_game_indices = list(range(len(self.all_games_data)))
            self.load_game_list()
            
            self.init_controller()
            self.poll_controller()
            
            # --- Bindings de Teclado (Simplificados) ---
            self.bind("<Up>", lambda e: (self.move_focus('up'), "break")[1])
            self.bind("<Down>", lambda e: (self.move_focus('down'), "break")[1])
            self.bind("<Left>", lambda e: (self.move_focus('left'), "break")[1])
            self.bind("<Right>", lambda e: (self.move_focus('right'), "break")[1])
            self.bind("<Return>", lambda e: (self.activate_focused_widget(), "break")[1])
            self.bind("<Escape>", lambda e: (self.handle_escape_key(), "break")[1])
            
            # Binding para devolver el foco a la ventana al hacer clic
            self.bind_all("<Button-1>", lambda e: self.after(1, lambda: self.focus_force()), add="+")
            
            self.bind("x", lambda e: self.btn_go_to_auto.invoke() if self.current_tab_index == 0 else (self.btn_auto_inject.invoke() if self.current_tab_index == 1 else (self.btn_manual_inject.invoke() if self.current_tab_index == 2 else None)))
            self.bind("y", lambda e: self.btn_auto_uninstall.invoke() if self.current_tab_index == 1 else (self.btn_manual_uninstall.invoke() if self.current_tab_index == 2 else None))

            self.bind("<Control-Tab>", lambda e: (self.change_tab(1), "break")[1])
            self.bind("<Control-Shift-Tab>", lambda e: (self.change_tab(-1), "break")[1])
            
            # Foco inicial
            self.focus_location = 'global'
            self.global_focused_index = 0
            self.focused_indices = { 0: [0, 0], 1: [0, 0], 2: [0, 0], 3: [0, 0], 4: [0, 0] }
            
            # Asegurar que la ventana tiene el foco para capturar eventos de teclado
            self.after(100, lambda: self.focus_force())
            self.after(150, lambda: self.update_focus_visuals())
            
            # NUEVO (V2.1 Performance): Actualizar indicador de cachéú después de crear interfaz
            self.after(200, lambda: self.update_caché_info_label() if hasattr(self, 'caché_info_label') else None)

            self.protocol("WM_DELETE_WINDOW", self.on_closing)

        except Exception as e:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("Error Crútico de Aplicaciún", f"Fallo al construir la interfaz gráfica: {e}\n\n{traceback.format_exc()}")
            self.destroy()

    # --- Funciones de Configuración ---
    
    # --- NUEVO (V2.1 Performance): Cargar cachéú de juegos ---
    def load_games_caché(self):
        """Carga la cachéú de juegos al iniciar la aplicaciún."""
        self.all_games_data = load_games_caché(self.log_message)
        if not self.all_games_data:
            self.log_message('INFO', "Biblioteca vacía. Use el botón '?? Escanear Juegos' para detectar juegos.")
    
    def update_caché_info_label(self):
        """Actualiza el label que muestra información de la cachéú."""
        if not hasattr(self, 'caché_info_label'):
            return
        
        try:
            if not os.path.exists(GAMES_caché_FILE):
                self.caché_info_label.configure(text="Sin caché - pulse el botón para escanear")
                return
            
            import datetime
            with open(GAMES_caché_FILE, 'r', encoding='utf-8') as f:
                caché_data = json.load(f)
            
            timestamp_str = caché_data.get("timestamp", "")
            games_count = caché_data.get("games_count", 0)
            
            if timestamp_str:
                try:
                    timestamp = datetime.datetime.fromisoformat(timestamp_str)
                    time_ago = datetime.datetime.now() - timestamp
                    
                    if time_ago.days > 0:
                        time_text = f"hace {time_ago.days} día(s)"
                    elif time_ago.seconds >= 3600:
                        hours = time_ago.seconds // 3600
                        time_text = f"hace {hours}h"
                    elif time_ago.seconds >= 60:
                        mins = time_ago.seconds // 60
                        time_text = f"hace {mins}m"
                    else:
                        time_text = "recién"
                    
                    self.caché_info_label.configure(
                        text=f"💾 {games_count} juegos en caché ({time_text})"
                    )
                except:
                    self.caché_info_label.configure(text=f"💾 {games_count} juegos en caché")
            else:
                self.caché_info_label.configure(text=f"💾 {games_count} juegos en caché")
        except Exception as e:
            self.caché_info_label.configure(text="⚠️ Error al leer caché")
    
    # --- MODIFICADO (Mejora 3): Carga/Guarda carpetas personalizadas ---
    def load_config(self):
        """Carga la configuración desde config.json."""
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                    # --- MODIFICADO (V2.0): Ya no carga mod_source_dir, lo detecta
                    self.gpu_choice.set(config.get("gpu_choice", 2 if self.is_nvidia else 1))
                    default_dll = SPOOFING_OPTIONS.get(1, "dxgi.dll")
                    self.spoof_dll_name_var.set(config.get("spoof_dll_name", default_dll))
                    self.fg_mode_var.set(config.get("fg_mode", "Automático"))
                    self.upscaler_var.set(config.get("upscaler", "Automático"))
                    self.upscale_mode_var.set(config.get("upscale_mode", "Automático"))
                    self.sharpness_var.set(config.get("sharpness", 0.8))
                    self.sharpness_label_var.set(f"{self.sharpness_var.get():.2f}")
                    self.overlay_var.set(config.get("overlay", False))
                    self.motion_blur_var.set(config.get("motion_blur", True))
                    self.theme_var.set(config.get("theme", "Oscuro"))
                    self.scale_var.set(config.get("scale", "100%"))
                    self.gaming_mode_var.set(config.get("gaming_mode", False))
                    self.custom_search_folders = config.get(CUSTOM_SEARCH_FOLDERS_CONFIG_KEY, [])
                    
                    # Apply theme and scale on startup
                    theme_map = {"Claro": "light", "Oscuro": "dark", "Sistema": "system"}
                    ctk.set_appearance_mode(theme_map.get(self.theme_var.get(), "dark"))
                    
                    scale_map = {"80%": 0.8, "90%": 0.9, "100%": 1.0, "110%": 1.1, "120%": 1.2}
                    ctk.set_widget_scaling(scale_map.get(self.scale_var.get(), 1.0))
                    
                    # Log para debug del gaming mode
                    gaming_loaded = self.gaming_mode_var.get()
                    self.log_message('INFO', f"Configuración cargada. Gaming mode: {gaming_loaded}")
                    self.log_message('INFO', f"Archivo config: {CONFIG_FILE}")
                    
                    if hasattr(self, 'custom_folders_list_frame'):
                        self.refresh_custom_folders_list(scan_on_load=False) # No escanear juegos aquú
            else:
                 self.log_message('INFO', "Archivo de configuración no encontrado, usando valores por defecto.")
                 self.gpu_choice.set(2 if self.is_nvidia else 1)
                 self.spoof_dll_name_var.set(SPOOFING_OPTIONS.get(1, "dxgi.dll"))
                 self.fg_mode_var.set("Automático")
                 self.upscaler_var.set("Automático")
                 self.upscale_mode_var.set("Automático")
                 self.sharpness_var.set(0.8)
                 self.sharpness_label_var.set("0.80")
                 self.overlay_var.set(False)
                 self.motion_blur_var.set(True)
                 self.theme_var.set("Oscuro")
                 self.scale_var.set("100%")
                 self.gaming_mode_var.set(False)
                 self.custom_search_folders = []
            
            # --- NUEVO (V2.0): Autodetectar mod_source_dir al inicio ---
            # COmenóTADO: Se ejecutarú después de crear las interfaces
            # self.autodetect_mod_source() # Esto ahora rellena el ComboBox
            
            # --- NUEVO (V5): Actualizar texto de botones de selecciún ---
            if hasattr(self, 'btn_dll_select'):
                self.btn_dll_select.configure(text=f"{self.spoof_dll_name_var.get()}")
            if hasattr(self, 'btn_fg_select'):
                self.btn_fg_select.configure(text=f"{self.fg_mode_var.get()}")
                self.btn_upscaler_select.configure(text=f"{self.upscaler_var.get()}")
            if hasattr(self, 'btn_upscale_select'):
                self.btn_upscale_select.configure(text=f"{self.upscale_mode_var.get()}")

            
            # --- NUEVO (V2.1 Handheld): Aplicar modo gaming si estaba activado ---
            gaming_should_apply = self.gaming_mode_var.get()
            print(f"[DEBUG] Fin de load_config - gaming_mode_var: {gaming_should_apply}")
            if gaming_should_apply:
                # Programar aplicaciún del modo gaming después de que la UI estú completamente construida
                self.after(200, self._apply_gaming_mode_on_startup)
                print("[DEBUG] Programado _apply_gaming_mode_on_startup para 200ms")
            else:
                # Programar aplicaciún del modo clúsico para asegurar que gaming estú oculto
                self.after(200, self._apply_classic_mode_on_startup)
                print("[DEBUG] Programado _apply_classic_mode_on_startup para 200ms")

        except Exception as e:
            self.log_message('ERROR', f"Error al cargar la configuración: {e}")
            # Establecer valores por defecto en caso de error
            self.gpu_choice.set(2 if self.is_nvidia else 1)
            self.spoof_dll_name_var.set(SPOOFING_OPTIONS.get(1, "dxgi.dll"))

            self.fg_mode_var.set("Automático")
            self.upscaler_var.set("Automático")
            self.upscale_mode_var.set("Automático")
            self.sharpness_var.set(0.8)
            self.sharpness_label_var.set("0.80")
            self.overlay_var.set(False)
            self.motion_blur_var.set(True)
            self.custom_search_folders = []
    
    def _apply_gaming_mode_on_startup(self):
        """Aplica el modo gaming al inicio sin llamar a toggle (que lo invertirúa)."""
        try:
            # Asegurarse que gaming_mode_var estú en True
            if not self.gaming_mode_var.get():
                self.gaming_mode_var.set(True)
            
            # Ocultar botones superiores (ayuda y gaming mode)
            if hasattr(self, 'btn_gaming_mode') and self.btn_gaming_mode.master:
                self.btn_gaming_mode.master.grid_remove()
            if hasattr(self, 'buttons_frame'):
                self.buttons_frame.grid_remove()
            # Ocultar interfaz normal y mostrar interfaz gaming
            if hasattr(self, 'notebook_frame'):
                self.notebook_frame.grid_remove()
            if hasattr(self, 'gaming_interface_frame'):
                self.gaming_interface_frame.grid()
                # Mostrar panel de juegos detectados por defecto
                self.show_gaming_auto()
                # Detectar quú preset estú activo basado en la configuración actual
                self._detect_active_preset()
                # Inicializar navegación gaming
                self.gaming_focus_location = 'nav'
                self.gaming_nav_focused_index = 1  # Empezar en el botón "auto" (segundo botón)
                self.after(100, lambda: self.update_focus_visuals_gaming())
                self.log_message('OK', f"?? Modo Gaming restaurado (gaming_mode={self.gaming_mode_var.get()})")
        except Exception as e:
            self.log_message('ERROR', f"Error al restaurar modo gaming: {e}")
    
    def _apply_classic_mode_on_startup(self):
        """Aplica el modo clúsico al inicio, asegurando que gaming estú oculto."""
        try:
            # Asegurarse que gaming_mode_var estú en False
            if self.gaming_mode_var.get():
                self.gaming_mode_var.set(False)
            
            # Mostrar botones superiores (ayuda y gaming mode)
            if hasattr(self, 'btn_gaming_mode') and self.btn_gaming_mode.master:
                self.btn_gaming_mode.master.grid()
            if hasattr(self, 'buttons_frame'):
                self.buttons_frame.grid()
            
            # Ocultar interfaz gaming y mostrar interfaz clúsica
            if hasattr(self, 'gaming_interface_frame'):
                self.gaming_interface_frame.grid_remove()
            if hasattr(self, 'notebook_frame'):
                self.notebook_frame.grid()
            
            self.log_message('OK', f"?? Modo Clúsico restaurado (gaming_mode={self.gaming_mode_var.get()})")
        except Exception as e:
            self.log_message('ERROR', f"Error al restaurar modo clúsico: {e}")
    
    def _detect_active_preset(self):
        """Detecta quú preset estú activo basíndose en la configuración actual."""
        # Definiciún de presets
        presets = {
            "default": {
                "upscaler": "Automático",
                "fg_mode": "Automático",
                "upscale_mode": "Automático",
                "sharpness": 0.8
            },
            "performance": {
                "upscaler": "FSR 3.1",
                "fg_mode": "FSR 3.1",
                "upscale_mode": "Rendimiento",
                "sharpness": 0.5
            },
            "balanced": {
                "upscaler": "FSR 3.1",
                "fg_mode": "Automático",
                "upscale_mode": "Equilibrado",
                "sharpness": 0.7
            },
            "quality": {
                "upscaler": "FSR 3.1",
                "fg_mode": "FSR 3.1",
                "upscale_mode": "Calidad",
                "sharpness": 0.9
            }
        }
        
        # Comparar configuración actual con cada preset
        current_config = {
            "upscaler": self.upscaler_var.get(),
            "fg_mode": self.fg_mode_var.get(),
            "upscale_mode": self.upscale_mode_var.get(),
            "sharpness": self.sharpness_var.get()
        }
        
        for preset_name, preset_config in presets.items():
            if all(current_config[key] == preset_config[key] for key in preset_config):
                self.update_gaming_preset_indicator(preset_name)
                return
        
        # Si no coincide con ningún preset, es Custom
        self.update_gaming_preset_indicator("custom")


    def save_config(self, *args):
        """Guarda la configuración actual en config.json."""
        # --- MODIFICADO (V2.0 Refactor): Asegurar que las variables estún actualizadas ---
        # (Esto ahora es redundante porque el callback de open_custom_select lo hace, pero es seguro)
        if hasattr(self, 'btn_dll_select'):
            self.spoof_dll_name_var.set(self.btn_dll_select.cget("text").split(":")[-1].strip().replace(" ?", ""))
        if hasattr(self, 'btn_fg_select'):
            self.fg_mode_var.set(self.btn_fg_select.cget("text").split(":")[-1].strip().replace(" ?", ""))
        if hasattr(self, 'btn_upscaler_select'):
            self.upscaler_var.set(self.btn_upscaler_select.cget("text").split(":")[-1].strip().replace(" ?", ""))
        if hasattr(self, 'btn_upscale_select'):
            self.upscale_mode_var.set(self.btn_upscale_select.cget("text").split(":")[-1].strip().replace(" ?", ""))

        config = {
            # "mod_source_dir" ya no se guarda, es automático
            "gpu_choice": self.gpu_choice.get(),
            "spoof_dll_name": self.spoof_dll_name_var.get(), 
            "fg_mode": self.fg_mode_var.get(),
            "upscaler": self.upscaler_var.get(),
            "upscale_mode": self.upscale_mode_var.get(),
            "sharpness": self.sharpness_var.get(),
            "overlay": self.overlay_var.get(),
            "motion_blur": self.motion_blur_var.get(),
            "theme": self.theme_var.get(),
            "scale": self.scale_var.get(),
            "gaming_mode": self.gaming_mode_var.get(),
            CUSTOM_SEARCH_FOLDERS_CONFIG_KEY: self.custom_search_folders
        }
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(config, f, indent=4)
            # Log para confirmar que se guardú
            print(f"[DEBUG] Config guardado - gaming_mode: {config['gaming_mode']}")
        except Exception as e:
            self.log_message('ERROR', f"Error al guardar la configuración: {e}")

    def on_closing(self):
        """Se ejecuta al cerrar la ventana."""
        # Log para debug
        gaming_state = self.gaming_mode_var.get()
        self.log_message('INFO', f"Cerrando app - Modo gaming: {gaming_state}")
        self.save_config()
        if PYGAME_AVAILABLE:
             pygame.quit()
        self.destroy()


    def on_theme_changed(self, value):
        """Callback para cambiar el tema de la aplicaciún."""
        theme_map = {"Claro": "light", "Oscuro": "dark", "Sistema": "system"}
        ctk.set_appearance_mode(theme_map.get(value, "dark"))
        self.theme_var.set(value)
        self.save_config()
        self.log_message('INFO', f"Tema cambiado a: {value}")

    def on_scale_changed(self, value):
        """Callback para cambiar la escala de la UI."""
        scale_map = {"80%": 0.8, "90%": 0.9, "100%": 1.0, "110%": 1.1, "120%": 1.2}
        ctk.set_widget_scaling(scale_map.get(value, 1.0))
        self.scale_var.set(value)
        self.save_config()
        self.log_message('INFO', f"Escala UI cambiada a: {value}")

    def toggle_gaming_mode(self):
        """Activa/desactiva el Modo Gaming compacto."""
        is_gaming = self.gaming_mode_var.get()
        new_state = not is_gaming
        self.gaming_mode_var.set(new_state)
        
        if new_state:
            # Activar modo gaming
            # Ocultar botones superiores (ayuda y gaming mode)
            if hasattr(self, 'btn_gaming_mode'):
                self.btn_gaming_mode.master.grid_remove()  # Oculta right_buttons_frame completo
            # Ocultar frame completo de botones superiores
            if hasattr(self, 'buttons_frame'):
                self.buttons_frame.grid_remove()
            # Ocultar interfaz normal y mostrar interfaz gaming
            self.notebook_frame.grid_remove()
            self.gaming_interface_frame.grid()
            # Poblar lista de juegos en modo gaming
            self.populate_gaming_games()
            # Inicializar navegación gaming
            self.gaming_focus_location = 'nav'
            self.gaming_nav_focused_index = 1  # Empezar en el botón "auto" (segundo botón)
            self.after(100, lambda: self.update_focus_visuals_gaming())
            self.log_message('OK', "?? Modo Gaming activado - Interfaz simplificada")
        else:
            # Desactivar modo gaming
            # Mostrar botones superiores (ayuda y gaming mode)
            if hasattr(self, 'btn_gaming_mode'):
                self.btn_gaming_mode.master.grid()  # Muestra right_buttons_frame completo
            # Mostrar frame completo de botones superiores
            if hasattr(self, 'buttons_frame'):
                self.buttons_frame.grid()
            # Ocultar interfaz gaming y mostrar interfaz normal
            self.gaming_interface_frame.grid_remove()
            self.notebook_frame.grid()
            self.log_message('INFO', "Modo Gaming desactivado - Interfaz completa restaurada")
        
        self.save_config()
    
    def populate_gaming_games(self):
        """Llena la lista de juegos en modo gaming."""
        # Limpiar lista actual
        for widget in self.gaming_games_scrollable.winfo_children():
            widget.destroy()
        
        # Limpiar diccionario de checkboxes
        self.gaming_game_checkboxes = {}
        
        if not self.all_games_data:
            ctk.CTkLabel(self.gaming_games_scrollable, text="No se encontraron juegos", 
                        font=ctk.CTkFont(size=14), text_color="gray").pack(pady=20)
            self.gaming_games_count_label.configure(text="0/0")
            return
        
        # Actualizar contador con formato X/Y
        total_games = len(self.all_games_data)
        self.gaming_games_count_label.configure(text=f"0/{total_games}")
        
        # Mostrar cada juego con checkbox y botones (con mejor contraste)
        for idx, (game_path, display_name, mod_status, exe_name, platform_tag) in enumerate(self.all_games_data):
            game_frame = ctk.CTkFrame(self.gaming_games_scrollable, fg_color="#1a1a1a", 
                                     border_width=2, border_color="#2a2a2a",
                                     corner_radius=8, height=80)
            game_frame.pack(fill='x', padx=10, pady=6)
            game_frame.grid_columnconfigure(2, weight=1)
            game_frame.pack_propagate(False)
            
            # Checkbox para selecciún con callback para actualizar contador
            var = ctk.BooleanVar(value=False)
            var.trace('w', lambda *args: self.update_gaming_selection_count())
            self.gaming_game_checkboxes[game_path] = var
            checkbox = ctk.CTkCheckBox(game_frame, text="", variable=var, width=30)
            checkbox.grid(row=0, column=0, rowspan=2, padx=(15,5), sticky='w')
            
            # Badge de estado mejorado
            if "INSTALADO" in mod_status or "usando" in mod_status:
                badge_text = "✓ APLICADO"
                badge_color = "#00AA00"
                badge_fg = "#003300"
            elif "AUSENTE" in mod_status or "No aplicado" in mod_status:
                badge_text = "❌ NO APLICADO"
                badge_color = "#CC0000"
                badge_fg = "#330000"
            else:
                badge_text = "❓ DESCONOCIDO"
                badge_color = "#888888"
                badge_fg = "#222222"
            
            badge = ctk.CTkLabel(game_frame, text=badge_text, font=ctk.CTkFont(size=11, weight="bold"),
                                text_color=badge_color, fg_color=badge_fg, corner_radius=4,
                                width=100, height=25)
            badge.grid(row=0, column=1, rowspan=2, padx=5, sticky='w')
            
            # Nombre del juego
            name_label = ctk.CTkLabel(game_frame, text=display_name.split(']')[-1].strip(), 
                                     font=ctk.CTkFont(size=14, weight="bold"), anchor='w')
            name_label.grid(row=0, column=2, sticky='w', padx=10, pady=(10,0))
            
            # Plataforma (Steam/Epic/etc)
            platform_text = platform_tag if platform_tag else "PC"
            platform_sub = ctk.CTkLabel(game_frame, text=platform_text, font=ctk.CTkFont(size=11), 
                                       text_color="gray", anchor='w')
            platform_sub.grid(row=1, column=2, sticky='w', padx=10, pady=(0,10))
            
            # Botones de acciún (optimizado para táctil: múnimo 44x44px)
            btn_frame = ctk.CTkFrame(game_frame, fg_color="transparent")
            btn_frame.grid(row=0, column=3, rowspan=2, padx=10)
            
            # Botón config individual (con feedback)
            def config_with_feedback(p, n, b):
                self.button_flash_feedback(b, "#3a3a3a", "#5a5a5a", 120)
                self.open_game_config(p, n)
            
            btn_config = ctk.CTkButton(btn_frame, text="⚙️", 
                                      command=lambda p=game_path, n=display_name, b=None: config_with_feedback(p, n, b or btn_config),
                                      width=58, height=58, font=ctk.CTkFont(size=26),
                                      fg_color="#3a3a3a", hover_color="#4a4a4a",
                                      border_width=2, border_color="#505050")
            btn_config.configure(command=lambda p=game_path, n=display_name, b=btn_config: config_with_feedback(p, n, b))
            btn_config.grid(row=0, column=0, padx=5)
            
            # Botón carpeta (con feedback)
            def folder_with_feedback(p, b):
                self.button_flash_feedback(b, "#3a3a3a", "#5a5a5a", 120)
                self.open_game_folder(p)
            
            btn_folder = ctk.CTkButton(btn_frame, text="📁",
                                      command=lambda p=game_path, b=None: folder_with_feedback(p, b or btn_folder),
                                      width=58, height=58, font=ctk.CTkFont(size=30),
                                      fg_color="#3a3a3a", hover_color="#4a4a4a",
                                      border_width=2, border_color="#505050")
            btn_folder.configure(command=lambda p=game_path, b=btn_folder: folder_with_feedback(p, b))
            btn_folder.grid(row=0, column=1, padx=5)
            
            # Botón lanzar juego (con feedback)
            if exe_name:
                def launch_with_feedback(p, e, b):
                    self.button_flash_feedback(b, "#3a3a3a", "#5a5a5a", 120)
                    self.launch_game(p, e)
                
                btn_launch = ctk.CTkButton(btn_frame, text="🚀", 
                                          command=lambda p=game_path, e=exe_name, b=None: launch_with_feedback(p, e, b or btn_launch),
                                          fg_color="#3a3a3a", hover_color="#4a4a4a",
                                          width=58, height=58, font=ctk.CTkFont(size=30),
                                          border_width=2, border_color="#505050")
                btn_launch.configure(command=lambda p=game_path, e=exe_name, b=btn_launch: launch_with_feedback(p, e, b))
                btn_launch.grid(row=0, column=2, padx=5)
    
    def update_gaming_selection_count(self):
        """Actualiza el contador de juegos seleccionados/total."""
        if not hasattr(self, 'gaming_game_checkboxes') or not hasattr(self, 'all_games_data'):
            return
        
        selected_count = sum(1 for var in self.gaming_game_checkboxes.values() if var.get())
        total_count = len(self.all_games_data)
        self.gaming_games_count_label.configure(text=f"{selected_count}/{total_count}")
    
    def quick_apply_mod(self, game_path, game_name):
        """Aplica el mod rúpidamenóte sin abrir ventana de configuración."""
        if not self.mod_source_dir.get():
            self.log_message('ERROR', "Primero selecciona una versión del mod")
            return
        
        # Verificar mod source
        source_dir, source_ok = check_mod_source_files(self.mod_source_dir.get(), self.log_message)
        if not source_ok:
            self.log_message('ERROR', "Mod source no vúlido")
            return
        
        # Usar configuración actual para aplicar
        self.log_message('INFO', f"Aplicando mod a: {game_name.split(']')[-1].strip()}")
        inject_fsr_mod(
            source_dir, game_path, self.log_message,
            spoof_dll_name=self.spoof_dll_name_var.get(),
            gpu_choice=self.gpu_choice.get(),
            fg_mode_selected=self.fg_mode_var.get(),
            upscaler_selected=self.upscaler_var.get(),
            upscale_mode_selected=self.upscale_mode_var.get(),
            sharpness_selected=self.sharpness_var.get(),
            overlay_selected=self.overlay_var.get(),
            mb_selected=self.motion_blur_var.get()
        )
        # Refrescar lista para actualizar estado
        self.after(100, self.populate_gaming_games)

    def gaming_apply_to_selected(self):
        """Aplica el mod a todos los juegos seleccionados en modo gaming."""
        if not self.mod_source_dir.get():
            from tkinter import messagebox
            response = messagebox.askyesno(
                "Mod no seleccionado", 
                "No has seleccionado ninguna versión del mod.\n\n¿Deseas ir a la gestión de mods ahora?",
                parent=self
            )
            if response:
                self.show_gaming_settings()
            return
        
        # Verificar mod source
        source_dir, source_ok = check_mod_source_files(self.mod_source_dir.get(), self.log_message)
        if not source_ok:
            from tkinter import messagebox
            messagebox.showerror(
                "Mod no válido",
                "La carpeta del mod seleccionada no contiene archivos vúlidos.\n\nPor favor, descarga o selecciona una versión correcta del mod.",
                parent=self
            )
            return
        
        # Obtener juegos seleccionados
        selected_games = [(path, name) for (path, name, _, _, _) in self.all_games_data 
                         if self.gaming_game_checkboxes.get(path, ctk.BooleanVar()).get()]
        
        if not selected_games:
            from tkinter import messagebox
            messagebox.showwarning("Sin selección", "No hay juegos seleccionados.", parent=self)
            return
        
        self.log_message('TITLE', f"Aplicando mod a {len(selected_games)} juego(s)...")
        
        success_count = 0
        error_count = 0
        
        for game_path, display_name in selected_games:
            game_name = display_name.split(']')[-1].strip()
            self.log_message('INFO', f"? {game_name}")
            result = inject_fsr_mod(
                source_dir, game_path, self.log_message,
                spoof_dll_name=self.spoof_dll_name_var.get(),
                gpu_choice=self.gpu_choice.get(),
                fg_mode_selected=self.fg_mode_var.get(),
                upscaler_selected=self.upscaler_var.get(),
                upscale_mode_selected=self.upscale_mode_var.get(),
                sharpness_selected=self.sharpness_var.get(),
                overlay_selected=self.overlay_var.get(),
                mb_selected=self.motion_blur_var.get()
            )
            if result:
                self.log_message('OK', f"  ? {game_name} - Mod aplicado correctamente")
                success_count += 1
            else:
                self.log_message('ERROR', f"  ? {game_name} - Error al aplicar mod")
                error_count += 1
        
        self.log_message('OK', f"Proceso completado: {success_count} Éxito, {error_count} errores")
        
        # Mostrar menósaje resumenó
        from tkinter import messagebox
        if error_count == 0:
            messagebox.showinfo(
                "Instalación Completada",
                f"✓ Mod aplicado correctamente a {success_count} juego(s).",
                parent=self
            )
        else:
            messagebox.showwarning(
                "Instalación Completada con Errores",
                f"✓ Mod aplicado: {success_count} juego(s)\n✗ Errores: {error_count} juego(s)\n\nRevisa el log para más detalles.",
                parent=self
            )
        
        # Refrescar lista para actualizar estados (reescanea y actualiza)
        # Añadir delay para asegurar que los archivos se escriben completamente
        self.after(500, self._refresh_game_list_after_operation)

    def gaming_remove_from_selected(self):
        """Desinstala el mod de todos los juegos seleccionados en modo gaming."""
        # Obtener juegos seleccionados
        selected_games = [(path, name) for (path, name, _, _, _) in self.all_games_data 
                         if self.gaming_game_checkboxes.get(path, ctk.BooleanVar()).get()]
        
        if not selected_games:
            from tkinter import messagebox
            messagebox.showwarning("Sin selección", "No hay juegos seleccionados.", parent=self)
            return
        
        self.log_message('TITLE', f"Desinstalando mod de {len(selected_games)} juego(s)...")
        
        success_count = 0
        error_count = 0
        
        for game_path, display_name in selected_games:
            game_name = display_name.split(']')[-1].strip()
            self.log_message('INFO', f"? {game_name}")
            result = uninstall_fsr_mod(game_path, self.log_message)
            if result:
                self.log_message('OK', f"  ? {game_name} - Mod desinstalado correctamente")
                success_count += 1
            else:
                self.log_message('ERROR', f"  ? {game_name} - Error al desinstalar mod")
                error_count += 1
        
        self.log_message('OK', f"Proceso completado: {success_count} Éxito, {error_count} errores")
        
        # Mostrar menósaje resumenó
        from tkinter import messagebox
        if error_count == 0:
            messagebox.showinfo(
                "Desinstalaciún Completada",
                f"✓ Mod eliminado correctamente de {success_count} juego(s).",
                parent=self
            )
        else:
            messagebox.showwarning(
                "Desinstalaciún Completada con Errores",
                f"✓ Mod eliminado: {success_count} juego(s)\n✗ Errores: {error_count} juego(s)\n\nRevisa el log para más detalles.",
                parent=self
            )
        
        # Refrescar lista para actualizar estados (reescanea y actualiza)
        # Añadir delay para asegurar que los archivos se eliminan completamente
        self.after(500, self._refresh_game_list_after_operation)

    def open_game_config(self, game_path, game_name):
        """Abre la ventana de configuración individual para un juego."""
        # Usar la ventana existente de configuración individual
        self.open_game_config_window(game_path, game_name)

    def on_preset_selected(self, choice):
        """Maneja la selecciún de preset desde el dropdown."""
        if choice == "Custom":
            return  # No hacer nada si selecciona Custom manualmente
        self.apply_preset(choice.lower())
    
    def apply_preset(self, preset_name, update_combo=True):
        """
        Aplica un preset de configuración rúpida.
        
        Args:
            preset_name: "default", "performance", "balanced", o "quality"
            update_combo: Si debe actualizar el combo de presets
        """
        presets = {
            "default": {
                "upscaler": "Automático",
                "fg_mode": "Automático",
                "upscale_mode": "Automático",
                "sharpness": 0.8,
                "description": "Configuración automática (recomendado)"
            },
            "performance": {
                "upscaler": "FSR 3.1",
                "fg_mode": "Activado",
                "upscale_mode": "Rendimiento",
                "sharpness": 0.5,
                "description": "Máximo FPS para baterúa"
            },
            "balanced": {
                "upscaler": "FSR 3.1",
                "fg_mode": "Automático",
                "upscale_mode": "Equilibrado",
                "sharpness": 0.7,
                "description": "Balance entre calidad y rendimiento"
            },
            "quality": {
                "upscaler": "FSR 3.1",
                "fg_mode": "Activado",
                "upscale_mode": "Calidad",
                "sharpness": 0.9,
                "description": "Máxima calidad cuando enchufado"
            }
        }
        
        if preset_name not in presets:
            return
        
        preset = presets[preset_name]
        
        # Bloquear callbacks temporalmenóte
        self._applying_preset = True
        
        # Aplicar configuración a las variables
        self.upscaler_var.set(preset["upscaler"])
        self.fg_mode_var.set(preset["fg_mode"])
        self.upscale_mode_var.set(preset["upscale_mode"])
        self.sharpness_var.set(preset["sharpness"])
        self.sharpness_label_var.set(f"{preset['sharpness']:.2f}")
        
        # Actualizar los textos de los botones (interfaz clásica)
        if hasattr(self, 'btn_upscaler_select'):
            self.btn_upscaler_select.configure(text=f"{preset['upscaler']} ⬇️")
        if hasattr(self, 'btn_fg_select'):
            self.btn_fg_select.configure(text=f"{preset['fg_mode']} ⬇️")
        if hasattr(self, 'btn_upscale_select'):
            self.btn_upscale_select.configure(text=f"{preset['upscale_mode']} ⬇️")
        
        # Actualizar combo a nombre del preset
        if update_combo and hasattr(self, 'preset_combo'):
            self.preset_combo.set(preset_name.capitalize())
        
        # Desbloquear callbacks
        self._applying_preset = False
        
        # Guardar
        self.save_config()
        
        # mensaje visual
        self.log_message('OK', f"✅ Preset '{preset_name.upper()}' aplicado: {preset['description']}")
    
    def mark_config_as_custom(self):
        """Marca la configuración como Custom cuando el usuario hace cambios manuales."""
        if hasattr(self, '_applying_preset') and self._applying_preset:
            return  # No cambiar a Custom si estamos aplicando un preset
        if hasattr(self, 'preset_combo'):
            self.preset_combo.set("Custom")
        # Actualizar tambiún en gaming mode
        if hasattr(self, 'gaming_active_preset_label'):
            self.update_gaming_preset_indicator("custom")
    
    def apply_preset_gaming(self, preset_name):
        """
        Aplica un preset en el modo gaming con indicadores visuales.
        
        Args:
            preset_name: "default", "performance", "balanced", "quality"
        """
        presets = {
            "default": {
                "upscaler": "Automático",
                "fg_mode": "Automático",
                "upscale_mode": "Automático",
                "sharpness": 0.8,
                "description": "?? Automático",
                "color": "#00AA00"
            },
            "performance": {
                "upscaler": "FSR 3.1",
                "fg_mode": "FSR 3.1",
                "upscale_mode": "Rendimiento",
                "sharpness": 0.5,
                "description": "?? Máximo FPS",
                "color": "#FF6B00"
            },
            "balanced": {
                "upscaler": "FSR 3.1",
                "fg_mode": "Automático",
                "upscale_mode": "Equilibrado",
                "sharpness": 0.7,
                "description": "?? Balance",
                "color": "#0088FF"
            },
            "quality": {
                "upscaler": "FSR 3.1",
                "fg_mode": "FSR 3.1",
                "upscale_mode": "Calidad",
                "sharpness": 0.9,
                "description": "? Máxima calidad",
                "color": "#9333EA"
            }
        }
        
        if preset_name not in presets:
            return
        
        preset = presets[preset_name]
        
        # Bloquear callbacks temporalmenóte
        self._applying_preset = True
        
        # Aplicar configuración
        self.upscaler_var.set(preset["upscaler"])
        self.fg_mode_var.set(preset["fg_mode"])
        self.upscale_mode_var.set(preset["upscale_mode"])
        self.sharpness_var.set(preset["sharpness"])
        self.sharpness_label_var.set(f"{preset['sharpness']:.2f}")
        
        # Actualizar indicadores visuales
        self.update_gaming_preset_indicator(preset_name)
        
        # Desbloquear callbacks
        self._applying_preset = False
        
        # Guardar
        self.save_config()
        
        # menósaje
        self.log_message('OK', f"? Preset aplicado: {preset['description']}")
    
    def update_gaming_preset_indicator(self, preset_name):
        """Actualiza los indicadores visuales del preset activo en gaming mode."""
        if not hasattr(self, 'gaming_preset_buttons'):
            return
        
        # Colores para cada preset
        colors = {
            "default": "#00AA00",
            "performance": "#FF6B00",
            "balanced": "#0088FF",
            "quality": "#9333EA",
            "custom": "#888888"
        }
        
        # Etiquetas para mostrar
        labels = {
            "default": "• Default",
            "performance": "• Performance",
            "balanced": "• Balanced",
            "quality": "• Quality",
            "custom": "• Custom"
        }
        
        # Resetear todos los botones a estado normal
        for btn in self.gaming_preset_buttons.values():
            btn.configure(fg_color="#3a3a3a", border_color="#505050", border_width=2)
        
        # Marcar el activo con borde de color
        if preset_name in self.gaming_preset_buttons:
            self.gaming_preset_buttons[preset_name].configure(
                border_color=colors.get(preset_name, "#888888"),
                border_width=3
            )
        
        # Actualizar label del header
        if hasattr(self, 'gaming_active_preset_label'):
            self.gaming_active_preset_label.configure(
                text=labels.get(preset_name, "? Custom"),
                text_color=colors.get(preset_name, "#888888")
            )

    def gaming_browse_manual_path(self):
        """Abre diúlogo para seleccionar carpeta manualmente."""
        folder = filedialog.askdirectory(title="Selecciona la carpeta del juego")
        if folder:
            self.manual_path_var.set(folder)
            # Verificar si el mod ya estú aplicado
            mod_status = check_mod_status(folder)
            if "?" in mod_status:
                self.manual_status_var.set("✓ Mod ya aplicado")
                self.manual_status_label.configure(text_color="#00FF00")
                self.manual_apply_btn.configure(state='disabled')
                self.manual_uninstall_btn.configure(state='normal')
            else:
                self.manual_status_var.set("❌ Mod no aplicado")
                self.manual_status_label.configure(text_color="#FFAA00")
                self.manual_apply_btn.configure(state='normal')
                self.manual_uninstall_btn.configure(state='disabled')
    
    def gaming_apply_manual_mod(self):
        """Aplica el mod a la ruta manual seleccionada."""
        path = self.manual_path_var.get()
        if path == "Ninguna carpeta seleccionada":
            return
        
        # Usar la funciún existente de aplicar mod
        game_name = os.path.basename(path)
        success = self.apply_mod_to_game(path, game_name)
        
        if success:
            self.manual_status_var.set("✓ Mod aplicado correctamente")
            self.manual_status_label.configure(text_color="#00FF00")
            self.manual_apply_btn.configure(state='disabled')
            self.manual_uninstall_btn.configure(state='normal')
            self.log_message('OK', f"Mod aplicado manualmente a: {game_name}")
            # Refrescar lista gaming si estú activa
            self._refresh_game_list_after_operation()
        else:
            self.manual_status_var.set("? Error al aplicar mod")
            self.manual_status_label.configure(text_color="#FF0000")
    
    def gaming_uninstall_manual_mod(self):
        """Elimina el mod de la ruta manual seleccionada."""
        path = self.manual_path_var.get()
        if path == "Ninguna carpeta seleccionada":
            return
        
        game_name = os.path.basename(path)
        
        # Confirmar acciún
        from tkinter import messagebox
        if not messagebox.askyesno("Confirmar", 
                                   f"úDeseas eliminar el mod de:\n{game_name}?",
                                   parent=self):
            return
        
        # Eliminar usando la funciún existente
        success = self.remove_mod_from_game(path, game_name)
        
        if success:
            self.manual_status_var.set("✓ Mod eliminado correctamente")
            self.manual_status_label.configure(text_color="#00FF00")
            self.manual_apply_btn.configure(state='normal')
            self.manual_uninstall_btn.configure(state='disabled')
            self.log_message('OK', f"Mod eliminado manualmente de: {game_name}")
            # Refrescar lista gaming si estú activa
            self._refresh_game_list_after_operation()
        else:
            self.manual_status_var.set("? Error al eliminar mod")
            self.manual_status_label.configure(text_color="#FF0000")

    def button_flash_feedback(self, button, original_color="#2b2b2b", flash_color="#4b4b4b", duration=150):
        """
        Proporciona feedback visual al pulsar un botón (Útil para pantallas táctiles).
        
        Args:
            button: El botón CTkButton
            original_color: Color normal del botón
            flash_color: Color durante el flash
            duration: Duraciún del flash en ms
        """
        button.configure(fg_color=flash_color)
        self.after(duration, lambda: button.configure(fg_color=original_color))

    def open_scan_folders_manager(self):
        """Abre ventana para gestionar carpetas de escaneo de juegos."""
        ScanFoldersWindow(self, self.log_message, self.refresh_detected_games)
    
    # --- NUEVO (V2.1 Performance): Escaneo Manual con Barra de Progreso ---
    def start_game_scan(self):
        """Inicia el escaneo de juegos en un thread separado con diúlogo de progreso."""
        # Crear ventana de progreso
        progress_window = ctk.CTkToplevel(self)
        progress_window.title("Escaneando Juegos...")
        progress_window.geometry("500x150")
        progress_window.resizable(False, False)
        progress_window.transient(self)
        progress_window.grab_set()
        
        # Centrar ventana
        progress_window.update_idletasks()
        x = (progress_window.winfo_screenwidth() // 2) - (500 // 2)
        y = (progress_window.winfo_screenheight() // 2) - (150 // 2)
        progress_window.geometry(f"500x150+{x}+{y}")
        
        # Label de estado
        status_label = ctk.CTkLabel(
            progress_window, 
            text="Iniciando escaneo...",
            font=ctk.CTkFont(size=14)
        )
        status_label.pack(pady=(20, 10))
        
        # Barra de progreso
        progress_bar = ctk.CTkProgressBar(progress_window, width=450)
        progress_bar.set(0)
        progress_bar.pack(pady=10)
        
        # Label de porcentaje
        percent_label = ctk.CTkLabel(
            progress_window,
            text="0%",
            font=ctk.CTkFont(size=12)
        )
        percent_label.pack(pady=5)
        
        # Variable para almacenar resultado
        scan_result = {'games': []}
        
        def update_progress(message, percent):
            """Actualiza la UI desde el thread."""
            status_label.configure(text=message)
            progress_bar.set(percent / 100.0)
            percent_label.configure(text=f"{percent}%")
        
        def scan_thread():
            """Ejecuta el escaneo en segundo plano."""
            try:
                # Simulamos progreso durante el escaneo
                self.after(0, lambda: update_progress("Escaneando Xbox...", 10))
                
                # Realizar escaneo real
                games = scan_games(self.log_message, self.custom_search_folders)
                scan_result['games'] = games
                
                self.after(0, lambda: update_progress("Escaneo completado", 100))
                
                # Esperar un momenóto para que se vea el 100%
                import time
                time.sleep(0.3)
                
                # Cerrar ventana y actualizar datos
                self.after(0, lambda: finish_scan(progress_window, games))
                
            except Exception as e:
                self.after(0, lambda: self.log_message('ERROR', f"Error en escaneo: {e}"))
                self.after(0, lambda: progress_window.destroy())
        
        def finish_scan(window, games):
            """Finaliza el escaneo y actualiza la interfaz."""
            window.destroy()
            
            # Actualizar datos
            self.all_games_data = games
            self.filtered_game_indices = list(range(len(self.all_games_data)))
            
            # Guardar cachéú
            save_games_caché(games, self.log_message)
            
            # Actualizar label de cachéú
            self.update_caché_info_label()
            
            # Actualizar listas visuales
            self.load_game_list()
            
            # Actualizar gaming si estú activo
            if hasattr(self, 'gaming_mode_var') and self.gaming_mode_var.get() and hasattr(self, 'gaming_games_scrollable'):
                self.populate_gaming_games()
            
            self.log_message('OK', f"? Escaneo completado: {len(games)} juegos encontrados")
        
        # Iniciar thread de escaneo
        scan_thread_obj = threading.Thread(target=scan_thread, daemon=True)
        scan_thread_obj.start()
    
    def refresh_detected_games(self):
        """Refresca la lista de juegos detectados después de cambios en carpetas."""
        self.log_message('INFO', "Actualizando lista de juegos...")
        self.all_games_data = scan_games(self.log_message, self.custom_search_folders)
        
        # Guardar cachéú actualizada
        save_games_caché(self.all_games_data, self.log_message)
        
        # Actualizar listbox en pestaña automática si estú visible
        if hasattr(self, 'games_listbox'):
            self.populate_games_listbox()
        
        # Actualizar lista gaming si estú en modo gaming
        if hasattr(self, 'gaming_mode_var') and self.gaming_mode_var.get() and hasattr(self, 'gaming_games_scrollable'):
            self.populate_gaming_games()
        
        self.log_message('OK', f"Lista actualizada: {len(self.all_games_data)} juegos encontrados")


    # --- Funciones de Log y Ayuda ---

    def log_message(self, message_type, message):
        """Muestra un menósaje con color en el úrea de log."""
        tag_config = {
            'INFO': ('#00FF00', '[INFO] '),  'WARN': ('#FFFF00', '[WARN] '),
            'ERROR': ('#FF4500', '[ERROR] '), 'TITLE': ('#00BFFF', '[OP] '),
            'OK': ('#00FF00', '[OK] ')
        }
        color, prefix = tag_config.get(message_type, ('white', ''))

        if hasattr(self, 'log_text'):
            self.log_text.configure(state="normal")
            self.log_text.insert("end", prefix, message_type)
            self.log_text.tag_config(message_type, foreground=color)
            self.log_text.insert("end", f"{message}\n")
            
            # --- NUEVO (V2.0 Mejora C): Auto-scroll condicional ---
            if self.log_auto_scroll_var.get():
                self.log_text.see("end")
                
            self.log_text.configure(state="disabled")
        else:
             print(f"{prefix}{message}")


    def show_recommended_settings(self):
        """Muestra la configuración recomenódada en el log al inicio."""
        check_registry_override(self.log_message)
        gpu_type = "NVIDIA (Detectado)" if self.gpu_choice.get() == 2 else "AMD/Intel (Detectado o por Defecto)"
        spoof_name = self.spoof_dll_name_var.get()
        self.log_message('INFO', "--------------------------------------------------")
        self.log_message('INFO', "AJUSTES RECOMENDADOS CARGADOS:")
        self.log_message('INFO', f"GPU: {gpu_type}")
        self.log_message('INFO', f"DLL de Inyecciún: {spoof_name}")
        self.log_message('INFO', f"Modo Frame Gen: {self.fg_mode_var.get()}")
        self.log_message('INFO', "--------------------------------------------------")

    # --- MODIFICADO (Mejora Mando): Registra popups ---
    def show_help_popup(self, title, message_text):
        """Muestra una ventana emergente (Toplevel) con texto de ayuda."""
        # --- MODIFICADO (V2.0 Pulida): Comprobaciún de Tooltip eliminada ---
        if self.active_popup: 
            try: self.active_popup.focus_force()
            except: self.on_popup_closed() # Limpiar popup muerto
            return
            
        try:
            help_window = ctk.CTkToplevel(self)
            help_window.title(title)
            
            win_width = 750
            win_height = 550
            x = self.winfo_x() + (self.winfo_width() // 2) - (win_width // 2)
            y = self.winfo_y() + (self.winfo_height() // 2) - (win_height // 2)
            help_window.geometry(f'{win_width}x{win_height}+{x}+{y}')
            
            help_window.transient(self) # Mantener por encima
            help_window.grab_set() # Modal
            
            # --- Registrar popup ---
            self.active_popup = help_window
            help_window.bind("<Destroy>", self.on_popup_closed)
            
            help_text_widget = ctk.CTkTextbox(help_window, wrap="word", corner_radius=8, font=ctk.CTkFont(size=12))
            help_text_widget.pack(fill='both', expand=True, padx=15, pady=15)
            help_text_widget.insert("end", message_text)
            help_text_widget.configure(state="disabled")
            
            close_btn = ctk.CTkButton(help_window, text="Cerrar (B / Esc)", command=help_window.destroy, fg_color="#3a3a3a", hover_color="#4a4a4a")
            close_btn.pack(pady=(0, 10))
            
            # --- NUEVO (Mejora 10): Binding de Teclado ---
            help_window.bind("<Escape>", lambda e: help_window.destroy())
            
            help_window.after(100, help_window.focus_force) # Forzar foco a la ventana
            
        except Exception as e:
            self.log_message('ERROR', f"No se pudo abrir la ventana de ayuda: {e}")
            if self.active_popup: self.active_popup = None # Reset
            
    # --- NUEVA FUNCIúN (Mejora Mando): Des-registra popups ---
    def on_popup_closed(self, event=None):
        """Se llama cuando una ventana emergente se cierra para des-registrarla."""
        # --- MODIFICADO (V2.0 Pulida): Comprobaciún de Tooltip eliminada ---

        # Solo des-registrar si la ventana que se cierra es la que tenúamos registrada
        if self.active_popup and event and str(event.widget).startswith(str(self.active_popup)):
             self.active_popup = None
        elif not event: # Limpieza forzada
             self.active_popup = None
        elif self.active_popup and not hasattr(self.active_popup, 'winfo_exists'):
            self.active_popup = None # Limpieza de popups muertos

    def update_sharpness_label_and_save(self, value):
        """Actualiza la etiqueta de nitidez y guarda la configuración."""
        self.sharpness_label_var.set(f"{value:.2f}")
        self.mark_config_as_custom()  # Marcar como Custom al cambiar
        self.save_config()

    # ==============================================================================
    # 5. Interfaz Grúfica (GUI) - V2.0
    # ==============================================================================

    # --- Creaciún de Widgets (V2.0 Refactor) ---

    def create_widgets(self):
        main_frame = ctk.CTkFrame(self, corner_radius=10)
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        main_frame.grid_columnconfigure(0, weight=1)
        row_counter = 0

        # --- TúTULO V2.0 y Botón de Ayuda ---
        title_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        title_frame.grid(row=row_counter, column=0, pady=(10, 5), sticky='ew')
        
        # --- MODIFICADO (V2.0 Pulida): Tútulo centrado (Lúgica de 3 columnas) ---
        title_frame.grid_columnconfigure(0, weight=1) # Espaciador izquierdo
        title_frame.grid_columnconfigure(1, weight=0) # Columna del tútulo (no se estira)
        title_frame.grid_columnconfigure(2, weight=1) # Espaciador/Botón derecho
        
        self.main_title = ctk.CTkLabel(title_frame, text="GESTOR AUTOMATIZADO DE OPTISCALER V2.0", text_color="#00BFFF", font=ctk.CTkFont(size=20, weight="bold"))
        self.main_title.grid(row=0, column=1, sticky='ew') # Columna central
        
        # --- Botones esquina superior derecha ---
        right_buttons_frame = ctk.CTkFrame(title_frame, fg_color="transparent")
        right_buttons_frame.grid(row=0, column=2, sticky='e')
        
        # Botón de ayuda
        self.btn_help = ctk.CTkButton(right_buttons_frame, text="❓", 
                                      command=lambda: self.show_help_popup("Guía Rápida del Gestor", APP_HELP_TEXT), 
                                      width=50, height=50, corner_radius=8, 
                                      fg_color="#3a3a3a", hover_color="#4a4a4a",
                                      font=ctk.CTkFont(size=28, weight="bold"))
        self.btn_help.pack(side='left', padx=(0, 5))
        
        # Botón gaming mode
        self.btn_gaming_mode = ctk.CTkButton(right_buttons_frame, text="🎮", 
                                             command=self.toggle_gaming_mode, 
                                             width=50, height=50, corner_radius=8, 
                                             fg_color="#3a3a3a", hover_color="#4a4a4a", 
                                             font=ctk.CTkFont(size=28))
        self.btn_gaming_mode.pack(side='left', padx=5)
        
        row_counter += 1
        
        # --- Botones superiores (solo en interfaz normal) ---
        self.buttons_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        self.buttons_frame.grid(row=row_counter, column=0, pady=(0, 10), sticky='ew')
        self.buttons_frame.grid_columnconfigure(1, weight=1)  # El desplegable se expande
        
        self.btn_download = ctk.CTkButton(self.buttons_frame, text="⬇️ Descargar / Gestionar Mod", command=self.open_mod_downloader, width=220, corner_radius=8, fg_color="#3a3a3a", hover_color="#4a4a4a", font=ctk.CTkFont(size=13, weight="bold"))
        self.btn_download.grid(row=0, column=0, sticky='w', padx=5)
        
        # Desplegable de versión del mod (sin texto, ancho disponible)
        self.mod_version_combo = ctk.CTkComboBox(self.buttons_frame, variable=self.mod_version_list, 
                                                 command=self.on_mod_version_selected,
                                                 font=ctk.CTkFont(size=12))
        self.mod_version_combo.grid(row=0, column=1, sticky='ew', padx=10)
        
        self.btn_select_manual = ctk.CTkButton(self.buttons_frame, text="📁", command=self.select_mod_dir_manual,
                                               width=50, height=40, corner_radius=8, font=ctk.CTkFont(size=24), 
                                               fg_color="#3a3a3a", hover_color="#4a4a4a")
        self.btn_select_manual.grid(row=0, column=2, sticky='e', padx=5)
        
        self.global_navigable_widgets = [self.btn_download, self.mod_version_combo, self.btn_select_manual]
        
        row_counter += 1

        # --- NUEVO (V2.1 Handheld): Guardar referencia al main_frame para alternar interfaces ---
        self.main_content_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        self.main_content_frame.grid(row=row_counter, column=0, sticky='ewns', pady=15)
        row_counter += 1
        main_frame.grid_rowconfigure(row_counter - 1, weight=1)
        
        # Crear ambas interfaces: Normal (notebook) y Gaming (simplificada)
        self.create_normal_interface()
        self.create_gaming_interface()
        
        # Mostrar interfaz normal por defecto
        self.gaming_interface_frame.grid_remove()  # Ocultar gaming
        
    def create_normal_interface(self):
        """Crea la interfaz normal con pestañas."""
        # Notebook (Pestañas)
        notebook_frame = ctk.CTkFrame(self.main_content_frame, fg_color="transparent")
        notebook_frame.grid(row=0, column=0, sticky='ewns')
        self.main_content_frame.grid_columnconfigure(0, weight=1)
        self.main_content_frame.grid_rowconfigure(0, weight=1)
        notebook_frame.grid_columnconfigure(1, weight=1)
        notebook_frame.grid_rowconfigure(0, weight=1)
        
        self.notebook_frame = notebook_frame  # Guardar referencia
        notebook_frame.grid_rowconfigure(0, weight=1)
        
        ctk.CTkLabel(notebook_frame, text="LB", font=ctk.CTkFont(size=14, weight="bold"), text_color="#FFFFFF", fg_color="#333333", corner_radius=6).grid(row=0, column=0, sticky='n', padx=10, pady=(10, 0))
        self.notebook = ctk.CTkTabview(notebook_frame, corner_radius=10, border_width=2)
        self.notebook.grid(row=0, column=1, sticky='ewns')
        ctk.CTkLabel(notebook_frame, text="RB", font=ctk.CTkFont(size=14, weight="bold"), text_color="#FFFFFF", fg_color="#333333", corner_radius=6).grid(row=0, column=2, sticky='n', padx=10, pady=(10, 0))

        # --- MODIFICADO: 5 Pestañas ---
        config_tab = self.notebook.add(self.tab_names[0])
        auto_tab = self.notebook.add(self.tab_names[1])
        manual_tab = self.notebook.add(self.tab_names[2])
        app_config_tab = self.notebook.add(self.tab_names[3]) # NUEVA Pestaña 4
        log_tab = self.notebook.add(self.tab_names[4])        # Pestaña 5

        config_tab.configure(fg_color="transparent")
        auto_tab.configure(fg_color="transparent")
        manual_tab.configure(fg_color="transparent")
        app_config_tab.configure(fg_color="transparent")
        log_tab.configure(fg_color="transparent")

        auto_tab.grid_columnconfigure(0, weight=1)
        auto_tab.grid_rowconfigure(2, weight=1) # Fila 2 (lista de juegos) se estira
        config_tab.grid_columnconfigure(0, weight=1)
        manual_tab.grid_columnconfigure(0, weight=1)
        app_config_tab.grid_columnconfigure(0, weight=1)
        app_config_tab.grid_rowconfigure(0, weight=1) # Frame de carpetas
        app_config_tab.grid_rowconfigure(1, weight=0) # Frame de limpieza
        log_tab.grid_columnconfigure(0, weight=1)
        log_tab.grid_rowconfigure(0, weight=1)

        # --- PESTAÑA 1: CONFIGURACIÓN (REFACTORIZADA CON GRID) ---
        
        # Frame para las opciones globales (Arriba)
        config_global_frame = ctk.CTkFrame(config_tab, fg_color="transparent")
        config_global_frame.grid(row=0, column=0, sticky='new', padx=5, pady=5)
        config_global_frame.grid_columnconfigure(2, weight=1) 
        
        current_config_row = 0
        help_btn_size = 28 # Tamaño para botones '?'
        
        # --- Fila PRESETS (NUEVA - Primera opción) ---
        ctk.CTkLabel(config_global_frame, text="Preset Rápido:", font=ctk.CTkFont(size=12, weight="bold")).grid(row=current_config_row, column=0, sticky='w', padx=(15, 5))
        btn_preset_help = ctk.CTkButton(config_global_frame, text="?", width=help_btn_size, fg_color="#3a3a3a", hover_color="#4a4a4a", height=help_btn_size, 
                                       command=lambda: self.show_help_popup("Ayuda: Presets Rápidos", 
                                       "PRESETS RÁPIDOS:\n\n"
                                       "⚡ Performance: Configuración optimizada para máximo rendimiento\n"
                                       "   - Upscaler: FSR 3.1\n"
                                       "   - Frame Gen: Activado\n"
                                       "   - Upscale Mode: Rendimiento\n"
                                       "   - Sharpness: 0.5\n\n"
                                       "⚖️ Balanced: Equilibrio entre calidad y rendimiento\n"
                                       "   - Upscaler: FSR 3.1\n"
                                       "   - Frame Gen: Automático\n"
                                       "   - Upscale Mode: Equilibrado\n"
                                       "   - Sharpness: 0.7\n\n"
                                       "💎 Quality: Máxima calidad visual\n"
                                       "   - Upscaler: FSR 3.1\n"
                                       "   - Frame Gen: Activado\n"
                                       "   - Upscale Mode: Calidad\n"
                                       "   - Sharpness: 0.9\n\n"
                                       "🔧 Custom: Configuración personalizada\n"
                                       "   Se selecciona automáticamente cuando modificas cualquier opción manualmente.\n\n"
                                       "Estos presets aplican automáticamente todas las configuraciones necesarias."))
        btn_preset_help.grid(row=current_config_row, column=1, sticky='w', padx=5)
        
        self.preset_combo = ctk.CTkComboBox(config_global_frame, 
                                       values=["Default", "Performance", "Balanced", "Quality", "Custom"],
                                       command=lambda choice: self.on_preset_selected(choice),
                                       width=200)
        self.preset_combo.grid(row=current_config_row, column=2, sticky='w', pady=5, padx=5)
        self.preset_combo.set("Custom")  # Por defecto Custom
        current_config_row += 1
        
        # --- Fila GPU ---
        ctk.CTkLabel(config_global_frame, text="Tipo de GPU (Global):", font=ctk.CTkFont(size=12, weight="bold")).grid(row=current_config_row, column=0, sticky='w', padx=(15, 5))
        btn_gpu_help = ctk.CTkButton(config_global_frame, text="?", width=help_btn_size, height=help_btn_size, fg_color="#3a3a3a", hover_color="#4a4a4a", command=lambda: self.show_help_popup("Ayuda: Tipo de GPU", GPU_HELP_TEXT))
        btn_gpu_help.grid(row=current_config_row, column=1, sticky='w', padx=5)
        
        gpu_frame = ctk.CTkFrame(config_global_frame, fg_color="transparent")
        gpu_frame.grid(row=current_config_row, column=2, sticky='w', pady=5, padx=5)
        self.r_gpu_amd = ctk.CTkRadioButton(gpu_frame, text="AMD / Intel", variable=self.gpu_choice, value=1, command=self.save_config)
        self.r_gpu_amd.pack(side='left', padx=10)
        self.r_gpu_nvidia = ctk.CTkRadioButton(gpu_frame, text="NVIDIA", variable=self.gpu_choice, value=2, command=self.save_config)
        self.r_gpu_nvidia.pack(side='left', padx=10)
        current_config_row += 1

        # --- Fila DLL (REFACTORIZADA - Mejora 6) ---
        ctk.CTkLabel(config_global_frame, text="DLL de Inyecciún (Global):", font=ctk.CTkFont(size=12, weight="bold")).grid(row=current_config_row, column=0, sticky='w', padx=(15, 5))
        btn_dll_help = ctk.CTkButton(config_global_frame, text="?", width=help_btn_size, height=help_btn_size, fg_color="#3a3a3a", hover_color="#4a4a4a", command=lambda: self.show_help_popup("Guía de DLL de Inyección", DLL_HELP_TEXT))
        btn_dll_help.grid(row=current_config_row, column=1, sticky='w', padx=5)
        
        self.btn_dll_select = ctk.CTkButton(config_global_frame, text=f"{self.spoof_dll_name_var.get()}", command=lambda: self.open_custom_select("DLL de Inyecciún", SPOOFING_DLL_NAMES, self.btn_dll_select, "", self.spoof_dll_name_var), fg_color="#3a3a3a", hover_color="#4a4a4a")
        self.btn_dll_select.grid(row=current_config_row, column=2, sticky='ew', pady=5, padx=15)
        current_config_row += 1

        # --- Fila Frame Generation (REFACTORIZADA - Mejora 6) ---
        fg_label_frame = ctk.CTkFrame(config_global_frame, fg_color="transparent")
        fg_label_frame.grid(row=current_config_row, column=0, sticky='w', padx=(15, 5))
        ctk.CTkLabel(fg_label_frame, text="Modo Frame Gen (Global):", font=ctk.CTkFont(size=12, weight="bold")).pack(side='left')
        ctk.CTkLabel(fg_label_frame, text="⚡ ~+80% FPS", font=ctk.CTkFont(size=10), text_color="#00FF00").pack(side='left', padx=(5,0))
        
        btn_fg_help = ctk.CTkButton(config_global_frame, text="?", width=help_btn_size, height=help_btn_size, command=lambda: self.show_help_popup("Ayuda: Frame Generation", FG_HELP_TEXT), fg_color="#3a3a3a", hover_color="#4a4a4a")
        btn_fg_help.grid(row=current_config_row, column=1, sticky='w', padx=5)
        
        self.btn_fg_select = ctk.CTkButton(config_global_frame, text=f"{self.fg_mode_var.get()}", command=lambda: self.open_custom_select("Modo Frame Gen", FG_OPTIONS, self.btn_fg_select, "", self.fg_mode_var), fg_color="#3a3a3a", hover_color="#4a4a4a")
        self.btn_fg_select.grid(row=current_config_row, column=2, sticky='ew', pady=5, padx=15)
        current_config_row += 1

        # --- Fila Reescalador (Backend) - NUEVA ---
        upscaler_label_frame = ctk.CTkFrame(config_global_frame, fg_color="transparent")
        upscaler_label_frame.grid(row=current_config_row, column=0, sticky='w', padx=(15, 5))
        ctk.CTkLabel(upscaler_label_frame, text="Reescalador (Global):", font=ctk.CTkFont(size=12, weight="bold")).pack(side='left')
        ctk.CTkLabel(upscaler_label_frame, text="🎮", font=ctk.CTkFont(size=10), text_color="#888888").pack(side='left', padx=(5,0))
        
        btn_upscaler_help = ctk.CTkButton(config_global_frame, text="?", width=help_btn_size, height=help_btn_size, command=lambda: self.show_help_popup("Ayuda: Reescalador", UPSCALER_HELP_TEXT), fg_color="#3a3a3a", hover_color="#4a4a4a")
        btn_upscaler_help.grid(row=current_config_row, column=1, sticky='w', padx=5)
        
        self.btn_upscaler_select = ctk.CTkButton(config_global_frame, text=f"{self.upscaler_var.get()}", command=lambda: self.open_custom_select("Reescalador", UPSCALER_OPTIONS, self.btn_upscaler_select, "", self.upscaler_var), fg_color="#3a3a3a", hover_color="#4a4a4a")
        self.btn_upscaler_select.grid(row=current_config_row, column=2, sticky='ew', pady=5, padx=15)
        current_config_row += 1

        # --- Fila Reescalado (REFACTORIZADA - Mejora 6) ---
        upscale_label_frame = ctk.CTkFrame(config_global_frame, fg_color="transparent")
        upscale_label_frame.grid(row=current_config_row, column=0, sticky='w', padx=(15, 5))
        ctk.CTkLabel(upscale_label_frame, text="Modo Reescalado (Global):", font=ctk.CTkFont(size=12, weight="bold")).pack(side='left')
        ctk.CTkLabel(upscale_label_frame, text="📊 +60% / +20%", font=ctk.CTkFont(size=10), text_color="#FFAA00").pack(side='left', padx=(5,0))
        
        btn_upscale_help = ctk.CTkButton(config_global_frame, text="?", width=help_btn_size, height=help_btn_size, command=lambda: self.show_help_popup("Ayuda: Modo de Reescalado", UPSCALE_HELP_TEXT), fg_color="#3a3a3a", hover_color="#4a4a4a")
        btn_upscale_help.grid(row=current_config_row, column=1, sticky='w', padx=5)

        self.btn_upscale_select = ctk.CTkButton(config_global_frame, text=f"{self.upscale_mode_var.get()}", command=lambda: self.open_custom_select("Modo Reescalado", UPSCALE_OPTIONS, self.btn_upscale_select, "", self.upscale_mode_var), fg_color="#3a3a3a", hover_color="#4a4a4a")
        self.btn_upscale_select.grid(row=current_config_row, column=2, sticky='ew', pady=5, padx=15)
        current_config_row += 1

        # --- Fila Nitidez ---
        ctk.CTkLabel(config_global_frame, text="Nitidez (Global):", font=ctk.CTkFont(size=12, weight="bold")).grid(row=current_config_row, column=0, sticky='w', padx=(15, 5))
        btn_sharp_help = ctk.CTkButton(config_global_frame, text="?", width=help_btn_size, height=help_btn_size, fg_color="#3a3a3a", hover_color="#4a4a4a", command=lambda: self.show_help_popup("Ayuda: Nitidez (Sharpness)", SHARPNESS_HELP_TEXT))
        btn_sharp_help.grid(row=current_config_row, column=1, sticky='w', padx=5)

        sharpness_frame = ctk.CTkFrame(config_global_frame, fg_color="transparent")
        sharpness_frame.grid(row=current_config_row, column=2, sticky='ew', pady=5, padx=15)
        sharpness_frame.grid_columnconfigure(0, weight=1)
        
        self.slider_sharpness = ctk.CTkSlider(sharpness_frame, from_=0.0, to=2.0, variable=self.sharpness_var, command=self.update_sharpness_label_and_save)
        self.slider_sharpness.grid(row=0, column=0, sticky='ew', padx=(10, 5))
        
        self.label_sharpness_value = ctk.CTkLabel(sharpness_frame, textvariable=self.sharpness_label_var, font=ctk.CTkFont(size=12), width=40)
        self.label_sharpness_value.grid(row=0, column=1, sticky='e', padx=(5,0))
        current_config_row += 1

        # --- Fila Toggles ---
        ctk.CTkLabel(config_global_frame, text="Opc. Adicionales (Global):", font=ctk.CTkFont(size=12, weight="bold")).grid(row=current_config_row, column=0, sticky='w', padx=(15, 5))
        btn_toggles_help = ctk.CTkButton(config_global_frame, text="?", width=help_btn_size, height=help_btn_size, fg_color="#3a3a3a", hover_color="#4a4a4a", command=lambda: self.show_help_popup("Ayuda: Opciones Adicionales", TOGGLES_HELP_TEXT))
        btn_toggles_help.grid(row=current_config_row, column=1, sticky='w', padx=5)

        toggles_frame = ctk.CTkFrame(config_global_frame, fg_color="transparent")
        toggles_frame.grid(row=current_config_row, column=2, sticky='w', pady=5, padx=5)
        overlay_frame = ctk.CTkFrame(toggles_frame, fg_color="transparent", corner_radius=6)
        overlay_frame.pack(side='left', padx=10, pady=5)
        self.switch_overlay = ctk.CTkSwitch(overlay_frame, text="Mostrar Overlay (Debug)", variable=self.overlay_var, onvalue=True, offvalue=False, command=self.save_config)
        self.switch_overlay.pack(padx=5, pady=5)
        mb_frame = ctk.CTkFrame(toggles_frame, fg_color="transparent", corner_radius=6)
        mb_frame.pack(side='left', padx=10, pady=5)
        self.switch_motion_blur = ctk.CTkSwitch(mb_frame, text="Forzar Desactivación Motion Blur", variable=self.motion_blur_var, onvalue=True, offvalue=False, command=self.save_config)
        self.switch_motion_blur.pack(padx=5, pady=5)
        current_config_row += 1
        
        # --- Fila Botones Inferiores (Pestaña 1) ---
        bottom_buttons_frame = ctk.CTkFrame(config_tab, fg_color="transparent")
        bottom_buttons_frame.grid(row=2, column=0, sticky='sew', pady=(20, 10), padx=15)
        bottom_buttons_frame.grid_columnconfigure(0, weight=1)
        bottom_buttons_frame.grid_columnconfigure(1, weight=1)
        config_tab.grid_rowconfigure(1, weight=1) # Fila vacía para empujar botones abajo

        self.btn_compat_list = ctk.CTkButton(bottom_buttons_frame, text="Lista de Compatibilidad (GitHub)", command=open_compatibility_list, corner_radius=8, fg_color="#3a3a3a", hover_color="#4a4a4a")
        self.btn_compat_list.grid(row=0, column=0, sticky='w', padx=(0, 10))
        
        self.btn_go_to_auto = ctk.CTkButton(bottom_buttons_frame, text="IR A AUTO ( X )", command=self.go_to_auto_tab, corner_radius=8, fg_color="#3a3a3a", hover_color="#4a4a4a")
        self.btn_go_to_auto.grid(row=0, column=1, sticky='e')
            
        # Lista de navegación de la Pestaña CONFIG (índice 0)
        # Estructura lógica: cada fila tiene [botón_ayuda, control_principal]
        # ARRIBA/ABAJO: cambia de fila
        # IZQUIERDA/DERECHA: navega dentro de la fila (ayuda <-> control)
        self.navigable_widgets[0] = [
            [self.preset_combo],  # Fila 0: Solo el combo de presets
            [btn_gpu_help, self.r_gpu_amd, self.r_gpu_nvidia],  # Fila 1: Ayuda + radio buttons
            [btn_dll_help, self.btn_dll_select],  # Fila 2: Ayuda + botón DLL
            [btn_fg_help, self.btn_fg_select],  # Fila 3: Ayuda + botón FG
            [btn_upscaler_help, self.btn_upscaler_select],  # Fila 4: Ayuda + botón Upscaler
            [btn_upscale_help, self.btn_upscale_select],  # Fila 5: Ayuda + botón Upscale Mode
            [btn_sharp_help, self.slider_sharpness],  # Fila 6: Ayuda + slider
            [btn_toggles_help, self.switch_overlay, self.switch_motion_blur],  # Fila 7: Ayuda + switches
            [self.btn_compat_list, self.btn_go_to_auto]  # Fila 8: Botones inferiores
        ]


        # --- PESTAÑA 2: GESTIÓN AUTOMÁTICA ---
        
        # --- REORGANIZADO: Fila única con botones y búsqueda ---
        top_controls_frame = ctk.CTkFrame(auto_tab, fg_color="transparent")
        top_controls_frame.grid(row=0, column=0, sticky='ew', padx=5, pady=(5,0))
        top_controls_frame.grid_columnconfigure(3, weight=1)  # La búsqueda ocupa el espacio restante
        
        # Botón de escaneo (lupa)
        # Botón de escaneo (lupa) - con icono
        icon_mgr = get_icon_manager()
        search_icon = icon_mgr.load_icon("rescan.png", size=(20, 20))
        self.btn_scan_games = ctk.CTkButton(
            top_controls_frame, 
            text="",
            image=search_icon if search_icon else None,
            command=self.start_game_scan,
            fg_color="#3a3a3a", hover_color="#4a4a4a",
            corner_radius=8,
            width=50,
            height=40
        )
        self.btn_scan_games.grid(row=0, column=0, padx=(0,5))
        
        # Botón de filtro (embudo)
        filter_icon = icon_mgr.load_icon("filter.png", size=(20, 20))
        self.btn_filter = ctk.CTkButton(
            top_controls_frame,
            text="",
            image=filter_icon if filter_icon else None,
            command=self.open_filter_popup,
            fg_color="#3a3a3a", hover_color="#4a4a4a",
            corner_radius=8,
            width=50,
            height=40
        )
        self.btn_filter.grid(row=0, column=1, padx=(0,10))
        
        # Label "Buscar juego:"
        ctk.CTkLabel(top_controls_frame, text="Buscar juego:", font=ctk.CTkFont(size=12)).grid(row=0, column=2, padx=(0,5))
        
        # Entry de búsqueda
        self.entry_filter = ctk.CTkEntry(top_controls_frame, textvariable=self.game_filter_var, placeholder_text="Escribe para filtrar...")
        self.entry_filter.grid(row=0, column=3, sticky='ew')
        self.entry_filter.bind("<KeyRelease>", self.filter_games)
        
        # Indicador de cachéú (segunda fila)
        caché_frame = ctk.CTkFrame(auto_tab, fg_color="transparent")
        caché_frame.grid(row=1, column=0, sticky='ew', padx=5, pady=(2,0))
        self.caché_info_label = ctk.CTkLabel(
            caché_frame,
            text="",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        self.caché_info_label.pack(anchor='w')

        # Lista de juegos (sin espacio extra)
        self.game_list_frame = ctk.CTkScrollableFrame(auto_tab, label_text="Juegos Detectados (Cruceta: Mover, A: Seleccionar, START: ⚙️ Config)", label_font=ctk.CTkFont(size=12, weight="bold"))
        self.game_list_frame.grid(row=2, column=0, sticky='nswe', pady=(0,5), padx=5)
        self.game_list_frame.grid_columnconfigure(0, weight=1)
        
        # --- MODIFICADO (V2.0 Mejora A): Barra de progreso para Pestaña 2 ---
        self.progress_bar_auto = ctk.CTkProgressBar(auto_tab, orientation="horizontal", mode="determinate")
        self.progress_bar_auto.set(0)
        self.progress_bar_auto.grid(row=4, column=0, sticky='ew', padx=5, pady=(5,5))
        self.progress_bar_auto.grid_remove() # Oculta por defecto
        
        auto_buttons_frame = ctk.CTkFrame(auto_tab, fg_color="transparent")
        auto_buttons_frame.grid(row=5, column=0, pady=(10, 0), sticky='ew')
        auto_buttons_frame.grid_columnconfigure(0, weight=1)
        auto_buttons_frame.grid_columnconfigure(1, weight=1)

        self.btn_auto_inject = ctk.CTkButton(auto_buttons_frame, text="INICIAR INYECCIÓN (X)", command=self.run_auto_injection, corner_radius=8, fg_color="#3a3a3a", hover_color="#4a4a4a", font=ctk.CTkFont(size=14, weight="bold"))
        self.btn_auto_inject.grid(row=0, column=0, sticky='ew', padx=(0, 5), pady=5)
        
        self.btn_auto_uninstall = ctk.CTkButton(auto_buttons_frame, text="DESINSTALAR (Y)", command=self.run_auto_uninstall, corner_radius=8, fg_color="#3a3a3a", hover_color="#4a4a4a", font=ctk.CTkFont(size=14, weight="bold"))
        self.btn_auto_uninstall.grid(row=0, column=1, sticky='ew', padx=(5, 0), pady=5)
        
        # --- NUEVO (V2.0 Mejora E): Botón de Actualizaciún por Lotes ---
        self.btn_batch_update = ctk.CTkButton(auto_tab, text="⚙️ Aplicar Config. Global a Seleccionados (Select)", command=self.run_batch_update_config, corner_radius=8, fg_color="#3a3a3a", hover_color="#4a4a4a")
        self.btn_batch_update.grid(row=6, column=0, pady=(5, 0), sticky='ew')
        
        # --- REFACTORIZADA (V5): Lista de navegación de la Pestaña AUTO (índice 1) ---
        # Estructura lógica visual:
        # Fila 0: Botón de escaneo y botón de filtro
        # Fila 1: Entry de búsqueda
        # Fila 2+: Lista de juegos (se aúade dinúmicamenóte)
        self.navigable_widgets[1] = [
            [self.btn_scan_games, self.btn_filter], # Fila 0: Botones de escaneo y filtro
            [self.entry_filter], # Fila 1: Buscador
            # Fila 2+ (Lista de juegos) se aúade dinúmicamenóte en populate_games
        ]
        

        # --- PESTAÑA 3: GESTIúN MANUAL ---
        
        manual_main_frame = ctk.CTkFrame(manual_tab, fg_color="transparent")
        manual_main_frame.grid(row=0, column=0, sticky='nsew', padx=5, pady=5)
        manual_main_frame.grid_columnconfigure(0, weight=1)
        manual_tab.grid_columnconfigure(0, weight=1)
        
        manual_path_frame = ctk.CTkFrame(manual_main_frame, fg_color="transparent")
        manual_path_frame.grid(row=0, column=0, pady=5, sticky='ew')
        manual_path_frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(manual_path_frame, text="Carpeta de Destino (CUALQUIERA): ", font=ctk.CTkFont(size=12)).grid(row=0, column=0, padx=5, sticky='w')
        
        self.entry_manual_path = ctk.CTkEntry(manual_main_frame, textvariable=self.manual_game_path)
        self.entry_manual_path.grid(row=1, column=0, padx=5, sticky='ew')
        
        # --- MODIFICADO (V2.0 Pulida): Botón Abrir Carpeta Manual ---
        manual_btn_frame = ctk.CTkFrame(manual_path_frame, fg_color="transparent")
        manual_btn_frame.grid(row=1, column=1, sticky='e')

        self.btn_manual_open_folder = ctk.CTkButton(manual_btn_frame, text="📁", command=lambda: self.open_game_folder(self.manual_game_path.get()), corner_radius=8, width=30, fg_color="#3a3a3a", hover_color="#4a4a4a")
        self.btn_manual_open_folder.pack(side='left', padx=(0, 5))

        self.btn_manual_select = ctk.CTkButton(manual_btn_frame, text="Seleccionar Carpeta", command=self.select_game_dir, corner_radius=8, fg_color="#3a3a3a", hover_color="#4a4a4a")

        self.btn_manual_select.pack(side='left')

        
        self.status_label_manual = ctk.CTkLabel(manual_main_frame, textvariable=self.mod_status_manual, font=ctk.CTkFont(size=12, weight="bold"))
        self.status_label_manual.grid(row=2, column=0, pady=10, sticky='w')
        
        manual_buttons_frame = ctk.CTkFrame(manual_main_frame, fg_color="transparent")
        manual_buttons_frame.grid(row=3, column=0, pady=(10, 5), sticky='ew')
        manual_buttons_frame.grid_columnconfigure(0, weight=1)
        manual_buttons_frame.grid_columnconfigure(1, weight=1)

        self.btn_manual_inject = ctk.CTkButton(manual_buttons_frame, text="INYECCIÓN MANUAL (X)", command=self.run_manual_injection, corner_radius=8, fg_color="#3a3a3a", hover_color="#4a4a4a", font=ctk.CTkFont(size=14, weight="bold"))
        self.btn_manual_inject.grid(row=0, column=0, sticky='ew', padx=(0, 5), pady=5)
        
        self.btn_manual_uninstall = ctk.CTkButton(manual_buttons_frame, text="DESINSTALAR MANUAL (Y)", command=self.run_manual_uninstall, corner_radius=8, fg_color="#3a3a3a", hover_color="#4a4a4a", font=ctk.CTkFont(size=14, weight="bold"))
        self.btn_manual_uninstall.grid(row=0, column=1, sticky='ew', padx=(5, 0), pady=5)
        
        self.btn_manual_restore_bak = ctk.CTkButton(manual_main_frame, text="Restaurar DLL Original (.bak)", command=self.run_manual_restore_bak, corner_radius=8, fg_color="#3a3a3a", hover_color="#4a4a4a")
        self.btn_manual_restore_bak.grid(row=4, column=0, pady=(10, 5), sticky='ew')
        
        # --- REFACTORIZADA (V5): Lista de navegación de la Pestaña MANUAL (índice 2) ---
        # Estructura lógica visual:
        # Fila 0: Entry de ruta + botón abrir carpeta + botón seleccionar
        # Fila 1: Botones de inyección y desinstalación
        # Fila 2: Botón de restaurar backup
        self.navigable_widgets[2] = [
            [self.entry_manual_path, self.btn_manual_open_folder, self.btn_manual_select], # Fila 0: Controles de ruta
            [self.btn_manual_inject, self.btn_manual_uninstall], # Fila 1: Botones principales
            [self.btn_manual_restore_bak] # Fila 2: Restaurar backup
        ]
        
        
        # --- NUEVA PESTAÑA 4: CONFIGURACIÓN APP ---
        
        app_config_main_frame = ctk.CTkFrame(app_config_tab, fg_color="transparent")
        app_config_main_frame.pack(fill='both', expand=True, padx=5, pady=5)
        app_config_main_frame.grid_columnconfigure(0, weight=1)
        app_config_main_frame.grid_rowconfigure(0, weight=1) # Fila Carpetas
        app_config_main_frame.grid_rowconfigure(1, weight=0) # Fila Limpieza
        
        # --- MOVIDO: Secciún Carpetas Personalizadas ---
        custom_folders_frame = ctk.CTkFrame(app_config_main_frame, fg_color="transparent")
        custom_folders_frame.grid(row=0, column=0, sticky='nsew', pady=0, padx=15)
        custom_folders_frame.grid_columnconfigure(0, weight=1)
        custom_folders_frame.grid_rowconfigure(1, weight=1)
        
        custom_folders_header_frame = ctk.CTkFrame(custom_folders_frame, fg_color="transparent")
        custom_folders_header_frame.grid(row=0, column=0, sticky='ew')
        custom_folders_header_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(custom_folders_header_frame, text="Carpetas de Búsqueda Adicionales (para Pestaña AUTO):", font=ctk.CTkFont(size=12, weight="bold")).grid(row=0, column=0, sticky='w')
        
        self.btn_add_folder = ctk.CTkButton(custom_folders_header_frame, text="➕", command=self.add_custom_folder, width=50, height=40, corner_radius=8, fg_color="#3a3a3a", hover_color="#4a4a4a", font=ctk.CTkFont(size=20))
        self.btn_add_folder.grid(row=0, column=1, sticky='e', padx=(0, 5))

        self.btn_rescan = ctk.CTkButton(custom_folders_header_frame, text="🔄", command=self.rescan_all_games_threaded, width=50, height=40, corner_radius=8, fg_color="#3a3a3a", hover_color="#4a4a4a", font=ctk.CTkFont(size=20))
        self.btn_rescan.grid(row=0, column=2, sticky='e')

        self.custom_folders_list_frame = ctk.CTkScrollableFrame(custom_folders_frame, corner_radius=8)
        self.custom_folders_list_frame.grid(row=1, column=0, sticky='nsew', pady=(5,0))
        self.custom_folders_list_frame.grid_columnconfigure(0, weight=1)

        # --- NUEVA SECCIúN: Apariencia ---
        appearance_frame = ctk.CTkFrame(app_config_main_frame, corner_radius=8)
        appearance_frame.grid(row=2, column=0, pady=(20, 5), sticky='ew', padx=15)
        appearance_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(appearance_frame, text="Apariencia", font=ctk.CTkFont(size=12, weight="bold")).grid(row=0, column=0, columnspan=2, pady=(5, 10), sticky='w', padx=10)
        
        ctk.CTkLabel(appearance_frame, text="Tema:").grid(row=1, column=0, sticky='w', padx=10, pady=5)
        self.theme_var = ctk.StringVar(value="Oscuro")
        theme_options = ctk.CTkComboBox(
            appearance_frame,
            values=["Claro", "Oscuro", "Sistema"],
            variable=self.theme_var,
            command=self.on_theme_changed
        )
        theme_options.grid(row=1, column=1, sticky='ew', padx=10, pady=5)
        
        ctk.CTkLabel(appearance_frame, text="Escala UI:").grid(row=2, column=0, sticky='w', padx=10, pady=5)
        self.scale_var = ctk.StringVar(value="100%")
        scale_options = ctk.CTkComboBox(
            appearance_frame,
            values=["80%", "90%", "100%", "110%", "120%"],
            variable=self.scale_var,
            command=self.on_scale_changed
        )
        scale_options.grid(row=2, column=1, sticky='ew', padx=10, pady=5)


        # --- MOVIDO: Secciún Limpieza ---
        clean_frame = ctk.CTkFrame(app_config_main_frame, corner_radius=8)
        clean_frame.grid(row=3, column=0, pady=(20, 5), sticky='ew', padx=15)
        clean_frame.grid_columnconfigure(0, weight=1)
        clean_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(clean_frame, text="Mantenimiento / Limpieza", font=ctk.CTkFont(size=12, weight="bold")).grid(row=0, column=0, columnspan=2, pady=(5, 10))
        
        self.btn_clean_logs = ctk.CTkButton(clean_frame, text="🗑️ Limpiar TODOS los Archivos .log", command=self.run_clean_logs_threaded, corner_radius=8, fg_color="#3a3a3a", hover_color="#4a4a4a")
        self.btn_clean_logs.grid(row=1, column=0, sticky='ew', padx=(10, 5), pady=10)
        
        self.btn_clean_orphan_baks = ctk.CTkButton(clean_frame, text="🗑️ Limpiar Backups Huérfanos", command=self.run_clean_orphan_baks_threaded, corner_radius=8, fg_color="#3a3a3a", hover_color="#4a4a4a")
        self.btn_clean_orphan_baks.grid(row=1, column=1, sticky='ew', padx=(5, 10), pady=10)
        
        # --- NUEVO (V2.0 Mejora A): Barra de progreso para Pestaña 4 ---
        self.progress_bar_app = ctk.CTkProgressBar(app_config_main_frame, orientation="horizontal", mode="determinate")
        self.progress_bar_app.set(0)
        self.progress_bar_app.grid(row=4, column=0, sticky='ew', padx=15, pady=(5, 10))
        self.progress_bar_app.grid_remove() # Oculta por defecto
        
        # --- REFACTORIZADA (V5): Lista de navegación de la Pestaña CONFIG APP (índice 3) ---
        # Estructura lógica visual:
        # Fila 0: Botones de aúadir carpeta y rescanear
        # Fila 1+: Lista de carpetas personalizadas (se aúade dinúmicamenóte)
        # Fila N: Segmenóted buttons de Tema y Escala
        # Fila N+1: Botones de limpieza
        self.navigable_widgets[3] = [
            [self.btn_add_folder, self.btn_rescan], # Fila 0: Gestiún de carpetas
            # Fila 1+ (lista de carpetas) se aúade dinúmicamenóte
            [theme_options, scale_options], # Fila N: Apariencia
            [self.btn_clean_logs, self.btn_clean_orphan_baks] # Fila N+1: Limpieza
        ]


        # --- PESTAÑA 5: LOG DE OPERACIONES ---
        log_frame = ctk.CTkFrame(log_tab, fg_color="transparent")
        log_frame.grid(row=0, column=0, sticky='nsew', padx=5, pady=5)
        log_tab.grid_rowconfigure(0, weight=1)
        log_tab.grid_columnconfigure(0, weight=1)
        log_frame.grid_rowconfigure(0, weight=1)
        log_frame.grid_columnconfigure(0, weight=1)

        self.log_text = ctk.CTkTextbox(log_frame, state="disabled", wrap="word", corner_radius=8, font=ctk.CTkFont(size=12))
        self.log_text.grid(row=0, column=0, columnspan=2, sticky='nswe') 
        self.log_text.bind("<Key>", lambda e: "break")
        
        # --- NUEVO (V2.0 Mejora B/C): Opciones de Log ---
        log_options_frame = ctk.CTkFrame(log_frame, fg_color="transparent")
        log_options_frame.grid(row=1, column=0, columnspan=2, sticky='ew', pady=(5,0))
        log_options_frame.grid_columnconfigure(0, weight=1)
        
        self.log_auto_scroll_checkbox = ctk.CTkCheckBox(log_options_frame, text="Auto-scroll", variable=self.log_auto_scroll_var, onvalue=True, offvalue=False)
        self.log_auto_scroll_checkbox.grid(row=0, column=0, sticky='w')
        
        self.btn_save_log = ctk.CTkButton(log_options_frame, text="💾 Guardar Log en .txt", command=self.save_log_to_file, corner_radius=8, fg_color="#3a3a3a", hover_color="#4a4a4a")
        self.btn_save_log.grid(row=0, column=1, sticky='e')
        
        self.log_text.tag_config('INFO', foreground='#00FF00')
        self.log_text.tag_config('WARN', foreground='#FFFF00')
        self.log_text.tag_config('ERROR', foreground='#FF4500')
        self.log_text.tag_config('TITLE', foreground='#00BFFF')
        self.log_text.tag_config('OK', foreground='#00FF00')
        
        # --- REFACTORIZADA (V5): Lista de navegación de la Pestaña LOG (índice 4) ---
        # Estructura lógica visual:
        # Fila 0: úrea de texto del log
        # Fila 1: Checkbox auto-scroll + botón guardar log
        self.navigable_widgets[4] = [
            [self.log_text], # Fila 0: Log de texto
            [self.log_auto_scroll_checkbox, self.btn_save_log] # Fila 1: Controles inferiores
        ]
        
        self.after(50, self._get_default_border_color)

    def create_gaming_interface(self):
        """Crea la interfaz Gaming tipo dashboard con navegación lateral."""
        self.gaming_interface_frame = ctk.CTkFrame(self.main_content_frame, fg_color="transparent")
        self.gaming_interface_frame.grid(row=0, column=0, sticky='ewns')
        self.gaming_interface_frame.grid_columnconfigure(1, weight=1)
        self.gaming_interface_frame.grid_rowconfigure(0, weight=1)
        
        # === PANEL IZQUIERDO: menóú de Navegaciún ===
        nav_panel = ctk.CTkFrame(self.gaming_interface_frame, fg_color="#1a1a1a", corner_radius=10, width=120)
        nav_panel.grid(row=0, column=0, sticky='ns', padx=(10,5), pady=10)
        nav_panel.grid_propagate(False)

        # Sin header - directamente los botones
        
        # Botones de navegación (solo iconos, optimizados para táctil)
        self.gaming_nav_buttons = {}
        nav_items = [
            ("config", "⚙️", self.show_gaming_config),
            ("auto", "🎮", self.show_gaming_auto),
            ("manual", "📁", self.show_gaming_manual),
            ("settings", "🔧", self.show_gaming_settings),
            ("help", "❓", self.show_gaming_help),
        ]
        
        for key, icon, command in nav_items:
            btn = ctk.CTkButton(nav_panel, text=icon, command=command,
                              fg_color="#3a3a3a", hover_color="#4a4a4a",
                              height=90, corner_radius=8,
                              font=ctk.CTkFont(size=36),
                              border_width=2, border_color="#505050")
            btn.pack(fill='x', padx=10, pady=12)
            self.gaming_nav_buttons[key] = btn
        
        # === PANEL CENTRAL: Contenido Dinámico ===
        self.gaming_content_frame = ctk.CTkFrame(self.gaming_interface_frame, fg_color="#2b2b2b", corner_radius=10)
        self.gaming_content_frame.grid(row=0, column=1, sticky='ewns', padx=(5,10), pady=10)
        self.gaming_content_frame.grid_columnconfigure(0, weight=1)
        self.gaming_content_frame.grid_rowconfigure(0, weight=1)
        
        # Crear todos los paneles de contenido (ocultos inicialmente)
        self.create_gaming_panels()
        
        # Mostrar panel de detección automática por defecto
        self.show_gaming_auto()
    
    def create_gaming_panels(self):
        """Crea todos los paneles de contenido para el modo gaming."""
        # Panel: Configuración del Mod
        self.gaming_config_panel = ctk.CTkFrame(self.gaming_content_frame, fg_color="transparent")
        self.gaming_config_panel.grid(row=0, column=0, sticky='ewns')
        self.gaming_config_panel.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(self.gaming_config_panel, text="⚙️ CONFIGURACIÓN DEL MOD", 
                     font=ctk.CTkFont(size=20, weight="bold")).pack(pady=20)
        
        config_scroll = ctk.CTkScrollableFrame(self.gaming_config_panel, fg_color="transparent")
        config_scroll.pack(fill='both', expand=True, padx=20, pady=(0,20))
        
        # === PRESETS RÁPIDOS ===
        presets_frame = ctk.CTkFrame(config_scroll, fg_color="#2a2a2a", corner_radius=10, border_width=1, border_color="#404040")
        presets_frame.pack(fill='x', pady=(0,15), padx=5)
        
        # Header con indicador de preset activo
        presets_header = ctk.CTkFrame(presets_frame, fg_color="transparent")
        presets_header.pack(fill='x', pady=(12,8), padx=15)
        ctk.CTkLabel(presets_header, text="⚡ PRESETS RÁPIDOS", 
                     font=ctk.CTkFont(size=14, weight="bold"), text_color="#CCCCCC").pack(side='left')
        self.gaming_active_preset_label = ctk.CTkLabel(presets_header, text="• Custom", 
                     font=ctk.CTkFont(size=12), text_color="#888888")
        self.gaming_active_preset_label.pack(side='right')
        
        presets_btns = ctk.CTkFrame(presets_frame, fg_color="transparent")
        presets_btns.pack(fill='x', padx=15, pady=(0,12))
        presets_btns.grid_columnconfigure((0,1,2,3,4), weight=1)
        
        # Botón Default (Automático)
        self.gaming_btn_default = ctk.CTkButton(presets_btns, text="🎯 Default", 
                                command=lambda: self.apply_preset_gaming("default"),
                                fg_color="#3a3a3a", hover_color="#4a4a4a",
                                height=55, font=ctk.CTkFont(size=12, weight="bold"),
                                corner_radius=8, border_width=2, border_color="#505050")
        self.gaming_btn_default.grid(row=0, column=0, padx=4, sticky='ew')
        
        # Botón Performance
        self.gaming_btn_perf = ctk.CTkButton(presets_btns, text="⚡ Performance", 
                                command=lambda: self.apply_preset_gaming("performance"),
                                fg_color="#3a3a3a", hover_color="#4a4a4a",
                                height=55, font=ctk.CTkFont(size=12, weight="bold"),
                                corner_radius=8, border_width=2, border_color="#505050")
        self.gaming_btn_perf.grid(row=0, column=1, padx=4, sticky='ew')
        
        # Botón Balanced
        self.gaming_btn_bal = ctk.CTkButton(presets_btns, text="⚖️ Balanced", 
                               command=lambda: self.apply_preset_gaming("balanced"),
                               fg_color="#3a3a3a", hover_color="#4a4a4a",
                               height=55, font=ctk.CTkFont(size=12, weight="bold"),
                               corner_radius=8, border_width=2, border_color="#505050")
        self.gaming_btn_bal.grid(row=0, column=2, padx=4, sticky='ew')
        
        # Botón Quality
        self.gaming_btn_qual = ctk.CTkButton(presets_btns, text="💎 Quality", 
                                command=lambda: self.apply_preset_gaming("quality"),
                                fg_color="#3a3a3a", hover_color="#4a4a4a",
                                height=55, font=ctk.CTkFont(size=12, weight="bold"),
                                corner_radius=8, border_width=2, border_color="#505050")
        self.gaming_btn_qual.grid(row=0, column=3, padx=4, sticky='ew')
        
        # Botón Custom
        self.gaming_btn_custom = ctk.CTkButton(presets_btns, text="• Custom", 
                                command=lambda: self.log_message('INFO', 'Preset Custom - Modifica manualmente'),
                                fg_color="#3a3a3a", hover_color="#4a4a4a",
                                height=55, font=ctk.CTkFont(size=12, weight="bold"),
                                corner_radius=8, border_width=2, border_color="#505050")
        self.gaming_btn_custom.grid(row=0, column=4, padx=4, sticky='ew')
        
        # Guardar referencias para actualización visual
        self.gaming_preset_buttons = {
            "default": self.gaming_btn_default,
            "performance": self.gaming_btn_perf,
            "balanced": self.gaming_btn_bal,
            "quality": self.gaming_btn_qual,
            "custom": self.gaming_btn_custom
        }
        
        # Separador
        ctk.CTkFrame(config_scroll, fg_color="gray30", height=2).pack(fill='x', pady=15)
        
        # GPU
        gpu_frame = ctk.CTkFrame(config_scroll, fg_color="#1a1a1a", corner_radius=8)
        gpu_frame.pack(fill='x', pady=10)
        ctk.CTkLabel(gpu_frame, text="Tipo de GPU:", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor='w', padx=15, pady=(10,5))
        gpu_btns = ctk.CTkFrame(gpu_frame, fg_color="transparent")
        gpu_btns.pack(fill='x', padx=15, pady=(0,10))
        ctk.CTkRadioButton(gpu_btns, text="AMD / Intel", variable=self.gpu_choice, value=1, 
                          font=ctk.CTkFont(size=13)).pack(side='left', padx=10)
        ctk.CTkRadioButton(gpu_btns, text="NVIDIA", variable=self.gpu_choice, value=2,
                          font=ctk.CTkFont(size=13)).pack(side='left', padx=10)
        
        # DLL
        dll_frame = ctk.CTkFrame(config_scroll, fg_color="#1a1a1a", corner_radius=8)
        dll_frame.pack(fill='x', pady=10)
        ctk.CTkLabel(dll_frame, text="DLL de Inyecciún:", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor='w', padx=15, pady=(10,5))
        self.gaming_dll_combo = ctk.CTkComboBox(dll_frame, values=list(SPOOFING_OPTIONS.values()),
                                               variable=self.spoof_dll_name_var, font=ctk.CTkFont(size=13))
        self.gaming_dll_combo.pack(fill='x', padx=15, pady=(0,10))
        
        # Frame Gen
        fg_frame = ctk.CTkFrame(config_scroll, fg_color="#1a1a1a", corner_radius=8)
        fg_frame.pack(fill='x', pady=10)
        fg_header = ctk.CTkFrame(fg_frame, fg_color="transparent")
        fg_header.pack(fill='x', padx=15, pady=(10,5))
        ctk.CTkLabel(fg_header, text="Frame Generation:", font=ctk.CTkFont(size=14, weight="bold")).pack(side='left')
        ctk.CTkLabel(fg_header, text="? ~+80% FPS", font=ctk.CTkFont(size=11), text_color="#00FF00").pack(side='right')
        self.gaming_fg_combo = ctk.CTkComboBox(fg_frame, values=FG_OPTIONS,
                                              variable=self.fg_mode_var, font=ctk.CTkFont(size=13),
                                              command=lambda _: self.mark_config_as_custom())
        self.gaming_fg_combo.pack(fill='x', padx=15, pady=(0,10))
        
        # Upscaler
        upscaler_frame = ctk.CTkFrame(config_scroll, fg_color="#1a1a1a", corner_radius=8)
        upscaler_frame.pack(fill='x', pady=10)
        upscaler_header = ctk.CTkFrame(upscaler_frame, fg_color="transparent")
        upscaler_header.pack(fill='x', padx=15, pady=(10,5))
        ctk.CTkLabel(upscaler_header, text="Reescalador:", font=ctk.CTkFont(size=14, weight="bold")).pack(side='left')
        ctk.CTkLabel(upscaler_header, text="🎮 Tecnología base", font=ctk.CTkFont(size=11), text_color="#888888").pack(side='right')
        self.gaming_upscaler_combo = ctk.CTkComboBox(upscaler_frame, values=UPSCALER_OPTIONS,
                                                     variable=self.upscaler_var, font=ctk.CTkFont(size=13),
                                                     command=lambda _: self.mark_config_as_custom())
        self.gaming_upscaler_combo.pack(fill='x', padx=15, pady=(0,10))
        
        # Upscale Mode
        upscale_frame = ctk.CTkFrame(config_scroll, fg_color="#1a1a1a", corner_radius=8)
        upscale_frame.pack(fill='x', pady=10)
        upscale_header = ctk.CTkFrame(upscale_frame, fg_color="transparent")
        upscale_header.pack(fill='x', padx=15, pady=(10,5))
        ctk.CTkLabel(upscale_header, text="Modo de Reescalado:", font=ctk.CTkFont(size=14, weight="bold")).pack(side='left')
        ctk.CTkLabel(upscale_header, text="📊 Performance: +60% | Quality: +20%", font=ctk.CTkFont(size=11), text_color="#FFAA00").pack(side='right')
        self.gaming_upscale_combo = ctk.CTkComboBox(upscale_frame, values=UPSCALE_OPTIONS,
                                                    variable=self.upscale_mode_var, font=ctk.CTkFont(size=13),
                                                    command=lambda _: self.mark_config_as_custom())
        self.gaming_upscale_combo.pack(fill='x', padx=15, pady=(0,10))
        
        # Sharpness
        sharp_frame = ctk.CTkFrame(config_scroll, fg_color="#1a1a1a", corner_radius=8)
        sharp_frame.pack(fill='x', pady=10)
        sharp_header = ctk.CTkFrame(sharp_frame, fg_color="transparent")
        sharp_header.pack(fill='x', padx=15, pady=(10,5))
        ctk.CTkLabel(sharp_header, text="Sharpness:", font=ctk.CTkFont(size=14, weight="bold")).pack(side='left')
        ctk.CTkLabel(sharp_header, text="✨ Nitidez visual", font=ctk.CTkFont(size=11), text_color="#888888").pack(side='right')
        sharp_control = ctk.CTkFrame(sharp_frame, fg_color="transparent")
        sharp_control.pack(fill='x', padx=15, pady=(0,15))
        sharp_control.grid_columnconfigure(0, weight=1)
        # Usamos un callback inline para evitar dependencias si el mútodo no existe en tiempo de construcciún
        self.gaming_sharpness_slider = ctk.CTkSlider(
            sharp_control,
            from_=0.0,
            to=1.0,
            variable=self.sharpness_var,
            height=20,
            button_length=24,
            command=lambda v: (
                self.sharpness_label_var.set(f"{float(v):.2f}"),
                self.mark_config_as_custom()
            )
        )
        self.gaming_sharpness_slider.grid(row=0, column=0, sticky='ew', padx=(0,15))
        self.gaming_sharpness_label = ctk.CTkLabel(sharp_control, textvariable=self.sharpness_label_var,
                                                   width=60, font=ctk.CTkFont(size=18, weight="bold"),
                                                   fg_color="#2a2a2a", corner_radius=5)
        self.gaming_sharpness_label.grid(row=0, column=1)
        
        # Overlay y Motion Blur
        extras_frame = ctk.CTkFrame(config_scroll, fg_color="#1a1a1a", corner_radius=8)
        extras_frame.pack(fill='x', pady=10)
        ctk.CTkLabel(extras_frame, text="Extras:", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor='w', padx=15, pady=(10,5))
        ctk.CTkCheckBox(extras_frame, text="Overlay (Ins)", variable=self.overlay_var,
                       command=self.save_config,
                       font=ctk.CTkFont(size=13)).pack(anchor='w', padx=15, pady=5)
        ctk.CTkCheckBox(extras_frame, text="Motion Blur", variable=self.motion_blur_var,
                       command=self.save_config,
                       font=ctk.CTkFont(size=13)).pack(anchor='w', padx=15, pady=(0,10))
        
        self.gaming_config_panel.grid_remove()  # Ocultar inicialmente
        
        # Panel: Detecciún Automútica
        self.gaming_auto_panel = ctk.CTkFrame(self.gaming_content_frame, fg_color="transparent")
        self.gaming_auto_panel.grid(row=0, column=0, sticky='ewns')
        self.gaming_auto_panel.grid_columnconfigure(0, weight=1)
        self.gaming_auto_panel.grid_rowconfigure(1, weight=1)
        
        auto_header = ctk.CTkFrame(self.gaming_auto_panel, fg_color="#1a1a1a", corner_radius=8)
        auto_header.grid(row=0, column=0, sticky='ew', padx=20, pady=20)
        auto_header.grid_columnconfigure(0, weight=1)
        
        # Padding interno del header
        header_content = ctk.CTkFrame(auto_header, fg_color="transparent")
        header_content.pack(fill='x', padx=15, pady=12)
        header_content.grid_columnconfigure(2, weight=1)
        
        # Botón de escaneo (lupa) - con icono
        icon_mgr = get_icon_manager()
        search_icon = icon_mgr.load_icon("rescan.png", size=(24, 24))
        self.btn_gaming_scan = ctk.CTkButton(header_content, text="", 
                                            image=search_icon if search_icon else None,
                                            command=self.start_game_scan,
                                            width=80, height=50,
                                            fg_color="#3a3a3a", hover_color="#4a4a4a",
                                            corner_radius=8, border_width=2, border_color="#505050")
        self.btn_gaming_scan.grid(row=0, column=0, sticky='w', padx=(0,10))
        
        # Botón de filtro (embudo) - con icono
        filter_icon = icon_mgr.load_icon("filter.png", size=(24, 24))
        self.btn_gaming_filter = ctk.CTkButton(header_content, text="", 
                                              image=filter_icon if filter_icon else None,
                                              command=self.open_filter_popup,
                                              width=80, height=50,
                                              fg_color="#3a3a3a", hover_color="#4a4a4a",
                                              font=ctk.CTkFont(size=20),
                                              corner_radius=8, border_width=2, border_color="#505050")
        self.btn_gaming_filter.grid(row=0, column=1, sticky='w', padx=(0,10))
        
        # Contador X/Y
        self.gaming_games_count_label = ctk.CTkLabel(header_content, text="0/0", 
                                                     font=ctk.CTkFont(size=18, weight="bold"), 
                                                     text_color="#00AAFF",
                                                     fg_color="#2a2a2a", corner_radius=5,
                                                     width=100, height=35)
        self.gaming_games_count_label.grid(row=0, column=2, sticky='w')
        
        # Botones para aplicar/desinstalar mod a juegos seleccionados
        btn_actions = ctk.CTkFrame(header_content, fg_color="transparent")
        btn_actions.grid(row=0, column=3, padx=15)
        
        self.btn_gaming_apply_selected = ctk.CTkButton(btn_actions, text="✓ APLICAR", 
                                                       command=self.gaming_apply_to_selected,
                                                       fg_color="#3a3a3a", hover_color="#4a4a4a",
                                                       height=44, font=ctk.CTkFont(size=14, weight="bold"),
                                                       border_width=2, border_color="#505050")
        self.btn_gaming_apply_selected.pack(side='left', padx=5)
        
        self.btn_gaming_remove_selected = ctk.CTkButton(btn_actions, text="❌ ELIMINAR", 
                                                        command=self.gaming_remove_from_selected,
                                                        fg_color="#3a3a3a", hover_color="#4a4a4a",
                                                        height=44, font=ctk.CTkFont(size=14, weight="bold"),
                                                        border_width=2, border_color="#505050")
        self.btn_gaming_remove_selected.pack(side='left', padx=5)
        
        self.gaming_games_scrollable = ctk.CTkScrollableFrame(self.gaming_auto_panel, fg_color="transparent")
        self.gaming_games_scrollable.grid(row=1, column=0, sticky='ewns', padx=20, pady=(0,20))
        self.gaming_games_scrollable.grid_columnconfigure(0, weight=1)
        
        self.gaming_auto_panel.grid_remove()  # Ocultar inicialmente
        
        # Panel: Ruta Manual
        self.gaming_manual_panel = ctk.CTkFrame(self.gaming_content_frame, fg_color="transparent")
        self.gaming_manual_panel.grid(row=0, column=0, sticky='ewns')
        self.gaming_manual_panel.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(self.gaming_manual_panel, text="📂 RUTA MANUAL", 
                     font=ctk.CTkFont(size=20, weight="bold")).pack(pady=20)
        
        manual_content = ctk.CTkFrame(self.gaming_manual_panel, fg_color="#1a1a1a", corner_radius=10,
                                     border_width=2, border_color="#2a2a2a")
        manual_content.pack(fill='both', expand=True, padx=30, pady=10)
        
        # Instrucciones con mejor contraste
        ctk.CTkLabel(manual_content, text="Selecciona la carpeta del juego manualmente:",
                     font=ctk.CTkFont(size=14), text_color="#CCCCCC").pack(pady=(20,10))
        
        # Path display mejorado
        self.manual_path_var = ctk.StringVar(value="Ninguna carpeta seleccionada")
        path_frame = ctk.CTkFrame(manual_content, fg_color="#0a0a0a", corner_radius=5,
                                 border_width=1, border_color="#333333")
        path_frame.pack(fill='x', padx=20, pady=10)
        ctk.CTkLabel(path_frame, textvariable=self.manual_path_var, 
                     font=ctk.CTkFont(size=12), text_color="#AAAAAA",
                     wraplength=500).pack(pady=15, padx=15)
        
        # Browse button con mejor diseúo
        browse_btn = ctk.CTkButton(manual_content, text="📁 EXAMINAR CARPETA",
                                   command=self.gaming_browse_manual_path,
                                   font=ctk.CTkFont(size=16, weight="bold"),
                                   height=55, fg_color="#3a3a3a", hover_color="#4a4a4a",
                                   corner_radius=8, border_width=2, border_color="#505050")
        browse_btn.pack(pady=20)
        
        # Status con mejor visibilidad
        self.manual_status_var = ctk.StringVar(value="")
        self.manual_status_label = ctk.CTkLabel(manual_content, textvariable=self.manual_status_var,
                                                font=ctk.CTkFont(size=14, weight="bold"))
        self.manual_status_label.pack(pady=10)
        
        # Botones de acciún (Aplicar y Eliminar)
        buttons_frame = ctk.CTkFrame(manual_content, fg_color="transparent")
        buttons_frame.pack(pady=(20,30))
        
        self.manual_apply_btn = ctk.CTkButton(buttons_frame, text="✅ APLICAR MOD",
                                             command=self.gaming_apply_manual_mod,
                                             font=ctk.CTkFont(size=16, weight="bold"),
                                             height=55, width=200, fg_color="#3a3a3a", hover_color="#4a4a4a",
                                             corner_radius=8, state='disabled',
                                             border_width=2, border_color="#505050")
        self.manual_apply_btn.pack(side='left', padx=10)
        
        self.manual_uninstall_btn = ctk.CTkButton(buttons_frame, text="❌ ELIMINAR MOD",
                                                 command=self.gaming_uninstall_manual_mod,
                                                 font=ctk.CTkFont(size=16, weight="bold"),
                                                 height=55, width=200, fg_color="#3a3a3a", hover_color="#4a4a4a",
                                                 corner_radius=8, state='disabled',
                                                 border_width=2, border_color="#505050")
        self.manual_uninstall_btn.pack(side='left', padx=10)
        
        self.gaming_manual_panel.grid_remove()
        
        # Panel: Ajustes de la App
        self.gaming_settings_panel = ctk.CTkFrame(self.gaming_content_frame, fg_color="transparent")
        self.gaming_settings_panel.grid(row=0, column=0, sticky='ewns')

        ctk.CTkLabel(self.gaming_settings_panel, text="⚙️ AJUSTES DE LA APP", 
                     font=ctk.CTkFont(size=20, weight="bold")).pack(pady=20)

        settings_scroll = ctk.CTkScrollableFrame(self.gaming_settings_panel, fg_color="transparent")
        settings_scroll.pack(fill='both', expand=True, padx=20, pady=(0,20))

        # Tema
        theme_frame = ctk.CTkFrame(settings_scroll, fg_color="#1a1a1a", corner_radius=8)
        theme_frame.pack(fill='x', pady=10)
        ctk.CTkLabel(theme_frame, text="Tema:", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor='w', padx=15, pady=(10,5))
        ctk.CTkComboBox(theme_frame, values=["Claro", "Oscuro", "Sistema"], variable=self.theme_var,
                       command=self.on_theme_changed, font=ctk.CTkFont(size=13)).pack(fill='x', padx=15, pady=(0,10))

        # Escala
        scale_frame = ctk.CTkFrame(settings_scroll, fg_color="#1a1a1a", corner_radius=8)
        scale_frame.pack(fill='x', pady=10)
        ctk.CTkLabel(scale_frame, text="Escala UI:", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor='w', padx=15, pady=(10,5))
        ctk.CTkComboBox(scale_frame, values=["80%", "90%", "100%", "110%", "120%"], variable=self.scale_var,
                       command=self.on_scale_changed, font=ctk.CTkFont(size=13)).pack(fill='x', padx=15, pady=(0,10))

        # Gestiún de Mod
        mod_mgmt_frame = ctk.CTkFrame(settings_scroll, fg_color="#1a1a1a", corner_radius=8)
        mod_mgmt_frame.pack(fill='x', pady=10)
        ctk.CTkLabel(mod_mgmt_frame, text="Mod (Descargas y Selecciún)", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor='w', padx=15, pady=(10,5))
        ctk.CTkButton(mod_mgmt_frame, text="⬇️ Descargar / Gestionar Mod", command=self.open_mod_downloader,
                      height=40, fg_color="#3a3a3a", hover_color="#4a4a4a", font=ctk.CTkFont(size=13, weight="bold"),
                      border_width=2, border_color="#505050").pack(fill='x', padx=15, pady=5)
        
        # Desplegable de versión del mod en gaming
        ctk.CTkLabel(mod_mgmt_frame, text="Versiún del Mod:", font=ctk.CTkFont(size=12)).pack(anchor='w', padx=15, pady=(10,5))
        self.gaming_mod_version_combo = ctk.CTkComboBox(mod_mgmt_frame, variable=self.mod_version_list, 
                                                        command=self.on_mod_version_selected,
                                                        font=ctk.CTkFont(size=12))
        self.gaming_mod_version_combo.pack(fill='x', padx=15, pady=(0,5))
        
        ctk.CTkButton(mod_mgmt_frame, text="📂 Seleccionar carpeta del Mod...", command=self.select_mod_dir_manual,
                      height=40, fg_color="#3a3a3a", hover_color="#4a4a4a",
                      border_width=2, border_color="#505050").pack(fill='x', padx=15, pady=(5,10))

        # Carpetas de Escaneo
        scan_frame = ctk.CTkFrame(settings_scroll, fg_color="#1a1a1a", corner_radius=8)
        scan_frame.pack(fill='x', pady=10)
        ctk.CTkLabel(scan_frame, text="Carpetas de Escaneo", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor='w', padx=15, pady=(10,5))
        ctk.CTkButton(scan_frame, text="📁 Gestionar Carpetas de Juegos...", command=self.open_scan_folders_manager,
                      height=40, fg_color="#3a3a3a", hover_color="#4a4a4a", font=ctk.CTkFont(size=13, weight="bold"),
                      border_width=2, border_color="#505050").pack(fill='x', padx=15, pady=(5,10))

        # Guardar Log
        log_frame = ctk.CTkFrame(settings_scroll, fg_color="#1a1a1a", corner_radius=8)
        log_frame.pack(fill='x', pady=10)
        ctk.CTkLabel(log_frame, text="Registro de Operaciones", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor='w', padx=15, pady=(10,5))
        ctk.CTkButton(log_frame, text="💾 Guardar Log", command=self.save_log_to_file,
                      height=40, fg_color="#3a3a3a", hover_color="#4a4a4a", font=ctk.CTkFont(size=13, weight="bold"),
                      border_width=2, border_color="#505050").pack(fill='x', padx=15, pady=(0,10))

        # Modo Gaming (al final)
        gaming_opts_frame = ctk.CTkFrame(settings_scroll, fg_color="#1a1a1a", corner_radius=8)
        gaming_opts_frame.pack(fill='x', pady=10)
        ctk.CTkLabel(gaming_opts_frame, text="Salir", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor='w', padx=15, pady=(10,5))
        ctk.CTkButton(gaming_opts_frame, text="Salir del Modo Gaming", command=self.toggle_gaming_mode,
                      height=40, fg_color="#3a3a3a", hover_color="#4a4a4a",
                      border_width=2, border_color="#505050").pack(fill='x', padx=15, pady=(0,10))

        self.gaming_settings_panel.grid_remove()
        
        # Detectar mods descargados después de crear los dropdowns
        self.autodetect_mod_source()
    
    def show_gaming_config(self):
        """Muestra el panel de configuración del mod."""
        self._hide_all_gaming_panels()
        self.gaming_config_panel.grid()
        self._update_gaming_nav_highlight("config")
        # Actualizar lista de widgets navegables si estamos en modo gaming
        if hasattr(self, 'gaming_mode_var') and self.gaming_mode_var.get():
            self.gaming_content_focused_index = 0  # Reiniciar índice
            self.after(50, self.rebuild_gaming_content_widgets)
    
    def show_gaming_auto(self):
        """Muestra el panel de detección automática."""
        self._hide_all_gaming_panels()
        self.gaming_auto_panel.grid()
        self._update_gaming_nav_highlight("auto")
        self.populate_gaming_games()
        # Actualizar lista de widgets navegables si estamos en modo gaming
        if hasattr(self, 'gaming_mode_var') and self.gaming_mode_var.get():
            self.gaming_content_focused_index = 0  # Reiniciar índice
            self.after(50, self.rebuild_gaming_content_widgets)
    
    def show_gaming_manual(self):
        """Muestra el panel de ruta manual."""
        self._hide_all_gaming_panels()
        self.gaming_manual_panel.grid()
        self._update_gaming_nav_highlight("manual")
        # Actualizar lista de widgets navegables si estamos en modo gaming
        if hasattr(self, 'gaming_mode_var') and self.gaming_mode_var.get():
            self.gaming_content_focused_index = 0  # Reiniciar índice
            self.after(50, self.rebuild_gaming_content_widgets)
    
    def show_gaming_settings(self):
        """Muestra el panel de ajustes de la app."""
        self._hide_all_gaming_panels()
        self.gaming_settings_panel.grid()
        self._update_gaming_nav_highlight("settings")
        # Actualizar lista de widgets navegables si estamos en modo gaming
        if hasattr(self, 'gaming_mode_var') and self.gaming_mode_var.get():
            self.gaming_content_focused_index = 0  # Reiniciar índice
            self.after(50, self.rebuild_gaming_content_widgets)
    
    def show_gaming_help(self):
        """Muestra la ventana de ayuda de la interfaz gaming."""
        self.show_help_popup("Guía Rúpida - Interfaz Gaming ??", GAMING_HELP_TEXT)
        # No cambiar de panel, mantener el activo
    
    def _hide_all_gaming_panels(self):
        """Oculta todos los paneles de contenido."""
        for panel in [self.gaming_config_panel, self.gaming_auto_panel, self.gaming_manual_panel,
                       self.gaming_settings_panel]:
            panel.grid_remove()
    
    def _update_gaming_nav_highlight(self, active_key):
        """Resalta el botón activo en el menóú de navegación con bordes de color."""
        # Guardar cuúl es el botón activo para usarlo en update_focus_visuals_gaming
        self.gaming_active_nav_key = active_key
        
        for key, btn in self.gaming_nav_buttons.items():
            if key == active_key:
                # Botón activo (panel abierto): borde AZUL
                btn.configure(border_color="#00BFFF", border_width=3)
            else:
                # Botones inactivos: borde gris suótil
                btn.configure(border_color="#505050", border_width=2)

    def _get_default_border_color(self):
        """Obtiene el color y ancho de borde por defecto de los widgets."""
        try:
             self.update_idletasks()
             # Intentar obtener un color de borde desde un widget existente; usar tema como respaldo
             if hasattr(self, 'btn_download'):
                 color_source = self.btn_download.cget("border_color")
             elif hasattr(self, 'main_content_frame'):
                 color_source = self.main_content_frame.cget("border_color")
             else:
                 color_source = ctk.ThemeManager.theme["CTkFrame"]["border_color"]

             self.default_frame_border_color = self._apply_appearance_mode(color_source)
             self.default_frame_border_width = ctk.ThemeManager.theme["CTkFrame"]["border_width"]
             if self.default_frame_border_width is None:
                self.default_frame_border_width = 0

             if self.default_frame_border_color is None or self.default_frame_border_color == "transparent":
                 self.default_frame_border_color = self._apply_appearance_mode(ctk.ThemeManager.theme["CTkFrame"]["border_color"])
                 if self.default_frame_border_color is None:
                     self.default_frame_border_color = "#565B5E"
             
             self.update_focus_visuals()
        except Exception as e:
            print(f"Error al obtener/aplicar color de borde por defecto: {e}")
            self.default_frame_border_color = "#565B5E"
            self.default_frame_border_width = 0
            
    # --- NUEVAS FUNCIONES (Mejora 3): Gestiún Carpetas Custom ---
    
    # --- MODIFICADO (V2.0 Mejora): Muestra contador de juegos ---
    def refresh_custom_folders_list(self, scan_on_load=True):
        """Limpia y recarga la lista de carpetas personalizadas en la Pestaña 4."""
        if not hasattr(self, 'custom_folders_list_frame'):
            return
            
        for widget in self.custom_folders_list_frame.winfo_children():
            widget.destroy()
        
        # --- REFACTORIZADA (V2.0): Aúadir a la lista de navegación ---
        self.navigable_widgets[3] = [
            [self.btn_add_folder, self.btn_rescan], # Fila 0
            # Fila 1 (lista de carpetas) se aúade dinúmicamenóte
            [self.btn_clean_logs, self.btn_clean_orphan_baks] # Fila 2
        ]
        folder_rows = []
        # --- Fin Refactor ---

        if not self.custom_search_folders:
            ctk.CTkLabel(self.custom_folders_list_frame, text="No se han aúadido carpetas.").pack(pady=10)
            return

        # Escanear solo si se pide (para no ralentizar el inicio)
        game_counts = {}
        if scan_on_load:
            for game_path, name, _, _, _ in self.all_games_data:
                if name.startswith("[CUSTOM]"):
                    # Encontrar a quú carpeta base pertenece
                    for folder_base in self.custom_search_folders:
                        try:
                            if os.path.samefile(os.path.commonpath([game_path, folder_base]), folder_base):
                                game_counts[folder_base] = game_counts.get(folder_base, 0) + 1
                                break
                        except Exception:
                            pass # Ignorar errores de path

        for i, folder_path in enumerate(self.custom_search_folders):
            item_frame = ctk.CTkFrame(self.custom_folders_list_frame, fg_color="transparent")
            item_frame.grid(row=i, column=0, sticky='ew', pady=2)
            item_frame.grid_columnconfigure(0, weight=1)
            
            count = game_counts.get(folder_path, 0)
            count_text = f" ({count} juego{'s' if count != 1 else ''} encontrado{'s' if count != 1 else ''})" if scan_on_load and count > 0 else ""
            
            label = ctk.CTkLabel(item_frame, text=f"{folder_path}{count_text}", font=ctk.CTkFont(size=12))
            label.grid(row=0, column=0, sticky='w', padx=5)
            
            remove_btn = ctk.CTkButton(item_frame, text="X", command=lambda p=folder_path: self.remove_custom_folder(p), width=30, height=30, fg_color="#3a3a3a", hover_color="#4a4a4a")
            remove_btn.grid(row=0, column=1, sticky='e', padx=5)
            
            # --- REFACTORIZADA (V2.0): Aúadir a la lista de navegación ---
            folder_rows.append([item_frame, remove_btn]) # Frame y botón son navegables
        
        # Insertar las filas de carpetas en la lista de navegación
        self.navigable_widgets[3] = self.navigable_widgets[3][:1] + folder_rows + self.navigable_widgets[3][1:]
    
    def add_custom_folder(self):
        """Abre un diúlogo para aúadir una carpeta de búsqueda."""
        initial_dir = r"C:\\"
        dir_path = filedialog.askdirectory(
            title="Seleccionar Carpeta que Contiene Juegos (ej. D:\\GOG Games)",
            initialdir=initial_dir
        )
        if dir_path:
            dir_path = os.path.normpath(dir_path)
            if dir_path not in self.custom_search_folders:
                self.custom_search_folders.append(dir_path)
                self.save_config()
                self.refresh_custom_folders_list(scan_on_load=False)
                self.log_message('INFO', f"Carpeta personalizada aúadida: {dir_path}")
                self.log_message('WARN', "úRecuerde pulsar 'Re-escanear' para encontrar los juegos!")
            else:
                self.log_message('WARN', "Esa carpeta ya estú en la lista.")
        else:
            self.log_message('WARN', "Selecciún de carpeta cancelada.")

    def remove_custom_folder(self, folder_path):
        """Quita una carpeta de la lista de búsqueda."""
        if folder_path in self.custom_search_folders:
            self.custom_search_folders.remove(folder_path)
            self.save_config()
            self.refresh_custom_folders_list(scan_on_load=True) # Refrescar con contadores
            self.log_message('INFO', f"Carpeta personalizada eliminada: {folder_path}")

    # --- NUEVO (V2.0 Mejora A): Barras de progreso indeterminadas ---
    def start_indeterminate_progress(self, tab_index):
        bar = self.progress_bar_app if tab_index == 3 else self.progress_bar_auto
        if tab_index == 3:
            bar.grid(row=2, column=0, sticky='ew', padx=15, pady=(5, 10))
        else:
            # --- MODIFICADO (V5): Fila de progreso actualizada ---
            bar.grid(row=3, column=0, sticky='ew', padx=5, pady=(5,5))
        bar.configure(mode="indeterminate")
        bar.start()

    def stop_indeterminate_progress(self, tab_index):
        bar = self.progress_bar_app if tab_index == 3 else self.progress_bar_auto
        bar.stop()
        bar.configure(mode="determinate")
        bar.set(0)
        bar.grid_remove() # Ocultarla

    def rescan_all_games_threaded(self):
        """Ejecuta rescan_all_games en un hilo para mostrar progreso."""
        self.start_indeterminate_progress(3)
        self.btn_rescan.configure(state="disabled")
        self.btn_add_folder.configure(state="disabled")
        threading.Thread(target=self._rescan_worker, daemon=True).start()
        
    def _rescan_worker(self):
        self.log_message('TITLE', "Iniciando re-escaneo de todos los juegos...")
        self.all_games_data = scan_games(self.log_message, self.custom_search_folders)
        
        # Guardar cachéú actualizada
        save_games_caché(self.all_games_data, self.log_message)
        
        self.filter_games() # Esto recarga y filtra la lista
        self.log_message('OK', "Re-escaneo completado.")
        self.after(0, self.refresh_custom_folders_list, True) # Actualizar contadores
        self.after(0, self.stop_indeterminate_progress, 3)
        self.after(0, self.btn_rescan.configure, {"state": "normal"})
        self.after(0, self.btn_add_folder.configure, {"state": "normal"})
    # --- NUEVO (Mejora #2): Bindear clicks a todos los widgets navegables ---
    def _bind_click_to_navigables(self):
        """Añade binding de click a todos los widgets navegables para actualizar foco."""
        for tab_idx, nav_list in self.navigable_widgets.items():
            for row in nav_list:
                for widget in row:
                    if isinstance(widget, (ctk.CTkButton, ctk.CTkRadioButton, ctk.CTkSwitch, ctk.CTkCheckBox)):
                        # Wrapper para capturar el widget correcto
                        widget.bind("<Button-1>", lambda e, w=widget: self.update_focus_from_click(w), add="+")
        
        
    # --- NUEVO (Mejora #2): Actualizar foco al hacer click ---
    def update_focus_from_click(self, widget):
        """Actualiza el índice de foco cuando se hace click en un widget navegable."""
        # Buscar el widget en la lista de navegación de la pestaña actual
        nav_list = self.navigable_widgets.get(self.current_tab_index, [])
        for row_idx, row in enumerate(nav_list):
            for col_idx, nav_widget in enumerate(row):
                if nav_widget == widget:
                    self.focus_location = 'content'
                    self.focused_indices[self.current_tab_index] = [row_idx, col_idx]
                    self.update_focus_visuals()
                    return
        
    # --- NUEVO (Mejora 6): Abrir selector custom ---
    def open_custom_select(self, title, options, button_widget, text_prefix, string_var):
        """Abre un popup de selecciún navegable."""
        # Actualizar foco al hacer click en el botón
        self.update_focus_from_click(button_widget)
        
        if self.active_popup:
            try: self.active_popup.focus_force()
            except: self.on_popup_closed()
            return
            
        current_value = string_var.get()
        
        # --- NUEVO (V5): Callback para manejar el resultado ---
        def on_selection_made(new_value):
            if new_value:
                string_var.set(new_value)
                button_widget.configure(text=f"{text_prefix}{new_value}")
                self.mark_config_as_custom()  # Marcar como Custom al cambiar
                self.save_config() # Guardar automáticamente al cambiar
            
            self.active_popup = None # De-registrar popup
            self.focus_set() # Devolver foco a la ventana principal

        select_window = CustomSelectWindow(self, title, options, current_value, self.log_message, on_selection_made)
        self.active_popup = select_window
        # --- NUEVO (Mejora 10): Binding de Teclado ---
        select_window.bind("<Escape>", lambda e: select_window.on_cancel())
        select_window.grab_set()
# --- Funciones de Configuración ---
    
    # --- MODIFICADO (Mejora 3): Carga/Guarda carpetas personalizadas ---
    def load_config(self):
        """Carga la configuración desde config.json."""
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                    # --- MODIFICADO (V2.0): Ya no carga mod_source_dir, lo detecta
                    self.gpu_choice.set(config.get("gpu_choice", 2 if self.is_nvidia else 1))
                    default_dll = SPOOFING_OPTIONS.get(1, "dxgi.dll")
                    self.spoof_dll_name_var.set(config.get("spoof_dll_name", default_dll))
                    self.fg_mode_var.set(config.get("fg_mode", "Automático"))
                    self.upscaler_var.set(config.get("upscaler", "Automático"))
                    self.upscale_mode_var.set(config.get("upscale_mode", "Automático"))
                    self.sharpness_var.set(config.get("sharpness", 0.8))
                    self.sharpness_label_var.set(f"{self.sharpness_var.get():.2f}")
                    self.overlay_var.set(config.get("overlay", False))
                    self.motion_blur_var.set(config.get("motion_blur", True))
                    self.theme_var.set(config.get("theme", "Oscuro"))
                    self.scale_var.set(config.get("scale", "100%"))
                    self.gaming_mode_var.set(config.get("gaming_mode", False))
                    self.custom_search_folders = config.get(CUSTOM_SEARCH_FOLDERS_CONFIG_KEY, [])
                    
                    # Apply theme and scale on startup
                    theme_map = {"Claro": "light", "Oscuro": "dark", "Sistema": "system"}
                    ctk.set_appearance_mode(theme_map.get(self.theme_var.get(), "dark"))
                    
                    scale_map = {"80%": 0.8, "90%": 0.9, "100%": 1.0, "110%": 1.1, "120%": 1.2}
                    ctk.set_widget_scaling(scale_map.get(self.scale_var.get(), 1.0))
                    
                    # Log para debug del gaming mode
                    gaming_loaded = self.gaming_mode_var.get()
                    self.log_message('INFO', f"Configuración cargada. Gaming mode: {gaming_loaded}")
                    self.log_message('INFO', f"Archivo config: {CONFIG_FILE}")
                    
                    if hasattr(self, 'custom_folders_list_frame'):
                        self.refresh_custom_folders_list(scan_on_load=False) # No escanear juegos aquú
            else:
                 self.log_message('INFO', "Archivo de configuración no encontrado, usando valores por defecto.")
                 self.gpu_choice.set(2 if self.is_nvidia else 1)
                 self.spoof_dll_name_var.set(SPOOFING_OPTIONS.get(1, "dxgi.dll"))
                 self.fg_mode_var.set("Automático")
                 self.upscaler_var.set("Automático")
                 self.upscale_mode_var.set("Automático")
                 self.sharpness_var.set(0.8)
                 self.sharpness_label_var.set("0.80")
                 self.overlay_var.set(False)
                 self.motion_blur_var.set(True)
                 self.theme_var.set("Oscuro")
                 self.scale_var.set("100%")
                 self.gaming_mode_var.set(False)
                 self.custom_search_folders = []
            
            # --- NUEVO (V2.0): Autodetectar mod_source_dir al inicio ---
            self.autodetect_mod_source() # Esto ahora rellena el ComboBox
            
            # --- NUEVO (V5): Actualizar texto de botones de selecciún ---
            if hasattr(self, 'btn_dll_select'):
                self.btn_dll_select.configure(text=f"{self.spoof_dll_name_var.get()}")
            if hasattr(self, 'btn_fg_select'):
                self.btn_fg_select.configure(text=f"{self.fg_mode_var.get()}")
            if hasattr(self, 'btn_upscaler_select'):
                self.btn_upscaler_select.configure(text=f"{self.upscaler_var.get()}")
            if hasattr(self, 'btn_upscale_select'):
                self.btn_upscale_select.configure(text=f"{self.upscale_mode_var.get()}")

            
            # --- NUEVO (V2.1 Handheld): Aplicar modo gaming si estaba activado ---
            gaming_should_apply = self.gaming_mode_var.get()
            print(f"[DEBUG] Fin de load_config - gaming_mode_var: {gaming_should_apply}")
            if gaming_should_apply:
                # Programar aplicaciún del modo gaming después de que la UI estú completamente construida
                self.after(200, self._apply_gaming_mode_on_startup)
                print("[DEBUG] Programado _apply_gaming_mode_on_startup para 200ms")
            else:
                # Programar aplicaciún del modo clúsico para asegurar que gaming estú oculto
                self.after(200, self._apply_classic_mode_on_startup)
                print("[DEBUG] Programado _apply_classic_mode_on_startup para 200ms")

        except Exception as e:
            self.log_message('ERROR', f"Error al cargar la configuración: {e}")

            # Establecer valores por defecto en caso de error
            self.gpu_choice.set(2 if self.is_nvidia else 1)
            self.spoof_dll_name_var.set(SPOOFING_OPTIONS.get(1, "dxgi.dll"))
            self.fg_mode_var.set("Automático")
            self.upscaler_var.set("Automático")
            self.upscale_mode_var.set("Automático")
            self.sharpness_var.set(0.8)
            self.sharpness_label_var.set("0.80")
            self.overlay_var.set(False)
            self.motion_blur_var.set(True)
            self.custom_search_folders = []
            self.custom_search_folders = []


    def save_config(self, *args):
        """Guarda la configuración actual en config.json."""
        # --- MODIFICADO (V2.0 Refactor): Asegurar que las variables estún actualizadas ---
        # (Esto ahora es redundante porque el callback de open_custom_select lo hace, pero es seguro)
        if hasattr(self, 'btn_dll_select'):
            self.spoof_dll_name_var.set(self.btn_dll_select.cget("text").split(":")[-1].strip().replace(" ?", ""))
        if hasattr(self, 'btn_fg_select'):
            self.fg_mode_var.set(self.btn_fg_select.cget("text").split(":")[-1].strip().replace(" ?", ""))
        if hasattr(self, 'btn_upscaler_select'):
            self.upscaler_var.set(self.btn_upscaler_select.cget("text").split(":")[-1].strip().replace(" ?", ""))
        if hasattr(self, 'btn_upscale_select'):
            self.upscale_mode_var.set(self.btn_upscale_select.cget("text").split(":")[-1].strip().replace(" ?", ""))

        config = {
            # "mod_source_dir" ya no se guarda, es automático
            "gpu_choice": self.gpu_choice.get(),
            "spoof_dll_name": self.spoof_dll_name_var.get(), 
            "fg_mode": self.fg_mode_var.get(),
            "upscaler": self.upscaler_var.get(),
            "upscale_mode": self.upscale_mode_var.get(),
            "sharpness": self.sharpness_var.get(),
            "overlay": self.overlay_var.get(),
            "motion_blur": self.motion_blur_var.get(),
            "theme": self.theme_var.get(),
            "scale": self.scale_var.get(),
            "gaming_mode": self.gaming_mode_var.get(),
            CUSTOM_SEARCH_FOLDERS_CONFIG_KEY: self.custom_search_folders
        }
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(config, f, indent=4)
            # Log para confirmar que se guardú
            print(f"[DEBUG] Config guardado - gaming_mode: {config['gaming_mode']}")
        except Exception as e:
            self.log_message('ERROR', f"Error al guardar la configuración: {e}")

    def on_closing(self):
        """Se ejecuta al cerrar la ventana."""
        # Log para debug
        gaming_state = self.gaming_mode_var.get()
        self.log_message('INFO', f"Cerrando app - Modo gaming: {gaming_state}")
        self.save_config()
        if PYGAME_AVAILABLE:
             pygame.quit()
        self.destroy()

    # --- Funciones de Log y Ayuda ---

    def log_message(self, message_type, message):
        """Muestra un menósaje con color en el úrea de log."""
        tag_config = {
            'INFO': ('#00FF00', '[INFO] '),  'WARN': ('#FFFF00', '[WARN] '),
            'ERROR': ('#FF4500', '[ERROR] '), 'TITLE': ('#00BFFF', '[OP] '),
            'OK': ('#00FF00', '[OK] ')
        }
        color, prefix = tag_config.get(message_type, ('white', ''))

        if hasattr(self, 'log_text'):
            self.log_text.configure(state="normal")
            self.log_text.insert("end", prefix, message_type)
            self.log_text.tag_config(message_type, foreground=color)
            self.log_text.insert("end", f"{message}\n")
            
            # --- NUEVO (V2.0 Mejora C): Auto-scroll condicional ---
            if self.log_auto_scroll_var.get():
                self.log_text.see("end")
                
            self.log_text.configure(state="disabled")
        else:
             print(f"{prefix}{message}")


    def show_recommended_settings(self):
        """Muestra la configuración recomenódada en el log al inicio."""
        check_registry_override(self.log_message)
        gpu_type = "NVIDIA (Detectado)" if self.gpu_choice.get() == 2 else "AMD/Intel (Detectado o por Defecto)"
        spoof_name = self.spoof_dll_name_var.get()
        self.log_message('INFO', "--------------------------------------------------")
        self.log_message('INFO', "AJUSTES RECOMENDADOS CARGADOS:")
        self.log_message('INFO', f"GPU: {gpu_type}")
        self.log_message('INFO', f"DLL de Inyecciún: {spoof_name}")
        self.log_message('INFO', f"Modo Frame Gen: {self.fg_mode_var.get()}")
        self.log_message('INFO', "--------------------------------------------------")

    # --- MODIFICADO (Mejora Mando): Registra popups ---
    def show_help_popup(self, title, message_text):
        """Muestra una ventana emergente (Toplevel) con texto de ayuda."""
        # --- MODIFICADO (V2.0 Pulida): Comprobaciún de Tooltip eliminada ---
        if self.active_popup: 
            try: self.active_popup.focus_force()
            except: self.on_popup_closed() # Limpiar popup muerto
            return
            
        try:
            help_window = ctk.CTkToplevel(self)
            help_window.title(title)
            
            win_width = 750
            win_height = 550
            x = self.winfo_x() + (self.winfo_width() // 2) - (win_width // 2)
            y = self.winfo_y() + (self.winfo_height() // 2) - (win_height // 2)
            help_window.geometry(f'{win_width}x{win_height}+{x}+{y}')
            
            help_window.transient(self) # Mantener por encima
            help_window.grab_set() # Modal
            
            # --- Registrar popup ---
            self.active_popup = help_window
            help_window.bind("<Destroy>", self.on_popup_closed)
            
            help_text_widget = ctk.CTkTextbox(help_window, wrap="word", corner_radius=8, font=ctk.CTkFont(size=12))
            help_text_widget.pack(fill='both', expand=True, padx=15, pady=15)
            help_text_widget.insert("end", message_text)
            help_text_widget.configure(state="disabled")
            
            close_btn = ctk.CTkButton(help_window, text="Cerrar (B / Esc)", command=help_window.destroy, fg_color="#3a3a3a", hover_color="#4a4a4a")
            close_btn.pack(pady=(0, 10))
            
            # --- NUEVO (Mejora 10): Binding de Teclado ---
            help_window.bind("<Escape>", lambda e: help_window.destroy())
            
            help_window.after(100, help_window.focus_force) # Forzar foco a la ventana
            
        except Exception as e:
            self.log_message('ERROR', f"No se pudo abrir la ventana de ayuda: {e}")
            if self.active_popup: self.active_popup = None # Reset
            
    # --- NUEVA FUNCIúN (Mejora Mando): Des-registra popups ---
    def on_popup_closed(self, event=None):
        """Se llama cuando una ventana emergente se cierra para des-registrarla."""
        # --- MODIFICADO (V2.0 Pulida): Comprobaciún de Tooltip eliminada ---

        # Solo des-registrar si la ventana que se cierra es la que tenúamos registrada
        if self.active_popup and event and str(event.widget).startswith(str(self.active_popup)):
             self.active_popup = None
        elif not event: # Limpieza forzada
             self.active_popup = None
        elif self.active_popup and not hasattr(self.active_popup, 'winfo_exists'):
            self.active_popup = None # Limpieza de popups muertos

    def update_sharpness_label_and_save(self, value):
        """Actualiza la etiqueta de nitidez y guarda la configuración."""
        self.sharpness_label_var.set(f"{value:.2f}")
        self.mark_config_as_custom()  # Marcar como Custom al cambiar
        self.save_config()


    # --- Funciones de Carga y Diúlogos ---
    
    def open_filter_popup(self):
        """Abre una ventana emergente con los filtros de plataforma."""
        filter_window = ctk.CTkToplevel(self)
        filter_window.title("Filtrar por Plataforma")
        filter_window.geometry("300x200")
        filter_window.transient(self)
        filter_window.grab_set()
        
        # Centrar ventana
        filter_window.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() // 2) - (300 // 2)
        y = self.winfo_y() + (self.winfo_height() // 2) - (200 // 2)
        filter_window.geometry(f"+{x}+{y}")
        
        ctk.CTkLabel(filter_window, text="Selecciona Plataformas:", 
                    font=ctk.CTkFont(size=14, weight="bold")).pack(pady=15)
        
        # Checkboxes de filtro
        cb_frame = ctk.CTkFrame(filter_window, fg_color="transparent")
        cb_frame.pack(fill='both', expand=True, padx=20)
        
        ctk.CTkCheckBox(cb_frame, text="Steam", variable=self.filter_steam_var, 
                       command=self.filter_games, font=ctk.CTkFont(size=13)).pack(anchor='w', pady=5)
        ctk.CTkCheckBox(cb_frame, text="Xbox", variable=self.filter_xbox_var, 
                       command=self.filter_games, font=ctk.CTkFont(size=13)).pack(anchor='w', pady=5)
        ctk.CTkCheckBox(cb_frame, text="Epic", variable=self.filter_epic_var, 
                       command=self.filter_games, font=ctk.CTkFont(size=13)).pack(anchor='w', pady=5)
        ctk.CTkCheckBox(cb_frame, text="Custom", variable=self.filter_custom_var, 
                       command=self.filter_games, font=ctk.CTkFont(size=13)).pack(anchor='w', pady=5)
        
        # Botón cerrar
        ctk.CTkButton(filter_window, text="Cerrar", command=filter_window.destroy,
                     fg_color="#3a3a3a", hover_color="#4a4a4a").pack(pady=10)
    
    # --- MODIFICADO (V5): Filtra por plataforma y texto ---
    def filter_games(self, event=None):
        """Filtra la lista de juegos basíndose en el texto y los checkboxes."""
        filter_text = self.game_filter_var.get().lower()
        
        # Obtener los filtros de plataforma
        active_filters = []
        if self.filter_steam_var.get(): active_filters.append("Steam")
        if self.filter_xbox_var.get(): active_filters.append("Xbox")
        if self.filter_epic_var.get(): active_filters.append("Epic")
        if self.filter_custom_var.get(): active_filters.append("Custom")

        self.filtered_game_indices = []
        for i, (_, name, _, _, platform_tag) in enumerate(self.all_games_data):
            # 1. Comprobar filtro de plataforma
            if platform_tag not in active_filters:
                continue
            # 2. Comprobar filtro de texto
            if filter_text and filter_text not in name.lower():
                continue
            
            # Si pasa ambos, aúadirlo
            self.filtered_game_indices.append(i)

        self.load_game_list(filtered_indices=self.filtered_game_indices)
        if self.current_tab_index == 1:
            self.focus_location = 'content'
            self.focused_indices[1] = [0, 0] # Resetear foco a [0,0]
            self.update_focus_visuals()

    # --- MODIFICADO (V5): Nuevo diseúo de fila y navegación 2D ---
    def load_game_list(self, filtered_indices=None):
        """Carga los juegos en el CTkScrollableFrame, opcionalmenóte filtrados."""
        for widget in self.game_list_frame.winfo_children():
            widget.destroy()
        
        # --- REFACTORIZADA (V5): Lista de navegación de la Pestaña AUTO (índice 1) ---
        # MODIFICADO (V2.1 Performance): índices ajustados por botón de escaneo y filtro
        self.navigable_widgets[1] = [
            [self.btn_scan_games, self.btn_filter],  # Fila 0 (Botones de escaneo y filtro)
            [self.entry_filter], # Fila 1 (Búsqueda)
            # Fila 2+ (Lista de juegos) se aúade dinúmicamenóte
            # Los botones de acciún de abajo se eliminan de la navegación (Mejora 11)
        ]
        game_rows = []
        # --- Fin Refactor ---

        indices_to_display = filtered_indices if filtered_indices is not None else list(range(len(self.all_games_data)))

        if not self.all_games_data:
            ctk.CTkLabel(self.game_list_frame, text="No se detectaron juegos instalados.").pack(pady=10)
            return
        if not indices_to_display:
            ctk.CTkLabel(self.game_list_frame, text="Ningún juego coincide con el filtro o las plataformas seleccionadas.").pack(pady=10)
            return

        self.highlight_color = ("#DCE4EE", "#003355")
        
        for display_index, original_index in enumerate(indices_to_display):
            game_path, name, status, exe_name, platform_tag = self.all_games_data[original_index]
            display_name = name.split(']')[-1].strip() # Quitar [STEAM], etc. del nombre
            status_text = f"({status})"
            is_installed = "INSTALADO" in status
            
            status_color = "#FFFFFF"
            if is_installed: status_color = "#00FF00"
            elif "AUSENTE" in status: status_color = "#FFFF00"
            elif "ERROR" in status: status_color = "#FF4500"

            item_frame = ctk.CTkFrame(self.game_list_frame, fg_color="transparent", corner_radius=6)
            item_frame.grid(row=display_index, column=0, sticky='ew', padx=5, pady=1)
            
            # --- NUEVA LúGICA DE GRID (Mejora 4) ---
            item_frame.grid_columnconfigure(0, weight=6) # Columna 0 (Nombre/Exe) - 60%
            item_frame.grid_columnconfigure(1, weight=2) # Columna 1 (Plataforma/DLL) - 20%
            item_frame.grid_columnconfigure(2, weight=3) # Columna 2 (Botones) - 30%
            
            if original_index not in self.game_checkbox_vars:
                self.game_checkbox_vars[original_index] = ctk.BooleanVar()
            checkbox_var = self.game_checkbox_vars[original_index]

            def on_toggle(var, frame_widget, orig_idx):
                highlight_bg = self._apply_appearance_mode(self.highlight_color)
                if var.get():
                    frame_widget.configure(fg_color=highlight_bg)
                else:
                    frame_widget.configure(fg_color="transparent")
            
            # --- Columna 0: Nombre y Checkbox ---
            name_frame = ctk.CTkFrame(item_frame, fg_color="transparent")
            name_frame.grid(row=0, column=0, rowspan=2, sticky='w', padx=5)
            
            cb = ctk.CTkCheckBox(name_frame, text=display_name, text_color="#FFFFFF", font=ctk.CTkFont(size=11), variable=checkbox_var)
            cb.configure(command=lambda v=checkbox_var, f=item_frame, oi=original_index: on_toggle(v, f, oi))
            cb.grid(row=0, column=0, sticky='w', pady=(4,0))
            
            exe_label_text = f"  -> {exe_name}" if exe_name else "  -> (No se detectú .exe)"
            exe_label = ctk.CTkLabel(name_frame, text=exe_label_text, text_color="gray70", font=ctk.CTkFont(size=9))
            exe_label.grid(row=1, column=0, sticky='w', pady=(0,4), padx=(20,0))
            
            # --- Columna 1: Plataforma y DLL ---
            info_frame = ctk.CTkFrame(item_frame, fg_color="transparent")
            info_frame.grid(row=0, column=1, rowspan=2, sticky='w', padx=5)
            
            plat_label = ctk.CTkLabel(info_frame, text=f"Plataforma: {platform_tag}", font=ctk.CTkFont(size=10))
            plat_label.grid(row=0, column=0, sticky='w')
            status_label = ctk.CTkLabel(info_frame, text=f"Estado: {status_text}", text_color=status_color, font=ctk.CTkFont(size=10, weight="bold"))
            status_label.grid(row=1, column=0, sticky='w')

            # --- Columna 2: Botones ---
            button_frame = ctk.CTkFrame(item_frame, fg_color="transparent")
            button_frame.grid(row=0, column=2, rowspan=2, sticky='e', padx=(0, 5))
            
            game_nav_row = [item_frame] # La fila navegable empieza con el frame (para seleccionar)
            
            if is_installed:
                btn_launch_game = ctk.CTkButton(
                    button_frame, text="🚀", width=30, height=28,
                    command=lambda p=game_path, e=exe_name: self.launch_game(p, e),
                    fg_color="#3a3a3a", hover_color="#4a4a4a"
                )
                btn_launch_game.grid(row=0, column=0, sticky='e', padx=(0, 5))
                if not exe_name: btn_launch_game.configure(state="disabled") # Desactivar si no hay .exe
                game_nav_row.append(btn_launch_game)
                
                btn_open_folder = ctk.CTkButton(
                    button_frame, text="📁", width=30, height=28,
                    command=lambda p=game_path: self.open_game_folder(p),
                    fg_color="#3a3a3a", hover_color="#4a4a4a"
                )
                btn_open_folder.grid(row=0, column=1, sticky='e', padx=(0, 5))
                game_nav_row.append(btn_open_folder)

                btn_config_game = ctk.CTkButton(
                    button_frame, text="⚙️", width=30, height=28,
                    command=lambda p=game_path, n=name: self.open_game_config_window(p, n),
                    fg_color="#3a3a3a", hover_color="#4a4a4a"
                )
                btn_config_game.grid(row=0, column=2, sticky='e', padx=(0, 5))
                game_nav_row.append(btn_config_game)
                
                btn_restore_bak = ctk.CTkButton(
                    button_frame, text="Rest.", width=50, height=28,
                    command=lambda p=game_path: self.run_game_list_restore_bak(p),
                    fg_color="#3a3a3a", hover_color="#4a4a4a"
                )
                btn_restore_bak.grid(row=0, column=3, sticky='e', padx=(0, 5))
                game_nav_row.append(btn_restore_bak)
            else:
                # Mostrar solo botón de abrir carpeta cuando no está instalado
                btn_open_folder = ctk.CTkButton(
                    button_frame, text="📁", width=30, height=28,
                    command=lambda p=game_path: self.open_game_folder(p),
                    fg_color="#3a3a3a", hover_color="#4a4a4a"
                )
                btn_open_folder.grid(row=0, column=0, sticky='e', padx=(0, 5))
                game_nav_row.append(btn_open_folder)
            
            def toggle_and_highlight(event, v=checkbox_var, f=item_frame, oi=original_index):
                v.set(not v.get())
                on_toggle(v, f, oi)
            
            item_frame.bind("<Button-1>", toggle_and_highlight)
            status_label.bind("<Button-1>", toggle_and_highlight)
            exe_label.bind("<Button-1>", toggle_and_highlight)
            plat_label.bind("<Button-1>", toggle_and_highlight)
            cb.bind("<Button-1>", lambda e: e.tk_focusPrev())
            
            item_frame.original_index = original_index 
            game_rows.append(game_nav_row) # Aúadir la fila de widgets navegables
        
        # Insertar las filas de juegos en la lista de navegación
        self.navigable_widgets[1] = self.navigable_widgets[1][:2] + game_rows + self.navigable_widgets[1][2:]
        
        # Resetear foco si estú fuera de lúmites
        current_focus = self.focused_indices[1]
        if current_focus[0] >= len(self.navigable_widgets[1]):
             self.focused_indices[1] = [0, 0]


    # --- NUEVA FUNCIúN (V2.0 Pulida): Abrir Carpeta ---
    def open_game_folder(self, game_path):
        """Abre la carpeta del juego en el explorador de archivos."""
        if not game_path or not os.path.isdir(game_path):
            self.log_message('ERROR', f"Ruta no vúlida o no seleccionada: {game_path}")
            messagebox.showerror("Error de Ruta", "La ruta de la carpeta no es vúlida o no existe.", parent=self)
            return
        
        try:
            self.log_message('INFO', f"Abriendo carpeta: {game_path}")
            # Usar os.path.realpath para resolver cualquier enlace simbúlico
            os.startfile(os.path.realpath(game_path))
        except Exception as e:
            self.log_message('ERROR', f"No se pudo abrir la carpeta {game_path}: {e}")
            messagebox.showerror("Error", f"No se pudo abrir la carpeta:\n{e}", parent=self)

    # --- NUEVA FUNCIúN (V2.0 Pulida): Lanzar Juego ---
    def launch_game(self, game_path, exe_name):
        """Lanza el ejecutable del juego."""
        if not game_path or not exe_name:
            self.log_message('ERROR', "Ruta o nombre de .exe no vúlidos para lanzar.")
            return
        
        exe_path = os.path.join(game_path, exe_name)
        
        if not os.path.exists(exe_path):
            self.log_message('ERROR', f"No se pudo lanzar: {exe_path} no existe.")
            messagebox.showerror("Error al Lanzar", f"El archivo ejecutable no se encontrú:\n{exe_path}", parent=self)
            return
        
        try:
            self.log_message('TITLE', f"Lanzando juego: {exe_name} desde {game_path}")
            # os.startfile es especúfico de Windows y es no bloqueante
            # Usamos cwd para asegurarnos de que el juego se lanza desde su carpeta
            os.startfile(exe_path, cwd=game_path)
        except Exception as e:
            self.log_message('ERROR', f"No se pudo lanzar {exe_path}: {e}")
            messagebox.showerror("Error", f"No se pudo lanzar el juego:\n{e}", parent=self)

    # --- MODIFICADO (V2.0): Ya no pide, solo selecciona ---
    def select_mod_dir_manual(self):
        """Permite al usuario seleccionar una carpeta de mod manualmente."""
        initial_dir = os.path.expanduser('~') + '/Downloads'
        dir_path = filedialog.askdirectory(
            title="Seleccionar la CARPETA donde extrajiste el Mod",
            initialdir=initial_dir
        )
        if dir_path:
            self.mod_source_dir.set(dir_path)
            self.mod_version_list.set(os.path.basename(dir_path)) # Actualizar selector
            self.log_message('INFO', f"Carpeta del mod manual seleccionada: {dir_path}")
        else:
            self.log_message('WARN', "Selecciún de carpeta de mod cancelada.")

    def select_game_dir(self):
        """Selecciona la carpeta de destino manual."""
        initial_dir = r"C:\Program Files"
        if not os.path.isdir(initial_dir):
             initial_dir = os.path.expanduser('~')
        dir_path = filedialog.askdirectory(title="Seleccionar la carpeta principal del juego (donde estú el .exe)", initialdir=initial_dir)
        if dir_path:
            smart_path, exe_name = find_executable_path(dir_path, self.log_message)
            self.manual_game_path.set(smart_path)
            self.update_mod_status_label_manual(smart_path)
            if smart_path != dir_path:
                self.log_message('INFO', f"Ruta manual ajustada a la carpeta del ejecutable: {smart_path} (Exe: {exe_name})")
        else:
             self.log_message('WARN', "Selecciún de carpeta manual cancelada.")


    # --- Funciones de Ejecuciún ---

    def _get_selected_original_indices(self):
        """Obtiene los índices ORIGINALES de los checkboxes marcados."""
        return [idx for idx, var in self.game_checkbox_vars.items() if var.get()]
    
    def _refresh_game_list_after_operation(self, modified_game_paths=None):
        """Refresca datos, aplica filtro y actualiza UI.
        
        Args:
            modified_game_paths: Lista de rutas de juegos modificados. Si se proporciona,
                                solo se re-escanea el estado de esos juegos especúficos.
        """
        self.log_message('INFO', "Actualizando la lista de juegos detectados...")
        
        if modified_game_paths:
            # Escaneo selectivo: solo actualizar estado de juegos modificados
            for idx, (game_path, display_name, _, exe_name, platform_tag) in enumerate(self.all_games_data):
                if game_path in modified_game_paths:
                    # Re-verificar estado de este juego
                    new_status = check_mod_status(game_path)
                    self.all_games_data[idx] = (game_path, display_name, new_status, exe_name, platform_tag)
                    self.log_message('INFO', f"Estado actualizado: {display_name} -> {new_status}")
        else:
            # Escaneo completo
            self.all_games_data = scan_games(self.log_message, self.custom_search_folders)
        
        # Guardar cachéú actualizada
        save_games_caché(self.all_games_data, self.log_message)
        
        # Actualizar label de cachéú
        if hasattr(self, 'caché_info_label'):
            self.update_caché_info_label()
        
        self.filter_games() # Re-aplica filtro y recarga la lista
        self.after(0, self.refresh_custom_folders_list, True) # Actualizar contadores
        
        # Refrescar lista gaming si estú en modo gaming
        if hasattr(self, 'gaming_mode_var') and self.gaming_mode_var.get():
            self.after(100, self.populate_gaming_games)
        
        self.update()
        
    def _get_common_mod_options(self):
        """Retorna un diccionario con todas las opciones de configuración seleccionadas."""
        # --- MODIFICADO (V2.0 Refactor): Lee de los botones ---
        self.save_config() # Forzar guardado para asegurar que las variables estún actualizadas
        
        return {
            "spoof_dll_name": self.spoof_dll_name_var.get(),
            "gpu_choice": self.gpu_choice.get(),
            "fg_mode_selected": self.fg_mode_var.get(),
            "upscaler_selected": self.upscaler_var.get(),
            "upscale_mode_selected": self.upscale_mode_var.get(),
            "sharpness_selected": self.sharpness_var.get(),
            "overlay_selected": self.overlay_var.get(),
            "mb_selected": self.motion_blur_var.get()
        }

    def run_auto_injection(self):
        """Inyecta el mod en los juegos seleccionados."""
        try:
            selected_original_indices = self._get_selected_original_indices()
            if not selected_original_indices:
                self.log_message('WARN', "Por favor, seleccione al menóos un juego de la lista.")
                return

            mod_dir = self.mod_source_dir.get()
            # --- MODIFICADO (V2.0): Llama a check_mod_source_files ---
            source_dir, source_ok = check_mod_source_files(mod_dir, self.log_message)
            if not source_ok:
                self.log_message('ERROR', "Debe seleccionar o descargar una Carpeta Origen del Mod vúlida.")
                self.open_mod_downloader()
                return
            
            mod_options = self._get_common_mod_options()
            total_count = len(selected_original_indices)
            self.log_message('TITLE', f"INICIANDO INYECCIÓN en {total_count} juego(s) con DLL: {mod_options['spoof_dll_name']}...")
            
            self.start_indeterminate_progress(1) # Barra en Pestaña 2
            
            success_count = 0
            modified_paths = []  # Rastrear juegos modificados
            for i, original_index in enumerate(selected_original_indices):
                game_path, game_name, _, _, _ = self.all_games_data[original_index]
                self.log_message('INFO', f"({i+1}/{total_count}) Intentando inyectar en: {game_name} -> {game_path}")
                
                # --- MODIFICADO (V2.0): Pasa source_dir, no mod_dir ---
                if inject_fsr_mod(source_dir, game_path, self.log_message, **mod_options):
                     self.log_message('OK', f"Inyecciún exitosa en: {game_name}")
                     success_count += 1
                     modified_paths.append(game_path)  # Aúadir a la lista de modificados
                else:
                     self.log_message('ERROR', f"  [FALLO] La inyección de {game_name} fallú.")
                
                self.progress_bar_auto.set((i + 1) / total_count)
                self.update_idletasks()

            self.stop_indeterminate_progress(1)
            self._refresh_game_list_after_operation(modified_paths)  # Escaneo selectivo
            self.log_message('TITLE', f"OPERACIúN DE INYECCIÓN AUTOMúTICA FINALIZADA ({success_count} completadas con Éxito).")

            if total_count > 0:
                if success_count == total_count:
                    messagebox.showinfo("Éxito", f"Inyección completada con Éxito en {success_count} juego(s).", parent=self)
                elif success_count > 0:
                    messagebox.showwarning("Éxito Parcial", f"Inyección completada en {success_count} de {total_count} juego(s).\n\nRevisa la pestaña 'LOG'.", parent=self)
                else:
                    messagebox.showerror("Error", "La inyección fallú para todos los juegos seleccionados.\n\nRevisa la pestaña 'LOG'.", parent=self)
            
        except Exception as e:
            self.log_message('ERROR', f"Fallo interno al procesar la inyección automática: {e}")
            messagebox.showerror("Error Crútico", f"Ha ocurrido un error inesperado:\n{e}\n\nRevisa la pestaña 'LOG'.", parent=self)
            self.stop_indeterminate_progress(1)

        
    def run_auto_uninstall(self):
        """Desinstala el mod de los juegos seleccionados."""
        try:
            selected_original_indices = self._get_selected_original_indices()
            if not selected_original_indices:
                self.log_message('WARN', "Por favor, seleccione al menóos un juego de la lista para desinstalar.")
                return
                
            total_count = len(selected_original_indices)
            self.log_message('TITLE', f"INICIANDO DESINSTALACIÓN en {total_count} juego(s)...")

            self.start_indeterminate_progress(1)
            success_count = 0
            all_found_backups = {}
            modified_paths = []  # Rastrear juegos modificados

            for i, original_index in enumerate(selected_original_indices):
                game_path, game_name, _, _, _ = self.all_games_data[original_index]
                self.log_message('INFO', f"({i+1}/{total_count}) Intentando desinstalar de: {game_name}")
                success, found_backups = uninstall_fsr_mod(game_path, self.log_message)
                
                if success:
                     self.log_message('OK', f"Desinstalaciún exitosa en: {game_name}")
                     success_count += 1
                     modified_paths.append(game_path)  # Aúadir a la lista de modificados
                if found_backups: # Guardar backups incluso si la desinstalación fallú
                     all_found_backups[game_path] = (game_name, found_backups)
                
                self.progress_bar_auto.set((i + 1) / total_count)
                self.update_idletasks()

            self.stop_indeterminate_progress(1)
            self._refresh_game_list_after_operation(modified_paths)  # Escaneo selectivo
            self.log_message('TITLE', f"OPERACIúN DE DESINSTALACIÓN AUTOMúTICA FINALIZADA ({success_count} completadas).")
            
            if all_found_backups:
                self._ask_to_restore_backups(all_found_backups)

            if total_count > 0 and success_count == 0 and not all_found_backups:
                 messagebox.showerror("Error", "La desinstalación fallú o el mod no se encontrú en los juegos seleccionados.\n\nRevisa la pestaña 'LOG'.", parent=self)
            elif total_count > 0 and success_count < total_count and success_count > 0:
                 messagebox.showwarning("Éxito Parcial", f"Desinstalación completada en {success_count} de {total_count} juego(s).\n\nRevisa la pestaña 'LOG'.", parent=self)
            elif success_count == total_count and total_count > 0:
                 messagebox.showinfo("Éxito", f"Desinstalación completada con Éxito en {success_count} juego(s).", parent=self)
            
        except Exception as e:
            self.log_message('ERROR', f"Fallo interno al procesar la desinstalación automática: {e}")
            messagebox.showerror("Error Crútico", f"Ha ocurrido un error inesperado:\n{e}\n\nRevisa la pestaña 'LOG'.", parent=self)
            self.stop_indeterminate_progress(1)

    def _ask_to_restore_backups(self, all_found_backups):
        """Pregunta al usuario si desea restaurar los backups encontrados."""
        restore_message = "Se encontraron los siguientes archivos de backup (.bak):\n\n"
        backup_details = []
        for game_path, (game_name, backups) in all_found_backups.items():
            game_name_short = game_name.split(']')[-1].strip() # Limpiar "[STEAM] ..."
            restore_message += f"En '{game_name_short}':\n"
            for bak_path, orig_name in backups:
                restore_message += f"  - {orig_name}.bak\n"
                backup_details.append((game_path, orig_name)) # Solo necesitamos la ruta del juego
        
        restore_message += "\núDeseas intentar restaurarlos? (sobrescribirú archivos actuales si existen)"

        if messagebox.askyesno("Restaurar Backups", restore_message, parent=self):
            self.log_message('TITLE', "Intentando restaurar backups...")
            restored_count = 0
            failed_restores = set()
            
            # Agrupar por juego
            game_paths_to_restore = set(p for p, _ in backup_details)
            
            for game_path in game_paths_to_restore:
                if restore_original_dll(game_path, self.log_message):
                    restored_count += 1
                else:
                    failed_restores.add(os.path.basename(game_path))
            
            if not failed_restores:
                messagebox.showinfo("Restauración Completa", f"Se restauraron los backups en {restored_count} juego(s).", parent=self)
            else:
                messagebox.showwarning("Restauración Parcial", f"Se restauraron backups en {restored_count} juego(s).\nFallaron en: {', '.join(failed_restores)}", parent=self)


    def run_manual_injection(self):
        try:
            mod_dir = self.mod_source_dir.get()
            game_path = self.manual_game_path.get()
            mod_options = self._get_common_mod_options()

            source_dir, source_ok = check_mod_source_files(mod_dir, self.log_message)
            if not source_ok:
                 self.log_message('ERROR', "Debe seleccionar o descargar una Carpeta Origen del Mod vúlida.")
                 self.open_mod_downloader()
                 return
            if not game_path or not os.path.isdir(game_path):
                 self.log_message('ERROR', "Debe seleccionar una Carpeta de Destino (Juego) vúlida.")
                 self.select_game_dir()
                 return

            self.log_message('TITLE', f"INICIANDO INYECCIÓN MANUAL en: {game_path} con DLL: {mod_options['spoof_dll_name']}...")
            
            if inject_fsr_mod(source_dir, game_path, self.log_message, **mod_options):
                self.update_mod_status_label_manual(game_path)
                self.log_message('TITLE', "OPERACIúN DE INYECCIÓN MANUAL FINALIZADA.")
                self._refresh_game_list_after_operation()
                messagebox.showinfo("Éxito", "Inyecciún manual completada con Éxito.", parent=self)
            else:
                self.log_message('ERROR', "Inyecciún manual fallida.")
                messagebox.showerror("Error", "La inyección manual fallú.\n\nRevisa la pestaña 'LOG'.", parent=self)
        except Exception as e:
            self.log_message('ERROR', f"Fallo interno al procesar la inyección manual: {e}")
            messagebox.showerror("Error Crútico", f"Ha ocurrido un error inesperado:\n{e}\n\nRevisa la pestaña 'LOG'.", parent=self)
            
    def run_manual_uninstall(self):
        try:
            game_path = self.manual_game_path.get()
            if not game_path or not os.path.isdir(game_path):
                 self.log_message('ERROR', "Debe seleccionar una Carpeta de Destino (Juego) vúlida.")
                 self.select_game_dir()
                 return
            
            self.log_message('TITLE', f"INICIANDO DESINSTALACIÓN MANUAL de: {game_path}")
            success, found_backups = uninstall_fsr_mod(game_path, self.log_message)
            
            if success:
                self.update_mod_status_label_manual(game_path)
                self.log_message('TITLE', "OPERACIúN DE DESINSTALACIÓN MANUAL FINALIZADA.")
                self._refresh_game_list_after_operation()
                messagebox.showinfo("Éxito", "Desinstalaciún manual completada con Éxito.", parent=self)
            else:
                self.log_message('WARN', "Desinstalaciún manual: no se encontraron archivos del mod.")
                if not found_backups:
                    messagebox.showerror("Error", "La desinstalación manual fallú o el mod no se encontrú.\n\nRevisa la pestaña 'LOG'.", parent=self)
            
            if found_backups:
                 game_name = os.path.basename(game_path)
                 self._ask_to_restore_backups({game_path: (game_name, found_backups)})
        
        except Exception as e:
            self.log_message('ERROR', f"Fallo interno al procesar la desinstalación manual: {e}")
            messagebox.showerror("Error Crútico", f"Ha ocurrido un error inesperado:\n{e}\n\nRevisa la pestaña 'LOG'.", parent=self)

    def run_manual_restore_bak(self):
        """Ejecuta la restauraciún de .bak en la carpeta manual."""
        game_path = self.manual_game_path.get()
        if not game_path or not os.path.isdir(game_path):
             self.log_message('ERROR', "Debe seleccionar una Carpeta de Destino (Juego) vúlida.")
             self.select_game_dir()
             return
        
        self.log_message('TITLE', f"INICIANDO RESTAURACIúN DE .BAK en: {game_path}")
        if restore_original_dll(game_path, self.log_message):
            self.update_mod_status_label_manual(game_path)
            self._refresh_game_list_after_operation()
            messagebox.showinfo("Éxito", "Restauraciún de .bak completada.", parent=self)
        else:
            messagebox.showwarning("Aviso", "No se encontraron archivos .bak relevantes para restaurar.\n\nRevisa la pestaña 'LOG'.", parent=self)

    def run_game_list_restore_bak(self, game_path):
        """Ejecuta la restauraciún de .bak desde un botón de la lista."""
        if not game_path or not os.path.isdir(game_path):
             self.log_message('ERROR', f"Ruta de juego no vúlida: {game_path}")
             return
        
        game_name_short = os.path.basename(game_path)
        self.log_message('TITLE', f"INICIANDO RESTAURACIúN DE .BAK en: {game_name_short}")
        if restore_original_dll(game_path, self.log_message):
            self._refresh_game_list_after_operation()
            messagebox.showinfo("Éxito", f"Restauraciún de .bak completada para {game_name_short}.", parent=self)
        else:
            messagebox.showwarning("Aviso", f"No se encontraron archivos .bak relevantes para {game_name_short}.\n\nRevisa la pestaña 'LOG'.", parent=self)

    def update_mod_status_label_manual(self, dir_path):
        """Actualiza la etiqueta de estado del mod en la sección manual."""
        status = check_mod_status(dir_path)
        self.mod_status_manual.set(f"[Estado: {status}]")
        colors = {"INSTALADO": "#00FF00", "AUSENTE": "#FFFF00", "ERROR": "#FF4500"}
        status_key = status.split(' ')[0].replace('?', '').replace('?', '') # Obtener la palabra clave
        self.status_label_manual.configure(text_color=colors.get(status_key, "#FF4500"))
            
    # --- MODIFICADO (V2.0): exe_name quitado ---
    def open_game_config_window(self, game_path, game_name):
        """Abre la ventana emergente para configurar un juego especúfico."""
        if self.active_popup: # Evitar popups duplicados
            try: self.active_popup.focus_force()
            except: self.on_popup_closed()
            return
            
        try:
            # Primero, leer la configuración actual de ese juego
            current_config = read_optiscaler_ini(game_path, self.log_message)
            
            # Abrir la ventana
            config_window = GameConfigWindow(self, game_path, game_name, current_config, self.log_message)
            
            # --- Registrar popup ---
            self.active_popup = config_window
            config_window.bind("<Destroy>", self.on_popup_closed)
            # --- NUEVO (Mejora 10): Binding de Teclado ---
            config_window.bind("<Escape>", lambda e: config_window.on_cancel_and_close())

            config_window.grab_set() # Hacerla modal
            
        except Exception as e:
            self.log_message('ERROR', f"Error al abrir la ventana de configuración: {e}")
            messagebox.showerror("Error", f"No se pudo abrir la ventana de configuración:\n{e}", parent=self)
            if self.active_popup: self.active_popup = None # Reset
            
    # --- NUEVAS FUNCIONES (V2.0): Auto-descarga y Limpieza ---
    
    # --- MODIFICADO (V2.0 Mejora): Rellena el ComboBox ---
    def autodetect_mod_source(self):
        """Busca la última versión descargada en MOD_SOURCE_DIR y la establece."""
        if not hasattr(self, 'mod_version_combo'):
            return False # UI no lista
            
        if not os.path.isdir(MOD_SOURCE_DIR):
            self.log_message('WARN', "No se encontrú la carpeta 'mod_source'. Use el botón de descarga.")
            self.mod_source_dir.set("")
            self.mod_version_combo.configure(values=["[Ninguna versión descargada]"], state="disabled")
            if hasattr(self, 'gaming_mod_version_combo'):
                self.gaming_mod_version_combo.configure(values=["[Ninguna versión descargada]"], state="disabled")
            self.mod_version_list.set("[Ninguna versión descargada]")
            return False

        subdirs = sorted(
            [d for d in os.listdir(MOD_SOURCE_DIR) if os.path.isdir(os.path.join(MOD_SOURCE_DIR, d))],
            reverse=True
        )
        if not subdirs:
            self.log_message('WARN', "La carpeta 'mod_source' estú vacía. Use el botón de descarga.")
            self.mod_source_dir.set("")
            self.mod_version_combo.configure(values=["[Carpeta 'mod_source' vacía]"], state="disabled")
            if hasattr(self, 'gaming_mod_version_combo'):
                self.gaming_mod_version_combo.configure(values=["[Carpeta 'mod_source' vacía]"], state="disabled")
            self.mod_version_list.set("[Carpeta 'mod_source' vacía]")
            return False
        
        self.mod_version_combo.configure(values=subdirs, state="readonly")
        if hasattr(self, 'gaming_mod_version_combo'):
            self.gaming_mod_version_combo.configure(values=subdirs, state="readonly")
        self.mod_version_list.set(subdirs[0]) # Seleccionar la más reciente
        self.on_mod_version_selected(subdirs[0])
        return True

    def on_mod_version_selected(self, selected_version_name):
        """Se llama cuando el usuario cambia la versión del mod en el ComboBox."""
        latest_mod_path = os.path.join(MOD_SOURCE_DIR, selected_version_name)
        self.mod_source_dir.set(latest_mod_path)
        self.log_message('OK', f"Versiún del Mod activa cambiada a: {selected_version_name}")

    def open_mod_downloader(self):
        """Abre la ventana del gestor de descargas de mods."""
        if self.active_popup:
            try: self.active_popup.focus_force()
            except: self.on_popup_closed()
            return

        # Lazy load requests solo cuando se abre el gestor
        if not ensure_requests_available():
            self.log_message('ERROR', "Faltan 'requests'. No se puede abrir el gestor.")
            messagebox.showerror("Error de Dependencias",
                                 "Falta la biblioteca 'requests'.\n\n"
                                 "Por favor, instúlela con:\n"
                                 "pip install requests", parent=self)
            return
        
        # --- úNUEVA LúGICA DE 7z! (V2.0 Pulida) ---
        # Comprobar 7z.exe aquú, justo antes de que se necesite.
        # Pasamos 'self' para que los popups sean modales a la ventana principal.
        if not check_and_download_7zip(self.log_message, self):
            self.log_message('ERROR', "Descarga de 7z.exe cancelada o fallida. Abortando gestor de descargas.")
            return
        
        # Comprobar si 7z.exe existe (doble chequeo por si acaso)
        seven_zip_exe = os.path.join(APP_DATA_DIR, SEVEN_ZIP_EXE_NAME)
        
        if not os.path.exists(seven_zip_exe):
             self.log_message('ERROR', f"úNo se encontrú {SEVEN_ZIP_EXE_NAME} después de la comprobaciún!")
             messagebox.showerror("Error de Dependencias",
                                  f"úNo se encontrú {SEVEN_ZIP_EXE_NAME}!\n\n"
                                  "Este error no deberúa ocurrir si la auto-descarga funcionú.\n"
                                  "Por favor, reinicie la app.", parent=self)
             return
        # --- Fin de la lógica de 7z ---
        
        try:
            downloader_window = ModDownloaderWindow(self, self.log_message)
            self.active_popup = downloader_window
            downloader_window.bind("<Destroy>", self.on_popup_closed)
            # --- NUEVO (Mejora 10): Binding de Teclado ---
            downloader_window.bind("<Escape>", lambda e: downloader_window.destroy())
            downloader_window.grab_set()
        except Exception as e:
            self.log_message('ERROR', f"No se pudo abrir el gestor de descargas: {e}")
            self.on_popup_closed()

    def run_clean_logs_threaded(self):
        """Ejecuta la limpieza de logs en un hilo."""
        game_paths = [path for path, _, _, _, _ in self.all_games_data]
        if not game_paths:
            self.log_message('WARN', "No hay juegos detectados para limpiar.")
            return
        if messagebox.askyesno("Confirmar Limpieza",
                               f"úEstú seguro de que desea eliminar 'OptiScaler.log' de las {len(game_paths)} carpetas de juegos detectadas?",
                               parent=self):
            self.start_indeterminate_progress(3)
            self.btn_clean_logs.configure(state="disabled")
            self.btn_clean_orphan_baks.configure(state="disabled")
            threading.Thread(target=self._clean_logs_worker, args=(game_paths,), daemon=True).start()

    def _clean_logs_worker(self, game_paths):
        self.log_message('TITLE', "Iniciando limpieza de archivos .log...")
        cleaned_count = clean_logs(game_paths, self.log_message)
        self.after(0, self.stop_indeterminate_progress, 3)
        self.after(0, self.btn_clean_logs.configure, {"state": "normal"})
        self.after(0, self.btn_clean_orphan_baks.configure, {"state": "normal"})
        self.after(0, messagebox.showinfo, "Limpieza Completada", f"Se eliminaron {cleaned_count} archivos .log.", parent=self)
            
    def run_clean_orphan_baks_threaded(self):
        """Ejecuta la limpieza de backups huérfanos en un hilo."""
        if not self.all_games_data:
            self.log_message('WARN', "No hay juegos detectados para limpiar.")
            return
        if messagebox.askyesno("Confirmar Limpieza",
                               "úEstú seguro de que desea eliminar archivos .bak de juegos donde el mod estú 'AUSENTE'?",
                               parent=self):
            self.start_indeterminate_progress(3)
            self.btn_clean_logs.configure(state="disabled")
            self.btn_clean_orphan_baks.configure(state="disabled")
            threading.Thread(target=self._clean_baks_worker, daemon=True).start()

    def _clean_baks_worker(self):
        self.log_message('TITLE', "Iniciando limpieza de backups huérfanos...")
        cleaned_count = clean_orphan_backups(self.all_games_data, self.log_message)
        self.after(0, self.stop_indeterminate_progress, 3)
        self.after(0, self.btn_clean_logs.configure, {"state": "normal"})
        self.after(0, self.btn_clean_orphan_baks.configure, {"state": "normal"})
        self.after(0, messagebox.showinfo, "Limpieza Completada", f"Se eliminaron {cleaned_count} backups huérfanos.", parent=self)
        self.after(0, self._refresh_game_list_after_operation)
        
    # --- NUEVO (V2.0 Mejora B): Guardar Log ---
    def save_log_to_file(self):
        """Guarda el contenido del widget de log en un archivo de texto."""
        log_content = self.log_text.get("1.0", "end-1c")
        if not log_content:
            self.log_message('WARN', "El log estú vacúo, no hay nada que guardar.")
            return
            
        file_path = filedialog.asksaveasfilename(
            title="Guardar Log como...",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialfile="gestor_optiscaler_log.txt",
            parent=self
        )
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(log_content)
                self.log_message('OK', f"Log guardado con Éxito en: {file_path}")
            except Exception as e:
                self.log_message('ERROR', f"No se pudo guardar el log: {e}")
                
    # --- NUEVO (V2.0 Mejora E): Actualizaciún por Lotes ---
    def run_batch_update_config(self):
        """Aplica la configuración global a todos los juegos seleccionados."""
        try:
            selected_original_indices = self._get_selected_original_indices()
            if not selected_original_indices:
                self.log_message('WARN', "Por favor, seleccione al menóos un juego para actualizar.")
                return

            mod_options = self._get_common_mod_options()
            total_count = len(selected_original_indices)
            
            if not messagebox.askyesno("Confirmar Actualizaciún por Lotes",
                               f"úEstú seguro de que desea aplicar la configuración GLOBAL (Pestaña 1) a los {total_count} juegos seleccionados?\n\n"
                               f"DLL: {mod_options['spoof_dll_name']}\n"
                               f"GPU: {'AMD/Intel' if mod_options['gpu_choice'] == 1 else 'NVIDIA'}\n"
                               f"Frame Gen: {mod_options['fg_mode_selected']}\n\n"
                               "Esto sobrescribirú cualquier ajuste individual que haya hecho.",
                               parent=self):
                self.log_message('INFO', "Actualizaciún por lotes cancelada.")
                return
                
            self.log_message('TITLE', f"INICIANDO ACTUALIZACIÓN POR LOTES en {total_count} juego(s)...")
            
            self.start_indeterminate_progress(1) # Barra en Pestaña 2
            
            success_count = 0
            for i, original_index in enumerate(selected_original_indices):
                game_path, game_name, _, _, _ = self.all_games_data[original_index]
                self.log_message('INFO', f"({i+1}/{total_count}) Actualizando: {game_name}")
                
                # 1. Renombrar DLL
                dll_ok = configure_and_rename_dll(game_path, mod_options['spoof_dll_name'], self.log_message)
                # 2. Actualizar INI
                ini_ok = update_optiscaler_ini(game_path, **mod_options, log_func=self.log_message)
                
                if dll_ok and ini_ok:
                     self.log_message('OK', f"Actualizaciún exitosa en: {game_name}")
                     success_count += 1
                else:
                     self.log_message('ERROR', f"  [FALLO] La actualización de {game_name} fallú.")
                
                self.progress_bar_auto.set((i + 1) / total_count)
                self.update_idletasks()

            self.stop_indeterminate_progress(1)
            self._refresh_game_list_after_operation()
            self.log_message('TITLE', f"ACTUALIZACIÓN POR LOTES FINALIZADA ({success_count} completadas con Éxito).")

            if total_count > 0 and success_count < total_count:
                messagebox.showwarning("Éxito Parcial", f"Actualizaciún completada en {success_count} de {total_count} juego(s).\n\nRevisa la pestaña 'LOG'.", parent=self)
            elif success_count == total_count:
                messagebox.showinfo("Éxito", f"Actualizaciún completada con Éxito en {success_count} juego(s).", parent=self)
            
        except Exception as e:
            self.log_message('ERROR', f"Fallo interno al procesar la actualización por lotes: {e}")
            messagebox.showerror("Error Crútico", f"Ha ocurrido un error inesperado:\n{e}\n\nRevisa la pestaña 'LOG'.", parent=self)
            self.stop_indeterminate_progress(1)
# --- Funciones de Mando (PYGAME) ---
    
    # --- NUEVO (Mejora 10): Manejar tecla Escape ---
    def handle_escape_key(self):
        """Maneja la pulsaciún de la tecla Escape."""
        if self.active_popup:
            # La lógica de cierre de popups se maneja en sus propios bindings
            pass
        else:
            # Si no hay popup, no hacer nada (o minimizar, etc.)
            pass 

    def init_controller(self):
        """Inicializa Pygame y busca un mando."""
        if not PYGAME_AVAILABLE:
            self.log_message('WARN', "Pygame no estú instalado. Soporte de mando desactivado.")
            return
        try:
            pygame.init()
            pygame.joystick.init()
            if pygame.joystick.get_count() > 0:
                self.controller = pygame.joystick.Joystick(0)
                self.controller.init()
                self.log_message('INFO', f"Mando detectado: {self.controller.get_name()}")
            else:
                self.log_message('WARN', "No se detectaron mandos. Conecte uno y reinicie la app.")
        except Exception as e:
            self.log_message('ERROR', f"Error al inicializar el mando: {e}")

    # --- MODIFICADO (V5): Lúgica de Mando Mejorada ---
    def poll_controller(self):
        """Bucle de sondeo para los eventos del mando."""
        if not self.controller:
            if PYGAME_AVAILABLE and (pygame.joystick.get_count() > 0):
                self.init_controller()
            self.after(1000, self.poll_controller)
            return

        try:
            for event in pygame.event.get():
                
                # --- NUEVA LúGICA (V5): Gestiún de Popups en Capas ---
                if self.active_popup:
                    # Pasar el evento al popup activo
                    if hasattr(self.active_popup, 'handle_controller_event'):
                        self.active_popup.handle_controller_event(event)
                    
                    # Lúgica de fallback para popups simples (Ayuda)
                    elif event.type == pygame.JOYBUTTONDOWN:
                        if event.button == 1: # Botón B
                            self.active_popup.destroy()
                            
                    continue # Ignorar el resto de controles si hay un popup
                
                # --- Lúgica de Navegaciún Principal (sin popup) ---

                # Navegaciún de Pestañas (LB/RB)
                if event.type == pygame.JOYBUTTONDOWN:
                    if event.button == 4: # LB
                        self.change_tab(-1)
                    elif event.button == 5: # RB
                        self.change_tab(1)
                
                # D-Pad (Navegaciún de Foco)
                if event.type == pygame.JOYHATMOTION:
                    if event.hat == 0:
                        hat_x, hat_y = event.value
                        if hat_y == 1: self.move_focus('up') # Arriba
                        elif hat_y == -1: self.move_focus('down') # Abajo
                        elif hat_x == -1: self.move_focus('left') # Izquierda
                        elif hat_x == 1: self.move_focus('right') # Derecha

                # Botones A, X, Y, START
                elif event.type == pygame.JOYBUTTONDOWN:
                    if event.button == 0: # Botón A
                        self.activate_focused_widget()
                        
                    # Botón START (Abrir Config. Juego)
                    elif event.button == 7: # START
                        if self.current_tab_index == 1 and self.focus_location == 'content':
                            try:
                                current_focus_row, current_focus_col = self.focused_indices[1]
                                nav_list = self.navigable_widgets.get(1, [])
                                
                                # Asegurarse de que el foco estú en la lista de juegos (Fila 0 y 1 son filtros)
                                game_list_start_row = 2
                                if current_focus_row >= game_list_start_row and current_focus_row < (len(nav_list)):
                                    widget_to_activate = nav_list[current_focus_row][0] # Col 0 es el item_frame
                                    
                                    if widget_to_activate and hasattr(widget_to_activate, 'original_index'):
                                        original_index = getattr(widget_to_activate, 'original_index', -1)
                                        if original_index != -1:
                                            game_path, game_name, _, _, _ = self.all_games_data[original_index]
                                            self.open_game_config_window(game_path, game_name)
                            except Exception as e:
                                self.log_message('ERROR', f"Error al abrir config con START: {e}")
                    
                    # --- NUEVO (Mejora 11): Botón Select ---
                    elif event.button == 6: # SELECT / BACK
                        if self.current_tab_index == 1: # AUTO
                            self.btn_batch_update.invoke()
                        
                    # Mapeo de X/Y por pestaña
                    if self.current_tab_index == 0: # CONFIG
                        if event.button == 2: # Botón X
                            self.btn_go_to_auto.invoke()
                    elif self.current_tab_index == 1: # AUTO
                        if event.button == 2: self.btn_auto_inject.invoke() # X
                        elif event.button == 3: self.btn_auto_uninstall.invoke() # Y
                    elif self.current_tab_index == 2: # MANUAL
                        if event.button == 2: self.btn_manual_inject.invoke() # X
                        elif event.button == 3: self.btn_manual_uninstall.invoke() # Y
                        
        except Exception as e:
            self.log_message('ERROR', f"Error en el bucle del mando: {e}")
            self.controller = None # Desactivar para evitar spam de errores

        self.after(50, self.poll_controller)

    # --- Funciones de Navegaciún y Foco (REFACTORIZADAS V5) ---

    def change_tab(self, direction):
        """Cambia la pestaña activa del notebook y gestiona el foco."""
        new_index = (self.current_tab_index + direction) % len(self.tab_names)
        self.current_tab_index = new_index
        self.notebook.set(self.tab_names[new_index])

        if self.focus_location != 'tabs':
            self.focus_location = 'content'
            self.focused_indices[new_index] = [0, 0] # Resetear foco a [0,0]
        
        self.update_focus_visuals()
            
    def go_to_auto_tab(self):
        """Cambia a la pestaña AUTO (índice 1) y pone el foco en su contenido."""
        self.current_tab_index = 1
        self.notebook.set(self.tab_names[self.current_tab_index])
        self.focus_location = 'content'
        self.focused_indices[self.current_tab_index] = [0, 0]
        self.update_focus_visuals()


    def clear_all_focus_visuals(self):
        """Quita el borde/fondo de foco de todos los widgets y pestañas."""
        default_border_color = self.default_frame_border_color
        default_border_width = self.default_frame_border_width

        if default_border_color is None:
            return # Aún no estú listo

        all_widget_lists = [self.global_navigable_widgets] + [row for tab in self.navigable_widgets.values() for row in tab]
        
        for widget_list in all_widget_lists:
            # Si el item es la lista de widgets globales (no es una lista anidada)
            if widget_list and isinstance(widget_list, ctk.CTkBaseClass):
                try:
                    widget_list.configure(border_color=default_border_color, border_width=default_border_width)
                except Exception: pass
                continue
                
            # Si es una lista de widgets (una fila)
            for widget in widget_list:
                if widget is None or not hasattr(widget, 'configure'):
                    continue
                
                # Manejo especial para frames de lista de juegos
                if hasattr(widget, 'original_index'):
                    original_index = getattr(widget, 'original_index', -1)
                    frame_fg_color = "transparent"
                    if original_index in self.game_checkbox_vars and self.game_checkbox_vars[original_index].get():
                        frame_fg_color = self._apply_appearance_mode(self.highlight_color)
                    widget.configure(fg_color=frame_fg_color, border_color=default_border_color, border_width=default_border_width)
                else:
                    try:
                        widget.configure(border_color=default_border_color, border_width=default_border_width)
                    except Exception: pass # Ignorar widgets que no aceptan borde

        # Limpiar bordes de pestañas
        for i in range(len(self.tab_names)):
            try:
                tab_button = self.notebook._tab_dict[self.tab_names[i]]
                tab_button.configure(border_width=0)
            except Exception:
                pass # Ignorar si la pestaña no existe
    
    def update_focus_visuals(self):
        """Aplica el borde/fondo de foco al widget/pestaña correcto."""
        try:
            # Si estamos en modo gaming, no hacer navegación de interfaz clúsica
            if hasattr(self, 'gaming_mode_var') and self.gaming_mode_var.get():
                return
            
            self.clear_all_focus_visuals()
            focus_border_width = 2
            w = None # Widget a enfocar

            if self.focus_location == 'global':
                if 0 <= self.global_focused_index < len(self.global_navigable_widgets):
                    w = self.global_navigable_widgets[self.global_focused_index]
            
            elif self.focus_location == 'tabs':
                tab_btns = list(self.notebook._tab_dict.values())
                if 0 <= self.current_tab_index < len(tab_btns):
                    w = tab_btns[self.current_tab_index]
            
            elif self.focus_location == 'content':
                tab_widgets = self.navigable_widgets.get(self.current_tab_index, [])
                if not tab_widgets: return # Pestaña vacía
                
                current_row, current_col = self.focused_indices[self.current_tab_index]
                
                if 0 <= current_row < len(tab_widgets) and 0 <= current_col < len(tab_widgets[current_row]):
                    w = tab_widgets[current_row][current_col]

            if w and hasattr(w, 'configure'):
                w.configure(border_color=self.focus_color, border_width=focus_border_width)
                
                # --- NUEVO: Aúadir binding de clic para actualizar foco ---
                if not hasattr(w, '_focus_click_bound'):
                    w.bind("<Button-1>", lambda e, widget=w: self.on_widget_clicked(widget), add="+")
                    w._focus_click_bound = True
                
                # --- NUEVO (Fix 2: Scroll): Hacer scroll si el widget es un frame de juego ---
                if self.current_tab_index == 1 and hasattr(w, 'original_index'):
                    self.game_list_frame._scroll_to_widget(w) # w es el item_frame
                elif self.current_tab_index == 3:
                    # Comprobar si es una fila de carpeta (estú dentro del frame scrolleable)
                    if hasattr(w, 'master') and hasattr(w.master, 'master') and w.master.master == self.custom_folders_list_frame:
                         self.custom_folders_list_frame._scroll_to_widget(w.master) # w.master es el item_frame

        except Exception as e:
            # self.log_message('ERROR', f"Error al actualizar visuales: {e}")
            pass # Ignorar errores visuales menores

    def _set_global_sharpness_edit_visuals(self, editing: bool):
        """Cambia el aspecto del slider de nitidez del tab global para indicar ediciún."""
        try:
            slider = self.slider_sharpness
            if not hasattr(self, "_global_slider_btn_color_default"):
                try:
                    self._global_slider_btn_color_default = slider.cget("button_color")
                except Exception:
                    self._global_slider_btn_color_default = None
            if not hasattr(self, "_global_slider_prog_color_default"):
                try:
                    self._global_slider_prog_color_default = slider.cget("progress_color")
                except Exception:
                    self._global_slider_prog_color_default = None
            if editing:
                highlight = "#00BFFF"
                try:
                    slider.configure(button_color=highlight)
                except Exception:
                    pass
                try:
                    slider.configure(progress_color=highlight)
                except Exception:
                    pass
            else:
                try:
                    if getattr(self, "_global_slider_btn_color_default", None) is not None:
                        slider.configure(button_color=self._global_slider_btn_color_default)
                except Exception:
                    pass
                try:
                    if getattr(self, "_global_slider_prog_color_default", None) is not None:
                        slider.configure(progress_color=self._global_slider_prog_color_default)
                except Exception:
                    pass
        except Exception:
            pass

    def on_widget_clicked(self, widget):
        """Actualiza el foco cuando se hace clic en un widget navegable."""
        try:
            # Asegurar que la ventana principal tiene el foco para capturar teclas
            self.focus_force()
            
            # Buscar el widget en la lista de navegación de la pestaña actual
            nav_list = self.navigable_widgets.get(self.current_tab_index, [])
            
            for row_idx, row in enumerate(nav_list):
                for col_idx, w in enumerate(row):
                    if w == widget:
                        # Actualizar los índices de foco
                        self.focus_location = 'content'
                        self.focused_indices[self.current_tab_index] = [row_idx, col_idx]
                        self.update_focus_visuals()
                        return
            
            # Si no se encuentra en content, buscar en global
            for idx, w in enumerate(self.global_navigable_widgets):
                if w == widget:
                    self.focus_location = 'global'
                    self.global_focused_index = idx
                    self.update_focus_visuals()
                    return
        except Exception as e:
            pass  # Ignorar errores

    def move_focus(self, direction): # 'up', 'down', 'left', 'right'
        """Mueve el foco virtual (entre global, pestañas y contenido)."""
        
        # Si estamos en modo gaming, usar sistema de navegación gaming
        if hasattr(self, 'gaming_mode_var') and self.gaming_mode_var.get():
            self.move_focus_gaming(direction)
            return
        
        # 1. Quitar foco de escritura si estamos en un Entry
        current_widget = None
        try:
            if self.focus_location == 'global':
                current_widget = self.global_navigable_widgets[self.global_focused_index]
            elif self.focus_location == 'content':
                current_row, current_col = self.focused_indices[self.current_tab_index]
                current_widget = self.navigable_widgets[self.current_tab_index][current_row][current_col]
        except Exception:
            pass # Foco fuera de rango, no hacer nada
            
        if isinstance(current_widget, ctk.CTkEntry):
             self.focus_set() # Devolver el foco a la ventana principal
        
        # 2. Lúgica de movimiento
        if self.focus_location == 'global':
            max_idx = len(self.global_navigable_widgets) - 1
            if direction == 'down': 
                if self.global_focused_index < max_idx: self.global_focused_index += 1
                else: self.focus_location = 'tabs'; self.global_focused_index = -1; self.update_focus_visuals()
            elif direction == 'up':
                if self.global_focused_index > 0: self.global_focused_index -= 1; self.update_focus_visuals()
            return # Movimiento global no necesita update al final
        
        elif self.focus_location == 'tabs':
            if direction == 'down':
                 self.focus_location = 'content'
                 self.focused_indices[self.current_tab_index] = [0, 0]
            elif direction == 'up':
                 self.focus_location = 'global'
                 self.global_focused_index = len(self.global_navigable_widgets) - 1
            # Izquierda/Derecha ya no hacen nada aquú (Mejora 7)
            
        elif self.focus_location == 'content':
            nav_list = self.navigable_widgets.get(self.current_tab_index, [])
            if not nav_list: return # No hay nada que navegar
            
            prev_row, prev_col = self.focused_indices[self.current_tab_index]
            current_row, current_col = prev_row, prev_col
            max_row = len(nav_list) - 1
            
            if direction == 'down':
                if current_row < max_row:
                    current_row += 1
                    # Mantener la columna si es posible; así los desplegables (col 1) saltan a los siguientes desplegables
                    current_col = min(current_col, len(nav_list[current_row]) - 1)
                # --- NUEVO (Mejora 11): No saltar a botones en Pestaña AUTO ---
                elif self.current_tab_index == 1:
                    pass # Quedarse en el último item
            elif direction == 'up':
                if current_row > 0:
                    current_row -= 1
                    # Mantener la misma columna si existe en la fila superior
                    current_col = min(current_col, len(nav_list[current_row]) - 1)
                else: # Estamos en la fila 0, saltar a 'tabs'
                    self.focus_location = 'tabs'
                    current_row, current_col = -1, -1
            elif direction == 'left':
                # Si estamos en el slider en pestaña CONFIG, ajustar valor en lugar de mover foco
                try:
                    if self.current_tab_index == 0:
                        current_widget = nav_list[current_row][current_col]
                        # Detectar si es el slider directamente o estú en un frame
                        target_slider = None
                        if isinstance(current_widget, ctk.CTkSlider):
                            target_slider = current_widget
                        elif isinstance(current_widget, ctk.CTkFrame) and self.slider_edit_mode:
                            for ch in current_widget.winfo_children():
                                if isinstance(ch, ctk.CTkSlider):
                                    target_slider = ch
                                    break
                        
                        if target_slider and self.slider_edit_mode:
                            # Ajustar paso del slider
                            value = float(target_slider.get())
                            new_value = max(0.0, value - 0.04)
                            target_slider.set(new_value)
                            # Asegurar actualización de etiqueta/guardado
                            try:
                                self.update_sharpness_label_and_save(new_value)
                            except Exception:
                                pass
                            # Mantener foco visual
                            self.update_focus_visuals()
                            return
                except Exception:
                    pass
                if current_col > 0:
                    current_col -= 1
            elif direction == 'right':
                # Si estamos en el slider en pestaña CONFIG, ajustar valor en lugar de mover foco
                try:
                    if self.current_tab_index == 0:
                        current_widget = nav_list[current_row][current_col]
                        # Detectar si es el slider directamente o estú en un frame
                        target_slider = None
                        if isinstance(current_widget, ctk.CTkSlider):
                            target_slider = current_widget
                        elif isinstance(current_widget, ctk.CTkFrame) and self.slider_edit_mode:
                            for ch in current_widget.winfo_children():
                                if isinstance(ch, ctk.CTkSlider):
                                    target_slider = ch
                                    break
                        
                        if target_slider and self.slider_edit_mode:
                            value = float(target_slider.get())
                            new_value = min(2.0, value + 0.04)
                            target_slider.set(new_value)
                            # Asegurar actualización de etiqueta/guardado
                            try:
                                self.update_sharpness_label_and_save(new_value)
                            except Exception:
                                pass
                            # Mantener foco visual
                            self.update_focus_visuals()
                            return
                except Exception:
                    pass
                if current_row >= 0: # Asegurarse de que no estamos en -1
                    max_col = len(nav_list[current_row]) - 1
                    if current_col < max_col:
                        current_col += 1
            
            self.focused_indices[self.current_tab_index] = [current_row, current_col]
            # Si cambiú el foco, salir de modo ediciún de slider
            if [current_row, current_col] != [prev_row, prev_col]:
                self.slider_edit_mode = False
                try:
                    self._set_global_sharpness_edit_visuals(False)
                except Exception:
                    pass

        self.update_focus_visuals()


    def activate_focused_widget(self):
        """Activa el widget/pestaña enfocado."""
        # Si estamos en modo gaming, usar sistema de activaciún gaming
        if hasattr(self, 'gaming_mode_var') and self.gaming_mode_var.get():
            self.activate_focused_widget_gaming()
            return
        
        widget_to_activate = None

        if self.focus_location == 'global':
            if 0 <= self.global_focused_index < len(self.global_navigable_widgets):
                widget_to_activate = self.global_navigable_widgets[self.global_focused_index]
        
        elif self.focus_location == 'tabs':
            self.move_focus('down') # Simular "Abajo" para entrar al contenido
            return
            
        elif self.focus_location == 'content':
            nav_list = self.navigable_widgets.get(self.current_tab_index, [])
            current_row, current_col = self.focused_indices[self.current_tab_index]
            
            if 0 <= current_row < len(nav_list) and 0 <= current_col < len(nav_list[current_row]):
                widget_to_activate = nav_list[current_row][current_col]

        if widget_to_activate is None: return

        try:
            # Caso especial: Pestaña AUTO, Fila de Juego (Col 0)
            if self.current_tab_index == 1 and hasattr(widget_to_activate, 'original_index'):
                original_index = getattr(widget_to_activate, 'original_index', -1)
                if original_index in self.game_checkbox_vars:
                     checkbox_var = self.game_checkbox_vars[original_index]
                     checkbox_var.set(not checkbox_var.get())
                     # Actualizar fondo del frame
                     highlight_bg = self._apply_appearance_mode(self.highlight_color)
                     widget_to_activate.configure(fg_color=highlight_bg if checkbox_var.get() else "transparent")
                     self.update_focus_visuals() # Re-aplicar borde
            
            # Caso especial: Pestaña CONFIG, RadioButton/Switch/Slider (estún en frames)
            elif self.current_tab_index == 0 and isinstance(widget_to_activate, ctk.CTkFrame): 
                target_widget = None
                for widget in widget_to_activate.winfo_children():
                    if isinstance(widget, (ctk.CTkRadioButton, ctk.CTkSwitch)):
                        target_widget = widget; break
                    elif isinstance(widget, ctk.CTkSlider): # Para el frame del slider
                        target_widget = widget; break
                if target_widget:
                    if isinstance(target_widget, ctk.CTkSlider):
                        # Toggle modo ediciún del slider con Enter
                        self.slider_edit_mode = not self.slider_edit_mode
                        try:
                            self._set_global_sharpness_edit_visuals(self.slider_edit_mode)
                        except Exception:
                            pass
                        if self.slider_edit_mode:
                            target_widget.focus()
                        else:
                            self.focus_set()
                    else:
                        target_widget.invoke()
            
            # Caso especial: Slider directo en pestaña CONFIG (no en frame extra)
            elif self.current_tab_index == 0 and isinstance(widget_to_activate, ctk.CTkSlider):
                # Toggle modo ediciún del slider con Enter
                self.slider_edit_mode = not self.slider_edit_mode
                try:
                    self._set_global_sharpness_edit_visuals(self.slider_edit_mode)
                except Exception:
                    pass
                if self.slider_edit_mode:
                    widget_to_activate.focus()
                else:
                    self.focus_set()
            
            # Caso especial: Pestaña CONFIG APP, Fila de Carpeta (Col 0)
            elif self.current_tab_index == 3 and 'custom_folders_list_frame' in str(widget_to_activate.master):
                 # No hacer nada al pulsar 'A' en la etiqueta de la carpeta
                 pass
                 
            # Entry
            elif isinstance(widget_to_activate, ctk.CTkEntry):
                 widget_to_activate.focus()
            
            # ComboBox (Selector de Versiún)
            elif isinstance(widget_to_activate, ctk.CTkComboBox):
                 try: widget_to_activate._open_dropdown_menóu()
                 except AttributeError: widget_to_activate.focus()
                 
            # Botones (úImportante para Fix 9!)
            elif isinstance(widget_to_activate, ctk.CTkButton):
                widget_to_activate.invoke()
                
            # Checkbox
            elif isinstance(widget_to_activate, ctk.CTkCheckBox):
                widget_to_activate.toggle()
                
            # Textbox (Log)
            elif isinstance(widget_to_activate, ctk.CTkTextbox):
                # No hacer nada al pulsar 'A' en el log
                pass

        except Exception as e:
            self.log_message('ERROR', f"Error al activar el widget enfocado: {e}")
    
    # ==============================================================================
    # NAVEGACIÓN POR TECLADO - MODO GAMING
    # ==============================================================================
    
    def move_focus_gaming(self, direction):
        """Navegación por teclado en la interfaz gaming con lógica bidimensional.
        
        Lógica de navegación:
        - En NAV: Arriba/Abajo mueve entre opciones, Derecha entra al panel activo
        - En CONTENT (Config): 
            * Arriba/Abajo: navega entre filas
            * Izquierda/Derecha en fila de presets: cambia entre presets
            * Izquierda/Derecha en fila de GPU: cambia entre AMD/NVIDIA
            * Izquierda/Derecha en fila de combo/slider: no hace nada (se activa con A)
            * Izquierda sin opción de interacción horizontal: vuelve a NAV
        """
        try:
            if self.gaming_focus_location == 'nav':
                # Navegando por el menú lateral
                nav_buttons = list(self.gaming_nav_buttons.values())
                nav_keys = list(self.gaming_nav_buttons.keys())
                max_idx = len(nav_buttons) - 1
                
                if direction == 'up':
                    self.gaming_nav_focused_index = max(0, self.gaming_nav_focused_index - 1)
                    self.update_focus_visuals_gaming()
                    
                elif direction == 'down':
                    self.gaming_nav_focused_index = min(max_idx, self.gaming_nav_focused_index + 1)
                    self.update_focus_visuals_gaming()
                    
                elif direction == 'right':
                    # Cambiar de panel automáticamente y entrar al contenido
                    if 0 <= self.gaming_nav_focused_index < len(nav_keys):
                        nav_buttons[self.gaming_nav_focused_index].invoke()
                        self.after(100, lambda: self._switch_to_gaming_content())
                    
                elif direction == 'left':
                    # Izquierda en el menú no hace nada
                    pass
                
            elif self.gaming_focus_location == 'content':
                # Determinar si estamos en panel de configuración (2D) u otro panel (1D)
                if hasattr(self, 'gaming_content_widgets_2d') and len(self.gaming_content_widgets_2d) > 0:
                    # Modo 2D para panel de configuración
                    self._move_focus_gaming_2d(direction)
                else:
                    # Modo 1D para otros paneles
                    self._move_focus_gaming_1d(direction)
                
        except Exception as e:
            pass  # Ignorar errores de navegación
    
    def _move_focus_gaming_2d(self, direction):
        """Navegación 2D para panel de configuración."""
        if not hasattr(self, 'gaming_content_focused_row'):
            self.gaming_content_focused_row = 0
            self.gaming_content_focused_col = 0
        
        max_row = len(self.gaming_content_widgets_2d) - 1
        current_row = self.gaming_content_widgets_2d[self.gaming_content_focused_row]
        
        if direction == 'up':
            # Subir a fila anterior
            if self.gaming_content_focused_row > 0:
                self.gaming_content_focused_row -= 1
                # Resetear columna al primer widget interactivo
                self.gaming_content_focused_col = self._get_first_widget_col(self.gaming_content_focused_row)
                self.update_focus_visuals_gaming()
                self._scroll_to_focused_gaming_widget()
                
        elif direction == 'down':
            # Bajar a fila siguiente
            if self.gaming_content_focused_row < max_row:
                self.gaming_content_focused_row += 1
                # Resetear columna al primer widget interactivo
                self.gaming_content_focused_col = self._get_first_widget_col(self.gaming_content_focused_row)
                self.update_focus_visuals_gaming()
                self._scroll_to_focused_gaming_widget()
                
        elif direction == 'left':
            # Lógica de izquierda: depende de la fila
            current_row_data = self.gaming_content_widgets_2d[self.gaming_content_focused_row]
            
            # Fila 0 (presets): navegar entre botones
            if self.gaming_content_focused_row == 0:
                if self.gaming_content_focused_col > 0:
                    self.gaming_content_focused_col -= 1
                    self.update_focus_visuals_gaming()
                else:
                    # Estamos en el primer preset, volver a nav
                    self.gaming_focus_location = 'nav'
                    self.update_focus_visuals_gaming()
            
            # Fila 1 (GPU con radiobuttons): navegar entre opciones
            elif len(current_row_data) > 2 and current_row_data[0] == 'GPU':
                if self.gaming_content_focused_col > 1:  # 1 es el primer radio, 2 el segundo
                    self.gaming_content_focused_col -= 1
                    # Activar automáticamente el radio
                    current_row_data[self.gaming_content_focused_col].invoke()
                    self.update_focus_visuals_gaming()
                else:
                    # Ya estamos en el primer radio, volver a nav
                    self.gaming_focus_location = 'nav'
                    self.update_focus_visuals_gaming()
            
            # Otras filas (combos, sliders, checkboxes): volver a nav O controlar slider
            else:
                # Caso especial: si es un slider, ajustar valor
                widget = current_row_data[self.gaming_content_focused_col]
                if isinstance(widget, ctk.CTkSlider):
                    value = float(widget.get())
                    new_value = max(0.0, value - 0.05)
                    widget.set(new_value)
                    # Actualizar label
                    try:
                        self.sharpness_label_var.set(f"{new_value:.2f}")
                        self.mark_config_as_custom()
                    except:
                        pass
                else:
                    # No es slider, volver a nav
                    self.gaming_focus_location = 'nav'
                    self.update_focus_visuals_gaming()
                
        elif direction == 'right':
            # Lógica de derecha: depende de la fila
            current_row_data = self.gaming_content_widgets_2d[self.gaming_content_focused_row]
            
            # Fila 0 (presets): navegar entre botones
            if self.gaming_content_focused_row == 0:
                if self.gaming_content_focused_col < len(current_row_data) - 1:
                    self.gaming_content_focused_col += 1
                    self.update_focus_visuals_gaming()
            
            # Fila 1 (GPU con radiobuttons): navegar entre opciones
            elif len(current_row_data) > 2 and current_row_data[0] == 'GPU':
                max_col = len(current_row_data) - 1
                if self.gaming_content_focused_col < max_col:
                    self.gaming_content_focused_col += 1
                    # Activar automáticamente el radio
                    current_row_data[self.gaming_content_focused_col].invoke()
                    self.update_focus_visuals_gaming()
            
            # Otras filas: controlar slider O no hacer nada
            else:
                # Caso especial: si es un slider, ajustar valor
                widget = current_row_data[self.gaming_content_focused_col]
                if isinstance(widget, ctk.CTkSlider):
                    value = float(widget.get())
                    new_value = min(1.0, value + 0.05)
                    widget.set(new_value)
                    # Actualizar label
                    try:
                        self.sharpness_label_var.set(f"{new_value:.2f}")
                        self.mark_config_as_custom()
                    except:
                        pass
                # Si no es slider, derecha no hace nada (se usa A para interactuar)
    
    def _move_focus_gaming_1d(self, direction):
        """Navegación 1D para paneles sin estructura bidimensional."""
        if not self.gaming_content_widgets:
            self.rebuild_gaming_content_widgets()
        
        if not self.gaming_content_widgets:
            return
        
        max_idx = len(self.gaming_content_widgets) - 1
        
        if direction == 'up':
            self.gaming_content_focused_index = max(0, self.gaming_content_focused_index - 1)
            self.update_focus_visuals_gaming()
            self._scroll_to_focused_gaming_widget()
            
        elif direction == 'down':
            self.gaming_content_focused_index = min(max_idx, self.gaming_content_focused_index + 1)
            self.update_focus_visuals_gaming()
            self._scroll_to_focused_gaming_widget()
            
        elif direction == 'left':
            # Volver al menú lateral
            self.gaming_focus_location = 'nav'
            self.update_focus_visuals_gaming()
            
        elif direction == 'right':
            # Derecha en contenido 1D no hace nada
            pass
    
    def _get_first_widget_col(self, row_idx):
        """Retorna el índice de la primera columna con widget interactivo en una fila."""
        if row_idx >= len(self.gaming_content_widgets_2d):
            return 0
        
        row_data = self.gaming_content_widgets_2d[row_idx]
        
        # Fila 0 (presets): columna 0
        if row_idx == 0:
            return 0
        
        # Otras filas: saltar el label de texto
        for i, item in enumerate(row_data):
            if not isinstance(item, str):
                return i
        
        return 0
    
    def _switch_to_gaming_content(self):
        """Helper para cambiar el foco al contenido después de activar un panel."""
        self.gaming_focus_location = 'content'
        self.rebuild_gaming_content_widgets()
        
        # Inicializar posición según tipo de panel
        if hasattr(self, 'gaming_content_widgets_2d') and len(self.gaming_content_widgets_2d) > 0:
            # Modo 2D: iniciar en fila 0, columna 0
            self.gaming_content_focused_row = 0
            self.gaming_content_focused_col = 0
        else:
            # Modo 1D: iniciar en índice 0
            self.gaming_content_focused_index = 0
        
        self.update_focus_visuals_gaming()
    
    def _scroll_to_focused_gaming_widget(self):
        """Hace scroll automático para mostrar el widget enfocado."""
        try:
            widget = None
            
            # Determinar widget según modo 2D o 1D
            if hasattr(self, 'gaming_content_widgets_2d') and len(self.gaming_content_widgets_2d) > 0:
                if hasattr(self, 'gaming_content_focused_row') and hasattr(self, 'gaming_content_focused_col'):
                    row_data = self.gaming_content_widgets_2d[self.gaming_content_focused_row]
                    widget = row_data[self.gaming_content_focused_col]
            else:
                if 0 <= self.gaming_content_focused_index < len(self.gaming_content_widgets):
                    widget = self.gaming_content_widgets[self.gaming_content_focused_index]
            
            if not widget or isinstance(widget, str):
                return
            
            # Buscar el frame scrolleable que contiene este widget
            parent = widget.master
            while parent:
                if isinstance(parent, ctk.CTkScrollableFrame):
                    # Hacer scroll al widget
                    try:
                        parent._scroll_to_widget(widget)
                    except:
                        # Método alternativo si _scroll_to_widget no existe
                        try:
                            widget_y = widget.winfo_y()
                            parent_height = parent.winfo_height()
                            widget_height = widget.winfo_height()
                            
                            # Calcular posición de scroll (0.0 a 1.0)
                            total_height = parent._parent_canvas.bbox("all")[3]
                            scroll_pos = max(0, min(1, widget_y / (total_height - parent_height)))
                            parent._parent_canvas.yview_moveto(scroll_pos)
                        except:
                            pass
                    break
                parent = parent.master if hasattr(parent, 'master') else None
        except Exception as e:
            pass
    
    def update_focus_visuals_gaming(self):
        """Actualiza los bordes visuales del foco en gaming.
        
        Sistema de colores:
        - Botón ACTIVO (panel abierto): Azul #00BFFF, ancho 3
        - Botón con FOCO (navegando): Verde brillante #00FF00, ancho 4
        - Botones inactivos: Gris #505050, ancho 2
        """
        try:
            # Limpiar todos los bordes de foco (pero mantener el activo)
            self.clear_all_gaming_focus_visuals()
            
            if self.gaming_focus_location == 'nav':
                # Resaltar botón del menú lateral con FOCO (verde brillante, más grueso)
                nav_buttons = list(self.gaming_nav_buttons.values())
                if 0 <= self.gaming_nav_focused_index < len(nav_buttons):
                    btn = nav_buttons[self.gaming_nav_focused_index]
                    # Verde brillante con borde MÁS GRUESO para distinguirlo del activo
                    btn.configure(border_color="#00FF00", border_width=4)
            
            elif self.gaming_focus_location == 'content':
                # Resaltar widget del contenido según modo 2D o 1D
                if hasattr(self, 'gaming_content_widgets_2d') and len(self.gaming_content_widgets_2d) > 0:
                    # Modo 2D: usar fila y columna
                    if hasattr(self, 'gaming_content_focused_row') and hasattr(self, 'gaming_content_focused_col'):
                        row_data = self.gaming_content_widgets_2d[self.gaming_content_focused_row]
                        widget = row_data[self.gaming_content_focused_col]
                        
                        if hasattr(widget, 'configure') and not isinstance(widget, str):
                            try:
                                widget.configure(border_color="#00FF00", border_width=3)
                            except:
                                pass
                else:
                    # Modo 1D: usar índice simple
                    if 0 <= self.gaming_content_focused_index < len(self.gaming_content_widgets):
                        widget = self.gaming_content_widgets[self.gaming_content_focused_index]
                        if hasattr(widget, 'configure'):
                            try:
                                widget.configure(border_color="#00FF00", border_width=3)
                            except:
                                pass
        except Exception as e:
            pass
    
    def clear_all_gaming_focus_visuals(self):
        """Limpia todos los bordes de foco en gaming, pero mantiene el highlight del botón activo."""
        try:
            # Restaurar bordes del menóú lateral
            nav_keys = list(self.gaming_nav_buttons.keys())
            for i, key in enumerate(nav_keys):
                btn = self.gaming_nav_buttons[key]
                
                # Determinar si este es el botón del panel activo
                is_active = hasattr(self, 'gaming_active_nav_key') and key == self.gaming_active_nav_key
                
                if is_active:
                    # Botón ACTIVO: restaurar borde AZUL (panel abierto)
                    btn.configure(border_color="#00BFFF", border_width=3)
                else:
                    # Botón inactivo: borde gris
                    btn.configure(border_color="#505050", border_width=2)
            
            # Limpiar contenido
            for widget in self.gaming_content_widgets:
                if hasattr(widget, 'configure'):
                    try:
                        # Restaurar bordes por defecto
                        widget.configure(border_color="#505050", border_width=2)
                    except:
                        pass
        except Exception as e:
            pass
    
    def rebuild_gaming_content_widgets(self):
        """Reconstruye la lista de widgets navegables del panel activo.
        
        Para panel de configuración: estructura 2D
        - Fila 0: [preset buttons] (5 botones, navegación horizontal)
        - Fila 1: ['GPU', radio_amd, radio_nvidia] (izq/der cambia entre radios)
        - Fila 2: ['DLL', combo_dll] (A/Enter abre selector)
        - Fila 3: ['FG', combo_fg]
        - Fila 4: ['Upscaler', combo_upscaler]
        - Fila 5: ['Upscale Mode', combo_upscale]
        - Fila 6: ['Sharpness', slider]
        - Fila 7: ['Overlay', checkbox_overlay]
        - Fila 8: ['Motion Blur', checkbox_blur]
        """
        self.gaming_content_widgets = []
        self.gaming_content_widgets_2d = []  # Nueva estructura 2D
        
        try:
            # Determinar qué panel está activo
            active_panel = None
            for panel in [self.gaming_config_panel, self.gaming_auto_panel, 
                         self.gaming_manual_panel, self.gaming_settings_panel]:
                if panel.winfo_ismapped():
                    active_panel = panel
                    break
            
            if not active_panel:
                return
            
            # Recolectar widgets navegables del panel activo
            if active_panel == self.gaming_config_panel:
                # Fila 0: Botones de presets (navegación horizontal)
                preset_row = [
                    self.gaming_btn_default, self.gaming_btn_perf, 
                    self.gaming_btn_bal, self.gaming_btn_qual, self.gaming_btn_custom
                ]
                self.gaming_content_widgets_2d.append(preset_row)
                
                # Fila 1: GPU (tipo especial con radiobuttons)
                # Necesitamos encontrar los radiobuttons de GPU
                gpu_radios = []
                for child in self.gaming_config_panel.winfo_children():
                    if isinstance(child, ctk.CTkScrollableFrame):
                        for frame in child.winfo_children():
                            if isinstance(frame, ctk.CTkFrame):
                                # Buscar frame de GPU por su contenido
                                for label in frame.winfo_children():
                                    if isinstance(label, ctk.CTkLabel) and "GPU" in label.cget("text"):
                                        # Encontrado frame de GPU, buscar radiobuttons
                                        for subframe in frame.winfo_children():
                                            if isinstance(subframe, ctk.CTkFrame):
                                                for radio in subframe.winfo_children():
                                                    if isinstance(radio, ctk.CTkRadioButton):
                                                        gpu_radios.append(radio)
                                        break
                if gpu_radios:
                    self.gaming_content_widgets_2d.append(['GPU'] + gpu_radios)
                
                # Fila 2: DLL combo
                if hasattr(self, 'gaming_dll_combo'):
                    self.gaming_content_widgets_2d.append(['DLL', self.gaming_dll_combo])
                
                # Fila 3: Frame Gen combo
                if hasattr(self, 'gaming_fg_combo'):
                    self.gaming_content_widgets_2d.append(['FG', self.gaming_fg_combo])
                
                # Fila 4: Upscaler combo
                if hasattr(self, 'gaming_upscaler_combo'):
                    self.gaming_content_widgets_2d.append(['Upscaler', self.gaming_upscaler_combo])
                
                # Fila 5: Upscale Mode combo
                if hasattr(self, 'gaming_upscale_combo'):
                    self.gaming_content_widgets_2d.append(['Upscale', self.gaming_upscale_combo])
                
                # Fila 6: Sharpness slider
                if hasattr(self, 'gaming_sharpness_slider'):
                    self.gaming_content_widgets_2d.append(['Sharpness', self.gaming_sharpness_slider])
                
                # Fila 7-8: Checkboxes (Overlay y Motion Blur)
                overlay_check = None
                blur_check = None
                for child in self.gaming_config_panel.winfo_children():
                    if isinstance(child, ctk.CTkScrollableFrame):
                        for frame in child.winfo_children():
                            if isinstance(frame, ctk.CTkFrame):
                                for checkbox in frame.winfo_children():
                                    if isinstance(checkbox, ctk.CTkCheckBox):
                                        if "Overlay" in checkbox.cget("text"):
                                            overlay_check = checkbox
                                        elif "Motion Blur" in checkbox.cget("text"):
                                            blur_check = checkbox
                
                if overlay_check:
                    self.gaming_content_widgets_2d.append(['Overlay', overlay_check])
                if blur_check:
                    self.gaming_content_widgets_2d.append(['MotionBlur', blur_check])
                
                # Crear también lista plana para compatibilidad
                for row in self.gaming_content_widgets_2d:
                    if isinstance(row, list):
                        for item in row:
                            if not isinstance(item, str):  # Saltar labels de texto
                                self.gaming_content_widgets.append(item)
                    else:
                        self.gaming_content_widgets.append(row)
                
            elif active_panel == self.gaming_auto_panel:
                # MEJORA: Panel auto - Navegaciún detallada por juegos y sus botones
                if hasattr(self, 'game_list_frame'):
                    for game_frame in self.game_list_frame.winfo_children():
                        if isinstance(game_frame, ctk.CTkFrame):
                            # Aúadir el frame del juego (para seleccionar checkbox)
                            self.gaming_content_widgets.append(game_frame)
                            
                            # Buscar el btn_frame que contiene los botones de acciún
                            for child in game_frame.winfo_children():
                                if isinstance(child, ctk.CTkFrame) and child.cget('fg_color') == 'transparent':
                                    # Este es el btn_frame, aúadir sus botones
                                    for btn in child.winfo_children():
                                        if isinstance(btn, ctk.CTkButton):
                                            self.gaming_content_widgets.append(btn)
                                    break
                
                # Aúadir botones de acciún globales al final
                if hasattr(self, 'btn_gaming_apply_selected'):
                    self.gaming_content_widgets.append(self.btn_gaming_apply_selected)
                if hasattr(self, 'btn_gaming_remove_selected'):
                    self.gaming_content_widgets.append(self.btn_gaming_remove_selected)
                    
            elif active_panel == self.gaming_manual_panel:
                # Panel manual: entry, botones
                pass  # Implemenótar si es necesario
                
            elif active_panel == self.gaming_settings_panel:
                # Panel settings: checkboxes, entries
                pass  # Implemenótar si es necesario
                
        except Exception as e:
            pass
    
    def activate_focused_widget_gaming(self):
        """Activa el widget actualmente enfocado en gaming."""
        try:
            if self.gaming_focus_location == 'nav':
                # Activar botón del menú lateral
                nav_buttons = list(self.gaming_nav_buttons.values())
                if 0 <= self.gaming_nav_focused_index < len(nav_buttons):
                    btn = nav_buttons[self.gaming_nav_focused_index]
                    btn.invoke()
                    # Reconstruir lista de widgets del nuevo panel
                    self.after(50, self.rebuild_gaming_content_widgets)
                    
            elif self.gaming_focus_location == 'content':
                # Determinar si estamos en modo 2D o 1D
                if hasattr(self, 'gaming_content_widgets_2d') and len(self.gaming_content_widgets_2d) > 0:
                    # Modo 2D: obtener widget de la estructura 2D
                    if hasattr(self, 'gaming_content_focused_row') and hasattr(self, 'gaming_content_focused_col'):
                        row_data = self.gaming_content_widgets_2d[self.gaming_content_focused_row]
                        widget = row_data[self.gaming_content_focused_col]
                        
                        if isinstance(widget, str):
                            return  # Es un label, no hacer nada
                        
                        # Botón de preset
                        if isinstance(widget, ctk.CTkButton):
                            widget.invoke()
                        
                        # RadioButton (GPU)
                        elif isinstance(widget, ctk.CTkRadioButton):
                            widget.invoke()
                        
                        # ComboBox (DLL, FG, Upscaler, etc.)
                        elif isinstance(widget, ctk.CTkComboBox):
                            try:
                                widget._open_dropdown_menu()
                            except:
                                widget.focus()
                        
                        # Slider (Sharpness) - no activar con A, se controla con izq/der
                        elif isinstance(widget, ctk.CTkSlider):
                            pass
                        
                        # Checkbox (Overlay, Motion Blur)
                        elif isinstance(widget, ctk.CTkCheckBox):
                            widget.toggle()
                
                else:
                    # Modo 1D: comportamiento original
                    if 0 <= self.gaming_content_focused_index < len(self.gaming_content_widgets):
                        widget = self.gaming_content_widgets[self.gaming_content_focused_index]
                        
                        # Frame de juego (toggle checkbox)
                        if isinstance(widget, ctk.CTkFrame) and hasattr(widget, 'original_index'):
                            original_index = widget.original_index
                            if original_index in self.game_checkbox_vars:
                                checkbox_var = self.game_checkbox_vars[original_index]
                                checkbox_var.set(not checkbox_var.get())
                                # Actualizar fondo
                                highlight_bg = self._apply_appearance_mode(self.highlight_color)
                                widget.configure(fg_color=highlight_bg if checkbox_var.get() else "transparent")
                                self.update_focus_visuals_gaming()
                        
                        # Botón
                        elif isinstance(widget, ctk.CTkButton):
                            widget.invoke()
                        
                        # ComboBox
                        elif isinstance(widget, ctk.CTkComboBox):
                            try:
                                widget._open_dropdown_menu()
                            except:
                                widget.focus()
                        
                        # Entry
                        elif isinstance(widget, ctk.CTkEntry):
                            widget.focus()
                        
        except Exception as e:
            pass

# ==============================================================================
# 6. NUEVAS CLASES DE VENTANA V2.0 (REFACTORIZADAS V5)
# ==============================================================================

# --- NUEVA CLASE (Mejora 6): Selector Personalizado Navegable ---
class CustomSelectWindow(ctk.CTkToplevel):
    def __init__(self, master, title, options, current_value, log_func, callback):
        super().__init__(master)
        self.log_func = log_func
        self.callback = callback
        self.options = options
        self.selected_value = None
        self.navigable_widgets = []
        self.focused_index = 0
        self.focus_color = ("#CCCCCC", "#999999")
        
        self.title(title)
        win_width = 400
        win_height = 300
        x = master.winfo_rootx() + (master.winfo_width() // 2) - (win_width // 2)
        y = master.winfo_rooty() + (master.winfo_height() // 2) - (win_height // 2)
        self.geometry(f'{win_width}x{win_height}+{x}+{y}')
        
        self.transient(master)
        self.protocol("WM_DELETE_WINDOW", self.on_cancel)
        self.bind("<Destroy>", self.on_destroy) # Asegurarse de que el callback se llame
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        scroll_frame = ctk.CTkScrollableFrame(self, label_text=title)
        scroll_frame.grid(row=0, column=0, sticky='nsew', padx=15, pady=15)
        scroll_frame.grid_columnconfigure(0, weight=1)

        for i, option in enumerate(options):
            btn = ctk.CTkButton(scroll_frame, text=option, command=lambda o=option: self.on_select(o), fg_color="#3a3a3a", hover_color="#4a4a4a")
            btn.grid(row=i, column=0, sticky='ew', padx=10, pady=4)
            self.navigable_widgets.append(btn)
            
            if option == current_value:
                self.focused_index = i
        
        self.after(50, self.update_focus_visuals) # Dar tiempo a que se dibujen
        self.after(100, lambda: self.navigable_widgets[self.focused_index].focus_set()) # Foco inicial
        
        # --- NUEVO (Mejora 10): Bindings de Teclado ---
        self.bind("<Up>", lambda e: self.move_focus(-1))
        self.bind("<Down>", lambda e: self.move_focus(1))
        self.bind("<Return>", lambda e: self.on_select(self.options[self.focused_index]))
        
    def on_destroy(self, event=None):
        """Llamado cuando la ventana se destruye por cualquier motivo."""
        if self.callback:
            # Si se destruye sin seleccionar, llama al callback con None
            self.callback(self.selected_value)
            self.callback = None # Evitar doble llamada
            
    def on_select(self, value=None):
        if value is None:
            value = self.options[self.focused_index]
        self.selected_value = value
        self.destroy() # Esto llamarú a on_destroy

    def on_cancel(self):
        self.selected_value = None
        self.destroy() # Esto llamarú a on_destroy

    def move_focus(self, direction):
        new_index = (self.focused_index + direction) % len(self.navigable_widgets)
        self.focused_index = new_index
        self.update_focus_visuals()

    def update_focus_visuals(self):
        for i, widget in enumerate(self.navigable_widgets):
            if i == self.focused_index:
                # Solo aplicar border_width si el widget lo soporta
                if not isinstance(widget, ctk.CTkRadioButton):
                    widget.configure(border_color=self.focus_color, border_width=2)
                else:
                    widget.configure(border_color=self.focus_color)
                widget.master._scroll_to_widget(widget) # Hacer scroll
            else:
                if not isinstance(widget, ctk.CTkRadioButton):
                    widget.configure(border_width=0)
                
    def handle_controller_event(self, event):
        """Maneja los eventos de mando pasados desde el padre."""
        if event.type == pygame.JOYHATMOTION:
            if event.hat == 0:
                hat_x, hat_y = event.value
                if hat_y == 1: self.move_focus(-1) # Arriba
                elif hat_y == -1: self.move_focus(1) # Abajo
        elif event.type == pygame.JOYBUTTONDOWN:
            if event.button == 0: # A
                self.on_select()
            elif event.button == 1: # B
                self.on_cancel()


# --- NUEVO: Detecciún de conexiún a internet ---
def check_internet_connection(timeout=3):
    """
    Verifica si hay conexiún a internet intentando conectar a GitHub.
    Returns: True si hay conexiún, False si no.
    """
    try:
        import socket
        socket.create_connection(("api.github.com", 443), timeout=timeout)
        return True
    except (socket.timeout, socket.error, OSError):
        return False


# --- MODIFICADA (V5): Clase de Descarga de Mod ---
class ModDownloaderWindow(ctk.CTkToplevel):
    def __init__(self, master, log_func):
        super().__init__(master)
        self.log_func = log_func
        self.master = master # Referencia a la app principal
        
        self.title("Gestor de Descargas de OptiScaler")
        win_width = 700
        win_height = 500
        x = master.winfo_x() + (master.winfo_width() // 2) - (win_width // 2)
        y = master.winfo_y() + (master.winfo_height() // 2) - (win_height // 2)
        self.geometry(f'{win_width}x{win_height}+{x}+{y}')
        
        self.transient(master)
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        
        # --- Lúgica de Navegaciún ---
        self.navigable_widgets = [] # Lista de listas [ [btn_refresh], [fila_release_1], [fila_release_2], ..., [btn_close] ]
        self.focused_indices = [0, 0] # [fila, col]
        self.focus_color = ("#CCCCCC", "#999999")

        # Header
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill='x', padx=15, pady=10)
        header_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(header_frame, text="Versiones de OptiScaler (GitHub)", font=ctk.CTkFont(size=14, weight="bold")).grid(row=0, column=0, sticky='w')
        self.btn_refresh = ctk.CTkButton(header_frame, text="🔄 Refrescar Lista (X)", command=self.on_refresh_clicked, fg_color="#3a3a3a", hover_color="#4a4a4a")
        self.btn_refresh.grid(row=0, column=1, sticky='e')
        
        # Lista
        self.release_list_frame = ctk.CTkScrollableFrame(self, corner_radius=8)
        self.release_list_frame.pack(fill='both', expand=True, padx=15, pady=5)
        self.release_list_frame.grid_columnconfigure(0, weight=1)
        
        # Footer (Progreso)
        footer_frame = ctk.CTkFrame(self, fg_color="transparent")
        footer_frame.pack(fill='x', padx=15, pady=10)
        footer_frame.grid_columnconfigure(0, weight=1)
        
        self.status_label = ctk.CTkLabel(footer_frame, text="Seleccione una versión para descargar...")
        self.status_label.grid(row=0, column=0, columnspan=2, sticky='w')
        
        self.progress_bar = ctk.CTkProgressBar(footer_frame, orientation="horizontal", mode="determinate")
        self.progress_bar.set(0)
        self.progress_bar.grid(row=1, column=0, sticky='ew', pady=(5,0))
        
        self.btn_close = ctk.CTkButton(footer_frame, text="Cerrar (B / Esc)", command=self.destroy, width=100, fg_color="#3a3a3a", hover_color="#4a4a4a")
        self.btn_close.grid(row=1, column=1, sticky='e', padx=(10,0))
        
        # Cargar datos
        self.after(100, self.on_refresh_clicked)
        
        # --- NUEVO (Mejora 10): Bindings de Teclado ---
        self.bind("<Return>", lambda e: self.activate_focused_widget())
        self.bind("<Up>", lambda e: self.move_focus('up'))
        self.bind("<Down>", lambda e: self.move_focus('down'))
        self.bind("<Left>", lambda e: self.move_focus('left'))
        self.bind("<Right>", lambda e: self.move_focus('right'))


    def on_refresh_clicked(self):
        """Inicia la búsqueda de releases."""
        for widget in self.release_list_frame.winfo_children():
            widget.destroy()
            
        # Verificar conexiún a internet primero
        if not check_internet_connection():
            from tkinter import messagebox
            self.status_label.configure(text="? Sin conexiún a internet")
            messagebox.showwarning(
                "Modo Offline",
                "No se detectú conexiún a internet.\n\n"
                "Solo puedes usar mods ya descargados en 'mod_source'.\n\n"
                "Para descargar nuevas versiones, conecta a WiFi y refresca.",
                parent=self
            )
            self.log_func('WARN', "Sin conexiún a internet. Modo offline activo.")
            return
        
        self.status_label.configure(text="Buscando versiones en GitHub...")
        self.progress_bar.set(0)
        self.update_idletasks()
        
        # Aúadir botones globales a la navegación
        self.navigable_widgets = [[self.btn_refresh], [self.btn_close]]
        self.focused_indices = [0, 0]
        
        # Usar un hilo para no congelar la UI de "Buscando..."
        threading.Thread(target=self.populate_releases, daemon=True).start()

    def populate_releases(self):
        """Busca y muestra las releases de GitHub."""
        releases = fetch_github_releases(self.log_func)
        
        def _update_ui():
            if not releases:
                self.status_label.configure(text="Error al buscar. Revise el Log.")
                ctk.CTkLabel(self.release_list_frame, text="No se pudieron cargar las versiones.").pack()
                self.focused_indices = [0, 0]
                self.after(50, self.update_focus_visuals)
                return

            self.master.github_releases = releases
            self.status_label.configure(text=f"Se encontraron {len(releases)} versiones. Seleccione una.")
            
            release_rows = []
            for i, release in enumerate(releases):
                item_frame = ctk.CTkFrame(self.release_list_frame, fg_color="transparent")
                item_frame.grid(row=i, column=0, sticky='ew', pady=2)
                item_frame.grid_columnconfigure(0, weight=1)
                
                label_text = f"{release['name']} (Publicado: {release['published_at'].split('T')[0]})"
                ctk.CTkLabel(item_frame, text=label_text).grid(row=0, column=0, sticky='w', padx=5)
                
                # Verificar si esta versión ya estú descargada (V2.1 Fix: buscar por nombre de asset)
                # El nombre de la carpeta es el nombre del archivo .7z sin la extensiún
                asset = next((a for a in release['assets'] if a['name'].endswith('.7z')), None)
                is_downloaded = False
                if asset:
                    release_folder_name = asset['name'].replace('.7z', '')  # Ej: OptiScaler_0.7.9
                    release_folder_path = os.path.join(MOD_SOURCE_DIR, release_folder_name)
                    is_downloaded = os.path.exists(release_folder_path) and os.path.isdir(release_folder_path)
                
                if is_downloaded:
                    btn = ctk.CTkButton(item_frame, text="❌", command=lambda r=release: self.on_delete_specific_clicked(r), width=40, fg_color="#3a3a3a", hover_color="#4a4a4a")
                else:
                    btn = ctk.CTkButton(item_frame, text="⬇️", command=lambda r=release: self.on_download_clicked(r), width=40, fg_color="#3a3a3a", hover_color="#4a4a4a")
                btn.grid(row=0, column=1, sticky='e', padx=5)
                release_rows.append([btn])  # Solo el botón es navegable

            # Insertar filas en la lista de navegación
            self.navigable_widgets = self.navigable_widgets[:1] + release_rows + self.navigable_widgets[1:]
            self.focused_indices = [0, 0]
            self.after(50, self.update_focus_visuals)
        
        self.after(0, _update_ui)

    def on_delete_clicked(self):
        """Elimina el mod descargado actualmenóte seleccionado."""
        import tkinter.messagebox as messagebox
        
        # Obtener carpeta de mod actual
        mod_source = getattr(self.master, 'mod_source_var', None)
        if not mod_source or not mod_source.get():
            messagebox.showwarning("Sin Mod", "No hay ningún mod seleccionado para eliminar.", parent=self)
            return
        
        mod_path = mod_source.get()
        
        # Confirmar eliminaciún
        response = messagebox.askyesno(
            "Confirmar Eliminaciún",
            f"úSeguro que desea eliminar el mod descargado?\n\nCarpeta:\n{mod_path}\n\nEsta acciún no se puede deshacer.",
            parent=self
        )
        
        if not response:
            return
        
        # Eliminar carpeta
        try:
            if os.path.exists(mod_path) and os.path.isdir(mod_path):
                shutil.rmtree(mod_path)
                self.log_func('OK', f"Mod eliminado: {os.path.basename(mod_path)}")
                messagebox.showinfo("Éxito", "El mod se eliminú correctamente.", parent=self)
                
                # Actualizar la app principal
                self.master.autodetect_mod_source()
                
                # Refrescar la lista para actualizar botones
                self.on_refresh_clicked()
            else:
                messagebox.showerror("Error", "La carpeta del mod no existe.", parent=self)
        except Exception as e:
            self.log_func('ERROR', f"Error al eliminar mod: {e}")
            messagebox.showerror("Error", f"No se pudo eliminar el mod:\n{e}", parent=self)
    
    def on_delete_specific_clicked(self, release_info):
        """Elimina un mod especúfico basado en la release."""
        import tkinter.messagebox as messagebox
        
        # Construir path del mod basado en el nombre del asset (V2.1 Fix)
        asset = next((a for a in release_info['assets'] if a['name'].endswith('.7z')), None)
        if not asset:
            messagebox.showerror("Error", "No se encontrú el asset .7z de esta release.", parent=self)
            return
            
        release_folder_name = asset['name'].replace('.7z', '')
        mod_path = os.path.join(MOD_SOURCE_DIR, release_folder_name)
        
        # Confirmar eliminaciún
        response = messagebox.askyesno(
            "Confirmar Eliminaciún",
            f"úSeguro que desea eliminar esta versión?\n\n{release_info['name']}\nCarpeta: {release_folder_name}\n\nEsta acciún no se puede deshacer.",
            parent=self
        )
        
        if not response:
            return
        
        # Eliminar carpeta
        try:
            if os.path.exists(mod_path) and os.path.isdir(mod_path):
                shutil.rmtree(mod_path)
                self.log_func('OK', f"Mod eliminado: {release_folder_name}")
                
                # También eliminar el archivo .7z si existe
                zip_file = mod_path + '.7z'
                if os.path.exists(zip_file):
                    os.remove(zip_file)
                    self.log_func('OK', f"Archivo .7z eliminado: {os.path.basename(zip_file)}")
                
                messagebox.showinfo("Éxito", "El mod se eliminú correctamente.", parent=self)
                
                # Actualizar la app principal
                self.master.autodetect_mod_source()
                
                # Refrescar la lista para actualizar botones
                self.on_refresh_clicked()
            else:
                messagebox.showerror("Error", "La carpeta del mod no existe.", parent=self)
        except Exception as e:
            self.log_func('ERROR', f"Error al eliminar mod: {e}")
            messagebox.showerror("Error", f"No se pudo eliminar el mod:\n{e}", parent=self)

    def on_download_clicked(self, release_info):
        """Inicia la descarga en un hilo separado."""
        # Desactivar todos los botones
        for row in self.navigable_widgets:
            for widget in row:
                if isinstance(widget, ctk.CTkButton):
                    widget.configure(state="disabled")
        
        self.status_label.configure(text="Iniciando descarga...")
        self.progress_bar.set(0)
        
        threading.Thread(target=download_mod_release, args=(release_info, self.update_progress_bar, self.log_func), daemon=True).start()

    def update_progress_bar(self, downloaded, total, done, message):
        """Callback thread-safe para actualizar la UI de progreso."""
        def _update_ui():
            if done:
                self.status_label.configure(text=message)
                self.progress_bar.set(1)
                for row in self.navigable_widgets:
                    for widget in row:
                         if isinstance(widget, ctk.CTkButton):
                            widget.configure(state="normal")
                # --- úIMPORTANTE! ---
                # Actualizar la carpeta de mod en la app principal
                self.master.autodetect_mod_source()
                # Refrescar la lista para actualizar botones (Descargar ? Borrar)
                self.on_refresh_clicked()
                
                # Auto-cerrar ventana después de 2 segundos (gestiún de RAM)
                if "Completado" in message or "completado" in message:
                    self.log_func('INFO', "Descarga completada. Cerrando gestor en 2 segundos...")
                    self.after(2000, self.destroy)
            else:
                progress = downloaded / total if total > 0 else 0
                self.progress_bar.set(progress)
                self.status_label.configure(text=f"Descargando... {downloaded//1024} KB / {total//1024} KB")
        
        self.after(0, _update_ui)

    def move_focus(self, direction): # 'up', 'down', 'left', 'right'
        """Mueve el foco entre los widgets navegables de la ventana."""
        if not self.navigable_widgets: return
        
        current_row, current_col = self.focused_indices
        max_row = len(self.navigable_widgets) - 1
        
        if direction == 'down':
            if current_row < max_row:
                current_row += 1
                # Mantener la columna si es posible, sino ir a la última columna disponible
                current_col = min(current_col, len(self.navigable_widgets[current_row]) - 1)
        elif direction == 'up':
            if current_row > 0:
                current_row -= 1
                # Mantener la columna si es posible, sino ir a la última columna disponible
                current_col = min(current_col, len(self.navigable_widgets[current_row]) - 1)
        elif direction == 'left':
            if current_col > 0:
                current_col -= 1
        elif direction == 'right':
            max_col = len(self.navigable_widgets[current_row]) - 1
            if current_col < max_col:
                current_col += 1
                
        self.focused_indices = [current_row, current_col]
        self.update_focus_visuals()

    def update_focus_visuals(self):
        for r_idx, row in enumerate(self.navigable_widgets):
            for c_idx, widget in enumerate(row):
                if r_idx == self.focused_indices[0] and c_idx == self.focused_indices[1]:
                    # Solo aplicar border_width si el widget lo soporta
                    if not isinstance(widget, ctk.CTkRadioButton):
                        widget.configure(border_color=self.focus_color, border_width=2)
                    else:
                        widget.configure(border_color=self.focus_color)
                    # Scroll si es una fila de release
                    if r_idx > 0 and r_idx < len(self.navigable_widgets) - 1:
                        widget.master.master._scroll_to_widget(widget.master)
                else:
                    if not isinstance(widget, ctk.CTkRadioButton):
                        widget.configure(border_width=0)
                    
    def activate_focused_widget(self):
        try:
            current_row, current_col = self.focused_indices
            widget = self.navigable_widgets[current_row][current_col]
            widget.invoke()
        except Exception:
            pass # Error al activar

    def handle_controller_event(self, event):
        """Maneja los eventos de mando pasados desde el padre."""
        if event.type == pygame.JOYHATMOTION:
            if event.hat == 0:
                hat_x, hat_y = event.value
                if hat_y == 1: self.move_focus('up')
                elif hat_y == -1: self.move_focus('down')
                elif hat_x == -1: self.move_focus('left')
                elif hat_x == 1: self.move_focus('right')
        elif event.type == pygame.JOYBUTTONDOWN:
            if event.button == 0: # A
                self.activate_focused_widget()
            elif event.button == 1: # B
                self.destroy()
            elif event.button == 2: # X
                self.on_refresh_clicked()


# --- MODIFICADO (V5): Ventana de Configuración de Juego (Mejora 6 y 12) ---
class GameConfigWindow(ctk.CTkToplevel):
    def __init__(self, master, game_path, game_name, current_config, log_func):
        super().__init__(master)
        
        self.master = master
        self.game_path = game_path
        self.log_func = log_func
        self.is_closing = False 
        self.slider_edit_mode = False
        
        # --- Lúgica de Navegaciún Hija (Mejora 12) ---
        self.child_popup = None
        self.navigable_widgets = []
        self.focused_indices = [0, 0]
        self.focus_color = ("#CCCCCC", "#999999")
        
        self.title(f"Configuración de: {game_name.split(']')[-1].strip()}")
        win_width = 800
        win_height = 550
        x = master.winfo_x() + (master.winfo_width() // 2) - (win_width // 2)
        y = master.winfo_y() + (master.winfo_height() // 2) - (win_height // 2)
        self.geometry(f'{win_width}x{win_height}+{x}+{y}')
        
        self.transient(master)
        self.protocol("WM_DELETE_WINDOW", self.on_cancel_and_close)
        
        # --- Control de presets ---
        self._applying_preset = False
        
        # --- Variables locales para esta ventana ---
        self.gpu_choice_var = ctk.IntVar(value=current_config.get("gpu_choice", 2))
        self.spoof_dll_name_var = ctk.StringVar(value=self.find_current_dll())
        self.fg_mode_var = ctk.StringVar(value=current_config.get("fg_mode", "Automático"))
        self.upscaler_var = ctk.StringVar(value=current_config.get("upscaler", "Automático"))
        self.upscale_mode_var = ctk.StringVar(value=current_config.get("upscale_mode", "Automático"))
        self.sharpness_var = ctk.DoubleVar(value=current_config.get("sharpness", 0.8))
        self.sharpness_label_var = ctk.StringVar(value=f"{self.sharpness_var.get():.2f}")
        self.overlay_var = ctk.BooleanVar(value=current_config.get("overlay", False))
        self.motion_blur_var = ctk.BooleanVar(value=current_config.get("motion_blur", True))

        # --- Construir la UI (similar a la Pestaña 1) ---
        config_main_frame = ctk.CTkFrame(self, fg_color="transparent")
        config_main_frame.pack(fill='both', expand=True, padx=15, pady=15)
        config_main_frame.grid_columnconfigure(1, weight=1)
        
        current_config_row = 0
        
        ctk.CTkLabel(config_main_frame, text=f"Editando OptiScaler.ini en:\n{self.game_path}", font=ctk.CTkFont(size=11), justify="left").grid(row=current_config_row, column=0, columnspan=2, sticky='w', padx=15, pady=(0, 10))
        current_config_row += 1

        # --- Fila Preset ---
        ctk.CTkLabel(config_main_frame, text="Preset Rápido:", font=ctk.CTkFont(size=12, weight="bold")).grid(row=current_config_row, column=0, sticky='w', padx=(15, 5))
        preset_frame = ctk.CTkFrame(config_main_frame, fg_color="transparent")
        preset_frame.grid(row=current_config_row, column=1, sticky='ew', pady=5, padx=15)
        preset_frame.grid_columnconfigure(0, weight=1)
        
        self.preset_combo = ctk.CTkComboBox(
            preset_frame,
            values=["Default", "Performance", "Balanced", "Quality", "Custom"],
            command=lambda choice: self.on_game_preset_selected(choice),
            width=200
        )
        self.preset_combo.set("Custom")
        self.preset_combo.grid(row=0, column=0, sticky='w', padx=5)
        
        btn_help_preset = ctk.CTkButton(
            preset_frame, 
            text="", 
            width=30, 
            height=30,
            font=ctk.CTkFont(size=16),
            command=lambda: self.show_help_popup("Presets Rápidos", 
                "Aplica configuraciones predefinidas optimizadas:\n\n" +
                "  • Performance: FSR 3.1, FG Activado, Upscale Rendimiento, Sharpness 0.5\n" +
                "  Prioriza FPS máximos con menor consumo de baterúa\n\n" +
                "ú Balanced: FSR 3.1, FG Automático, Upscale Equilibrado, Sharpness 0.7\n" +
                "  Balance úptimo entre rendimiento y calidad visual\n\n" +
                "  • Quality: FSR 3.1, FG Activado, Upscale Calidad, Sharpness 0.9\n" +
                "  Prioriza calidad visual, ideal para conectado a corriente\n\n" +
                "ú Custom: Configuración personalizada manual")
        )
        btn_help_preset.grid(row=0, column=1, padx=5)
        current_config_row += 1

        # --- Fila GPU ---
        ctk.CTkLabel(config_main_frame, text="Tipo de GPU:", font=ctk.CTkFont(size=12, weight="bold")).grid(row=current_config_row, column=0, sticky='w', padx=(15, 5))
        gpu_frame = ctk.CTkFrame(config_main_frame, fg_color="transparent")
        gpu_frame.grid(row=current_config_row, column=1, sticky='w', pady=5, padx=5)
        self.r_gpu_amd = ctk.CTkRadioButton(gpu_frame, text="AMD / Intel", variable=self.gpu_choice_var, value=1)
        self.r_gpu_amd.pack(side='left', padx=10)
        self.r_gpu_nvidia = ctk.CTkRadioButton(gpu_frame, text="NVIDIA", variable=self.gpu_choice_var, value=2)
        self.r_gpu_nvidia.pack(side='left', padx=10)
        current_config_row += 1

        # --- Fila DLL (REFACTORIZADA - Mejora 6b) ---
        ctk.CTkLabel(config_main_frame, text="DLL de Inyecciún:", font=ctk.CTkFont(size=12, weight="bold")).grid(row=current_config_row, column=0, sticky='w', padx=(15, 5))
        self.btn_dll_select = ctk.CTkButton(config_main_frame, text=f"{self.spoof_dll_name_var.get()}", command=lambda: self.open_custom_select("DLL de Inyecciún", SPOOFING_DLL_NAMES, self.btn_dll_select, "", self.spoof_dll_name_var), fg_color="#3a3a3a", hover_color="#4a4a4a")
        self.btn_dll_select.grid(row=current_config_row, column=1, sticky='ew', pady=5, padx=15)
        current_config_row += 1

        # --- Fila Frame Generation (REFACTORIZADA - Mejora 6b) ---
        fg_label_frame = ctk.CTkFrame(config_main_frame, fg_color="transparent")
        fg_label_frame.grid(row=current_config_row, column=0, sticky='w', padx=(15, 5))
        ctk.CTkLabel(fg_label_frame, text="Modo Frame Gen:", font=ctk.CTkFont(size=12, weight="bold")).pack(side='left')
        ctk.CTkLabel(fg_label_frame, text="⚡ ~+80% FPS", font=ctk.CTkFont(size=10), text_color="#00FF00").pack(side='left', padx=(5,0))
        
        self.btn_fg_select = ctk.CTkButton(config_main_frame, text=f"{self.fg_mode_var.get()}", command=lambda: self.open_custom_select("Modo Frame Gen", FG_OPTIONS, self.btn_fg_select, "", self.fg_mode_var), fg_color="#3a3a3a", hover_color="#4a4a4a")
        self.btn_fg_select.grid(row=current_config_row, column=1, sticky='ew', pady=5, padx=15)
        current_config_row += 1

        # --- Fila Reescalador (Backend) - NUEVA ---
        upscaler_label_frame = ctk.CTkFrame(config_main_frame, fg_color="transparent")
        upscaler_label_frame.grid(row=current_config_row, column=0, sticky='w', padx=(15, 5))
        ctk.CTkLabel(upscaler_label_frame, text="Reescalador:", font=ctk.CTkFont(size=12, weight="bold")).pack(side='left')
        ctk.CTkLabel(upscaler_label_frame, text="🎮", font=ctk.CTkFont(size=10), text_color="#888888").pack(side='left', padx=(5,0))
        
        self.btn_upscaler_select = ctk.CTkButton(config_main_frame, text=f"{self.upscaler_var.get()}", command=lambda: self.open_custom_select("Reescalador", UPSCALER_OPTIONS, self.btn_upscaler_select, "", self.upscaler_var), fg_color="#3a3a3a", hover_color="#4a4a4a")
        self.btn_upscaler_select.grid(row=current_config_row, column=1, sticky='ew', pady=5, padx=15)
        current_config_row += 1

        # --- Fila Reescalado (REFACTORIZADA - Mejora 6b) ---
        upscale_label_frame = ctk.CTkFrame(config_main_frame, fg_color="transparent")
        upscale_label_frame.grid(row=current_config_row, column=0, sticky='w', padx=(15, 5))
        ctk.CTkLabel(upscale_label_frame, text="Modo de Reescalado:", font=ctk.CTkFont(size=12, weight="bold")).pack(side='left')
        ctk.CTkLabel(upscale_label_frame, text="📊 +60% / +20%", font=ctk.CTkFont(size=10), text_color="#FFAA00").pack(side='left', padx=(5,0))
        
        self.btn_upscale_select = ctk.CTkButton(config_main_frame, text=f"{self.upscale_mode_var.get()}", command=lambda: self.open_custom_select("Modo Reescalado", UPSCALE_OPTIONS, self.btn_upscale_select, "", self.upscale_mode_var), fg_color="#3a3a3a", hover_color="#4a4a4a")
        self.btn_upscale_select.grid(row=current_config_row, column=1, sticky='ew', pady=5, padx=15)
        current_config_row += 1

        # --- Fila Nitidez ---
        ctk.CTkLabel(config_main_frame, text="Nitidez (Sharpness):", font=ctk.CTkFont(size=12, weight="bold")).grid(row=current_config_row, column=0, sticky='w', padx=(15, 5))
        sharpness_frame = ctk.CTkFrame(config_main_frame, fg_color="transparent")
        sharpness_frame.grid(row=current_config_row, column=1, sticky='ew', pady=5, padx=15)
        sharpness_frame.grid_columnconfigure(0, weight=1)
        self.slider_sharpness = ctk.CTkSlider(sharpness_frame, from_=0.0, to=2.0, variable=self.sharpness_var, 
                                              command=lambda v: self.on_sharpness_changed(v))
        self.slider_sharpness.grid(row=0, column=0, sticky='ew', padx=(10, 5))
        self.label_sharpness_value = ctk.CTkLabel(sharpness_frame, textvariable=self.sharpness_label_var, font=ctk.CTkFont(size=12), width=40)
        self.label_sharpness_value.grid(row=0, column=1, sticky='e', padx=(5,0))
        current_config_row += 1

        # --- Fila Toggles ---
        ctk.CTkLabel(config_main_frame, text="Opc. Adicionales:", font=ctk.CTkFont(size=12, weight="bold")).grid(row=current_config_row, column=0, sticky='w', padx=(15, 5))
        toggles_frame = ctk.CTkFrame(config_main_frame, fg_color="transparent")
        toggles_frame.grid(row=current_config_row, column=1, sticky='w', pady=5, padx=5)
        self.switch_overlay = ctk.CTkSwitch(toggles_frame, text="Mostrar Overlay (Debug)", variable=self.overlay_var, onvalue=True, offvalue=False)
        self.switch_overlay.pack(side='left', padx=10, pady=5)
        self.switch_motion_blur = ctk.CTkSwitch(toggles_frame, text="Forzar Desactivación Motion Blur", variable=self.motion_blur_var, onvalue=True, offvalue=False)
        self.switch_motion_blur.pack(side='left', padx=10, pady=5)
        current_config_row += 1

        # --- Fila Modo AMD/Handheld (Dual-Mod) ---
        self.install_nukem = ctk.BooleanVar(value=current_config.get("install_nukem", False))
        ctk.CTkLabel(config_main_frame, text="Instalación:", font=ctk.CTkFont(size=12, weight="bold")).grid(row=current_config_row, column=0, sticky='w', padx=(15, 5))
        nukem_frame = ctk.CTkFrame(config_main_frame, fg_color="transparent")
        nukem_frame.grid(row=current_config_row, column=1, sticky='w', pady=5, padx=5)
        nukem_frame.grid_columnconfigure(0, weight=1)
        
        self.checkbox_nukem = ctk.CTkCheckBox(
            nukem_frame,
            text="🎮 Modo AMD/Handheld (Frame Generation para AMD/Intel)",
            variable=self.install_nukem,
            onvalue=True,
            offvalue=False
        )
        self.checkbox_nukem.grid(row=0, column=0, sticky='w', padx=10, pady=5)
        
        nukem_info = ctk.CTkLabel(
            nukem_frame,
            text="ℹ️ Instala OptiScaler (upscaling) + dlssg-to-fsr3 (frame generation para GPUs AMD/Intel)",
            font=ctk.CTkFont(size=10),
            text_color="#888888"
        )
        nukem_info.grid(row=1, column=0, sticky='w', padx=10)
        current_config_row += 1

        # --- Botones Guardar/Cancelar ---
        bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        bottom_frame.pack(fill='x', pady=(10, 15), padx=15)
        bottom_frame.grid_columnconfigure(0, weight=1)
        
        btn_cancel = ctk.CTkButton(bottom_frame, text="Cancelar (B / Esc)", command=self.on_cancel_and_close, fg_color="#3a3a3a", hover_color="#4a4a4a")
        btn_cancel.grid(row=0, column=0, sticky='w', padx=10)
        
        btn_apply_close = ctk.CTkButton(bottom_frame, text="✅ Aplicar y Cerrar", command=self.on_save_and_close, 
                                fg_color="#3a3a3a", hover_color="#4a4a4a",
                                font=ctk.CTkFont(size=13, weight="bold"))
        btn_apply_close.grid(row=0, column=1, sticky='e', padx=10)

        # --- Lista de navegación (Mejora 12) ---
        self.navigable_widgets = [
            [self.preset_combo],
            [self.r_gpu_amd, self.r_gpu_nvidia],
            [self.btn_dll_select],
            [self.btn_fg_select],
            [self.btn_upscaler_select],
            [self.btn_upscale_select],
            [self.slider_sharpness],
            [self.switch_overlay, self.switch_motion_blur],
            [btn_cancel, btn_apply_close]
        ]
        self.after(50, self.update_focus_visuals)
        
        # --- Binding de Enter: activar el widget enfocado (abre desplegables, toggle switches, guardar, etc.) ---
        self.bind("<Return>", lambda e: self.activate_focused_widget())
        self.bind("<Up>", lambda e: self.move_focus('up'))
        self.bind("<Down>", lambda e: self.move_focus('down'))
        self.bind("<Left>", lambda e: self.move_focus('left'))
        self.bind("<Right>", lambda e: self.move_focus('right'))

    def find_current_dll(self):
        """Detecta quú DLL de inyección estú activo en la carpeta del juego."""
        for dll_name in SPOOFING_DLL_NAMES:
            if os.path.exists(os.path.join(self.game_path, dll_name)):
                try:
                    size_mb = os.path.getsize(os.path.join(self.game_path, dll_name)) / (1024*1024)
                    if size_mb > 0.5:
                        return dll_name
                except Exception:
                     return dll_name 
        
        if os.path.exists(os.path.join(self.game_path, 'OptiScaler.dll')):
             return 'OptiScaler.dll' 
             
        return SPOOFING_DLL_NAMES[0] 

    def on_cancel_and_close(self):
        """Se ejecuta al pulsar 'Cancelar', 'B' o la X de la ventana."""
        if self.is_closing: return
        self.is_closing = True
        
        self.log_func('INFO', f"Configuración de {os.path.basename(self.game_path)} cancelada.")
        self.destroy() 

    def on_apply_without_close(self):
        """Aplica cambios sin cerrar la ventana - Útil para testear."""
        self.log_func('TITLE', f"Aplicando configuración para: {os.path.basename(self.game_path)}")
        
        # 1. Gestionar el renombrado del DLL
        new_dll_name = self.spoof_dll_name_var.get()
        current_dll_name = self.find_current_dll()
        
        if new_dll_name != current_dll_name:
            self.log_func('INFO', f"Cambiando DLL de '{current_dll_name}' a '{new_dll_name}'...")
            
            # 1.1. Restaurar el DLL actual a OptiScaler.dll
            current_dll_path = os.path.join(self.game_path, current_dll_name)
            optiscaler_dll_path = os.path.join(self.game_path, 'OptiScaler.dll')
            
            if os.path.exists(current_dll_path) and current_dll_name != 'OptiScaler.dll':
                try:
                    if os.path.exists(optiscaler_dll_path): os.remove(optiscaler_dll_path)
                    os.rename(current_dll_path, optiscaler_dll_path)
                    self.log_func('INFO', f"'{current_dll_name}' renombrado de vuelta a 'OptiScaler.dll'.")
                except Exception as e:
                    self.log_func('ERROR', f"Fallo al restaurar {current_dll_name} a OptiScaler.dll: {e}")
            
            # 1.2. Renombrar OptiScaler.dll al nuevo nombre
            if new_dll_name != 'OptiScaler.dll':
                if not configure_and_rename_dll(self.game_path, new_dll_name, self.log_func):
                    self.log_func('ERROR', "úFallo crútico al renombrar al nuevo DLL!")
                    messagebox.showerror("Error de Renombrado", "No se pudo renombrar al nuevo DLL. úJuego abierto?", parent=self)
                    return
            
        else:
            self.log_func('INFO', "El DLL de inyección no ha cambiado.")

        # 2. Actualizar el INI
        update_optiscaler_ini(
            target_dir=self.game_path,
            gpu_choice=self.gpu_choice_var.get(),
            fg_mode_selected=self.fg_mode_var.get(),
            upscaler_selected=self.upscaler_var.get(),
            upscale_mode_selected=self.upscale_mode_var.get(),
            sharpness_selected=self.sharpness_var.get(),
            overlay_selected=self.overlay_var.get(),
            mb_selected=self.motion_blur_var.get(),
            log_func=self.log_func
        )
        
        self.log_func('OK', "? Configuración aplicada (ventana permanece abierta)")
        
        # 3. Refrescar la lista de juegos en la ventana principal
        if hasattr(self.master, '_refresh_game_list_after_operation'):
            self.master._refresh_game_list_after_operation()
        
        # Mostrar feedback visual
        from tkinter import messagebox
        messagebox.showinfo("Configuración Aplicada", 
                          "? Cambios guardados correctamente.\n\nAhora puedes lanzar el juego desde Steam/Launcher.",
                          parent=self)

    def on_save_and_close(self):
        """Se ejecuta al pulsar 'Guardar' o 'X' en el mando."""
        if self.is_closing: return
        self.is_closing = True
        
        self.log_func('TITLE', f"Guardando configuración para: {os.path.basename(self.game_path)}")
        
        # 1. Gestionar el renombrado del DLL
        new_dll_name = self.spoof_dll_name_var.get()
        current_dll_name = self.find_current_dll()
        
        if new_dll_name != current_dll_name:
            self.log_func('INFO', f"Cambiando DLL de '{current_dll_name}' a '{new_dll_name}'...")
            
            # 1.1. Restaurar el DLL actual a OptiScaler.dll
            current_dll_path = os.path.join(self.game_path, current_dll_name)
            optiscaler_dll_path = os.path.join(self.game_path, 'OptiScaler.dll')
            
            if os.path.exists(current_dll_path) and current_dll_name != 'OptiScaler.dll':
                try:
                    if os.path.exists(optiscaler_dll_path): os.remove(optiscaler_dll_path)
                    os.rename(current_dll_path, optiscaler_dll_path)
                    self.log_func('INFO', f"'{current_dll_name}' renombrado de vuelta a 'OptiScaler.dll'.")
                except Exception as e:
                    self.log_func('ERROR', f"Fallo al restaurar {current_dll_name} a OptiScaler.dll: {e}")
            
            # 1.2. Renombrar OptiScaler.dll al nuevo nombre
            if new_dll_name != 'OptiScaler.dll':
                if not configure_and_rename_dll(self.game_path, new_dll_name, self.log_func):
                    self.log_func('ERROR', "úFallo crútico al renombrar al nuevo DLL!")
                    messagebox.showerror("Error de Renombrado", "No se pudo renombrar al nuevo DLL. úJuego abierto?", parent=self)
            
        else:
            self.log_func('INFO', "El DLL de inyección no ha cambiado.")

        # 2. Actualizar el INI
        update_optiscaler_ini(
            target_dir=self.game_path,
            gpu_choice=self.gpu_choice_var.get(),
            fg_mode_selected=self.fg_mode_var.get(),
            upscaler_selected=self.upscaler_var.get(),
            upscale_mode_selected=self.upscale_mode_var.get(),
            sharpness_selected=self.sharpness_var.get(),
            overlay_selected=self.overlay_var.get(),
            mb_selected=self.motion_blur_var.get(),
            log_func=self.log_func
        )
        
        self.log_func('OK', "Configuración por juego guardada.")
        
        # 3. Refrescar la lista de juegos en la ventana principal
        if hasattr(self.master, '_refresh_game_list_after_operation'):
            self.master._refresh_game_list_after_operation()
            
        self.destroy()
    
    def apply_game_preset(self, preset_name):
        """Aplica un preset a la configuración del juego individual."""
        presets = {
            "performance": {
                "upscaler": "FSR 3.1",
                "fg_mode": "Activado",
                "upscale_mode": "Rendimiento",
                "sharpness": 0.5
            },
            "balanced": {
                "upscaler": "FSR 3.1",
                "fg_mode": "Automático",
                "upscale_mode": "Equilibrado",
                "sharpness": 0.7
            },
            "quality": {
                "upscaler": "FSR 3.1",
                "fg_mode": "Activado",
                "upscale_mode": "Calidad",
                "sharpness": 0.9
            }
        }
        
        if preset_name not in presets:
            return
        
        preset = presets[preset_name]
        
        # Bloquear callbacks temporalmenóte
        self._applying_preset = True
        
        # Aplicar valores
        self.upscaler_var.set(preset["upscaler"])
        self.btn_upscaler_select.configure(text=f"{preset['upscaler']} ⬇️")
        
        self.fg_mode_var.set(preset["fg_mode"])
        self.btn_fg_select.configure(text=f"{preset['fg_mode']} ⬇️")
        
        self.upscale_mode_var.set(preset["upscale_mode"])
        self.btn_upscale_select.configure(text=f"{preset['upscale_mode']} ⬇️")
        
        self.sharpness_var.set(preset["sharpness"])
        self.sharpness_label_var.set(f"{preset['sharpness']:.2f}")
        
        # Actualizar combo
        self.preset_combo.set(preset_name.capitalize())
        
        # Desbloquear callbacks
        self._applying_preset = False
        
        self.log_func('INFO', f"Preset '{preset_name.capitalize()}' aplicado a {os.path.basename(self.game_path)}")
    
    def on_game_preset_selected(self, choice):
        """Maneja la selección de preset en ventana de configuración individual."""
        if choice == "Custom":
            return
        self.apply_game_preset(choice.lower())
    
    def mark_game_config_as_custom(self):
        """Marca la configuración del juego como Custom cuando se hace un cambio manual."""
        if hasattr(self, '_applying_preset') and self._applying_preset:
            return
        if hasattr(self, 'preset_combo'):
            self.preset_combo.set("Custom")
    
    def on_sharpness_changed(self, value):
        """Callback cuando cambia el slider de nitidez."""
        self.sharpness_label_var.set(f"{value:.2f}")
        self.mark_game_config_as_custom()
    
    def on_gaming_sharpness_changed(self, value):
        """Callback cuando cambia el slider de nitidez en modo gaming."""
        self.sharpness_label_var.set(f"{value:.2f}")
        self.mark_config_as_custom()
    
    def show_help_popup(self, title, message):
        """Muestra una ventana de ayuda con información."""
        help_window = ctk.CTkToplevel(self)
        help_window.title(title)
        help_window.geometry("500x350")
        help_window.transient(self)
        help_window.grab_set()
        
        x = self.winfo_x() + (self.winfo_width() // 2) - 250
        y = self.winfo_y() + (self.winfo_height() // 2) - 175
        help_window.geometry(f"500x350+{x}+{y}")
        
        text_widget = ctk.CTkTextbox(help_window, wrap="word", font=ctk.CTkFont(size=12))
        text_widget.pack(fill="both", expand=True, padx=15, pady=15)
        text_widget.insert("1.0", message)
        text_widget.configure(state="disabled")
        
        btn_close = ctk.CTkButton(help_window, text="Cerrar", command=help_window.destroy, fg_color="#3a3a3a", hover_color="#4a4a4a")
        btn_close.pack(pady=(0, 15))

    # --- NUEVO (Mejora 12): Lúgica de popup para GameConfigWindow ---
    # --- NUEVO (Mejora #2): Actualizar foco al hacer click ---
    def update_focus_from_click(self, widget):
        """Actualiza el índice de foco cuando se hace click en un widget navegable."""
        for row_idx, row in enumerate(self.navigable_widgets):
            for col_idx, nav_widget in enumerate(row):
                if nav_widget == widget:
                    self.focused_indices = [row_idx, col_idx]
                    self.update_focus_visuals()
                    return
    
    def open_custom_select(self, title, options, button_widget, text_prefix, string_var):
        """Abre un popup de selecciún modal a ESTA ventana."""
        # Actualizar foco al hacer click en el botón
        self.update_focus_from_click(button_widget)
        
        if self.child_popup:
            try: self.child_popup.focus_force()
            except: self.child_popup = None
            return
            
        current_value = string_var.get()

        def on_selection_made(new_value):
            if new_value:
                string_var.set(new_value)
                button_widget.configure(text=f"{text_prefix}{new_value}")
                self.mark_game_config_as_custom()  # Marcar como Custom al cambiar
            self.child_popup = None # De-registrar popup
            self.grab_set() # Re-tomar el foco
            self.focus_set() # Devolver foco a esta ventana
            self.update_focus_visuals() # Reactivar el foco visual

        select_window = CustomSelectWindow(self, title, options, current_value, self.log_func, on_selection_made)
        self.child_popup = select_window
        # --- NUEVO (Mejora 10): Binding de Teclado ---
        select_window.bind("<Escape>", lambda e: select_window.on_cancel())
        select_window.grab_set()
        
    def move_focus(self, direction): # 'up', 'down', 'left', 'right'
        """Mueve el foco entre los widgets navegables de la ventana de configuración."""
        if not self.navigable_widgets: return
        
        prev_row, prev_col = self.focused_indices
        current_row, current_col = prev_row, prev_col
        max_row = len(self.navigable_widgets) - 1
        
        if direction == 'down':
            if current_row < max_row:
                current_row += 1
                # Mantener la columna si es posible, sino ir a la última columna disponible
                current_col = min(current_col, len(self.navigable_widgets[current_row]) - 1)
        elif direction == 'up':
            if current_row > 0:
                current_row -= 1
                # Mantener la columna si es posible, sino ir a la última columna disponible
                current_col = min(current_col, len(self.navigable_widgets[current_row]) - 1)
        elif direction == 'left':
            # Si el widget enfocado es el slider y estamos en modo ediciún, ajustar valor
            try:
                w = self.navigable_widgets[current_row][current_col]
                if isinstance(w, ctk.CTkSlider) and self.slider_edit_mode:
                    value = float(self.sharpness_var.get())
                    new_value = max(0.0, value - 0.04)
                    self.slider_sharpness.set(new_value)
                    # Asegurar actualización visual de etiqueta en ajustes por teclado (sin guardar aquú)
                    try:
                        self.sharpness_label_var.set(f"{new_value:.2f}")
                    except Exception:
                        pass
                    self.update_focus_visuals()
                    return
            except Exception:
                pass
            if current_col > 0:
                current_col -= 1
        elif direction == 'right':
            try:
                w = self.navigable_widgets[current_row][current_col]
                if isinstance(w, ctk.CTkSlider) and self.slider_edit_mode:
                    value = float(self.sharpness_var.get())
                    new_value = min(2.0, value + 0.04)
                    self.slider_sharpness.set(new_value)
                    # Asegurar actualización visual de etiqueta en ajustes por teclado (sin guardar aquú)
                    try:
                        self.sharpness_label_var.set(f"{new_value:.2f}")
                    except Exception:
                        pass
                    self.update_focus_visuals()
                    return
            except Exception:
                pass
            max_col = len(self.navigable_widgets[current_row]) - 1
            if current_col < max_col:
                current_col += 1
                
        self.focused_indices = [current_row, current_col]
        if [current_row, current_col] != [prev_row, prev_col]:
            self.slider_edit_mode = False
            try:
                self._set_slider_edit_visuals(False)
            except Exception:
                pass
        self.update_focus_visuals()

    def update_focus_visuals(self):
        for r_idx, row in enumerate(self.navigable_widgets):
            for c_idx, widget in enumerate(row):
                if r_idx == self.focused_indices[0] and c_idx == self.focused_indices[1]:
                    # Solo aplicar border_width si el widget lo soporta (no RadioButton)
                    if not isinstance(widget, ctk.CTkRadioButton):
                        widget.configure(border_color=self.focus_color, border_width=2)
                    else:
                        widget.configure(border_color=self.focus_color)
                else:
                    if not isinstance(widget, ctk.CTkRadioButton):
                        widget.configure(border_width=0)
                    
    def activate_focused_widget(self):
        try:
            current_row, current_col = self.focused_indices
            widget = self.navigable_widgets[current_row][current_col]
            
            if isinstance(widget, (ctk.CTkButton, ctk.CTkRadioButton, ctk.CTkSwitch)):
                widget.invoke()
            elif isinstance(widget, ctk.CTkSlider):
                # Toggle ediciún con Enter
                self.slider_edit_mode = not self.slider_edit_mode
                try:
                    self._set_slider_edit_visuals(self.slider_edit_mode)
                except Exception:
                    pass
                if self.slider_edit_mode:
                    widget.focus_set()
                else:
                    self.focus_set()
        except Exception as e:
            self.log_func('ERROR', f"GameConfig: Error al activar widget: {e}")

    def _set_slider_edit_visuals(self, editing: bool):
        """Cambiar colores del slider para indicar modo ediciún."""
        try:
            slider = self.slider_sharpness
            # Guardar colores iniciales solo una vez
            if not hasattr(self, "_slider_btn_color_default"):
                try:
                    self._slider_btn_color_default = slider.cget("button_color")
                except Exception:
                    self._slider_btn_color_default = None
            if not hasattr(self, "_slider_prog_color_default"):
                try:
                    self._slider_prog_color_default = slider.cget("progress_color")
                except Exception:
                    self._slider_prog_color_default = None

            if editing:
                # Color de realce
                highlight = "#00BFFF"
                try:
                    slider.configure(button_color=highlight)
                except Exception:
                    pass
                try:
                    slider.configure(progress_color=highlight)
                except Exception:
                    pass
            else:
                # Restaurar
                try:
                    if getattr(self, "_slider_btn_color_default", None) is not None:
                        slider.configure(button_color=self._slider_btn_color_default)
                except Exception:
                    pass
                try:
                    if getattr(self, "_slider_prog_color_default", None) is not None:
                        slider.configure(progress_color=self._slider_prog_color_default)
                except Exception:
                    pass
        except Exception:
            pass

    def handle_controller_event(self, event):
        """Maneja los eventos de mando pasados desde el padre."""
        # 1. Si hay un popup hijo, pasarle el evento
        if self.child_popup:
            if hasattr(self.child_popup, 'handle_controller_event'):
                self.child_popup.handle_controller_event(event)
            return
            
        # 2. Si no, manejarlo nosotros
        if event.type == pygame.JOYHATMOTION:
            if event.hat == 0:
                hat_x, hat_y = event.value
                if hat_y == 1: self.move_focus('up')
                elif hat_y == -1: self.move_focus('down')
                elif hat_x == -1: self.move_focus('left')
                elif hat_x == 1: self.move_focus('right')
        elif event.type == pygame.JOYBUTTONDOWN:
            if event.button == 0: # A
                self.activate_focused_widget()
            elif event.button == 1: # B
                self.on_cancel_and_close()
            elif event.button == 2: # X
                self.on_save_and_close()


# ==============================================================================
# 7. Punto de Entrada
# ==============================================================================

# --- Fin de la clase FSRInjectorApp ---

if __name__ == "__main__":
    # Crear carpeta de mod_source si no existe
    if not os.path.exists(MOD_SOURCE_DIR):
        try:
            os.makedirs(MOD_SOURCE_DIR)
        except Exception as e:
            print(f"Error al crear la carpeta mod_source: {e}")
            
    try:
        run_as_admin() # Esta funciún ahora estú vacía, --uac-admin se encarga
        app = FSRInjectorApp()
        app.mainloop()
    except Exception as e:
        print(f"Error fatal al iniciar la aplicaciún: {e}")
        print(traceback.format_exc())
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("Error Fatal", f"No se pudo iniciar la aplicaciún:\n{e}\n\nConsulte la consola para más detalles.")
        except:
            pass


# === VENTANA DE GESTIúN DE CARPETAS DE ESCANEO ===

class ScanFoldersWindow(ctk.CTkToplevel):
    """Ventana para agregar/quitar carpetas de escaneo de juegos."""
    
    def __init__(self, master, log_func, refresh_callback):
        super().__init__(master)
        self.master_app = master
        self.log_func = log_func
        self.refresh_callback = refresh_callback
        
        self.title("Gestiún de Carpetas de Escaneo")
        self.geometry("700x500")
        self.resizable(True, True)
        
        # Centrar ventana
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (700 // 2)
        y = (self.winfo_screenheight() // 2) - (500 // 2)
        self.geometry(f"700x500+{x}+{y}")
        
        # Header
        header = ctk.CTkFrame(self, fg_color="#2b2b2b", corner_radius=0)
        header.pack(fill='x')
        ctk.CTkLabel(header, text="📁 GESTIÓN DE CARPETAS DE ESCANEO", 
                     font=ctk.CTkFont(size=18, weight="bold"),
                     text_color="white").pack(pady=15)
        
        # Instrucciones
        info_frame = ctk.CTkFrame(self, fg_color="transparent")
        info_frame.pack(fill='x', padx=20, pady=10)
        ctk.CTkLabel(info_frame, 
                     text="Agrega carpetas donde se encuentran instalados tus juegos.\nEl escúner buscarú juegos compatibles en estas ubicaciones.",
                     font=ctk.CTkFont(size=12),
                     text_color="gray").pack()
        
        # Lista de carpetas
        list_frame = ctk.CTkFrame(self, fg_color="transparent")
        list_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        ctk.CTkLabel(list_frame, text="Carpetas actuales:", 
                     font=ctk.CTkFont(size=14, weight="bold")).pack(anchor='w', pady=(0,5))
        
        self.folders_listbox = ctk.CTkTextbox(list_frame, font=ctk.CTkFont(size=12),
                                              fg_color="#2a2a2a", wrap="none")
        self.folders_listbox.pack(fill='both', expand=True)
        
        # Botones
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill='x', padx=20, pady=(0,20))
        
        ctk.CTkButton(btn_frame, text="➕ Agregar Carpeta", 
                     command=self.add_folder,
                     height=40, fg_color="#3a3a3a", hover_color="#4a4a4a",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(side='left', padx=5, expand=True, fill='x')
        
        ctk.CTkButton(btn_frame, text="➖ Quitar Seleccionada", 
                     command=self.remove_folder,
                     height=40, fg_color="#CC3333", hover_color="#AA2222",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(side='left', padx=5, expand=True, fill='x')
        
        ctk.CTkButton(btn_frame, text="🔄 Actualizar Escaneo", 
                     command=self.refresh_scan,
                     height=40, fg_color="#3a3a3a", hover_color="#4a4a4a",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(side='left', padx=5, expand=True, fill='x')
        
        # Cargar carpetas actuales
        self.load_folders()
        
        # Hacer modal
        self.grab_set()
        self.focus()
    
    def load_folders(self):
        """Carga las carpetas desde el config."""
        self.folders_listbox.configure(state="normal")
        self.folders_listbox.delete("1.0", "end")
        
        # Acceder a custom_search_folders del master
        scan_folders = self.master_app.custom_search_folders
        
        if not scan_folders:
            self.folders_listbox.insert("1.0", "No hay carpetas configuradas.\nAgrega una carpeta para comenózar a escanear juegos.")
        else:
            for i, folder in enumerate(scan_folders, 1):
                self.folders_listbox.insert("end", f"{i}. {folder}\n")
        
        self.folders_listbox.configure(state="disabled")
    
    def add_folder(self):
        """Agrega una nueva carpeta."""
        folder = filedialog.askdirectory(title="Selecciona una carpeta para escanear")
        if not folder:
            return
        
        # Verificar si ya existe
        if folder in self.master_app.custom_search_folders:
            messagebox.showinfo("Informaciún", "Esta carpeta ya estú en la lista.", parent=self)
            return
        
        # Agregar
        self.master_app.custom_search_folders.append(folder)
        self.master_app.save_config()
        
        self.log_func('OK', f"Carpeta agregada: {folder}")
        self.load_folders()
    
    def remove_folder(self):
        """Quita la carpeta seleccionada."""
        # Obtener lúnea seleccionada
        try:
            selection = self.folders_listbox.selection_get()
        except:
            messagebox.showwarning("Advertencia", "Por favor, selecciona una lúnea en la lista.", parent=self)
            return
        
        # Extraer número de carpeta
        try:
            line_text = selection.strip()
            if not line_text or "No hay carpetas" in line_text:
                return
            
            folder_num = int(line_text.split('.')[0]) - 1
            
            if 0 <= folder_num < len(self.master_app.custom_search_folders):
                removed_folder = self.master_app.custom_search_folders.pop(folder_num)
                self.master_app.save_config()
                
                self.log_func('OK', f"Carpeta eliminada: {removed_folder}")
                self.load_folders()
            else:
                messagebox.showerror("Error", "Número de carpeta invúlido.", parent=self)
        except (ValueError, IndexError):
            messagebox.showerror("Error", "No se pudo identificar la carpeta seleccionada.", parent=self)
    
    def refresh_scan(self):
        """Actualiza el escaneo de juegos."""
        self.log_func('INFO', "Actualizando escaneo de juegos...")
        self.refresh_callback()
        self.log_func('OK', "Escaneo actualizado")
        messagebox.showinfo("Éxito", "El escaneo de juegos se ha actualizado.", parent=self)












