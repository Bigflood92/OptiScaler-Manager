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

from ..config.paths import (
    STEAM_COMMON_DIR, EPIC_COMMON_DIR, XBOX_GAMES_DIR,
    RECURSIVE_EXE_PATTERNS, COMMON_EXE_SUBFOLDERS_DIRECT
)
from .settings import EXE_BLACKLIST_KEYWORDS
from ..config.constants import MOD_CHECK_FILES
from ..config.settings import SPOOFING_DLL_NAMES


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
    try:
        # 1. Direct subfolders
        for subfolder in COMMON_EXE_SUBFOLDERS_DIRECT:
            potential_path = os.path.normpath(os.path.join(base_game_path, subfolder))
            if os.path.isdir(potential_path):
                exe_name, size = get_best_exe_in_folder(potential_path, log_func)
                if exe_name:
                    log_func('INFO', f"  -> Ruta inteligente (directa) encontrada: {potential_path} (Exe: {exe_name}, {size//(1024*1024)}MB)")
                    return potential_path, exe_name

        # 2. Recursive patterns
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
    if not os.path.isdir(game_target_dir):
        return "ERROR: Carpeta no válida"
    for dll_name in SPOOFING_DLL_NAMES:
        if os.path.exists(os.path.join(game_target_dir, dll_name)):
            try:
                size_mb = os.path.getsize(os.path.join(game_target_dir, dll_name)) / (1024*1024)
                if size_mb > 0.5:
                    return f"✅ INSTALADO (usando {dll_name})"
            except Exception:
                return f"✅ INSTALADO (usando {dll_name})"
    if any(os.path.exists(os.path.join(game_target_dir, f)) for f in MOD_CHECK_FILES):
        return "✅ INSTALADO (OptiScaler.dll)"
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


def scan_games(log_func, custom_folders=None):
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
    return all_games
