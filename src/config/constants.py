"""Core constants for the application.

Keep only truly global, rarely-changing values here. Move
paths/search settings and user-facing option-maps to
`settings.py` and `paths.py` respectively.
"""

import os

# Application Info
APP_TITLE = "Gestor OptiScaler"
APP_VERSION = "2.0"

# Filenames / small paths (kept as strings for backwards compatibility)
CONFIG_FILE = "injector_config.json"
MOD_SOURCE_DIR = os.path.join(os.getcwd(), "mod_source")
CACHE_DIR = os.path.join(os.getcwd(), ".cache")

# GitHub configuration
GITHUB_REPO_OWNER = "optiscaler"
GITHUB_REPO_NAME = "OptiScaler"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/releases"
GITHUB_LATEST_RELEASE_URL = f"{GITHUB_API_URL}/latest"
COMPATIBILITY_URL = f"https://github.com/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/wiki/FSR4-Compatibility-List"

# 7-Zip helper
SEVEN_ZIP_DOWNLOAD_URL = "https://www.7-zip.org/a/7zr.exe"
SEVEN_ZIP_EXE_NAME = "7z.exe"

# Files and folders related to the mod (used for install/uninstall)
MOD_CHECK_FILES = ['OptiScaler.dll', 'dlssg_to_fsr3_amd_is_better.dll']

TARGET_MOD_FILES = [
    'dlssg_to_fsr3_amd_is_better.dll', 'version.dll', 'nvngx_dlss.dll', 'fsr3_config.json',
    'OptiScaler.dll', 'OptiScaler.ini', 'OptiScaler.log',
    'amd_fidelityfx_framegeneration_dx12.dll', 'amd_fidelityfx_upscaler_dx12.dll',
    'amd_fidelityfx_vk.dll', 'amd_fidelityfx_dx12.dll', 'libxess.dll', 'libxess_dx11.dll',
    'nvngx.dll', 'libxess_fg.dll', 'libxell.dll', 'fakenvapi.dll', 'fakenvapi.ini',
    'dxgi.dll', 'd3d12.dll', 'winmm.dll', 'dinput8.dll', 'dbghelp.dll', 'wininet.dll', 'winhttp.dll'
]

TARGET_MOD_DIRS = ['D3D12_Optiscaler', 'DlssOverrides', 'Licenses']
GENERIC_SPOOF_FILES = ['dxgi.dll', 'd3d12.dll', 'winmm.dll', 'dinput8.dll']