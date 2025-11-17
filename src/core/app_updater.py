"""
Sistema de auto-actualización de la aplicación.
"""

import os
import sys
import subprocess
import tempfile
import requests
from pathlib import Path
from typing import Optional, Tuple
import shutil


def get_current_version() -> str:
    """Obtiene la versión actual de la aplicación."""
    from ..config.constants import APP_VERSION
    return APP_VERSION


def check_for_updates(logger=None) -> Optional[Tuple[str, dict]]:
    """
    Verifica si hay actualizaciones disponibles en GitHub.
    
    Returns:
        Tuple[str, dict]: (versión, release_info) si hay actualización, None si no hay
    """
    try:
        current_version = get_current_version()
        
        if logger:
            logger("INFO", f"Verificando actualizaciones (versión actual: {current_version})...")
        
        # Obtener última release desde GitHub
        api_url = "https://api.github.com/repos/Bigflood92/OptiScaler-Manager/releases/latest"
        response = requests.get(api_url, timeout=5)
        response.raise_for_status()
        
        release_info = response.json()
        latest_version = release_info.get("tag_name", "").lstrip("v")
        
        if logger:
            logger("INFO", f"Última versión disponible: {latest_version}")
        
        # Comparar versiones (simple comparación de strings, asumiendo formato semver)
        if _is_newer_version(current_version, latest_version):
            if logger:
                logger("OK", f"Nueva versión disponible: {latest_version}")
            return (latest_version, release_info)
        else:
            if logger:
                logger("INFO", "No hay actualizaciones disponibles")
            return None
            
    except requests.RequestException as e:
        if logger:
            logger("WARN", f"No se pudo verificar actualizaciones: {e}")
        return None
    except Exception as e:
        if logger:
            logger("ERROR", f"Error inesperado verificando actualizaciones: {e}")
        return None


def _is_newer_version(current: str, latest: str) -> bool:
    """
    Compara dos versiones en formato semver.
    
    Returns:
        bool: True si latest es más nueva que current
    """
    try:
        current_parts = [int(x) for x in current.split(".")]
        latest_parts = [int(x) for x in latest.split(".")]
        
        # Rellenar con ceros si tienen diferente longitud
        max_len = max(len(current_parts), len(latest_parts))
        current_parts += [0] * (max_len - len(current_parts))
        latest_parts += [0] * (max_len - len(latest_parts))
        
        return latest_parts > current_parts
    except:
        # Si falla la comparación numérica, comparar como strings
        return latest > current


def download_and_install_update(release_info: dict, logger=None, progress_callback=None) -> bool:
    """
    Descarga e instala la actualización.
    
    Args:
        release_info: Información del release desde GitHub API
        logger: Función de logging
        progress_callback: Callback para reportar progreso (downloaded, total, done, message)
        
    Returns:
        bool: True si fue exitoso
    """
    try:
        # Buscar el asset del ejecutable
        assets = release_info.get("assets", [])
        exe_asset = None
        
        for asset in assets:
            if asset["name"].endswith(".exe"):
                exe_asset = asset
                break
        
        if not exe_asset:
            if logger:
                logger("ERROR", "No se encontró ejecutable en el release")
            return False
        
        download_url = exe_asset["browser_download_url"]
        file_size = exe_asset["size"]
        file_name = exe_asset["name"]
        
        if logger:
            logger("INFO", f"Descargando actualización: {file_name} ({file_size / 1024 / 1024:.2f} MB)")
        
        # Crear directorio temporal
        temp_dir = tempfile.gettempdir()
        temp_file = os.path.join(temp_dir, file_name)
        
        # Descargar archivo
        response = requests.get(download_url, stream=True, timeout=30)
        response.raise_for_status()
        
        downloaded = 0
        with open(temp_file, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    if progress_callback:
                        progress = downloaded / file_size if file_size > 0 else 0
                        progress_callback(
                            downloaded,
                            file_size,
                            False,
                            f"Descargando... {progress * 100:.1f}%"
                        )
        
        if logger:
            logger("OK", f"Descarga completada: {temp_file}")
        
        if progress_callback:
            progress_callback(file_size, file_size, False, "Preparando actualización...")
        
        # Preparar script de actualización
        current_exe = sys.executable if getattr(sys, 'frozen', False) else None
        
        if not current_exe or not current_exe.endswith('.exe'):
            if logger:
                logger("ERROR", "No se pudo determinar el ejecutable actual")
            return False
        
        current_dir = os.path.dirname(current_exe)
        current_name = os.path.basename(current_exe)
        backup_name = current_name.replace(".exe", "_old.exe")
        backup_path = os.path.join(current_dir, backup_name)
        new_exe_path = os.path.join(current_dir, file_name)
        
        # Crear script batch para actualización
        batch_script = f"""@echo off
echo Actualizando OptiScaler Manager...
timeout /t 2 /nobreak > nul

REM Intentar eliminar backup anterior
if exist "{backup_path}" del /f /q "{backup_path}"

REM Renombrar ejecutable actual a backup
move /y "{current_exe}" "{backup_path}"

REM Copiar nuevo ejecutable
move /y "{temp_file}" "{new_exe_path}"

REM Si el nuevo tiene nombre diferente, renombrarlo al nombre actual
if not "{file_name}"=="{current_name}" (
    move /y "{new_exe_path}" "{current_exe}"
)

REM Iniciar nueva versión
start "" "{current_exe}"

REM Limpiar backup antiguo (opcional)
timeout /t 2 /nobreak > nul
if exist "{backup_path}" del /f /q "{backup_path}"

REM Auto-eliminar este script
del /f /q "%~f0"
"""
        
        batch_path = os.path.join(temp_dir, "update_optiscaler.bat")
        with open(batch_path, "w", encoding="utf-8") as f:
            f.write(batch_script)
        
        if logger:
            logger("OK", "Script de actualización preparado")
        
        if progress_callback:
            progress_callback(file_size, file_size, True, "Actualización lista")
        
        # Ejecutar script y cerrar aplicación
        subprocess.Popen(
            ["cmd.exe", "/c", batch_path],
            creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS,
            close_fds=True
        )
        
        if logger:
            logger("OK", "Cerrando aplicación para actualizar...")
        
        return True
        
    except requests.RequestException as e:
        if logger:
            logger("ERROR", f"Error descargando actualización: {e}")
        if progress_callback:
            progress_callback(0, 1, True, f"Error: {e}")
        return False
    except Exception as e:
        if logger:
            logger("ERROR", f"Error instalando actualización: {e}")
        if progress_callback:
            progress_callback(0, 1, True, f"Error: {e}")
        return False
