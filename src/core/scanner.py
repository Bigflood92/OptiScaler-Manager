"""Game scanning helpers extracted from the monolithic script.

Functions:
- get_dynamic_steam_paths
- get_dynamic_epic_paths
- find_executable_path
- get_game_name
- check_mod_status
- scan_games
- check_registry_override

These use constants from src.config.
"""
from typing import List, Tuple
import os
import glob
import re
import platform
import winreg
from functools import lru_cache
from threading import Lock

from ..config.paths import (
    STEAM_COMMON_DIR, EPIC_COMMON_DIR, XBOX_GAMES_DIR,
    RECURSIVE_EXE_PATTERNS, COMMON_EXE_SUBFOLDERS_DIRECT
)
from .settings import EXE_BLACKLIST_KEYWORDS
from ..config.constants import MOD_CHECK_FILES, MOD_CHECK_FILES_OPTISCALER, MOD_CHECK_FILES_NUKEM
from ..config.settings import SPOOFING_DLL_NAMES

# Cache simple para scan_games
_scan_cache = None
_scan_cache_lock = Lock()


def invalidate_scan_cache():
    """Invalida el cache de scan_games para forzar un nuevo escaneo."""
    global _scan_cache
    with _scan_cache_lock:
        _scan_cache = None


def get_dynamic_steam_paths(log_func) -> List[str]:
    paths = {str(STEAM_COMMON_DIR)}
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


def get_dynamic_epic_paths(log_func) -> List[str]:
    paths = {str(EPIC_COMMON_DIR)}
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


def get_best_exe_in_folder(folder_path: str, log_func) -> Tuple[str, int]:
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

    if good_candidates:
        good_candidates.sort(key=lambda x: x[1], reverse=True)
        best_exe_path, best_size = good_candidates[0]
        return os.path.basename(best_exe_path), best_size
    if bad_candidates:
        bad_candidates.sort(key=lambda x: x[1], reverse=True)
        best_bad_exe_path, best_bad_size = bad_candidates[0]
        log_func('WARN', f"  -> No se encontraron .exes 'buenos', usando el mejor de la lista negra: {os.path.basename(best_bad_exe_path)}")
        return os.path.basename(best_bad_exe_path), best_bad_size
    return None, 0


def find_executable_path(base_game_path: str, log_func) -> Tuple[str, str]:
    """
    OPTIMIZACIÓN: Limita profundidad de búsqueda para evitar timeouts en juegos grandes (Forza, COD).
    Estrategia:
    1. Subcarpetas conocidas (bin/, binaries/, etc)
    2. Búsqueda recursiva limitada a 4 niveles de profundidad
    3. Root folder como último recurso
    """
    try:
        # 1. Direct subfolders
        for subfolder in COMMON_EXE_SUBFOLDERS_DIRECT:
            potential_path = os.path.normpath(os.path.join(base_game_path, subfolder))
            if os.path.isdir(potential_path):
                exe_name, size = get_best_exe_in_folder(potential_path, log_func)
                if exe_name:
                    log_func('INFO', f"  -> Ruta inteligente (directa) encontrada: {potential_path} (Exe: {exe_name}, {size//(1024*1024)}MB)")
                    return potential_path, exe_name

        # 2. BUGFIX: Búsqueda inteligente con profundidad limitada (4 niveles)
        log_func('INFO', f"  -> Buscando recursivamente ejecutables en: {base_game_path}")
        
        # Patrones conocidos de ejecutables de juego (mayor prioridad)
        GAME_EXE_PATTERNS = [
            '*-WinGDK-Shipping.exe',   # Unreal Engine Xbox/Windows Store
            '*-Win64-Shipping.exe',    # Unreal Engine PC
            '*-Win64.exe',             # Unreal Engine variants
            '*Game.exe',               # Patrones comunes de juego
            '*Main.exe',
            '*.exe'                    # Genérico (último recurso)
        ]
        
        best_recursive_exe = None
        best_recursive_size = 0
        best_recursive_dir = None
        best_pattern_priority = 999  # Menor = mejor prioridad
        
        MAX_DEPTH = 4  # OPTIMIZACIÓN: Limitar recursión para evitar timeout en juegos masivos
        
        def limited_glob(base_path: str, pattern: str, max_depth: int):
            """Búsqueda recursiva con profundidad limitada."""
            results = []
            base_depth = base_path.count(os.sep)
            
            for root, dirs, files in os.walk(base_path):
                current_depth = root.count(os.sep) - base_depth
                if current_depth > max_depth:
                    dirs[:] = []  # No bajar más niveles
                    continue
                    
                # Buscar archivos que coincidan con el patrón
                for file in files:
                    if file.lower().endswith('.exe'):
                        # Aplicar patrón (simple matching)
                        pattern_clean = pattern.replace('*', '').replace('.exe', '')
                        if not pattern_clean or pattern_clean.lower() in file.lower():
                            results.append(os.path.join(root, file))
            return results
        
        for priority, pattern in enumerate(GAME_EXE_PATTERNS):
            found_exes_paths = limited_glob(base_game_path, pattern, MAX_DEPTH)
            
            for exe_path in found_exes_paths:
                exe_name_lower = os.path.basename(exe_path).lower()
                is_blacklisted = any(keyword in exe_name_lower for keyword in EXE_BLACKLIST_KEYWORDS)
                if is_blacklisted:
                    continue
                    
                try:
                    size = os.path.getsize(exe_path)
                    # Priorizar por patrón, luego por tamaño
                    if priority < best_pattern_priority or (priority == best_pattern_priority and size > best_recursive_size):
                        best_pattern_priority = priority
                        best_recursive_size = size
                        best_recursive_exe = os.path.basename(exe_path)
                        best_recursive_dir = os.path.dirname(exe_path)
                except Exception:
                    pass

        if best_recursive_exe:
            log_func('INFO', f"  -> Ruta inteligente (recursiva) encontrada: {best_recursive_dir} (Exe: {best_recursive_exe}, {best_recursive_size//(1024*1024)}MB)")
            return best_recursive_dir, best_recursive_exe

        # 3. Root folder
        exe_name_root, size_root = get_best_exe_in_folder(base_game_path, log_func)
        if exe_name_root:
            log_func('INFO', f"  -> No se encontraron subcarpetas, usando la raíz: {base_game_path} (Exe: {exe_name_root}, {size_root//(1024*1024)}MB)")
            return base_game_path, exe_name_root

        log_func('WARN', f"  -> No se encontró .exe en {base_game_path} o subcarpetas. Usando la raíz por defecto.")
        return base_game_path, None
    except Exception as e:
        log_func('ERROR', f"  -> Error en búsqueda inteligente: {e}. Usando raíz: {base_game_path}")
        return base_game_path, None


def get_game_name(folder_name: str) -> str:
    name_parts = folder_name.split(' - ')
    if len(name_parts) > 1 and len(name_parts[0]) > 0:
        return name_parts[0]
    return folder_name


def check_mod_status(game_target_dir: str) -> str:
    """Verifica el estado de instalación de los mods.
    
    Detecta:
    - OptiScaler (upscaling): OptiScaler.dll o dlls de spoofing
    - dlssg-to-fsr3 (frame generation): dlssg_to_fsr3_amd_is_better.dll
    
    Args:
        game_target_dir: Directorio del juego a verificar
        
    Returns:
        str: Estado de instalación con emojis
    """
    if not os.path.isdir(game_target_dir):
        return "ERROR: Carpeta no válida"
        
    # Detectar OptiScaler instalado
    optiscaler_installed = False
    for dll_name in SPOOFING_DLL_NAMES:
        dll_path = os.path.join(game_target_dir, dll_name)
        if os.path.exists(dll_path):
            try:
                size_mb = os.path.getsize(dll_path) / (1024*1024)
                if size_mb > 0.5:  # OptiScaler renombrado es >1MB
                    optiscaler_installed = True
                    break
            except Exception:
                optiscaler_installed = True
                break
                
    if not optiscaler_installed:
        # Verificar OptiScaler.dll directamente
        if any(os.path.exists(os.path.join(game_target_dir, f)) for f in MOD_CHECK_FILES_OPTISCALER):
            optiscaler_installed = True
            
    # Detectar dlssg-to-fsr3 instalado
    nukem_installed = any(
        os.path.exists(os.path.join(game_target_dir, f)) 
        for f in MOD_CHECK_FILES_NUKEM
    )
    
    # Retornar estado combinado
    if optiscaler_installed and nukem_installed:
        return "✅ COMPLETO (Upscaling + FG)"
    elif optiscaler_installed:
        return "✅ OptiScaler (Upscaling)"
    elif nukem_installed:
        return "⚠️ Solo Frame Generation"
    else:
        return "❌ AUSENTE"


def check_registry_override(log_func) -> bool:
    if platform.system() != "Windows":
        return True
    try:
        key_path = r"SOFTWARE\NVIDIA Corporation\Global\NVAPI\Render\Software\NVAPI"
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_READ)
        value, _ = winreg.QueryValueEx(key, "DisableSignatureChecks")
        winreg.CloseKey(key)

        if value == 1:
            log_func('INFO', "VERIFICACIÓN REGISTRO: ✅ Firma de DLSS deshabilitada (OK).")
            return True
        else:
            log_func('WARN', "VERIFICACIÓN REGISTRO: ❌ Comprobación de firma ACTIVA (Valor = 0).")
            log_func('WARN', "¡MOD BLOQUEADO! Ejecute el archivo 'DISABLE...' REG si el mod no funciona.")
            return False
    except FileNotFoundError:
        log_func('WARN', "VERIFICACIÓN REGISTRO: ❌ Clave de 'DisableSignatureChecks' NO encontrada.")
        log_func('WARN', "¡MOD BLOQUEADO! Ejecute el archivo 'DISABLE...' REG si el mod no funciona.")
        return False
    except Exception as e:
        log_func('ERROR', f"VERIFICACIÓN REGISTRO: Fallo al leer el Registro: {e}")
        return False


def scan_games(log_func, custom_folders=None, use_cache=True):
    """
    Escanea juegos en Steam, Epic, Xbox y carpetas personalizadas.
    
    Args:
        log_func: Función para logging
        custom_folders: Carpetas adicionales a escanear
        use_cache: Si True, devuelve resultado cacheado si existe (útil para evitar rescans costosos)
    
    Returns:
        Lista de tuplas (path, name, status, exe_name, platform_tag)
    """
    global _scan_cache
    
    # Si hay cache válido y se permite usarlo, devolver cache
    if use_cache and _scan_cache is not None:
        log_func('INFO', "Usando caché de juegos escaneados")
        return _scan_cache
    
    if custom_folders is None:
        custom_folders = []
    all_games = []
    processed_paths = set()

    def add_game_entry(path, name, status, exe_name, platform_tag):
        all_games.append((path, name, status, exe_name, platform_tag))

    # XBOX
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
                    if not exe_name:
                        log_func('WARN', f"  -> Omitiendo {folder_name}: No se encontró .exe válido.")
                        continue
                    if final_injection_path in processed_paths: continue
                    processed_paths.add(final_injection_path)
                    mod_status = check_mod_status(final_injection_path)
                    clean_name = get_game_name(folder_name)
                    add_game_entry(final_injection_path, f"[XBOX] {clean_name}", mod_status, exe_name, "Xbox")
        except Exception as e:
            log_func('ERROR', f"Error al escanear {XBOX_GAMES_DIR}: {e}")

    # STEAM
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
                        if not exe_name:
                            log_func('WARN', f"  -> Omitiendo {folder_name}: No se encontró .exe válido.")
                            continue
                        if final_injection_path in processed_paths: continue
                        processed_paths.add(final_injection_path)
                        mod_status = check_mod_status(final_injection_path)
                        add_game_entry(final_injection_path, f"[STEAM] {folder_name}", mod_status, exe_name, "Steam")
            except Exception as e:
                log_func('ERROR', f"Error al escanear {base_dir}: {e}")

    # EPIC
    epic_dirs = get_dynamic_epic_paths(log_func)
    for game_path in epic_dirs:
         game_path = os.path.normpath(game_path)
         if os.path.exists(game_path):
             final_injection_path, exe_name = find_executable_path(game_path, log_func)
             if not exe_name:
                log_func('WARN', f"  -> Omitiendo {os.path.basename(game_path)}: No se encontró .exe válido.")
                continue
             if final_injection_path in processed_paths: continue
             processed_paths.add(final_injection_path)
             folder_name = os.path.basename(game_path)
             mod_status = check_mod_status(final_injection_path)
             add_game_entry(final_injection_path, f"[EPIC] {folder_name}", mod_status, exe_name, "Epic")

    # CUSTOM
    for base_dir in custom_folders:
        base_dir = os.path.normpath(base_dir)
        if os.path.exists(base_dir):
            log_func('INFO', f"Escaneando Carpeta Personalizada: {base_dir}")
            try:
                for folder_name in os.listdir(base_dir):
                    game_path = os.path.normpath(os.path.join(base_dir, folder_name))
                    if os.path.isdir(game_path) and not folder_name.startswith('$'):
                        final_injection_path, exe_name = find_executable_path(game_path, log_func)
                        if not exe_name:
                            log_func('WARN', f"  -> Omitiendo {folder_name}: No se encontró .exe válido.")
                            continue
                        if final_injection_path in processed_paths: continue
                        processed_paths.add(final_injection_path)
                        mod_status = check_mod_status(final_injection_path)
                        add_game_entry(final_injection_path, f"[CUSTOM] {folder_name}", mod_status, exe_name, "Custom")
            except Exception as e:
                log_func('ERROR', f"Error al escanear carpeta personalizada {base_dir}: {e}")

    all_games.sort(key=lambda x: x[1])
    log_func('INFO', f"Escaneo completado. {len(all_games)} juegos encontrados.")
    
    # Guardar en cache global
    with _scan_cache_lock:
        _scan_cache = all_games
    
    return all_games
