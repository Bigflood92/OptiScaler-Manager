"""Configuration management for FSR Injector."""

import os
import json
from typing import Dict, Any, List, Optional, Callable
from ..utils.error_handling import ConfigurationError, error_handler
from ..config.constants import CONFIG_FILE, CUSTOM_SEARCH_FOLDERS_CONFIG_KEY

class ConfigManager:
    """Manages FSR Injector configuration."""
    
    def __init__(self, logger: Optional[Callable] = None):
        """Initialize the configuration manager.
        
        Args:
            logger: Optional logging function to use
        """
        self.logger = logger or print
        self.config = {
            "gpu_choice": None,
            "spoof_dll_name": None,
            "fg_mode": "Automático",
            "upscale_mode": "Automático",
            "sharpness": 0.8,
            "overlay": False,
            "motion_blur": True,
            CUSTOM_SEARCH_FOLDERS_CONFIG_KEY: []
        }
        
    @error_handler()
    def load_config(self) -> bool:
        """Load configuration from file.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r') as f:
                    saved_config = json.load(f)
                    
                # Update config with saved values
                self.config.update(saved_config)
                
                self.logger('INFO', "Configuration loaded successfully")
                return True
            else:
                self.logger('INFO', "No configuration file found, using defaults")
                return False
                
        except json.JSONDecodeError as e:
            raise ConfigurationError(f"Invalid configuration file format: {e}")
        except Exception as e:
            raise ConfigurationError(f"Failed to load configuration: {e}")
            
    @error_handler()
    def save_config(self) -> bool:
        """Save current configuration to file.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(self.config, f, indent=4)
                
            self.logger('INFO', "Configuration saved successfully")
            return True
            
        except Exception as e:
            raise ConfigurationError(f"Failed to save configuration: {e}")
            
    def get_config(self) -> Dict[str, Any]:
        """Get current configuration.
        
        Returns:
            Dict containing current configuration
        """
        return self.config.copy()
        
    def update_config(self, updates: Dict[str, Any]) -> None:
        """Update configuration with new values.
        
        Args:
            updates: Dictionary of configuration updates
        """
        self.config.update(updates)
        self.save_config()
        
    def get_custom_folders(self) -> List[str]:
        """Get list of custom search folders.
        
        Returns:
            List of custom folder paths
        """
        return self.config.get(CUSTOM_SEARCH_FOLDERS_CONFIG_KEY, [])
        
    def add_custom_folder(self, folder_path: str) -> bool:
        """Add a custom search folder.
        
        Args:
            folder_path: Path to add
            
        Returns:
            bool: True if added, False if already exists
        """
        folders = self.get_custom_folders()
        if folder_path not in folders:
            folders.append(folder_path)
            self.config[CUSTOM_SEARCH_FOLDERS_CONFIG_KEY] = folders
            self.save_config()
            return True
        return False
        
    def remove_custom_folder(self, folder_path: str) -> bool:
        """Remove a custom search folder.
        
        Args:
            folder_path: Path to remove
            
        Returns:
            bool: True if removed, False if not found
        """
        folders = self.get_custom_folders()
        if folder_path in folders:
            folders.remove(folder_path)
            self.config[CUSTOM_SEARCH_FOLDERS_CONFIG_KEY] = folders
            self.save_config()
            return True
        return False
        
    def get_gpu_choice(self) -> int:
        """Get GPU choice setting.
        
        Returns:
            int: GPU choice (1=AMD/Intel, 2=NVIDIA)
        """
        return self.config.get("gpu_choice", 2)
        
    def set_gpu_choice(self, choice: int) -> None:
        """Set GPU choice setting.
        
        Args:
            choice: GPU choice to set
        """
        if choice not in [1, 2]:
            raise ConfigurationError("Invalid GPU choice")
        self.config["gpu_choice"] = choice
        self.save_config()
        
    def get_spoof_dll(self) -> str:
        """Get spoofing DLL name.
        
        Returns:
            str: Name of DLL to use
        """
        return self.config.get("spoof_dll_name", "dxgi.dll")
        
    def set_spoof_dll(self, dll_name: str) -> None:
        """Set spoofing DLL name.
        
        Args:
            dll_name: Name of DLL to use
        """
        self.config["spoof_dll_name"] = dll_name
        self.save_config()
        
    def get_frame_gen_mode(self) -> str:
        """Get frame generation mode.
        
        Returns:
            str: Current frame generation mode
        """
        return self.config.get("fg_mode", "Automático")
        
    def set_frame_gen_mode(self, mode: str) -> None:
        """Set frame generation mode.
        
        Args:
            mode: Mode to set
        """
        self.config["fg_mode"] = mode
        self.save_config()
        
    def get_upscale_mode(self) -> str:
        """Get upscaling mode.
        
        Returns:
            str: Current upscaling mode
        """
        return self.config.get("upscale_mode", "Automático")
        
    def set_upscale_mode(self, mode: str) -> None:
        """Set upscaling mode.
        
        Args:
            mode: Mode to set
        """
        self.config["upscale_mode"] = mode
        self.save_config()
        
    def get_sharpness(self) -> float:
        """Get sharpness value.
        
        Returns:
            float: Current sharpness value
        """
        return float(self.config.get("sharpness", 0.8))
        
    def set_sharpness(self, value: float) -> None:
        """Set sharpness value.
        
        Args:
            value: Sharpness value to set
        """
        if not 0.0 <= value <= 2.0:
            raise ConfigurationError("Sharpness value must be between 0.0 and 2.0")
        self.config["sharpness"] = value
        self.save_config()
        
    def get_overlay_enabled(self) -> bool:
        """Get overlay enabled status.
        
        Returns:
            bool: True if enabled, False otherwise
        """
        return bool(self.config.get("overlay", False))
        
    def set_overlay_enabled(self, enabled: bool) -> None:
        """Set overlay enabled status.
        
        Args:
            enabled: True to enable, False to disable
        """
        self.config["overlay"] = enabled
        self.save_config()
        
    def get_motion_blur_enabled(self) -> bool:
        """Get motion blur enabled status.
        
        Returns:
            bool: True if enabled, False otherwise
        """
        return bool(self.config.get("motion_blur", True))
        
    def set_motion_blur_enabled(self, enabled: bool) -> None:
        """Set motion blur enabled status.
        
        Args:
            enabled: True to enable, False to disable
        """
        self.config["motion_blur"] = enabled
        self.save_config()