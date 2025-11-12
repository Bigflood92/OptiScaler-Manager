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
    SEVEN_ZIP_EXE_NAME, SEVEN_ZIP_DOWNLOAD_URL,
    TARGET_MOD_FILES, TARGET_MOD_DIRS, GENERIC_SPOOF_FILES, MOD_CHECK_FILES,
    GITHUB_API_URL, NUKEM_REQUIRED_FILES, NUKEM_OPTIONAL_FILES,
    MOD_CHECK_FILES_OPTISCALER, MOD_CHECK_FILES_NUKEM
)
from ..config.paths import (
    MOD_SOURCE_DIR,
    OPTISCALER_DIR,
    DLSSG_TO_FSR3_DIR,
    SEVEN_ZIP_PATH
)
from ..config.settings import (
    FG_MODE_MAP, UPSCALE_MODE_MAP, UPSCALER_MAP,
    FG_MODE_MAP_INVERSE, UPSCALE_MODE_MAP_INVERSE, UPSCALER_MAP_INVERSE
)

try:
    import requests
    REQUESTS_AVAILABLE = True
except Exception:
    REQUESTS_AVAILABLE = False


def _map_upscaler_to_api(upscaler_code, api):
    """
    Mapea un código de upscaler genérico a su equivalente válido para una API específica.
    
    Args:
        upscaler_code: Código genérico (auto, fsr31, fsr22, xess, dlss, fsr40, fsr21)
        api: 'dx11', 'dx12', o 'vulkan'
    
    Returns:
        Código válido para esa API según OptiScaler.ini
    """
    if upscaler_code in ('auto', 'dlss'):
        return upscaler_code
    
    if api == 'dx11':
        # Dx11 nativo: fsr22, fsr31, xess
        if upscaler_code in ('fsr22', 'fsr31', 'xess'):
            return upscaler_code
        elif upscaler_code == 'fsr21':
            return 'fsr21_12'  # Emular vía Dx12
        elif upscaler_code == 'fsr40':
            return 'fsr31'  # FSR4 → FSR3.1
        return 'auto'
    
    elif api == 'dx12':
        # Dx12: fsr31 cubre fsr40
        if upscaler_code == 'fsr40':
            return 'fsr31'
        elif upscaler_code in ('xess', 'fsr21', 'fsr22', 'fsr31'):
            return upscaler_code
        return 'auto'
    
    elif api == 'vulkan':
        # Vulkan: fsr21, fsr22, fsr31, xess
        if upscaler_code in ('fsr21', 'fsr22', 'fsr31', 'xess'):
            return upscaler_code
        elif upscaler_code == 'fsr40':
            return 'fsr31'
        return 'auto'
    
    return 'auto'


def get_script_base_path() -> str:
    try:
        if getattr(sys, 'frozen', False):
            return os.path.dirname(sys.executable)
        else:
            # Retornar src/ (un nivel arriba de src/core/)
            return os.path.dirname(os.path.dirname(__file__))
    except Exception:
        return os.path.abspath('.')


def check_and_download_7zip(log_func, master_widget=None) -> bool:
    # Asegurar que el directorio mod_source existe
    os.makedirs(os.path.dirname(SEVEN_ZIP_PATH), exist_ok=True)
    
    if os.path.exists(SEVEN_ZIP_PATH):
        log_func('INFO', f"{SEVEN_ZIP_EXE_NAME} encontrado en {SEVEN_ZIP_PATH}")
        return True

    log_func('ERROR', f"¡No se encontró {SEVEN_ZIP_EXE_NAME}!")
    try:
        with urllib.request.urlopen(SEVEN_ZIP_DOWNLOAD_URL) as response, open(SEVEN_ZIP_PATH, 'wb') as out_file:
            out_file.write(response.read())
        log_func('OK', f"{SEVEN_ZIP_EXE_NAME} descargado con éxito en {SEVEN_ZIP_PATH}")
        return True
    except Exception as e:
        log_func('ERROR', f"Fallo al descargar {SEVEN_ZIP_EXE_NAME}: {e}")
        return False


def check_mod_source_files(mod_source_dir: str, log_func) -> Tuple[str, bool]:
    target_files_check = ['dlssg_to_fsr3_amd_is_better.dll', 'OptiScaler.dll']
    source_dir = mod_source_dir
    dll_found = False
    if not source_dir or not os.path.isdir(source_dir):
        # Buscar en ambos directorios de mods
        for mod_dir in [OPTISCALER_DIR, DLSSG_TO_FSR3_DIR]:
            if not os.path.isdir(mod_dir):
                continue
            log_func('WARN', f"Buscando en {mod_dir}...")
            subdirs = sorted([d for d in os.listdir(mod_dir) if os.path.isdir(os.path.join(mod_dir, d))], reverse=True)
            if subdirs:
                source_dir = os.path.join(mod_dir, subdirs[0])
                log_func('INFO', f"Carpeta de Mod detectada: {source_dir}")
                break
        
        if not source_dir or not os.path.isdir(source_dir):
            log_func('ERROR', "No se encontraron mods descargados. Por favor, descargue el mod.")
            return None, False

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
    if not os.path.exists(SEVEN_ZIP_PATH):
        log_func('ERROR', f"¡No se encontró {SEVEN_ZIP_EXE_NAME} en {SEVEN_ZIP_PATH}!")
        return False
    try:
        if os.path.isdir(extract_path):
            shutil.rmtree(extract_path)
        command = [str(SEVEN_ZIP_PATH), 'x', archive_path, f'-o{extract_path}', '-y']
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
    """Actualiza OptiScaler.ini con las opciones seleccionadas.

    Ajustado para coincidir con la estructura real del INI:
      - FrameGen -> FGType
      - Upscalers -> Dx12Upscaler (por ahora; se podría extender a Dx11/Vulkan)
      - Sharpness -> sección [Sharpness] Sharpness
    Valores previos escritos en secciones inexistentes se mantienen como fallback para compatibilidad.
    """
    ini_path = os.path.join(target_dir, 'OptiScaler.ini')
    if not os.path.exists(ini_path):
        log_func('WARN', "OptiScaler.ini no encontrado en el destino. No se pueden aplicar configuraciones.")
        return False
    try:
        config = configparser.ConfigParser(comment_prefixes=';', allow_no_value=True)
        with open(ini_path, 'r', encoding='utf-8') as f:
            config.read_file(f)
        changes_made = False

        # GPU spoof (Dxgi)
        dxgi_value = 'true' if gpu_choice == 1 else 'auto'
        if not config.has_section('Spoofing'):  # Dxgi vive en [Spoofing] según INI (Dxgi=auto)
            config.add_section('Spoofing')
        if config.get('Spoofing', 'Dxgi', fallback='auto') != dxgi_value:
            config.set('Spoofing', 'Dxgi', dxgi_value)
            log_func('INFO', f"OptiScaler.ini: [Spoofing] Dxgi -> {dxgi_value}")
            changes_made = True

        # Frame Generation Type
        fg_code = fg_mode_selected  # ya viene mapeado (auto/optifg/nukems/nofg)
        if not config.has_section('FrameGen'):
            config.add_section('FrameGen')
        if config.get('FrameGen', 'FGType', fallback='auto') != fg_code:
            config.set('FrameGen', 'FGType', fg_code)
            log_func('INFO', f"OptiScaler.ini: [FrameGen] FGType -> {fg_code}")
            changes_made = True
        # OptiFG enable flag si corresponde
        if fg_code == 'optifg':
            if not config.has_section('OptiFG'):
                config.add_section('OptiFG')
            if config.get('OptiFG', 'Enabled', fallback='false') != 'true':
                config.set('OptiFG', 'Enabled', 'true')
                log_func('INFO', "OptiScaler.ini: [OptiFG] Enabled -> true")
                changes_made = True
        elif fg_code in ('nukems', 'nofg'):
            if config.has_section('OptiFG') and config.get('OptiFG', 'Enabled', fallback='false') != 'false':
                config.set('OptiFG', 'Enabled', 'false')
                log_func('INFO', "OptiScaler.ini: [OptiFG] Enabled -> false")
                changes_made = True

        # Upscaler backend (mapear a opciones válidas por API)
        upscaler_code = upscaler_selected  # codes como fsr40, fsr31, fsr22, xess, dlss
        if not config.has_section('Upscalers'):
            config.add_section('Upscalers')
        
        changed_local = False
        
        # Dx12
        dx12_code = _map_upscaler_to_api(upscaler_code, 'dx12')
        if config.get('Upscalers', 'Dx12Upscaler', fallback='auto') != dx12_code:
            config.set('Upscalers', 'Dx12Upscaler', dx12_code)
            log_func('INFO', f"OptiScaler.ini: [Upscalers] Dx12Upscaler -> {dx12_code}")
            changed_local = True
        
        # Dx11
        dx11_code = _map_upscaler_to_api(upscaler_code, 'dx11')
        if config.get('Upscalers', 'Dx11Upscaler', fallback='auto') != dx11_code:
            config.set('Upscalers', 'Dx11Upscaler', dx11_code)
            log_func('INFO', f"OptiScaler.ini: [Upscalers] Dx11Upscaler -> {dx11_code}")
            changed_local = True
        
        # Vulkan
        vulkan_code = _map_upscaler_to_api(upscaler_code, 'vulkan')
        if config.get('Upscalers', 'VulkanUpscaler', fallback='auto') != vulkan_code:
            config.set('Upscalers', 'VulkanUpscaler', vulkan_code)
            log_func('INFO', f"OptiScaler.ini: [Upscalers] VulkanUpscaler -> {vulkan_code}")
            changed_local = True
        
        if changed_local:
            changes_made = True

        # Upscale quality mode (legacy + aplicar ratios si existe sección QualityOverrides)
        upscale_code = upscale_mode_selected
        if not config.has_section('Upscale'):
            config.add_section('Upscale')
        if config.get('Upscale', 'Mode', fallback='auto') != upscale_code:
            config.set('Upscale', 'Mode', upscale_code)
            log_func('INFO', f"OptiScaler.ini: [Upscale] Mode -> {upscale_code}")
            changes_made = True

        # Opcional: ratios mapeados básicos (usar override sólo si usuario no ha personalizado INI)
        ratio_map = {
            'quality': 1.5,
            'balanced': 1.7,
            'performance': 2.0,
            'ultra_performance': 3.0
        }
        if upscale_code in ratio_map:
            if not config.has_section('QualityOverrides'):
                config.add_section('QualityOverrides')
            # Activar si no estaba
            if config.get('QualityOverrides', 'QualityRatioOverrideEnabled', fallback='false') != 'true':
                config.set('QualityOverrides', 'QualityRatioOverrideEnabled', 'true')
                log_func('INFO', 'OptiScaler.ini: [QualityOverrides] QualityRatioOverrideEnabled -> true')
                changes_made = True
            # Establecer sólo la categoría seleccionada como ratio base, mantener otras en auto
            key_map = {
                'quality': 'QualityRatioQuality',
                'balanced': 'QualityRatioBalanced',
                'performance': 'QualityRatioPerformance',
                'ultra_performance': 'QualityRatioUltraPerformance'
            }
            ratio_key = key_map[upscale_code]
            new_ratio_val = f"{ratio_map[upscale_code]:.2f}"
            if config.get('QualityOverrides', ratio_key, fallback='auto') != new_ratio_val:
                config.set('QualityOverrides', ratio_key, new_ratio_val)
                log_func('INFO', f"OptiScaler.ini: [QualityOverrides] {ratio_key} -> {new_ratio_val}")
                changes_made = True

        # Sharpness (en INI real está en [Sharpness] Sharpness)
        sharpness_str = f"{sharpness_selected:.2f}"
        if not config.has_section('Sharpness'):
            config.add_section('Sharpness')
        if config.get('Sharpness', 'Sharpness', fallback='0.30') != sharpness_str:
            config.set('Sharpness', 'Sharpness', sharpness_str)
            log_func('INFO', f"OptiScaler.ini: [Sharpness] Sharpness -> {sharpness_str}")
            changes_made = True

        # Overlay (aprox: usar [Menu] OverlayMenu=true/basic/off). Simplificamos a habilitar menú si overlay_selected
        if not config.has_section('Menu'):
            config.add_section('Menu')
        overlay_val = 'true' if overlay_selected else 'auto'
        if config.get('Menu', 'OverlayMenu', fallback='auto') != overlay_val:
            config.set('Menu', 'OverlayMenu', overlay_val)
            log_func('INFO', f"OptiScaler.ini: [Menu] OverlayMenu -> {overlay_val}")
            changes_made = True

        # Motion blur (no existe sección directa; ignoramos para no introducir claves ficticias)

        if changes_made:
            with open(ini_path, 'w', encoding='utf-8') as f:
                config.write(f, space_around_delimiters=False)
            log_func('OK', "OptiScaler.ini actualizado con éxito.")
        else:
            log_func('INFO', "OptiScaler.ini ya estaba actualizado.")
        return True
    except configparser.Error as e:
        log_func('ERROR', f"Error al parsear OptiScaler.ini: {e}")
        return False
    except Exception as e:
        log_func('ERROR', f"Error al actualizar OptiScaler.ini: {e}")
        return False


def read_optiscaler_ini(target_dir: str, log_func):
    """Lee OptiScaler.ini devolviendo valores normalizados según mappings.

    Usa las secciones reales y mantiene compatibilidad con nombres legacy.
    """
    ini_path = os.path.join(target_dir, 'OptiScaler.ini')
    defaults = {
        "gpu_choice": 2,
        "fg_mode": "Automático",
        "upscaler": "auto",
        "upscale_mode": "auto",
        "sharpness": 0.8,
        "overlay": False,
        "motion_blur": True
    }
    if not os.path.exists(ini_path):
        log_func('WARN', f"No se encontró OptiScaler.ini en {target_dir}. Usando valores por defecto.")
        return defaults
    try:
        config = configparser.ConfigParser(comment_prefixes=';', allow_no_value=True)
        config.read(ini_path)
        # GPU spoof
        dxgi_value = config.get('Spoofing', 'Dxgi', fallback='auto')
        gpu_choice = 1 if dxgi_value == 'true' else 2
        # Frame Generation Type
        fg_type_code = config.get('FrameGen', 'FGType', fallback='auto')
        # Upscaler (Simplificado a Dx12Upscaler)
        upscaler_code = config.get('Upscalers', 'Dx12Upscaler', fallback='auto')
        # Upscale quality mode (legacy fallback)
        upscale_mode_code = config.get('Upscale', 'Mode', fallback='auto')
        # Sharpness
        sharpness_val = config.getfloat('Sharpness', 'Sharpness', fallback=0.30)
        # Overlay
        overlay_ini = config.get('Menu', 'OverlayMenu', fallback='auto')
        overlay_enabled = (overlay_ini in ('true', 'basic'))

        log_func('INFO', f"Lectura de {ini_path} exitosa.")
        return {
            "gpu_choice": gpu_choice,
            "fg_mode": fg_type_code,  # devolver código; ventana lo mapeará a label
            "upscaler": upscaler_code,
            "upscale_mode": upscale_mode_code,
            "sharpness": sharpness_val,
            "overlay": overlay_enabled,
            "motion_blur": True  # placeholder; no mapeado todavía
        }
    except Exception as e:
        log_func('ERROR', f"Error al leer OptiScaler.ini: {e}. Usando valores por defecto.")
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


def check_nukem_mod_files(nukem_source_dir: str, log_func) -> Tuple[str, bool]:
    """Verifica y encuentra archivos del mod dlssg-to-fsr3 de Nukem.
    
    Args:
        nukem_source_dir: Directorio de origen del mod Nukem
        log_func: Función de logging
        
    Returns:
        Tuple[str, bool]: (ruta_source_dir, archivos_encontrados)
    """
    source_dir = nukem_source_dir
    mod_found = False
    
    if not source_dir or not os.path.isdir(source_dir):
        log_func('ERROR', "La carpeta de origen del mod dlssg-to-fsr3 no está seleccionada.")
        return None, False
        
    try:
        # Buscar recursivamente los archivos requeridos
        for root, _, files in os.walk(source_dir):
            if all(f in files for f in NUKEM_REQUIRED_FILES):
                source_dir = root
                mod_found = True
                break
    except Exception as e:
        log_func('ERROR', f"Error al escanear la carpeta del mod dlssg-to-fsr3: {e}")
        return None, False

    if not mod_found:
        log_func('ERROR', f"La carpeta de origen NO contiene los archivos clave del mod dlssg-to-fsr3: {', '.join(NUKEM_REQUIRED_FILES)}")
        return None, False
        
    log_func('INFO', f"Archivos del mod dlssg-to-fsr3 encontrados en: {source_dir}")
    return source_dir, True


def install_nukem_mod(nukem_source_dir: str, target_dir: str, log_func) -> bool:
    """Instala el mod dlssg-to-fsr3 (Frame Generation para AMD/Intel).
    
    Args:
        nukem_source_dir: Directorio de origen con archivos de dlssg-to-fsr3
        target_dir: Directorio de destino del juego
        log_func: Función de logging
        
    Returns:
        bool: True si la instalación fue exitosa
    """
    source_dir, source_ok = check_nukem_mod_files(nukem_source_dir, log_func)
    if not source_ok:
        return False
        
    try:
        log_func('TITLE', "Instalando dlssg-to-fsr3 (Frame Generation)...")
        copied_files = 0
        created_backups = []
        
        # Lista de archivos a copiar (requeridos + opcionales)
        files_to_copy = NUKEM_REQUIRED_FILES + NUKEM_OPTIONAL_FILES
        
        for filename in files_to_copy:
            source_file = os.path.join(source_dir, filename)
            if not os.path.exists(source_file):
                if filename in NUKEM_REQUIRED_FILES:
                    log_func('ERROR', f"Archivo requerido no encontrado: {filename}")
                    return False
                else:
                    log_func('INFO', f"Archivo opcional no encontrado, omitiendo: {filename}")
                    continue
                    
            target_file = os.path.join(target_dir, filename)
            
            # Crear backup si el archivo ya existe
            if os.path.exists(target_file):
                backup_path = target_file + ".bak"
                try:
                    if os.path.exists(backup_path):
                        os.remove(backup_path)
                    os.rename(target_file, backup_path)
                    log_func('WARN', f"Archivo existente {filename} renombrado a {filename}.bak")
                    created_backups.append(backup_path)
                except Exception as e:
                    log_func('ERROR', f"No se pudo crear backup de {filename}: {e}")
                    # Continuar de todos modos
                    
            # Copiar archivo
            try:
                shutil.copy2(source_file, target_dir)
                copied_files += 1
                log_func('INFO', f"  -> Copiado: {filename}")
            except Exception as e:
                log_func('ERROR', f"Error al copiar {filename}: {e}")
                if filename in NUKEM_REQUIRED_FILES:
                    # Restaurar backups si falla archivo crítico
                    for bak_file in created_backups:
                        original_file = bak_file[:-4]
                        try:
                            if os.path.exists(original_file):
                                os.remove(original_file)
                            os.rename(bak_file, original_file)
                        except Exception:
                            pass
                    return False
                    
        log_func('OK', f"dlssg-to-fsr3 instalado con éxito. Archivos copiados: {copied_files}")
        log_func('INFO', "NOTA: dlssg-to-fsr3 proporciona FRAME GENERATION para GPUs AMD/Intel.")
        return True
        
    except PermissionError:
        log_func('ERROR', "ACCESO DENEGADO. Asegúrese de que el juego está CERRADO.")
        return False
    except Exception as e:
        log_func('ERROR', f"Error al instalar dlssg-to-fsr3: {e}")
        return False


def install_combined_mods(
    optiscaler_source_dir: str,
    nukem_source_dir: str, 
    target_dir: str,
    log_func,
    spoof_dll_name: str = "dxgi.dll",
    gpu_choice: int = 2,
    fg_mode_selected: str = "Automático",
    upscaler_selected: str = "Automático", 
    upscale_mode_selected: str = "Automático",
    sharpness_selected: float = 0.8,
    overlay_selected: bool = False,
    mb_selected: bool = True,
    install_nukem: bool = True
) -> bool:
    """Instala OptiScaler (upscaling) y opcionalmente dlssg-to-fsr3 (frame generation).
    
    Esta función combina ambos mods para proporcionar soporte completo en GPUs AMD/Intel
    y handhelds (Steam Deck, ROG Ally, Legion Go):
    - OptiScaler: Upscaling (FSR, XeSS, DLSS)
    - dlssg-to-fsr3: Frame Generation (intercepta DLSS-G → FSR3 FG)
    
    Args:
        optiscaler_source_dir: Directorio de origen de OptiScaler
        nukem_source_dir: Directorio de origen de dlssg-to-fsr3
        target_dir: Directorio de destino del juego
        log_func: Función de logging
        spoof_dll_name: Nombre del DLL de inyección para OptiScaler
        gpu_choice: 1=NVIDIA, 2=AMD/Intel
        fg_mode_selected: Modo de Frame Generation
        upscaler_selected: Backend de upscaling
        upscale_mode_selected: Modo de calidad de upscaling
        sharpness_selected: Nivel de sharpness
        overlay_selected: Habilitar overlay
        mb_selected: Habilitar motion blur
        install_nukem: Si True, instala dlssg-to-fsr3 además de OptiScaler
        
    Returns:
        bool: True si la instalación fue exitosa
    """
    log_func('TITLE', "=== INSTALACIÓN COMBINADA: OptiScaler + dlssg-to-fsr3 ===")
    log_func('INFO', "OptiScaler = UPSCALING (FSR/XeSS/DLSS quality modes)")
    log_func('INFO', "dlssg-to-fsr3 = FRAME GENERATION (FSR3 FG para AMD/Intel)")
    log_func('INFO', "")
    
    # 1. Instalar OptiScaler primero
    log_func('TITLE', "Paso 1/2: Instalando OptiScaler (Upscaling)...")
    optiscaler_ok = inject_fsr_mod(
        optiscaler_source_dir,
        target_dir,
        log_func,
        spoof_dll_name,
        gpu_choice,
        fg_mode_selected,
        upscaler_selected,
        upscale_mode_selected,
        sharpness_selected,
        overlay_selected,
        mb_selected
    )
    
    if not optiscaler_ok:
        log_func('ERROR', "Instalación de OptiScaler falló. Abortando.")
        return False
        
    # 2. Instalar dlssg-to-fsr3 si se solicita
    if install_nukem:
        log_func('INFO', "")
        log_func('TITLE', "Paso 2/2: Instalando dlssg-to-fsr3 (Frame Generation)...")
        nukem_ok = install_nukem_mod(nukem_source_dir, target_dir, log_func)
        
        if not nukem_ok:
            log_func('ERROR', "Instalación de dlssg-to-fsr3 falló.")
            log_func('WARN', "⚠️ INSTALACIÓN PARCIAL: OptiScaler instalado, pero dlssg-to-fsr3 falló.")
            log_func('INFO', "El juego tendrá upscaling pero no frame generation.")
            # Retornar True porque OptiScaler sí se instaló correctamente
            return True
            
        log_func('INFO', "")
        log_func('OK', "=== INSTALACIÓN COMPLETA ===")
        log_func('OK', "✅ OptiScaler: Upscaling habilitado")
        log_func('OK', "✅ dlssg-to-fsr3: Frame Generation habilitado")
        log_func('INFO', "Tu GPU AMD/Intel ahora tiene upscaling + frame generation!")
    else:
        log_func('INFO', "")
        log_func('OK', "=== INSTALACIÓN BÁSICA COMPLETA ===")
        log_func('OK', "✅ OptiScaler: Upscaling habilitado")
        log_func('INFO', "💡 Para Frame Generation en AMD/Intel, activa 'Modo AMD/Handheld'")
        
    return True


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
