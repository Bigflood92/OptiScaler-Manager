"""Installer and mod management functions extracted from the monolith.

Contains functions to check mod source, extract archives, copy files,
configure INI and perform install/uninstall operations.
"""
import os
import sys
import shutil
import subprocess
import platform
import urllib.request
import configparser

from typing import Tuple

from ..config.constants import (
    MOD_SOURCE_DIR, SEVEN_ZIP_EXE_NAME, SEVEN_ZIP_DOWNLOAD_URL,
    TARGET_MOD_FILES, TARGET_MOD_DIRS, GENERIC_SPOOF_FILES, MOD_CHECK_FILES,
    GITHUB_API_URL
)
from ..config.settings import (
    FG_MODE_MAP, UPSCALE_MODE_MAP, UPSCALER_MAP
)

try:
    import requests
    REQUESTS_AVAILABLE = True
except Exception:
    REQUESTS_AVAILABLE = False


def get_script_base_path() -> str:
    try:
        if getattr(sys, 'frozen', False):
            return os.path.dirname(sys.executable)
        else:
            return os.path.dirname(__file__)
    except Exception:
        return os.path.abspath('.')


def check_and_download_7zip(log_func, master_widget=None) -> bool:
    base_path = get_script_base_path()
    seven_zip_exe_path = os.path.join(base_path, SEVEN_ZIP_EXE_NAME)
    if os.path.exists(seven_zip_exe_path):
        log_func('INFO', f"{SEVEN_ZIP_EXE_NAME} encontrado. Extracción habilitada.")
        return True

    log_func('ERROR', f"¡No se encontró {SEVEN_ZIP_EXE_NAME}!")
    try:
        with urllib.request.urlopen(SEVEN_ZIP_DOWNLOAD_URL) as response, open(seven_zip_exe_path, 'wb') as out_file:
            out_file.write(response.read())
        log_func('OK', f"{SEVEN_ZIP_EXE_NAME} descargado con éxito en {seven_zip_exe_path}")
        return True
    except Exception as e:
        log_func('ERROR', f"Fallo al descargar {SEVEN_ZIP_EXE_NAME}: {e}")
        return False


def check_mod_source_files(mod_source_dir: str, log_func) -> Tuple[str, bool]:
    target_files_check = ['dlssg_to_fsr3_amd_is_better.dll', 'OptiScaler.dll']
    source_dir = mod_source_dir
    dll_found = False
    if not source_dir or not os.path.isdir(source_dir):
        if not os.path.isdir(MOD_SOURCE_DIR):
            log_func('ERROR', "La carpeta de origen del Mod no está seleccionada.")
            return None, False
        log_func('WARN', "Usando la carpeta de auto-descarga. Buscando la última versión...")
        subdirs = sorted([d for d in os.listdir(MOD_SOURCE_DIR) if os.path.isdir(os.path.join(MOD_SOURCE_DIR, d))], reverse=True)
        if not subdirs:
            log_func('ERROR', "La carpeta 'mod_source' está vacía. Por favor, descargue el mod.")
            return None, False
        source_dir = os.path.join(MOD_SOURCE_DIR, subdirs[0])
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
        log_func('ERROR', "La carpeta de origen NO contiene los archivos clave del mod. Asegúrese de haber EXTRAÍDO la carpeta.")
        return None, False
    log_func('INFO', f"Archivos clave del Mod encontrados en: {source_dir}")
    return source_dir, True


def extract_mod_archive(archive_path: str, extract_path: str, log_func) -> bool:
    base_path = get_script_base_path()
    seven_zip_exe = os.path.join(base_path, SEVEN_ZIP_EXE_NAME)
    if not os.path.exists(seven_zip_exe):
        log_func('ERROR', f"¡No se encontró {SEVEN_ZIP_EXE_NAME}!")
        return False
    try:
        if os.path.isdir(extract_path):
            shutil.rmtree(extract_path)
        command = [seven_zip_exe, 'x', archive_path, f'-o{extract_path}', '-y']
        startupinfo = None
        if platform.system() == "Windows":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
        result = subprocess.run(command, capture_output=True, text=True, startupinfo=startupinfo, encoding='latin-1')
        if result.returncode != 0:
            log_func('ERROR', f"{SEVEN_ZIP_EXE_NAME} falló con el código {result.returncode}")
            log_func('ERROR', f"Detalle: {result.stderr}")
            return False
        log_func('OK', f"Extracción con {SEVEN_ZIP_EXE_NAME} completada.")
        subfolders = [d for d in os.listdir(extract_path) if os.path.isdir(os.path.join(extract_path, d))]
        if len(subfolders) == 1:
            subfolder_path = os.path.join(extract_path, subfolders[0])
            if any(f in os.listdir(subfolder_path) for f in MOD_CHECK_FILES):
                log_func('WARN', "Mod detectado en subcarpeta, moviendo archivos...")
                for item in os.listdir(subfolder_path):
                    shutil.move(os.path.join(subfolder_path, item), extract_path)
                shutil.rmtree(subfolder_path)
        return True
    except Exception as e:
        log_func('ERROR', f"Fallo al ejecutar {SEVEN_ZIP_EXE_NAME}: {e}")
        return False


def configure_and_rename_dll(target_dir: str, spoof_dll_name: str, log_func) -> bool:
    original_dll = os.path.join(target_dir, 'OptiScaler.dll')
    selected_filename = spoof_dll_name
    if not selected_filename:
        log_func('ERROR', "Nombre de DLL de inyección no válido.")
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
            log_func('ERROR', f"OptiScaler.dll no fue copiado al destino y {selected_filename} no existe. Fallo crítico.")
            return False
    try:
        os.rename(original_dll, new_dll_path)
        log_func('INFO', f"OptiScaler.dll renombrado a {selected_filename}.")
        return True
    except Exception as e:
        log_func('ERROR', f"Fallo al renombrar DLL: {e}. ¿Está el juego abierto?")
        if 'backup_path' in locals() and os.path.exists(backup_path):
            try:
                if os.path.exists(new_dll_path): os.remove(new_dll_path)
                os.rename(backup_path, new_dll_path)
                log_func('INFO', f"Backup {os.path.basename(backup_path)} restaurado.")
            except Exception as e_restore:
                 log_func('ERROR', f"Fallo al restaurar backup: {e_restore}")
        return False


def update_optiscaler_ini(target_dir: str, gpu_choice: int, fg_mode_selected: str, upscaler_selected: str, upscale_mode_selected: str, sharpness_selected: float, overlay_selected: bool, mb_selected: bool, log_func) -> bool:
    ini_path = os.path.join(target_dir, 'OptiScaler.ini')
    if not os.path.exists(ini_path):
        log_func('WARN', "OptiScaler.ini no encontrado en el destino. No se pueden aplicar configuraciones.")
        return False
    try:
        config = configparser.ConfigParser(comment_prefixes=';', allow_no_value=True)
        from io import StringIO
        with open(ini_path, 'r', encoding='utf-8') as f:
            ini_content = f.read()
        stringio_content = StringIO(ini_content)
        config.read_file(stringio_content)
        changes_made = False
        dxgi_value = 'true' if gpu_choice == 1 else 'auto'
        if not config.has_section('Dxgi'): config.add_section('Dxgi')
        if config.get('Dxgi', 'Dxgi', fallback='auto') != dxgi_value:
            config.set('Dxgi', 'Dxgi', dxgi_value)
            log_func('INFO', f"OptiScaler.ini: [Dxgi] Dxgi cambiado a '{dxgi_value}'.")
            changes_made = True
        fg_mode_ini_value = fg_mode_selected
        if not config.has_section('FrameGeneration'): config.add_section('FrameGeneration')
        if config.get('FrameGeneration', 'Mode', fallback='auto') != fg_mode_ini_value:
             config.set('FrameGeneration', 'Mode', fg_mode_ini_value)
             log_func('INFO', f"OptiScaler.ini: [FrameGeneration] Mode cambiado a '{fg_mode_ini_value}'.")
             changes_made = True
        # Upscaler Backend
        upscaler_ini_value = upscaler_selected
        if not config.has_section('Upscaler'): config.add_section('Upscaler')
        if config.get('Upscaler', 'Backend', fallback='auto') != upscaler_ini_value:
            config.set('Upscaler', 'Backend', upscaler_ini_value)
            log_func('INFO', f"OptiScaler.ini: [Upscaler] Backend cambiado a '{upscaler_ini_value}'.")
            changes_made = True
        upscale_mode_ini_value = upscale_mode_selected
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
        overlay_ini_value = "basic" if overlay_selected else "off"
        if not config.has_section('Overlay'): config.add_section('Overlay')
        if config.get('Overlay', 'Mode', fallback='off') != overlay_ini_value:
            config.set('Overlay', 'Mode', overlay_ini_value)
            log_func('INFO', f"OptiScaler.ini: [Overlay] Mode cambiado a '{overlay_ini_value}'.")
            changes_made = True
        mb_ini_value = "true" if mb_selected else "false"
        if not config.has_section('MotionBlur'): config.add_section('MotionBlur')
        if config.get('MotionBlur', 'Disable', fallback='false') != mb_ini_value:
            config.set('MotionBlur', 'Disable', mb_ini_value)
            log_func('INFO', f"OptiScaler.ini: [MotionBlur] Disable cambiado a '{mb_ini_value}'.")
            changes_made = True
        if changes_made:
             with open(ini_path, 'w', encoding='utf-8') as f:
                 config.write(f, space_around_delimiters=False)
             log_func('OK', "OptiScaler.ini actualizado con éxito.")
        return True
    except configparser.Error as e:
         log_func('ERROR', f"Error al parsear OptiScaler.ini: {e}")
         return False
    except Exception as e:
        log_func('ERROR', f"Error al actualizar OptiScaler.ini: {e}")
        return False


def read_optiscaler_ini(target_dir: str, log_func):
    ini_path = os.path.join(target_dir, 'OptiScaler.ini')
    defaults = {
        "gpu_choice": 2,
        "fg_mode": "Automático",
        "upscale_mode": "Automático",
        "sharpness": 0.8,
        "overlay": False,
        "motion_blur": True
    }
    if not os.path.exists(ini_path):
        log_func('WARN', f"No se encontró OptiScaler.ini en {target_dir}. Devolviendo valores por defecto.")
        return defaults
    try:
        config = configparser.ConfigParser(comment_prefixes=';', allow_no_value=True)
        config.read(ini_path)
        dxgi_value = config.get('Dxgi', 'Dxgi', fallback='auto')
        gpu_choice = 1 if dxgi_value == 'true' else 2
        fg_mode_ini = config.get('FrameGeneration', 'Mode', fallback='auto')
        upscaler_ini = config.get('Upscaler', 'Backend', fallback='auto')
        upscale_mode_ini = config.get('Upscale', 'Mode', fallback='auto')
        sharpness = config.getfloat('Upscale', 'Sharpness', fallback=0.8)
        overlay_ini = config.get('Overlay', 'Mode', fallback='off')
        overlay = (overlay_ini != 'off')
        mb_ini = config.get('MotionBlur', 'Disable', fallback='false')
        motion_blur = (mb_ini == 'true')
        log_func('INFO', f"Lectura de {ini_path} exitosa.")
        return {
            "gpu_choice": gpu_choice,
            "fg_mode": fg_mode_ini,
            "upscaler": upscaler_ini,
            "upscale_mode": upscale_mode_ini,
            "sharpness": sharpness,
            "overlay": overlay,
            "motion_blur": motion_blur
        }
    except Exception as e:
        log_func('ERROR', f"Error al leer OptiScaler.ini: {e}. Devolviendo valores por defecto.")
        return defaults


def inject_fsr_mod(mod_source_dir: str, target_dir: str, log_func, spoof_dll_name: str = "dxgi.dll", gpu_choice: int = 2, fg_mode_selected: str = "Automático",
                   upscaler_selected: str = "Automático", upscale_mode_selected: str = "Automático", sharpness_selected: float = 0.8, overlay_selected: bool = False, mb_selected: bool = True) -> bool:
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
                        log_func('ERROR', f"No se pudo crear backup de {item_name}: {e}. Se intentará sobrescribir.")
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
        # Map UI strings to INI codes
        fg_code = FG_MODE_MAP.get(fg_mode_selected, 'auto')
        upscaler_code = UPSCALER_MAP.get(upscaler_selected, 'auto')
        upscale_code = UPSCALE_MODE_MAP.get(upscale_mode_selected, 'auto')
        if not update_optiscaler_ini(target_dir, gpu_choice, fg_code, upscaler_code, upscale_code, sharpness_selected, overlay_selected, mb_selected, log_func):
            log_func('ERROR', "Fallo al configurar OptiScaler.ini. La inyección puede no funcionar como se espera.")
        setup_bat_path = os.path.join(target_dir, 'setup_windows.bat')
        if os.path.exists(setup_bat_path): os.remove(setup_bat_path)
        reg_files = [f for f in os.listdir(target_dir) if f.lower().endswith('.reg')]
        if reg_files:
            log_func('WARN', '-------------------------------------------------------')
            log_func('WARN', f"¡ACCIÓN MANUAL! Ejecute el archivo REG que DESHABILITA la firma ({reg_files[0]}) si el juego falla al iniciar.")
            log_func('WARN', '-------------------------------------------------------')
        spoof_name = spoof_dll_name
        log_func('INFO', "-------------------------------------------------------")
        log_func('INFO', "VERIFICACIÓN MANUAL REQUERIDA:")
        log_func('INFO', f"1. DLL RENOMBRADO: Compruebe la existencia de '{spoof_name}'.")
        log_func('INFO', f"2. CONFIG. INI: Compruebe OptiScaler.ini para Dxgi, FrameGeneration, etc.")
        log_func('INFO', "-------------------------------------------------------")
        log_func('OK', f"Inyección completa y configurada. Total de archivos copiados: {copied_files}")
        return True
    except PermissionError:
        log_func('ERROR', "ACCESO DENEGADO. Asegúrese de que el juego o su launcher están CERRADOS.")
        return False
    except Exception as e:
        log_func('ERROR', f"Ocurrió un error desconocido al inyectar: {e}")
        return False


def restore_original_dll(target_dir: str, log_func) -> bool:
    if not target_dir or not os.path.isdir(target_dir):
        log_func('ERROR', "La Carpeta de Destino del Juego no es válida.")
        return False
    restored_count = 0
    try:
        for filename in os.listdir(target_dir):
            if filename.lower().endswith('.bak'):
                original_name = filename[:-4]
                if original_name in GENERIC_SPOOF_FILES:
                    bak_path = os.path.join(target_dir, filename)
                    original_path = os.path.join(target_dir, original_name)
                    try:
                        if os.path.exists(original_path):
                            os.remove(original_path)
                            log_func('INFO', f"Restaurando .bak: Se eliminó el DLL activo '{original_name}'.")
                        os.rename(bak_path, original_path)
                        log_func('OK', f"¡ÉXITO! Se restauró '{original_name}' desde '{filename}'.")
                        restored_count += 1
                    except PermissionError:
                         log_func('ERROR', f"Fallo al restaurar {filename}. ¿Está el juego abierto?")
                    except Exception as e_restore:
                         log_func('ERROR', f"Error al restaurar {filename}: {e_restore}")
        if restored_count > 0:
            log_func('OK', f"Restauración de {restored_count} archivo(s) .bak completada.")
            return True
        else:
            log_func('WARN', "No se encontraron archivos .bak relevantes (ej. dxgi.dll.bak) para restaurar.")
            return False
    except Exception as e:
        log_func('ERROR', f"Error durante la búsqueda de backups: {e}")
        return False


def uninstall_fsr_mod(target_dir: str, log_func):
    if not target_dir or not os.path.isdir(target_dir):
        log_func('ERROR', "La Carpeta de Destino del Juego no es válida.")
        return False, []
    files_to_try_to_remove = set(TARGET_MOD_FILES + GENERIC_SPOOF_FILES + ['nvngx.dll', 'libxess_fg.dll', 'libxell.dll', 'fakenvapi.dll', 'fakenvapi.ini'])
    dirs_to_remove = TARGET_MOD_DIRS
    found_backups = []
    log_func('WARN', f"Intentando ELIMINAR OptiScaler y archivos relacionados de: {target_dir}")
    try:
        removed_files = 0
        removed_dirs = 0
        for filename in files_to_try_to_remove:
            if filename.lower().endswith('.bak'): continue
            file_path = os.path.join(target_dir, filename)
            if os.path.exists(file_path) and os.path.isfile(file_path):
                try:
                    os.remove(file_path)
                    removed_files += 1
                    log_func('INFO', f"  -> Eliminado archivo específico: {filename}")
                except PermissionError:
                     log_func('ERROR', f"Fallo al eliminar {filename}. ¿Está el juego abierto?")
                except Exception as e_rem:
                     log_func('ERROR', f"Error al eliminar {filename}: {e_rem}")
        for dirname in dirs_to_remove:
            dir_path = os.path.join(target_dir, dirname)
            if os.path.isdir(dir_path):
                try:
                    shutil.rmtree(dir_path)
                    removed_dirs += 1
                    log_func('INFO', f"  -> Eliminada carpeta recursiva: {dirname}")
                except PermissionError:
                     log_func('ERROR', f"Fallo al eliminar carpeta {dirname}. ¿Hay archivos en uso?")
                except Exception as e_rem_dir:
                     log_func('ERROR', f"Error al eliminar carpeta {dirname}: {e_rem_dir}")
        current_files = os.listdir(target_dir)
        for filename in current_files:
            file_path = os.path.join(target_dir, filename)
            if not os.path.isfile(file_path):
                continue
            if filename.lower().endswith('.bak'):
                original_name = filename[:-4]
                if original_name in GENERIC_SPOOF_FILES or original_name == 'OptiScaler.dll':
                    found_backups.append((file_path, original_name))
                    log_func('INFO', f"  -> Encontrado archivo backup: {filename}")
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
        log_func('ERROR', f"FALLO AL ACCEDER A LA CARPETA DURANTE LA DESINSTALACIÓN. ¿JUEGO CERRADO? Detalle: {e}")
        return False, []
    except Exception as e:
        log_func('ERROR', f"Ocurrió un error desconocido al eliminar archivos: {e}.")
        return False, []


def clean_logs(game_folders, log_func):
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
    cleaned_count = 0
    for game_path, _, mod_status, _, _ in all_games_data:
        if "AUSENTE" in mod_status:
            try:
                for filename in os.listdir(game_path):
                    if filename.lower().endswith('.bak'):
                        original_name = filename[:-4]
                        if original_name in GENERIC_SPOOF_FILES or original_name == 'OptiScaler.dll':
                            bak_path = os.path.join(game_path, filename)
                            os.remove(bak_path)
                            log_func('INFO', f"Backup huérfano '{filename}' eliminado de: {os.path.basename(game_path)}")
                            cleaned_count += 1
            except Exception as e:
                log_func('ERROR', f"No se pudo limpiar backups de {os.path.basename(game_path)}: {e}")
    log_func('OK', f"Limpieza de {cleaned_count} backups huérfanos completada.")
    return cleaned_count


def fetch_github_releases(log_func):
    if not REQUESTS_AVAILABLE:
        log_func('ERROR', "'requests' no está instalado. No se pueden buscar versiones.")
        return None
    try:

        log_func('INFO', "Buscando versiones del mod en GitHub...")
        response = requests.get(GITHUB_API_URL, timeout=10)
        response.raise_for_status()
        releases = response.json()
        log_func('INFO', f"Se encontraron {len(releases)} versiones.")
        return releases
    except Exception as e:
        log_func('ERROR', f"Error al buscar versiones en GitHub: {e}")
        return None


def download_mod_release(release_info, progress_callback, log_func):
    try:
        if not REQUESTS_AVAILABLE:
             log_func('ERROR', "Faltan 'requests'. Abortando descarga.")
             progress_callback(0, 0, True, "Error: Faltan dependencias.")
             return
        asset = next((a for a in release_info['assets'] if a['name'].endswith('.7z')), None)
        if not asset:
            log_func('ERROR', "Esta release no tiene un archivo .7z")
            progress_callback(0, 0, True, "Error: No se encontró .7z")
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
        extract_path = os.path.join(MOD_SOURCE_DIR, file_name.replace('.7z', ''))
        if extract_mod_archive(download_path, extract_path, log_func):
            log_func('OK', f"Extracción completada en: {extract_path}")
            try: os.remove(download_path)
            except Exception: pass
            progress_callback(total_size, total_size, True, f"¡Completado! Listo para usar: {file_name.replace('.7z', '')}")
        else:
            raise Exception("Fallo en la extracción. Revise el log.")
    except Exception as e:
        log_func('ERROR', f"Fallo en la descarga/extracción: {e}")
        progress_callback(0, 0, True, f"Error: {e}")
