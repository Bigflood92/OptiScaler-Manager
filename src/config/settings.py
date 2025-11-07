"""Application settings and UI option maps.

This file contains values used by the UI to populate
choice lists and default settings for the app. Path
and filesystem related constants live in `paths.py`.
"""

from .constants import SEVEN_ZIP_DOWNLOAD_URL, SEVEN_ZIP_EXE_NAME
from .paths import COMMON_EXE_SUBFOLDERS_DIRECT, RECURSIVE_EXE_PATTERNS

# Config Keys
CUSTOM_SEARCH_FOLDERS_CONFIG_KEY = "custom_search_folders"

# Tools and Dependencies (refer to constants for canonical values)
SEVEN_ZIP_DOWNLOAD_URL = SEVEN_ZIP_DOWNLOAD_URL
SEVEN_ZIP_EXE_NAME = SEVEN_ZIP_EXE_NAME

# FSR / GPU options
GPU_CHOICES = {
    "AMD": "AMD (FSR)",
    "NVIDIA": "NVIDIA (DLSS)"
}

# DLL spoofing options shown to users (index -> filename)
SPOOFING_OPTIONS = {
    1: 'dxgi.dll',
    2: 'winmm.dll',
    3: 'version.dll',
    4: 'dbghelp.dll',
    5: 'd3d12.dll',
    6: 'wininet.dll',
    7: 'winhttp.dll',
    8: 'OptiScaler.asi'
}
SPOOFING_DLL_NAMES = list(SPOOFING_OPTIONS.values())

# Frame Generation Options
FG_OPTIONS = ["Automático", "FSR 4.0", "FSR 3.1", "FSR 3.0", "XeSS", "Desactivada"]
FG_MODE_MAP = {
    "Automático": "auto",
    "FSR 4.0": "fsr40",
    "FSR 3.1": "fsr31",
    "FSR 3.0": "fsr30",
    "XeSS": "xess",
    "Desactivada": "off"
}
FG_MODE_MAP_INVERSE = {v: k for k, v in FG_MODE_MAP.items()}

# Upscaler Backend Options (Reescalador)
UPSCALER_OPTIONS = [
    "Automático",
    "FSR 4.0",
    "FSR 3.1",
    "FSR 2.2",
    "XeSS",
    "DLSS"
]
UPSCALER_MAP = {
    "Automático": "auto",
    "FSR 4.0": "fsr40",
    "FSR 3.1": "fsr31",
    "FSR 2.2": "fsr22",
    "XeSS": "xess",
    "DLSS": "dlss"
}
UPSCALER_MAP_INVERSE = {v: k for k, v in UPSCALER_MAP.items()}

# Upscaling Options
UPSCALE_OPTIONS = ["Automático", "Calidad", "Equilibrado", "Rendimiento", "Ultra Rendimiento"]
UPSCALE_MODE_MAP = {
    "Automático": "auto",
    "Calidad": "quality",
    "Equilibrado": "balanced",
    "Rendimiento": "performance",
    "Ultra Rendimiento": "ultra_performance"
}
UPSCALE_MODE_MAP_INVERSE = {v: k for k, v in UPSCALE_MODE_MAP.items()}

# Default Values
DEFAULT_SHARPNESS = 0.8
DEFAULT_OVERLAY = False
DEFAULT_MOTION_BLUR = False

# Expose common search patterns here for convenience
COMMON_EXE_SUBFOLDERS_DIRECT = COMMON_EXE_SUBFOLDERS_DIRECT
RECURSIVE_EXE_PATTERNS = RECURSIVE_EXE_PATTERNS
