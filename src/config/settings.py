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

# Frame Generation Type Options (actual OptiScaler FGType values)
# Nota: Antes la lista contenía opciones de reescalado (FSR/XeSS) que pertenecen a UPSCALER_OPTIONS.
# Ahora se alinean con los valores reales soportados por OptiScaler.ini -> [FrameGen] FGType
FG_OPTIONS = ["Automático", "OptiFG", "NukemFG", "Desactivada"]
FG_MODE_MAP = {  # Conservamos el nombre para compatibilidad con imports existentes
    "Automático": "auto",
    "OptiFG": "optifg",
    "NukemFG": "nukems",
    "Desactivada": "nofg"
}
FG_MODE_MAP_INVERSE = {v: k for k, v in FG_MODE_MAP.items()}

# Upscaler Backend Options (Reescalador)
UPSCALER_OPTIONS = [
    "Automático",
    "FSR 4.0",
    "FSR 3.1",
    "FSR 2.2",
    "FSR 2.1",
    "XeSS",
    "DLSS"
]
UPSCALER_MAP = {
    "Automático": "auto",
    "FSR 4.0": "fsr40",
    "FSR 3.1": "fsr31",
    "FSR 2.2": "fsr22",
    "FSR 2.1": "fsr21",
    "XeSS": "xess",
    "DLSS": "dlss"
}
UPSCALER_MAP_INVERSE = {v: k for k, v in UPSCALER_MAP.items()}

# Upscaler options específicas por API (según OptiScaler.ini real)
# Nota: Estas son las opciones válidas que OptiScaler acepta para cada backend
UPSCALER_OPTIONS_DX11 = [
    "Automático",
    "FSR 2.2 (nativo)",
    "FSR 3.1 (nativo)",
    "XeSS (nativo)",
    "XeSS 1.2 (Dx11on12)",
    "FSR 2.1 1.2 (Dx11on12)",
    "FSR 2.2 1.2 (Dx11on12)",
    "FSR 3.1 1.2 (Dx11on12)",
    "DLSS"
]

UPSCALER_MAP_DX11 = {
    "Automático": "auto",
    "FSR 2.2 (nativo)": "fsr22",
    "FSR 3.1 (nativo)": "fsr31",
    "XeSS (nativo)": "xess",
    "XeSS 1.2 (Dx11on12)": "xess_12",
    "FSR 2.1 1.2 (Dx11on12)": "fsr21_12",
    "FSR 2.2 1.2 (Dx11on12)": "fsr22_12",
    "FSR 3.1 1.2 (Dx11on12)": "fsr31_12",
    "DLSS": "dlss"
}

UPSCALER_OPTIONS_DX12 = [
    "Automático",
    "XeSS",
    "FSR 2.1",
    "FSR 2.2",
    "FSR 3.1 (también FSR4)",
    "DLSS"
]

UPSCALER_MAP_DX12 = {
    "Automático": "auto",
    "XeSS": "xess",
    "FSR 2.1": "fsr21",
    "FSR 2.2": "fsr22",
    "FSR 3.1 (también FSR4)": "fsr31",  # fsr31 cubre también fsr40 en Dx12
    "DLSS": "dlss"
}

UPSCALER_OPTIONS_VULKAN = [
    "Automático",
    "FSR 2.1",
    "FSR 2.2",
    "FSR 3.1",
    "XeSS",
    "DLSS"
]

UPSCALER_MAP_VULKAN = {
    "Automático": "auto",
    "FSR 2.1": "fsr21",
    "FSR 2.2": "fsr22",
    "FSR 3.1": "fsr31",
    "XeSS": "xess",
    "DLSS": "dlss"
}

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
