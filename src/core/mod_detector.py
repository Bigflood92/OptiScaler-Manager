"""Mod detection and version tracking for installed games.

Provides functions to:
 - Detect if OptiScaler is installed in a game directory
 - Read version metadata from per-game version.json
 - Compare installed version vs available version
 - Determine update status and generate badge info
"""

import os
import json
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class ModStatus:
    """Estado de instalación del mod en un juego."""
    installed: bool
    game_version: Optional[str]
    latest_version: Optional[str]
    needs_update: bool
    incomplete: bool
    installed_at: Optional[str]
    badge_text: str
    badge_color: str


def read_version_json(path: Path) -> Optional[Dict[str, Any]]:
    """Lee y parsea version.json si existe."""
    try:
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception:
        pass
    return None


def is_optiscaler_installed(game_dir: Path) -> bool:
    """Verifica si OptiScaler está instalado buscando DLL principal."""
    # Puede estar como OptiScaler.dll o renombrado (nvngx.dll, dxgi.dll, etc)
    dll_indicators = ['OptiScaler.dll', 'OptiScaler.ini']
    for indicator in dll_indicators:
        if (game_dir / indicator).exists():
            return True
    return False


def check_installation_complete(game_dir: Path) -> bool:
    """Verifica si la instalación tiene archivos esenciales (no huérfana).
    
    Una instalación se considera completa si tiene:
    - OptiScaler.dll O su versión renombrada (dxgi.dll, nvngx.dll, etc.)
    - OptiScaler.ini (configuración)
    - D3D12_Optiscaler/ (carpeta runtime OBLIGATORIA)
    """
    # Verificar OptiScaler.ini (OBLIGATORIO)
    if not (game_dir / 'OptiScaler.ini').exists():
        return False
    
    # Verificar DLL principal (puede estar como OptiScaler.dll o renombrado)
    # Buscar OptiScaler.dll o variantes comunes de spoof
    dll_found = False
    possible_dlls = [
        'OptiScaler.dll',  # Original
        'dxgi.dll',        # Spoof común
        'nvngx.dll',       # Spoof NVIDIA
        'd3d11.dll',       # Spoof D3D11
        'd3d12.dll',       # Spoof D3D12
        'winmm.dll',       # Spoof WinMM
        'version.dll'      # Spoof Version
    ]
    
    for dll in possible_dlls:
        if (game_dir / dll).exists():
            dll_found = True
            break
    
    if not dll_found:
        return False
    
    # La carpeta D3D12_Optiscaler es OBLIGATORIA
    # Esta carpeta contiene los archivos runtime necesarios para el funcionamiento del mod
    d3d12_folder = game_dir / 'D3D12_Optiscaler'
    if not d3d12_folder.exists():
        return False
    
    # Verificar que la carpeta no esté vacía
    try:
        if not any(d3d12_folder.iterdir()):
            return False
    except Exception:
        return False
    
    return True


def compare_versions(game_ver: Optional[str], latest_ver: Optional[str]) -> bool:
    """Compara versiones (semver simple) y determina si hay actualización disponible.
    
    Returns:
        True si latest > game (necesita actualización)
    """
    if not game_ver or not latest_ver:
        return False
    
    try:
        # Limpiar prefijo 'v' si existe
        gv = game_ver.lstrip('v').split('.')
        lv = latest_ver.lstrip('v').split('.')
        
        # Convertir a enteros y comparar
        g_parts = [int(p) for p in gv]
        l_parts = [int(p) for p in lv]
        
        return l_parts > g_parts
    except (ValueError, IndexError):
        # Fallback lexicográfico
        return latest_ver > game_ver


def compute_game_mod_status(
    game_dir: Path,
    optiscaler_base_dir: Path
) -> ModStatus:
    """Calcula el estado del mod instalado en un juego.
    
    Args:
        game_dir: Directorio del juego
        optiscaler_base_dir: Directorio base de OptiScaler (mod_source/OptiScaler)
        
    Returns:
        ModStatus con información completa del estado
    """
    # Leer metadata del juego
    game_meta = read_version_json(game_dir / 'version.json')
    
    # Leer metadata global (última disponible en mod_source)
    global_meta = read_version_json(optiscaler_base_dir / 'version.json')
    
    # Detectar instalación
    installed = is_optiscaler_installed(game_dir)
    
    if not installed:
        return ModStatus(
            installed=False,
            game_version=None,
            latest_version=global_meta.get('version') if global_meta else None,
            needs_update=False,
            incomplete=False,
            installed_at=None,
            badge_text="⚪ Sin mod",
            badge_color="#888888"
        )
    
    # Extraer versiones
    game_version = game_meta.get('version') if game_meta else None
    latest_version = global_meta.get('version') if global_meta else None
    installed_at = game_meta.get('installed_at') if game_meta else None
    
    # Verificar completitud
    complete = check_installation_complete(game_dir)
    
    if not complete:
        return ModStatus(
            installed=True,
            game_version=game_version,
            latest_version=latest_version,
            needs_update=False,
            incomplete=True,
            installed_at=installed_at,
            badge_text="❌ Instalación incompleta",
            badge_color="#FF4444"
        )
    
    # Comparar versiones
    needs_update = compare_versions(game_version, latest_version)
    
    if needs_update:
        ver_text = f"v{game_version}" if game_version else "?"
        return ModStatus(
            installed=True,
            game_version=game_version,
            latest_version=latest_version,
            needs_update=True,
            incomplete=False,
            installed_at=installed_at,
            badge_text=f"⚠️ Actualización disponible ({ver_text} → v{latest_version})",
            badge_color="#FFA500"
        )
    
    # Instalado y actualizado
    ver_text = f"v{game_version}" if game_version else "instalado"
    return ModStatus(
        installed=True,
        game_version=game_version,
        latest_version=latest_version,
        needs_update=False,
        incomplete=False,
        installed_at=installed_at,
        badge_text=f"✅ OptiScaler {ver_text}",
        badge_color="#00FF88"
    )


def get_version_badge_info(game_dir: str, optiscaler_base_dir: str) -> Dict[str, Any]:
    """Helper wrapper que devuelve diccionario con info del badge.
    
    Útil para integración en UI sin usar dataclass directamente.
    """
    status = compute_game_mod_status(Path(game_dir), Path(optiscaler_base_dir))
    return {
        'installed': status.installed,
        'game_version': status.game_version,
        'latest_version': status.latest_version,
        'needs_update': status.needs_update,
        'incomplete': status.incomplete,
        'installed_at': status.installed_at,
        'badge_text': status.badge_text,
        'badge_color': status.badge_color
    }


__all__ = [
    'ModStatus',
    'compute_game_mod_status',
    'get_version_badge_info',
    'is_optiscaler_installed',
    'compare_versions'
]
