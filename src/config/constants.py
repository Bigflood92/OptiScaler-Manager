"""Core constants for the application.

Keep only truly global, rarely-changing values here. Move
paths/search settings and user-facing option-maps to
`settings.py` and `paths.py` respectively.
"""

import os

# Application Info
APP_TITLE = "Gestor OptiScaler"
APP_VERSION = "2.4.1"

# Filenames / small paths (kept as strings for backwards compatibility)
CONFIG_FILE = "injector_config.json"

# GitHub configuration - OptiScaler (upscaler)
GITHUB_REPO_OWNER = "optiscaler"
GITHUB_REPO_NAME = "OptiScaler"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/releases"
GITHUB_LATEST_RELEASE_URL = f"{GITHUB_API_URL}/latest"
COMPATIBILITY_URL = f"https://github.com/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/wiki/FSR4-Compatibility-List"

# GitHub configuration - dlssg-to-fsr3 (frame generation para AMD/no-RTX40)
NUKEM_REPO_OWNER = "Nukem9"
NUKEM_REPO_NAME = "dlssg-to-fsr3"
NUKEM_API_URL = f"https://api.github.com/repos/{NUKEM_REPO_OWNER}/{NUKEM_REPO_NAME}/releases"
NUKEM_LATEST_RELEASE_URL = f"{NUKEM_API_URL}/latest"

# GitHub configuration - OptiPatcher (ASI plugin para OptiScaler)
OPTIPATCHER_REPO_OWNER = "optiscaler"
OPTIPATCHER_REPO_NAME = "OptiPatcher"
OPTIPATCHER_API_URL = f"https://api.github.com/repos/{OPTIPATCHER_REPO_OWNER}/{OPTIPATCHER_REPO_NAME}/releases"
OPTIPATCHER_LATEST_RELEASE_URL = f"{OPTIPATCHER_API_URL}/latest"

# Archivos requeridos de dlssg-to-fsr3 (Nukem) para Frame Generation
NUKEM_REQUIRED_FILES = [
    'dlssg_to_fsr3_amd_is_better.dll',  # Core FG implementation
    'nvngx.dll',                         # NVNGX wrapper (o version.dll, etc.)
]

# Archivos opcionales de dlssg-to-fsr3
NUKEM_OPTIONAL_FILES = [
    'version.dll',      # Alternative wrapper
    'winhttp.dll',      # Alternative wrapper
    'dbghelp.dll',      # Alternative wrapper
    'dlssg_to_fsr3.ini' # Optional config for debug overlay
]

# 7-Zip helper
SEVEN_ZIP_DOWNLOAD_URL = "https://www.7-zip.org/a/7zr.exe"
SEVEN_ZIP_EXE_NAME = "7z.exe"

# Files and folders related to the mod (used for install/uninstall)
# OptiScaler files
MOD_CHECK_FILES_OPTISCALER = ['OptiScaler.dll', 'OptiScaler.ini']
# dlssg-to-fsr3 files
MOD_CHECK_FILES_NUKEM = ['dlssg_to_fsr3_amd_is_better.dll', 'nvngx.dll']
# Combined check (any of these indicates mods installed)
MOD_CHECK_FILES = MOD_CHECK_FILES_OPTISCALER + MOD_CHECK_FILES_NUKEM

TARGET_MOD_FILES = [
    # dlssg-to-fsr3 (Nukem) files
    'dlssg_to_fsr3_amd_is_better.dll', 'dlssg_to_fsr3.ini',
    # OptiScaler files
    'version.dll', 'nvngx_dlss.dll', 'fsr3_config.json',
    'OptiScaler.dll', 'OptiScaler.ini', 'OptiScaler.log',
    # AMD FidelityFX libraries
    'amd_fidelityfx_framegeneration_dx12.dll', 'amd_fidelityfx_upscaler_dx12.dll',
    'amd_fidelityfx_vk.dll', 'amd_fidelityfx_dx12.dll',
    # XeSS libraries
    'libxess.dll', 'libxess_dx11.dll', 'libxess_fg.dll', 'libxell.dll',
    # Shared NVNGX wrapper
    'nvngx.dll',
    # Fake NVAPI
    'fakenvapi.dll', 'fakenvapi.ini',
    # DLL spoofing files (will be cleaned if they match backup patterns)
    'dxgi.dll', 'd3d12.dll', 'winmm.dll', 'dinput8.dll', 'dbghelp.dll', 'wininet.dll', 'winhttp.dll'
]

TARGET_MOD_DIRS = ['D3D12_Optiscaler', 'DlssOverrides', 'Licenses']
GENERIC_SPOOF_FILES = ['dxgi.dll', 'd3d12.dll', 'winmm.dll', 'dinput8.dll']