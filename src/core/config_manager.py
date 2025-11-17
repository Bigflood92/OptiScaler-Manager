"""Gestión simple de configuración (injector_config.json).

Proporciona load/save y valores por defecto usados por la GUI y los módulos core.
"""
import os
import json
from typing import Dict, Any

from ..config.paths import MOD_SOURCE_DIR, CONFIG_FILE, CACHE_DIR


def get_config_path() -> str:
    """Obtiene la ruta del archivo de configuración desde paths.py"""
    return str(CONFIG_FILE)


def default_config() -> Dict[str, Any]:
    return {
        "mod_source_dir": str(MOD_SOURCE_DIR),
        "last_spoof_name": "dxgi.dll",
        "gpu_choice": 2,
        "fg_mode": "Automático",
        "upscale_mode": "Automático",
        "sharpness": 0.8,
        "overlay": False,
        "motion_blur": True,
        "custom_game_folders": [],
        "cache_dir": CACHE_DIR
    }


def load_config(path: str = None) -> Dict[str, Any]:
    cfg_path = path or get_config_path()
    cfg = default_config()
    if not os.path.exists(cfg_path):
        return cfg
    try:
        with open(cfg_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return cfg
        # merge shallow
        cfg.update(data)
        return cfg
    except Exception:
        return cfg


def save_config(cfg: Dict[str, Any], path: str = None) -> bool:
    cfg_path = path or get_config_path()
    try:
        base_dir = os.path.dirname(cfg_path)
        if base_dir and not os.path.exists(base_dir):
            os.makedirs(base_dir, exist_ok=True)
        with open(cfg_path, 'w', encoding='utf-8') as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
        return True
    except Exception:
        return False


def ensure_mod_source_dir(cfg: Dict[str, Any]) -> str:
    path = cfg.get('mod_source_dir') or str(MOD_SOURCE_DIR)
    try:
        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)
    except Exception:
        pass
    return path
