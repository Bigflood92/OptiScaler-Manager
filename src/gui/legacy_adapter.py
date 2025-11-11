"""Legacy adapter module that provides compatibility functions for the original GUI.

This module exposes core functionality in a way that matches the original
monolith's function signatures, allowing the legacy GUI to work with the
new modular structure without modification.
"""

import os
from typing import Any, Dict, List, Tuple

from ..core import scanner, installer, config_manager
from ..config.constants import (
    MOD_SOURCE_DIR, MOD_CHECK_FILES, GENERIC_SPOOF_FILES,
    TARGET_MOD_FILES, TARGET_MOD_DIRS
)

# Re-export constants used by legacy GUI
__all__ = [
    'MOD_SOURCE_DIR',
    'MOD_CHECK_FILES',
    'GENERIC_SPOOF_FILES',
    'TARGET_MOD_FILES',
    'TARGET_MOD_DIRS',
    'scan_games',
    'inject_fsr_mod',
    'install_combined_mods',
    'check_mod_source_files',
    'check_nukem_mod_files',
    'install_nukem_mod',
    'restore_original_dll',
    'uninstall_fsr_mod',
    'clean_logs',
    'clean_orphan_backups',
    'load_config',
    'save_config',
    'default_config'
]

# Function adapters that match original signatures
def scan_games(log_func, custom_folders=None):
    """Adapter for scanner.scan_games() that matches legacy signature."""
    return scanner.scan_games(log_func, custom_folders or [])

def inject_fsr_mod(
    mod_source_dir: str, target_dir: str, log_func, 
    spoof_dll_name: str = "dxgi.dll",
    gpu_choice: int = 2,
    fg_mode_selected: str = "Automático",
    upscaler_selected: str = "Automático",
    upscale_mode_selected: str = "Automático",
    sharpness_selected: float = 0.8,
    overlay_selected: bool = False,
    mb_selected: bool = True
) -> bool:
    """Adapter for installer.inject_fsr_mod() that matches legacy signature."""
    return installer.inject_fsr_mod(
        mod_source_dir, target_dir, log_func,
        spoof_dll_name, gpu_choice, fg_mode_selected,
        upscaler_selected, upscale_mode_selected,
        sharpness_selected, overlay_selected, mb_selected
    )

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
    """Adapter for installer.install_combined_mods() with legacy signature."""
    return installer.install_combined_mods(
        optiscaler_source_dir, nukem_source_dir, target_dir, log_func,
        spoof_dll_name, gpu_choice, fg_mode_selected,
        upscaler_selected, upscale_mode_selected,
        sharpness_selected, overlay_selected, mb_selected, install_nukem
    )

def check_nukem_mod_files(nukem_source_dir: str, log_func) -> Tuple[str, bool]:
    """Adapter for installer.check_nukem_mod_files()."""
    return installer.check_nukem_mod_files(nukem_source_dir, log_func)

def install_nukem_mod(nukem_source_dir: str, target_dir: str, log_func) -> bool:
    """Adapter for installer.install_nukem_mod()."""
    return installer.install_nukem_mod(nukem_source_dir, target_dir, log_func)

def check_mod_source_files(mod_source_dir: str, log_func) -> Tuple[str, bool]:
    """Adapter for installer.check_mod_source_files()."""
    return installer.check_mod_source_files(mod_source_dir, log_func)

def restore_original_dll(target_dir: str, log_func) -> bool:
    """Adapter for installer.restore_original_dll()."""
    return installer.restore_original_dll(target_dir, log_func)

def uninstall_fsr_mod(target_dir: str, log_func) -> Tuple[bool, List[Tuple[str, str]]]:
    """Adapter for installer.uninstall_fsr_mod()."""
    return installer.uninstall_fsr_mod(target_dir, log_func)

def clean_logs(game_folders: List[str], log_func) -> int:
    """Adapter for installer.clean_logs()."""
    return installer.clean_logs(game_folders, log_func)

def clean_orphan_backups(all_games_data: List[Tuple[str, ...]], log_func) -> int:
    """Adapter for installer.clean_orphan_backups()."""
    return installer.clean_orphan_backups(all_games_data, log_func)

def load_config(path: str = None) -> Dict[str, Any]:
    """Adapter for config_manager.load_config()."""
    return config_manager.load_config(path)

def save_config(cfg: Dict[str, Any], path: str = None) -> bool:
    """Adapter for config_manager.save_config()."""
    return config_manager.save_config(cfg, path)

def default_config() -> Dict[str, Any]:
    """Adapter for config_manager.default_config()."""
    return config_manager.default_config()