"""Path and system utilities for FSR Injector."""

import os
import sys
import glob
import winreg
import ctypes
from typing import List, Tuple, Optional
from ..config.constants import (
    STEAM_COMMON_DIR,
    EPIC_COMMON_DIR,
    XBOX_GAMES_DIR,
    NVIDIA_CHECK_FILE
)

def is_admin() -> bool:
    """Check if running with admin privileges.
    
    Returns:
        bool: True if running as admin
    """
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False

def get_script_base_path() -> str:
    """Get base path for the application.
    
    Returns:
        str: Base path
    """
    try:
        if getattr(sys, 'frozen', False):
            # Running as compiled executable
            return os.path.dirname(sys.executable)
        else:
            # Running as script
            return os.path.dirname(os.path.dirname(__file__))
    except Exception:
        return os.path.abspath(".")

def get_steam_paths() -> List[str]:
    """Get Steam library paths.
    
    Returns:
        List of Steam library paths
    """
    paths = {STEAM_COMMON_DIR}
    
    try:
        # Get Steam installation path from registry
        key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\WOW6432Node\Valve\Steam"
        )
        steam_path = winreg.QueryValueEx(key, "InstallPath")[0]
        winreg.CloseKey(key)
        
        # Add main Steam library path
        main_common = os.path.join(steam_path, "steamapps", "common")
        if os.path.isdir(main_common):
            paths.add(main_common)
            
        # Find additional library paths from libraryfolders.vdf
        vdf_path = os.path.join(steam_path, "steamapps", "libraryfolders.vdf")
        if os.path.exists(vdf_path):
            with open(vdf_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Parse library paths using basic regex
            import re
            lib_paths = re.findall(r'"path"\s+"([^"]+)"', content)
            
            for lib_path in lib_paths:
                lib_path = lib_path.replace('\\\\', '\\')
                lib_common = os.path.join(lib_path, "steamapps", "common")
                if os.path.isdir(lib_common):
                    paths.add(lib_common)
                    
    except Exception:
        # Fall back to default path if registry access fails
        pass
        
    return list(paths)

def get_epic_paths() -> List[str]:
    """Get Epic Games installation paths.
    
    Returns:
        List of Epic Games paths
    """
    paths = {EPIC_COMMON_DIR}
    
    try:
        # Check registry uninstall keys for Epic games
        uninstall_key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"
        )
        
        i = 0
        while True:
            try:
                subkey_name = winreg.EnumKey(uninstall_key, i)
                subkey_path = os.path.join(uninstall_key.name, subkey_name)
                
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, subkey_path) as subkey:
                    try:
                        publisher = winreg.QueryValueEx(subkey, "Publisher")[0]
                        if "Epic Games" in publisher:
                            install_loc = winreg.QueryValueEx(subkey, "InstallLocation")[0]
                            if os.path.isdir(install_loc):
                                paths.add(install_loc)
                    except FileNotFoundError:
                        pass
                i += 1
            except OSError:
                break
                
        winreg.CloseKey(uninstall_key)
        
    except Exception:
        # Fall back to default path if registry access fails
        pass
        
    return list(paths)

def get_xbox_paths() -> List[str]:
    """Get Xbox game installation paths.
    
    Returns:
        List of Xbox game paths
    """
    paths = {XBOX_GAMES_DIR}
    
    try:
        # Check WindowsApps directory in ProgramFiles
        xbox_paths = glob.glob(r"C:\Program Files\WindowsApps\*\*")
        for path in xbox_paths:
            if os.path.isdir(path):
                paths.add(path)
                
    except Exception:
        # Fall back to default path if access fails
        pass
        
    return list(paths)

def is_nvidia_gpu() -> bool:
    """Check if system has NVIDIA GPU.
    
    Returns:
        bool: True if NVIDIA GPU detected
    """
    return os.path.exists(NVIDIA_CHECK_FILE)

def normalize_path(path: str) -> str:
    """Normalize a file system path.
    
    Args:
        path: Path to normalize
        
    Returns:
        Normalized path string
    """
    return os.path.normpath(path)

def resolve_relative_path(base_path: str, relative_path: str) -> str:
    """Resolve a relative path against a base path.
    
    Args:
        base_path: Base path to resolve against
        relative_path: Relative path to resolve
        
    Returns:
        Absolute path string
    """
    return os.path.normpath(os.path.join(base_path, relative_path))

def find_exe_in_path(path: str) -> Tuple[str, str]:
    """Find an executable in a path.
    
    Args:
        path: Path to search
        
    Returns:
        Tuple of (exe_path, exe_name)
    """
    if not os.path.isdir(path):
        return "", ""
        
    exe_files = glob.glob(os.path.join(path, "*.exe"))
    if not exe_files:
        return "", ""
        
    # Get largest executable (likely the main game exe)
    largest_exe = ""
    largest_size = 0
    
    for exe_file in exe_files:
        try:
            size = os.path.getsize(exe_file)
            if size > largest_size:
                largest_size = size
                largest_exe = exe_file
        except Exception:
            continue
            
    if largest_exe:
        return largest_exe, os.path.basename(largest_exe)
        
    return "", ""

def check_file_access(path: str) -> bool:
    """Check if a file can be accessed for reading/writing.
    
    Args:
        path: Path to check
        
    Returns:
        bool: True if file is accessible
    """
    try:
        # Try to open for both reading and writing
        with open(path, 'ab+') as f:
            f.seek(0)
            f.read(1)
        return True
    except Exception:
        return False

def create_directory(path: str) -> bool:
    """Create a directory and any necessary parents.
    
    Args:
        path: Path to create
        
    Returns:
        bool: True if successful
    """
    try:
        os.makedirs(path, exist_ok=True)
        return True
    except Exception:
        return False

def get_file_type(path: str) -> Optional[str]:
    """Get the type of a file.
    
    Args:
        path: Path to check
        
    Returns:
        String describing file type or None
    """
    try:
        if os.path.isfile(path):
            _, ext = os.path.splitext(path)
            return ext.lower() if ext else None
        elif os.path.isdir(path):
            return 'directory'
        else:
            return None
    except Exception:
        return None