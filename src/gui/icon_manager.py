"""
Icon Manager - Sistema centralizado de gestión de iconos
Permite cambiar fácilmente entre emojis y iconos personalizados (PNG/SVG)
"""

import os
import sys
import customtkinter as ctk
from pathlib import Path

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("Warning: PIL no disponible, solo se usarán emojis")


class IconManager:
    """
    Gestiona todos los iconos de la aplicación.
    Soporta emojis (por defecto) e imágenes personalizadas (PNG/SVG).
    """
    
    # Mapa de emojis por defecto (fallback universal)
    EMOJI_MAP = {
        # Interfaz general
        "help": "?",
        "gaming_mode": "🎮",
        "download": "⬇️",
        "folder_open": "📂",
        "folder_file": "📁",
        "filter": "🔽",  # Icono de filtro (embudo)
        
        # Modo Gaming - Navegación
        "nav_config": "⚙️",
        "nav_auto": "🎯",
        "nav_manual": "📁",
        "nav_settings": "🔧",
        
        # Modo Gaming - Acciones por juego
        "game_config": "⚙️",
        "game_folder": "📁",
        "game_launch": "🚀",
        
        # Modo Gaming - Acciones globales
        "apply_mod": "✔️",
        "exit_gaming": "←",
        
        # Otros
        "add": "➕",
        "rescan": "🔄",
        "status_ok": "●",
        "status_error": "●",
        "status_none": "●",
    }
    
    # Tamaños de fuente para emojis (ajustables por tipo de icono)
    EMOJI_SIZES = {
        "small": 20,      # Botones pequeños
        "medium": 24,     # Botones estándar
        "large": 28,      # Botones grandes (gaming)
        "xlarge": 32,     # Navegación lateral
    }
    
    def __init__(self, use_custom_icons=False, icons_dir=None):
        """
        Inicializa el gestor de iconos.
        
        Args:
            use_custom_icons: Si True, intentará cargar iconos personalizados
            icons_dir: Ruta a la carpeta de iconos personalizados
        """
        self.use_custom = use_custom_icons and PIL_AVAILABLE
        self.icons_dir = icons_dir or self._get_default_icons_dir()
        self.custom_icons = {}
        self._image_references = []  # Mantener referencias a las imágenes PIL
        
        if self.use_custom:
            self._load_custom_icons()
    
    def _get_default_icons_dir(self):
        """Obtiene la ruta por defecto de la carpeta de iconos."""
        # Detectar si estamos en un ejecutable compilado.
        # PyInstaller uses sys._MEIPASS. Nuitka onefile may extract data next to the
        # executable directory. Try multiple likely locations and fall back to
        # the project `icons/` when running from source.
        possible = []
        try:
            if getattr(sys, 'frozen', False):
                # PyInstaller
                if hasattr(sys, '_MEIPASS'):
                    possible.append(Path(sys._MEIPASS) / "icons")
                # Nuitka onefile (extracted next to the executable in many setups)
                try:
                    possible.append(Path(os.path.dirname(sys.executable)) / "icons")
                except Exception:
                    pass
        except Exception:
            pass

        # When running as script, assume project-root/icons
        try:
            current_file = Path(__file__).resolve()
            project_root = current_file.parent.parent.parent
            possible.append(project_root / "icons")
        except Exception:
            pass

        # Return the first existing candidates, otherwise default to the first candidate
        for p in possible:
            try:
                if p.exists():
                    return p
            except Exception:
                pass

        # If nothing exists, return the first candidate (useful for diagnostic logs)
        return possible[0] if possible else Path("icons")
    
    def _load_custom_icons(self):
        """Carga iconos personalizados desde la carpeta icons/."""
        if not self.icons_dir.exists():
            print(f"Info: Carpeta de iconos no encontrada en {self.icons_dir}")
            return
        
        icon_files = {
            # Mapeo: nombre_icono -> archivo
            "help": "help.png",
            "gaming_mode": "gaming.png",
            "download": "download.png",
            "folder_open": "folder_open.png",
            "folder_file": "folder.png",
            "filter": "filter.png",  # Icono de filtro personalizado
            "nav_config": "config.png",
            "nav_auto": "auto.png",
            "nav_manual": "manual.png",
            "nav_settings": "settings.png",
            "game_config": "config.png",
            "game_folder": "folder.png",
            "game_launch": "launch.png",
            "apply_mod": "apply.png",
            "exit_gaming": "exit.png",
            "add": "add.png",
            "rescan": "rescan.png",
        }
        
        for icon_name, filename in icon_files.items():
            icon_path = self.icons_dir / filename
            if icon_path.exists():
                try:
                    # Cargar imagen con PIL
                    pil_image = Image.open(str(icon_path))
                    pil_image.load()  # Forzar carga completa en memoria
                    # Guardar referencia a la imagen PIL
                    self._image_references.append(pil_image)
                    # Crear CTkImage
                    self.custom_icons[icon_name] = ctk.CTkImage(
                        light_image=pil_image,
                        dark_image=pil_image,
                        size=(32, 32)  # Tamaño por defecto
                    )
                except Exception as e:
                    print(f"Error al cargar icono {filename}: {e}")
    
    def get_icon(self, name, size="medium", as_image=False):
        """
        Obtiene un icono (emoji o CTkImage).
        
        Args:
            name: Nombre del icono (ej: "game_launch")
            size: Tamaño del emoji ("small", "medium", "large", "xlarge")
            as_image: Si True, retorna CTkImage si está disponible; si False, siempre emoji
        
        Returns:
            str (emoji) o CTkImage (si use_custom=True y as_image=True)
        """
        # Si se solicita imagen y hay icono personalizado disponible
        if as_image and self.use_custom and name in self.custom_icons:
            return self.custom_icons[name]
        
        # Fallback a emoji
        return self.EMOJI_MAP.get(name, "●")
    
    def get_emoji_size(self, size="medium"):
        """Obtiene el tamaño de fuente para un emoji."""
        return self.EMOJI_SIZES.get(size, 24)
    
    def load_icon(self, filename, size=(32, 32)):
        """
        Carga un icono directamente desde un archivo.
        
        Args:
            filename: Nombre del archivo (ej: "embudo.png")
            size: Tupla (width, height) para el tamaño del icono
        
        Returns:
            CTkImage o None si no se puede cargar
        """
        if not PIL_AVAILABLE:
            return None
        
        icon_path = self.icons_dir / filename
        if not icon_path.exists():
            print(f"Info: Icono {filename} no encontrado en {self.icons_dir}")
            return None
        
        try:
            pil_image = Image.open(str(icon_path))
            pil_image.load()  # Forzar carga completa
            self._image_references.append(pil_image)
            return ctk.CTkImage(
                light_image=pil_image,
                dark_image=pil_image,
                size=size
            )
        except Exception as e:
            print(f"Error al cargar icono {filename}: {e}")
            return None
    
    def set_icon_size(self, icon_name, width, height):
        """
        Ajusta el tamaño de un icono personalizado específico.
        
        Args:
            icon_name: Nombre del icono
            width: Ancho en píxeles
            height: Alto en píxeles
        """
        if icon_name in self.custom_icons:
            # Recargar con nuevo tamaño
            icon_path = self.icons_dir / f"{icon_name}.png"
            if icon_path.exists():
                try:
                    pil_image = Image.open(str(icon_path))
                    pil_image.load()
                    self._image_references.append(pil_image)
                    self.custom_icons[icon_name] = ctk.CTkImage(
                        light_image=pil_image,
                        dark_image=pil_image,
                        size=(width, height)
                    )
                except Exception as e:
                    print(f"Error al redimensionar icono {icon_name}: {e}")
    
    def enable_custom_icons(self):
        """Activa el uso de iconos personalizados."""
        if PIL_AVAILABLE:
            self.use_custom = True
            self._load_custom_icons()
        else:
            print("Error: PIL no disponible, no se pueden usar iconos personalizados")
    
    def disable_custom_icons(self):
        """Desactiva iconos personalizados (vuelve a emojis)."""
        self.use_custom = False
    
    def get_status_color(self, status_type):
        """
        Obtiene el color para un indicador de estado.
        
        Args:
            status_type: "ok", "error", o "none"
        
        Returns:
            str: Color en formato hex
        """
        colors = {
            "ok": "#00FF00",      # Verde
            "error": "#FF0000",   # Rojo
            "none": "gray"        # Gris
        }
        return colors.get(status_type, "gray")


# Instancia global (singleton) del gestor de iconos
_icon_manager_instance = None

def get_icon_manager(use_custom_icons=False, icons_dir=None):
    """
    Obtiene la instancia global del IconManager (patrón Singleton).
    
    Args:
        use_custom_icons: Si True, usa iconos personalizados (solo primera llamada)
        icons_dir: Ruta personalizada a carpeta de iconos (solo primera llamada)
    
    Returns:
        IconManager: Instancia del gestor de iconos
    """
    global _icon_manager_instance
    if _icon_manager_instance is None:
        _icon_manager_instance = IconManager(use_custom_icons, icons_dir)
    return _icon_manager_instance
