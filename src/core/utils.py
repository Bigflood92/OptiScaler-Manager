"""Funciones auxiliares generales."""

import os
import sys
import platform
import ctypes
import winreg
import re
import glob
from urllib.request import urlopen

from ..config.paths import (
    STEAM_COMMON_DIR, COMMON_EXE_SUBFOLDERS_DIRECT,
    RECURSIVE_EXE_PATTERNS
)
from .settings import EXE_BLACKLIST_KEYWORDS
from ..config.constants import (
    SEVEN_ZIP_DOWNLOAD_URL, SEVEN_ZIP_EXE_NAME
)

def is_admin():
    """Verifica si el script se ejecuta con permisos de administrador en Windows."""
    try:
        if platform.system() == "Windows":
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        return True
    except Exception:
        return False

def run_as_admin():
    """Relanza el proceso actual con privilegios de administrador (UAC).

    Returns:
        bool: True si se lanzó correctamente la elevación (el proceso actual
              debe salir inmediatamente después). False si falló.
    """
    try:
        # Construir los parámetros del proceso actual
        params = " ".join([f'"{arg}"' for arg in sys.argv[1:]])

        # Ejecutar con "runas" para disparar UAC
        ret = ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, params, None, 1)
        # ShellExecuteW devuelve un valor > 32 en caso de éxito
        return ret > 32
    except Exception:
        return False

def get_script_base_path():
    """Obtiene la ruta base del script o del .exe compilado."""
    try:
        if getattr(sys, 'frozen', False):
            # Estamos ejecutando en un .exe compilado
            return os.path.dirname(sys.executable)
        else:
            # Estamos ejecutando como un .py normal
            return os.path.dirname(__file__)
    except Exception:
        return os.path.abspath(".")

def check_and_download_7zip(log_func, master_widget=None):
    """
    Verifica si 7z.exe existe y, si no, lo descarga.
    Devuelve True si 7z.exe está listo, False si no.
    """
    base_path = get_script_base_path()
    seven_zip_exe_path = os.path.join(base_path, SEVEN_ZIP_EXE_NAME)

    if os.path.exists(seven_zip_exe_path):
        log_func('INFO', f"{SEVEN_ZIP_EXE_NAME} encontrado. Extracción habilitada.")
        return True

    log_func('ERROR', f"¡No se encontró {SEVEN_ZIP_EXE_NAME}!")
    
    try:
        log_func('TITLE', f"Descargando {SEVEN_ZIP_EXE_NAME}...")
        with urlopen(SEVEN_ZIP_DOWNLOAD_URL) as response:
            data = response.read()
            with open(seven_zip_exe_path, 'wb') as out_file:
                out_file.write(data)
        
        log_func('OK', f"{SEVEN_ZIP_EXE_NAME} descargado con éxito en {seven_zip_exe_path}")
        return True
            
    except Exception as e:
        log_func('ERROR', f"Fallo al descargar {SEVEN_ZIP_EXE_NAME}: {e}")
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
        log_func('WARN', "No se encontró la instalación de Steam en el registro. Usando fallback.")
    except Exception as e:
        log_func('ERROR', f"Error al buscar rutas de Steam: {e}")
    return list(paths)

def get_dynamic_epic_paths(log_func):
    """Encuentra juegos de Epic Games iterando las claves de desinstalación en el registro."""
    paths = set()
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
        log_func('WARN', "No se encontró la clave de desinstalación de Epic. Usando fallback.")
    except Exception as e:
        log_func('ERROR', f"Error al buscar rutas de Epic: {e}")
    return list(paths)

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
        
        # 2. Si no, buscar RECURSIVAMENTE con patrones glob
        log_func('INFO', f"  -> Buscando recursivamente ejecutables en: {base_game_path}")
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
                    
        # 3. Si no se encuentra nada recursivamente, comprobar la RAÍZ
        exe_name_root, size_root = get_best_exe_in_folder(base_game_path)
        if exe_name_root:
            log_func('INFO', f"  -> No se encontraron subcarpetas, usando la raíz: {base_game_path} (Exe: {exe_name_root}, {size_root//(1024*1024)}MB)")
            return base_game_path, exe_name_root
        
        # 4. Si no hay .exe en ningún lado, devolver la base como fallback
        log_func('WARN', f"  -> No se encontró .exe en {base_game_path} o subcarpetas. Usando la raíz por defecto.")
        return base_game_path, None
        
    except Exception as e:
        log_func('ERROR', f"  -> Error en búsqueda inteligente: {e}. Usando raíz: {base_game_path}")
        return base_game_path, None

def get_game_name(folder_name):
    """Limpia el nombre de la carpeta de Game Pass para obtener un nombre legible."""
    name_parts = folder_name.split(' - ')
    if len(name_parts) > 1 and len(name_parts[0]) > 0:
        return name_parts[0]
    return folder_name


def detect_gpu_vendor():
    """Detecta el fabricante de GPU principal del sistema.
    
    Returns:
        str: 'nvidia', 'amd', 'intel', o 'unknown'
    """
    if platform.system() != "Windows":
        return 'unknown'
    
    try:
        # Buscar en el registro de Windows
        gpu_key_path = r"SYSTEM\CurrentControlSet\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}"
        
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, gpu_key_path) as key:
            i = 0
            gpus_found = []
            
            while True:
                try:
                    subkey_name = winreg.EnumKey(key, i)
                    subkey_path = f"{gpu_key_path}\\{subkey_name}"
                    
                    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, subkey_path) as subkey:
                        try:
                            # Leer descripción de la GPU
                            desc = str(winreg.QueryValueEx(subkey, "DriverDesc")[0]).lower()
                            
                            # Clasificar por vendor
                            if 'nvidia' in desc or 'geforce' in desc or 'rtx' in desc or 'gtx' in desc:
                                gpus_found.append(('nvidia', desc))
                            elif 'amd' in desc or 'radeon' in desc:
                                gpus_found.append(('amd', desc))
                            elif 'intel' in desc or 'arc' in desc:
                                gpus_found.append(('intel', desc))
                        except:
                            pass
                    i += 1
                except OSError:
                    break
            
            # Priorizar: NVIDIA > AMD > Intel
            # (Porque si tiene NVIDIA, probablemente quiere usar DLSS nativo)
            for vendor, desc in gpus_found:
                if vendor == 'nvidia':
                    return 'nvidia'
            for vendor, desc in gpus_found:
                if vendor == 'amd':
                    return 'amd'
            for vendor, desc in gpus_found:
                if vendor == 'intel':
                    return 'intel'
                    
    except Exception:
        pass
    
    return 'unknown'


def should_use_dual_mod(gpu_vendor=None):
    """Determina si debe usar dual-mod (OptiScaler + dlssg-to-fsr3).
    
    Args:
        gpu_vendor: Vendor de GPU ('nvidia', 'amd', 'intel', 'unknown').
                   Si es None, se detecta automáticamente.
    
    Returns:
        bool: True si debe usar dual-mod (AMD/Intel), False si solo OptiScaler (NVIDIA)
    """
    if gpu_vendor is None:
        gpu_vendor = detect_gpu_vendor()
    
    # AMD e Intel necesitan dlssg-to-fsr3 para frame generation
    return gpu_vendor in ('amd', 'intel', 'unknown')