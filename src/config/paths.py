"""Common directory paths and file locations."""

import os
import sys
from pathlib import Path

# Application paths
APP_DIR = Path(os.path.dirname(sys.argv[0] if hasattr(sys, 'frozen') else __file__))
CONFIG_FILE = APP_DIR / "injector_config.json"
MOD_SOURCE_DIR = APP_DIR / "mod_source"
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
    '**/*Game/Binaries/Win64/*.exe', '**/*Shipping.exe',
    '**/bin/x64/*.exe', '**/x64/*.exe'
]