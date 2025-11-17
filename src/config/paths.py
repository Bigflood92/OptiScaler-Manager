"""Common directory paths and file locations."""

import os
import sys
from pathlib import Path

# Get base directory (where the exe will be or where the script is run from)
# Check for Nuitka onefile FIRST (before sys.frozen, because Nuitka doesn't set it reliably)
if 'NUITKA_ONEFILE_DIRECTORY' in os.environ:
    # Nuitka onefile: use the directory where the original .exe is located
    BASE_DIR = Path(os.environ['NUITKA_ONEFILE_DIRECTORY'])
elif hasattr(sys, 'frozen'):
    # PyInstaller or other freezers
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller onefile
        BASE_DIR = Path(os.path.dirname(sys.executable))
    else:
        # Other frozen executables
        BASE_DIR = Path(os.path.dirname(sys.executable))
else:
    # Running as script - go up to project root
    BASE_DIR = Path(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Application configuration directory (next to exe)
APP_DIR = BASE_DIR / "Config Optiscaler Gestor"

# Configuration and cache files
CONFIG_FILE = APP_DIR / "injector_config.json"
GAMES_CACHE_FILE = APP_DIR / "games_caché.json"
RELEASES_CACHE_FILE = APP_DIR / "releases_caché.json"

# Mod source directories
MOD_SOURCE_DIR = APP_DIR / "mod_source"
OPTISCALER_DIR = MOD_SOURCE_DIR / "OptiScaler"
DLSSG_TO_FSR3_DIR = MOD_SOURCE_DIR / "dlssg-to-fsr3"

# Tools
SEVEN_ZIP_PATH = MOD_SOURCE_DIR / "7z.exe"

# Other directories
CACHE_DIR = APP_DIR / ".cache"
LOG_DIR = APP_DIR / "logs"

# Default game installation paths
XBOX_GAMES_DIR = Path(r"C:\XboxGames")
STEAM_COMMON_DIR = Path(r"C:\Program Files (x86)\Steam\steamapps\common")
EPIC_COMMON_DIR = Path(r"C:\Program Files\Epic Games")
NVIDIA_CHECK_FILE = Path(r"C:\Windows\system32\nvapi64.dll")

# Executable search paths
COMMON_EXE_SUBFOLDERS_DIRECT = [
    'Binaries/Win64', 'Binaries/WinGDK', 'bin/x64',
    'Engine/Binaries/Win64', 'Engine/Binaries/ThirdParty',
    'x64', 'Binaries', 'bin'
]

RECURSIVE_EXE_PATTERNS = [
    '**/Binaries/Win64/*.exe', '**/Binaries/WinGDK/*.exe',
    '**/*Game/Binaries/Win64/*.exe', '**/x64/*.exe'
]


def initialize_directories():
    """Create all required directories if they don't exist."""
    directories = [
        APP_DIR,
        MOD_SOURCE_DIR,
        OPTISCALER_DIR,
        DLSSG_TO_FSR3_DIR,
        CACHE_DIR,
        LOG_DIR
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)


def get_config_dir():
    """Return the application configuration directory path."""
    return APP_DIR