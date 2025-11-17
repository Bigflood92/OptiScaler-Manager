

"""
Gaming Mode App - Interfaz principal de la aplicación.

Estructura:
- Sidebar izquierdo con 4 iconos (Config, Auto, Manual, Ajustes)
- 4 paneles intercambiables:
  1. ⚙️ Configuración del Mod (presets + config global)
  2. 🎮 Detección Automática (lista juegos)
  3. 📁 Ruta Manual
  4. 🔧 Ajustes de la App
"""

import os
import sys
import platform
import subprocess
import webbrowser
from pathlib import Path
from datetime import datetime
import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading
import pygame
import time

# Imports de módulos core
from ..core.scanner import scan_games, invalidate_scan_cache
from ..core.config_manager import load_config, save_config
from ..core.installer import inject_fsr_mod, uninstall_fsr_mod, install_combined_mods, install_optipatcher, uninstall_optipatcher
from ..core.mod_detector import compute_game_mod_status, get_version_badge_info
from ..core.utils import detect_gpu_vendor, should_use_dual_mod
from ..core.github import GitHubClient
from ..utils.logging import LogManager
from ..config.paths import MOD_SOURCE_DIR, OPTISCALER_DIR, DLSSG_TO_FSR3_DIR, SEVEN_ZIP_PATH, APP_DIR, get_config_dir
from .components.windows.welcome_tutorial import WelcomeTutorial, should_show_tutorial
from .components.collapsible_section import CollapsibleSection
from .components.wide_combobox import WideComboBox

# Constantes
APP_VERSION = "2.4.0"
APP_TITLE = f"GESTOR AUTOMATIZADO DE OPTISCALER V{APP_VERSION}"

# Colores para feedback visual
COLOR_PRIMARY = "#00BFFF"
COLOR_PRIMARY_HOVER = "#00D4FF"
COLOR_SECONDARY = "#3a3a3a"
COLOR_SECONDARY_HOVER = "#4a4a4a"
COLOR_SUCCESS = "#00FF00"
COLOR_WARNING = "#FFA500"
COLOR_ERROR = "#FF4444"
COLOR_SELECTED = "#005080"
COLOR_FOCUS = "#00BFFF"

# Tamaños de fuente estandarizados para handheld PC
FONT_TITLE = 20          # Títulos principales
FONT_SECTION = 16        # Títulos de sección
FONT_NORMAL = 13         # Texto normal, botones
FONT_SMALL = 11          # Detalles, labels secundarios
FONT_TINY = 10           # Info muy pequeña


class GamingApp(ctk.CTk):

    def mark_preset_custom(self):
        """Marca el preset activo como 'Custom' sin restaurar snapshot previo.
        Se invoca en modificaciones manuales para no perder el cambio recién hecho."""
        if getattr(self, '_suppress_custom', False):
            return
        # Resaltar botón Custom y quitar bordes de otros
        if hasattr(self, 'preset_buttons'):
            for key, btn in self.preset_buttons.items():
                if key == 'custom':
                    color, width = self.preset_borders.get('custom', ("#B0BEC5", 3))
                    btn.configure(border_width=width, border_color=color)
                else:
                    btn.configure(border_width=0)
        if hasattr(self, 'active_preset_label'):
            self.active_preset_label.configure(text="✏️ Custom")

    def update_custom_state(self):
        """Guarda la configuración actual como estado del preset Custom si está activo."""
        if getattr(self, '_suppress_custom', False):
            return
        if not hasattr(self, 'active_preset_label'):
            return
        if self.active_preset_label.cget('text') != '✏️ Custom':
            return
        self.custom_preset_state = {
            'fg_mode': self.fg_mode_var.get(),
            'upscale_mode': self.upscale_mode_var.get(),
            'upscaler': self.upscaler_var.get(),
            'sharpness': self.sharpness_var.get(),
            'fps_limit': self.fps_limit_var.get(),
            'dll_name': self.dll_name_var.get(),
            # HDR Settings
            'auto_hdr': self.auto_hdr_var.get(),
            'nvidia_hdr_override': self.nvidia_hdr_override_var.get(),
            'hdr_rgb_range': self.hdr_rgb_range_var.get(),
            # Debug/Logging
            'log_level': self.log_level_var.get(),
            'open_console': self.open_console_var.get(),
            'log_to_file': self.log_to_file_var.get(),
            # Quality Overrides
            'quality_override_enabled': self.quality_override_enabled_var.get(),
            'quality_ratio': self.quality_ratio_var.get(),
            'balanced_ratio': self.balanced_ratio_var.get(),
            'performance_ratio': self.performance_ratio_var.get(),
            'ultra_perf_ratio': self.ultra_perf_ratio_var.get(),
            # CAS Sharpening
            'cas_enabled': self.cas_enabled_var.get(),
            'cas_type': self.cas_type_var.get(),
            'cas_sharpness': self.cas_sharpness_var.get(),
            # NVNGX Spoofing
            'nvngx_dx12': self.nvngx_dx12_var.get(),
            'nvngx_dx11': self.nvngx_dx11_var.get(),
            'nvngx_vulkan': self.nvngx_vulkan_var.get(),
            # Overlay Settings
            'overlay_mode': self.overlay_mode_var.get(),
            'overlay_show_fps': self.overlay_show_fps_var.get(),
            'overlay_show_frametime': self.overlay_show_frametime_var.get(),
            'overlay_show_messages': self.overlay_show_messages_var.get(),
            'overlay_position': self.overlay_position_var.get(),
            'overlay_scale': self.overlay_scale_var.get(),
            'overlay_font_size': self.overlay_font_size_var.get()
        }
    """Aplicación Gaming Mode - Interfaz completa."""
    
    def __init__(self):
        super().__init__()

        # Configuración ventana
        self.title(APP_TITLE)
        self.geometry("1400x800")
        self.minsize(1000, 600)
        
        # Tema
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")
        
        # Logger
        self.log_manager = LogManager()
        self.log = lambda level, msg: self.log_manager.log_to_ui(level, msg)
        
        # Variables para navegación con gamepad
        self.current_focused_widget = None
        self.focus_zone = 'sidebar'  # 'sidebar' o 'content'
        self.slider_active = False  # True cuando un slider está siendo ajustado
        
        # Detectar GPU automáticamente
        self.gpu_vendor = detect_gpu_vendor()
        self.use_dual_mod = should_use_dual_mod(self.gpu_vendor)
        
        gpu_names = {
            'nvidia': 'NVIDIA',
            'amd': 'AMD',
            'intel': 'Intel',
            'unknown': 'Desconocida'
        }
        gpu_name = gpu_names.get(self.gpu_vendor, 'Desconocida')
        mod_mode = "Dual-Mod (OptiScaler + Frame Gen)" if self.use_dual_mod else "OptiScaler solo"
        
        self.log('INFO', f"GPU detectada: {gpu_name}")
        self.log('INFO', f"Modo de instalación: {mod_mode}")
        
        # Cargar configuración
        self.config = load_config()
        
        # Asegurar que exista la lista de carpetas personalizadas
        if "custom_game_folders" not in self.config:
            self.config["custom_game_folders"] = []
        
        # Variables
        self.games_data = {}  # {game_path: (name, status, exe, platform)}
        self.selected_games = set()  # Paths de juegos seleccionados
        
        # Variables de filtrado
        self.filter_platform = ctk.StringVar(value="Todas")
        self.filter_mod_status = ctk.StringVar(value="Todos")
        self.filter_search = ctk.StringVar(value="")
        self.active_filters = {"platform": "Todas", "mod_status": "Todos", "search": ""}
        
        # Variables de GUI
        self.theme_var = ctk.StringVar(value="Oscuro")
        self.scale_var = ctk.StringVar(value="100%")
        self.mod_version_list = ctk.StringVar(value="[Ninguna versión descargada]")
        self.manual_path_var = ctk.StringVar(value="Ninguna carpeta seleccionada")
        self.manual_status_var = ctk.StringVar(value="")
        
        # Variables de configuración del mod
        self.gpu_var = ctk.IntVar(value=self.config.get("gpu_choice", 2))
        self.fg_mode_var = ctk.StringVar(value=self.config.get("fg_mode", "Desactivado"))
        self.upscale_mode_var = ctk.StringVar(value=self.config.get("upscale_mode", "Automático"))
        self.upscaler_var = ctk.StringVar(value="Automático")
        self.dll_name_var = ctk.StringVar(value=self.config.get("last_spoof_name", "dxgi.dll"))
        self.fps_limit_var = ctk.IntVar(value=self.config.get("fps_limit", 0))
        self.sharpness_var = ctk.DoubleVar(value=self.config.get("sharpness", 0.5))
        self.overlay_var = ctk.StringVar(value=self.config.get("overlay", "Desactivado"))
        self.mb_var = ctk.StringVar(value=self.config.get("motion_blur", "Activado"))
        # Opciones avanzadas nuevas
        self.native_aa_var = ctk.BooleanVar(value=self.config.get("use_native_aa", True))
        self.mipmap_bias_var = ctk.DoubleVar(value=self.config.get("mipmap_bias", 0.0))
        
        # Overlay Settings variables
        self.overlay_mode_var = ctk.StringVar(value=self.config.get("overlay_mode", "Desactivado"))  # Desactivado/Básico/Completo
        self.overlay_show_fps_var = ctk.BooleanVar(value=self.config.get("overlay_show_fps", True))
        self.overlay_show_frametime_var = ctk.BooleanVar(value=self.config.get("overlay_show_frametime", True))
        self.overlay_show_messages_var = ctk.BooleanVar(value=self.config.get("overlay_show_messages", True))
        self.overlay_position_var = ctk.StringVar(value=self.config.get("overlay_position", "Superior Izquierda"))
        self.overlay_scale_var = ctk.DoubleVar(value=self.config.get("overlay_scale", 1.0))
        self.overlay_font_size_var = ctk.IntVar(value=self.config.get("overlay_font_size", 14))
        
        # HDR Settings variables
        self.auto_hdr_var = ctk.BooleanVar(value=self.config.get("auto_hdr", True))
        self.nvidia_hdr_override_var = ctk.BooleanVar(value=self.config.get("nvidia_hdr_override", False))
        self.hdr_rgb_range_var = ctk.DoubleVar(value=self.config.get("hdr_rgb_range", 100.0))
        
        # Debug/Logging variables
        self.log_level_var = ctk.StringVar(value=self.config.get("log_level", "Info"))
        self.open_console_var = ctk.BooleanVar(value=self.config.get("open_console", False))
        self.log_to_file_var = ctk.BooleanVar(value=self.config.get("log_to_file", True))
        
        # Quality Overrides variables
        self.quality_override_enabled_var = ctk.BooleanVar(value=self.config.get("quality_override_enabled", False))
        self.quality_ratio_var = ctk.DoubleVar(value=self.config.get("quality_ratio", 1.5))
        self.balanced_ratio_var = ctk.DoubleVar(value=self.config.get("balanced_ratio", 1.7))
        self.performance_ratio_var = ctk.DoubleVar(value=self.config.get("performance_ratio", 2.0))
        self.ultra_perf_ratio_var = ctk.DoubleVar(value=self.config.get("ultra_perf_ratio", 3.0))
        
        # CAS Sharpening variables
        self.cas_enabled_var = ctk.BooleanVar(value=self.config.get("cas_enabled", False))
        self.cas_sharpness_var = ctk.DoubleVar(value=self.config.get("cas_sharpness", 0.5))
        self.cas_type_var = ctk.StringVar(value=self.config.get("cas_type", "RCAS"))  # "RCAS" o "CAS"
        
        # NVNGX Spoofing variables (por defecto todos activados)
        self.nvngx_dx12_var = ctk.BooleanVar(value=self.config.get("nvngx_dx12", True))
        self.nvngx_dx11_var = ctk.BooleanVar(value=self.config.get("nvngx_dx11", True))
        self.nvngx_vulkan_var = ctk.BooleanVar(value=self.config.get("nvngx_vulkan", True))
        
        # Flag para suprimir cambio a Custom durante aplicación programática de presets
        self._suppress_custom = False
        # Estado persistente de configuración personalizada
        self.custom_preset_state = {}

        # Cargar iconos
        self.load_icons()
        
        # Inicializar sistema de gamepad
        self.gamepad_connected = False
        self.gamepad = None
        self.gamepad_thread = None
        self.gamepad_running = False
        # BUGFIX: Mover init_gamepad a after() para evitar "main thread is not in main loop"
        # Error ocurre porque pygame.event.pump() se llama antes que mainloop() arranque
        self.after(500, self.init_gamepad)
        
        # Grid configuration
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        
        # Crear UI (SIN header - igual que legacy)
        self.create_sidebar()
        self.create_content_area()
        self.create_panels()
        
        # Mostrar panel de detección automática por defecto
        self.show_panel("auto")
        
        # Actualizar visibilidad de config al inicio
        self.update_config_visibility()
        
        # Protocolo cierre
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Configurar navegación con teclado
        self.setup_keyboard_navigation()
        
        # Establecer foco inicial en botón de auto-detección
        self.after(100, self.set_initial_focus)
        
        # Mostrar tutorial de bienvenida si es la primera vez
        self.after(500, self.show_welcome_if_needed)
        
        # Verificar actualizaciones de la aplicación
        self.after(1500, self.check_app_updates)

    # ==================================================================================
    # ICONOS Y RECURSOS
    # ==================================================================================
    
    def load_icons(self):
        """Carga todos los iconos de la aplicación."""
        self.icons = {}
        
        # Cargar iconos PNG (funciona tanto en script como en .exe)
        try:
            from PIL import Image
            
            # Detectar ruta correcta según si estamos en ejecutable o script
            if getattr(sys, 'frozen', False):
                # Ejecutando en .exe compilado (PyInstaller o Nuitka)
                if hasattr(sys, '_MEIPASS'):
                    # PyInstaller
                    icons_dir = os.path.join(sys._MEIPASS, "icons")
                else:
                    # Nuitka
                    icons_dir = os.path.join(os.path.dirname(sys.executable), "icons")
            else:
                # Ejecutando como script Python
                icons_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "icons")
            
            icon_files = {
                "scan": "rescan.png",
                "filter": "filter.png",
                "auto": "auto.png",
                "rescan": "rescan.png"
            }
            
            for key, filename in icon_files.items():
                try:
                    icon_path = os.path.join(icons_dir, filename)
                    if os.path.exists(icon_path):
                        # Tamaño grande para botones principales (scan, filter)
                        size = (40, 40) if key in ["scan", "filter"] else (48, 48)
                        self.icons[key] = ctk.CTkImage(
                            light_image=Image.open(icon_path),
                            dark_image=Image.open(icon_path),
                            size=size
                        )
                    else:
                        self.icons[key] = None
                except Exception as e:
                    self.log('WARNING', f"No se pudo cargar icono {filename}: {e}")
                    self.icons[key] = None
        except Exception as e:
            self.log('WARNING', f"Error al cargar iconos: {e}")
    
    # ==================================================================================
    # SISTEMA DE GAMEPAD
    # ==================================================================================
    
    def setup_keyboard_navigation(self):
        """Configura navegación con teclado (mismo comportamiento que gamepad)."""
        # Flechas de navegación
        self.bind("<Up>", lambda e: self.on_keyboard_arrow('up'))
        self.bind("<Down>", lambda e: self.on_keyboard_arrow('down'))
        self.bind("<Left>", lambda e: self.on_keyboard_arrow('left'))
        self.bind("<Right>", lambda e: self.on_keyboard_arrow('right'))
        
        # Enter = A (aceptar/activar)
        self.bind("<Return>", lambda e: self.on_keyboard_button('enter'))
        
        # Escape = B (volver/cancelar)
        self.bind("<Escape>", lambda e: self.on_keyboard_button('escape'))
        
        # Tab y Shift+Tab ya funcionan nativamente para navegación
        # pero vamos a interceptarlos para respetar las zonas de foco
        # (comentado para mantener comportamiento nativo de Tab por ahora)
        
        self.log('INFO', "Navegación con teclado configurada (Flechas, Enter, Esc)")
    
    def on_keyboard_arrow(self, direction):
        """Maneja eventos de flechas del teclado.
        
        Args:
            direction: 'up', 'down', 'left', 'right'
        """
        # Usar la misma lógica que gamepad
        self.navigate_focus(direction)
        return "break"  # Prevenir comportamiento por defecto
    
    def on_keyboard_button(self, button):
        """Maneja eventos de botones especiales del teclado.
        
        Args:
            button: 'enter' (A) o 'escape' (B)
        """
        if button == 'enter':
            # Enter = A (aceptar/activar)
            self.gamepad_button_press('A')
        elif button == 'escape':
            # Escape = B (volver/cancelar)
            self.gamepad_button_press('B')
        
        return "break"  # Prevenir comportamiento por defecto
    
    def init_gamepad(self):
        """Inicializa pygame y comienza monitoreo de gamepad."""
        try:
            pygame.init()
            pygame.joystick.init()
            self.log('INFO', "Sistema de gamepad inicializado")
            
            # Iniciar thread de monitoreo
            self.gamepad_running = True
            self.gamepad_thread = threading.Thread(target=self.monitor_gamepad, daemon=True)
            self.gamepad_thread.start()
        except Exception as e:
            self.log('ERROR', f"Error al inicializar gamepad: {e}")
    
    def monitor_gamepad(self):
        """Thread que monitorea conexión/desconexión de gamepad."""
        last_gamepad_count = 0
        
        while self.gamepad_running:
            try:
                pygame.event.pump()  # Actualizar eventos de pygame
                current_count = pygame.joystick.get_count()
                
                # Detectar cambios en conexión
                if current_count > 0 and not self.gamepad_connected:
                    self.gamepad = pygame.joystick.Joystick(0)
                    self.gamepad.init()
                    self.gamepad_connected = True
                    gamepad_name = self.gamepad.get_name()
                    self.after(0, lambda: self.log('SUCCESS', f"🎮 Gamepad conectado: {gamepad_name}"))
                    self.after(0, self.update_gamepad_indicator)
                    self.after(0, self.start_gamepad_input_loop)
                    
                elif current_count == 0 and self.gamepad_connected:
                    self.gamepad_connected = False
                    self.gamepad = None
                    self.after(0, lambda: self.log('WARNING', "🎮 Gamepad desconectado"))
                    self.after(0, self.update_gamepad_indicator)
                
                last_gamepad_count = current_count
                time.sleep(0.5)  # Check cada 500ms
                
            except Exception as e:
                self.log('ERROR', f"Error en monitor de gamepad: {e}")
                time.sleep(1)
    
    def start_gamepad_input_loop(self):
        """Inicia el loop de lectura de inputs del gamepad."""
        if self.gamepad_connected:
            self.process_gamepad_input()
    
    def process_gamepad_input(self):
        """Procesa inputs del gamepad con acceso seguro y throttling de errores."""
        if not self.gamepad_connected or not self.gamepad:
            return

        try:
            pygame.event.pump()

            # Helpers seguros (evita excepciones en dispositivos con menos botones/ejes)
            def safe_btn(idx):
                try:
                    return idx < self.gamepad.get_numbuttons() and self.gamepad.get_button(idx)
                except Exception as e:
                    raise e
            def safe_axis(idx):
                try:
                    return idx < self.gamepad.get_numaxes() and self.gamepad.get_axis(idx)
                except Exception as e:
                    raise e

            # Navegación
            if self.gamepad.get_hat(0)[1] == 1 or safe_axis(1) < -0.5:
                self.navigate_focus('up')
            elif self.gamepad.get_hat(0)[1] == -1 or safe_axis(1) > 0.5:
                self.navigate_focus('down')
            elif self.gamepad.get_hat(0)[0] == -1 or safe_axis(0) < -0.5:
                self.navigate_focus('left')
            elif self.gamepad.get_hat(0)[0] == 1 or safe_axis(0) > 0.5:
                self.navigate_focus('right')

            # Botones acción
            if safe_btn(0):
                self.gamepad_button_press('A'); time.sleep(0.15)
            if safe_btn(1):
                self.gamepad_button_press('B'); time.sleep(0.2)
            if safe_btn(2):
                self.gamepad_button_press('X'); time.sleep(0.2)
            if safe_btn(3):
                self.gamepad_button_press('Y'); time.sleep(0.2)

            # Bumpers
            if safe_btn(4):
                self.navigate_tabs(-1); time.sleep(0.3)
            if safe_btn(5):
                self.navigate_tabs(1); time.sleep(0.3)

            # Triggers (scroll)
            ax2 = safe_axis(2)
            if ax2 and ax2 > 0.5:
                self.quick_scroll(-200)
            ax5 = safe_axis(5)
            if ax5 and ax5 > 0.5:
                self.quick_scroll(200)

            # Especiales
            if safe_btn(7):
                self.gamepad_button_press('START'); time.sleep(0.3)
            if safe_btn(6):
                self.show_panel('help'); time.sleep(0.3)

        except Exception as e:
            msg = str(e)
            if 'Invalid joystick button' in msg:
                if not getattr(self, '_gamepad_disabled_invalid', False):
                    self._gamepad_disabled_invalid = True
                    self.log('WARNING', 'Gamepad no compatible (botones fuera de rango). Lectura desactivada.')
                self.gamepad_connected = False
                return
            now = time.time()
            if not hasattr(self, '_last_gamepad_err_ts'):
                self._last_gamepad_err_ts = 0
            if now - self._last_gamepad_err_ts > 2:
                self._last_gamepad_err_ts = now
                self.log('ERROR', f"Error procesando gamepad: {e}")

        if self.gamepad_connected:
            self.after(50, self.process_gamepad_input)

    def show_installation_details(self, game_path: str, game_name: str, status_text: str):
        """Muestra detalles de archivos del mod en un juego."""
        import configparser
        
        # Analizar archivos instalados
        details = []
        details.append(f"📁 Juego: {game_name}")
        details.append(f"📂 Ruta: {game_path}")
        details.append(f"📊 Estado: {status_text}")
        details.append("")
        details.append("═" * 60)
        details.append("🔍 ARCHIVOS CORE DE OPTISCALER:")
        details.append("═" * 60)
        
        # Archivos core requeridos
        # OptiScaler.dll es renombrado a dxgi/d3d11/d3d12/winmm, así que verificamos las versiones renombradas
        core_dll_names = ['dxgi.dll', 'd3d11.dll', 'd3d12.dll', 'winmm.dll']
        core_dll_found = False
        
        for dll_name in core_dll_names:
            file_path = os.path.join(game_path, dll_name)
            if os.path.exists(file_path):
                try:
                    size = os.path.getsize(file_path) / 1024  # KB
                    details.append(f"  ✅ {dll_name} ({size:.1f} KB)")
                    core_dll_found = True
                except:
                    details.append(f"  ✅ {dll_name}")
                    core_dll_found = True
        
        if not core_dll_found:
            details.append(f"  ❌ OptiScaler.dll - NO ENCONTRADO (debe estar renombrado como dxgi/d3d11/d3d12/winmm)")
        
        # Verificar OptiScaler.ini
        ini_path = os.path.join(game_path, 'OptiScaler.ini')
        ini_exists = os.path.exists(ini_path)
        
        if ini_exists:
            try:
                size = os.path.getsize(ini_path) / 1024  # KB
                details.append(f"  ✅ OptiScaler.ini ({size:.1f} KB)")
            except:
                details.append(f"  ✅ OptiScaler.ini")
        else:
            details.append(f"  ❌ OptiScaler.ini - NO ENCONTRADO")
            core_dll_found = False  # Si falta el .ini, el core está incompleto
        
        # ========== NUEVA SECCIÓN: CONFIGURACIÓN DEL INI ==========
        if ini_exists:
            details.append("")
            details.append("═" * 60)
            details.append("⚙️ CONFIGURACIÓN (OptiScaler.ini):")
            details.append("═" * 60)
            
            try:
                config = configparser.ConfigParser()
                config.read(ini_path)
                
                # Frame Generation
                fg_type = config.get('FrameGen', 'fgtype', fallback='auto').lower()
                optifg_enabled = config.get('OptiFG', 'enabled', fallback='false').lower()
                
                if fg_type == 'optifg' and optifg_enabled == 'true':
                    details.append("  ✅ Frame Generation: ACTIVADO (OptiFG)")
                elif fg_type == 'nukems':
                    # Verificar si dlssg-to-fsr3 está instalado
                    nukem_dll = os.path.join(game_path, 'dlssg_to_fsr3_amd_is_better.dll')
                    if os.path.exists(nukem_dll):
                        details.append("  ✅ Frame Generation: ACTIVADO (Nukem's DLSSG-to-FSR3)")
                    else:
                        details.append("  ⚠️ Frame Generation: Configurado como Nukem's pero DLL no encontrado")
                elif fg_type == 'nofg':
                    details.append("  ⚪ Frame Generation: DESACTIVADO")
                else:
                    details.append(f"  ℹ️ Frame Generation: {fg_type.upper()}")
                
                # Upscaler
                dx12_upscaler = config.get('Upscalers', 'dx12upscaler', fallback='auto')
                dx11_upscaler = config.get('Upscalers', 'dx11upscaler', fallback='auto')
                details.append(f"  📊 Upscaler DX12: {dx12_upscaler.upper()}")
                details.append(f"  📊 Upscaler DX11: {dx11_upscaler.upper()}")
                
                # Upscale Mode
                upscale_mode = config.get('Upscale', 'mode', fallback='auto')
                details.append(f"  📐 Modo de escalado: {upscale_mode.upper()}")
                
                # Sharpness
                sharpness = config.get('Sharpness', 'sharpness', fallback='auto')
                if sharpness != 'auto':
                    details.append(f"  🔪 Nitidez: {sharpness}")
                
                # GPU Spoofing
                dxgi_spoofing = config.get('Spoofing', 'dxgi', fallback='auto')
                if dxgi_spoofing != 'auto':
                    gpu_type = "NVIDIA" if dxgi_spoofing.lower() == 'true' else "AMD/Intel"
                    details.append(f"  🎭 GPU Spoofing: {gpu_type}")
                
                # ========== NUEVAS SECCIONES DE CONFIGURACIÓN ==========
                
                # HDR Settings
                auto_hdr = config.get('HDR', 'EnableAutoHDR', fallback='true').lower()
                nvidia_override = config.get('HDR', 'NvidiaOverride', fallback='false').lower()
                hdr_range = config.get('HDR', 'HDRRGBMaxRange', fallback='100.0')
                details.append(f"  ✨ Auto HDR: {'ACTIVADO' if auto_hdr == 'true' else 'DESACTIVADO'}")
                if nvidia_override == 'true':
                    details.append(f"  🎮 NVIDIA HDR Override: ACTIVADO")
                details.append(f"  💡 HDR Max Range: {hdr_range} nits")
                
                # Logging Settings
                log_level_map = {'0': 'Off', '1': 'Error', '2': 'Warn', '3': 'Info', '4': 'Debug', '5': 'Trace'}
                log_level = config.get('Logging', 'LogLevel', fallback='3')
                open_console = config.get('Logging', 'OpenConsole', fallback='false').lower()
                log_to_file = config.get('Logging', 'LogToFile', fallback='true').lower()
                details.append(f"  📊 Nivel de Log: {log_level_map.get(log_level, log_level)}")
                details.append(f"  🖥️ Consola: {'ACTIVADA' if open_console == 'true' else 'DESACTIVADA'}")
                details.append(f"  💾 Log a archivo: {'ACTIVADO' if log_to_file == 'true' else 'DESACTIVADO'}")
                
                # Quality Overrides
                quality_override = config.get('QualityOverrides', 'QualityRatioOverrideEnabled', fallback='false').lower()
                if quality_override == 'true':
                    details.append(f"  🎯 Quality Override: ACTIVADO")
                    quality_ratio = config.get('QualityOverrides', 'Quality', fallback='1.5')
                    balanced_ratio = config.get('QualityOverrides', 'Balanced', fallback='1.7')
                    performance_ratio = config.get('QualityOverrides', 'Performance', fallback='2.0')
                    ultra_ratio = config.get('QualityOverrides', 'UltraPerformance', fallback='3.0')
                    details.append(f"     Quality: {quality_ratio}, Balanced: {balanced_ratio}, Performance: {performance_ratio}, Ultra: {ultra_ratio}")
                
                # CAS Sharpening
                cas_enabled = config.get('CAS', 'Enabled', fallback='false').lower()
                if cas_enabled == 'true':
                    cas_type = config.get('CAS', 'Type', fallback='1')
                    cas_sharpness = config.get('CAS', 'Sharpness', fallback='0.5')
                    cas_type_name = 'RCAS' if cas_type == '1' else 'CAS'
                    details.append(f"  ✨ CAS Sharpening: ACTIVADO ({cas_type_name}, Nitidez: {cas_sharpness})")
                
                # NVNGX Spoofing
                nvngx_dx12 = config.get('Nvngx', 'Dx12Spoofing', fallback='true').lower()
                nvngx_dx11 = config.get('Nvngx', 'Dx11Spoofing', fallback='true').lower()
                nvngx_vulkan = config.get('Nvngx', 'VulkanSpoofing', fallback='true').lower()
                enabled_apis = []
                if nvngx_dx12 == 'true': enabled_apis.append('DX12')
                if nvngx_dx11 == 'true': enabled_apis.append('DX11')
                if nvngx_vulkan == 'true': enabled_apis.append('Vulkan')
                details.append(f"  🎭 NVNGX Spoofing: {', '.join(enabled_apis) if enabled_apis else 'DESACTIVADO'}")
                
                # Overlay Settings
                overlay_menu = config.get('Menu', 'OverlayMenu', fallback='auto').lower()
                overlay_map = {'auto': 'Desactivado', 'basic': 'Básico', 'true': 'Completo'}
                overlay_status = overlay_map.get(overlay_menu, overlay_menu.upper())
                details.append(f"  📊 Overlay: {overlay_status}")
                
                if overlay_menu in ['basic', 'true']:
                    # Mostrar opciones adicionales del overlay si está activado
                    overlay_fps = config.get('Menu', 'OverlayShowFPS', fallback='true').lower()
                    overlay_frametime = config.get('Menu', 'OverlayShowFrameTime', fallback='true').lower()
                    overlay_messages = config.get('Menu', 'OverlayShowMessages', fallback='true').lower()
                    overlay_position = config.get('Menu', 'OverlayPosition', fallback='0')
                    overlay_scale = config.get('Menu', 'OverlayScale', fallback='1.00')
                    overlay_font_size = config.get('Menu', 'OverlayFontSize', fallback='14')
                    
                    position_map = {
                        '0': 'Superior Izquierda', '1': 'Superior Centro', '2': 'Superior Derecha',
                        '3': 'Centro Izquierda', '4': 'Centro', '5': 'Centro Derecha',
                        '6': 'Inferior Izquierda', '7': 'Inferior Centro', '8': 'Inferior Derecha'
                    }
                    
                    metrics = []
                    if overlay_fps == 'true': metrics.append('FPS')
                    if overlay_frametime == 'true': metrics.append('Frame Time')
                    if overlay_messages == 'true': metrics.append('Messages')
                    
                    details.append(f"     Métricas: {', '.join(metrics) if metrics else 'Ninguna'}")
                    details.append(f"     Posición: {position_map.get(overlay_position, overlay_position)}")
                    scale_percent = float(overlay_scale) * 100
                    details.append(f"     Escala: {scale_percent:.0f}%, Fuente: {overlay_font_size}px")
                
            except Exception as e:
                details.append(f"  ⚠️ Error al leer configuración: {e}")
        
        # Archivos adicionales de OptiScaler
        details.append("")
        details.append("═" * 60)
        details.append("🔍 ARCHIVOS ADICIONALES DE OPTISCALER:")
        details.append("═" * 60)
        
        # No incluir las DLLs core (dxgi, d3d11, d3d12, winmm) aquí ya que se revisaron arriba
        additional_files = [
            'amd_fidelityfx_dx12.dll', 'amd_fidelityfx_vk.dll',
            'amd_fidelityfx_upscaler_dx12.dll', 'amd_fidelityfx_framegeneration_dx12.dll',
            'libxess.dll', 'libxess_dx11.dll', 'nvngx.dll'
        ]
        
        found_additional = []
        for file in additional_files:
            file_path = os.path.join(game_path, file)
            if os.path.exists(file_path):
                try:
                    size = os.path.getsize(file_path) / 1024
                    found_additional.append(f"  ✅ {file} ({size:.1f} KB)")
                except:
                    found_additional.append(f"  ✅ {file}")
        
        if found_additional:
            details.extend(found_additional)
        else:
            details.append("  ℹ️ Ninguno encontrado")
        
        # Verificar carpetas
        details.append("")
        details.append("═" * 60)
        details.append("🔍 CARPETAS DE RUNTIME:")
        details.append("═" * 60)
        
        runtime_dirs = ['D3D12_Optiscaler', 'nvngx_dlss', 'DlssOverrides']
        found_runtime = False
        
        for dir_name in runtime_dirs:
            dir_path = os.path.join(game_path, dir_name)
            if os.path.exists(dir_path) and os.path.isdir(dir_path):
                try:
                    file_count = len([f for f in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path, f))])
                    details.append(f"  ✅ {dir_name}/ ({file_count} archivos)")
                    found_runtime = True
                except:
                    details.append(f"  ✅ {dir_name}/")
                    found_runtime = True
        
        if not found_runtime:
            details.append("  ⚠️ No se encontraron carpetas de runtime")
            details.append("     (Puede ser normal en versiones antiguas de OptiScaler)")
            
        # Verificar dlssg-to-fsr3
        details.append("")
        details.append("═" * 60)
        details.append("🔍 DLSSG-TO-FSR3 (Nukem's):")
        details.append("═" * 60)
        
        nukem_files = [
            'dlssg_to_fsr3_amd_is_better.dll',
            'dlssg_to_fsr3.ini'
        ]
        
        found_nukem = []
        for file in nukem_files:
            file_path = os.path.join(game_path, file)
            if os.path.exists(file_path):
                try:
                    size = os.path.getsize(file_path) / 1024
                    found_nukem.append(f"  ✅ {file} ({size:.1f} KB)")
                except:
                    found_nukem.append(f"  ✅ {file}")
        
        if found_nukem:
            details.extend(found_nukem)
        else:
            details.append("  ℹ️ No instalado")
        
        # === Verificar OptiPatcher ===
        details.append("")
        details.append("═" * 60)
        details.append("🔍 OPTIPATCHER (PLUGIN ASI):")
        details.append("═" * 60)
        
        plugins_dir = os.path.join(game_path, "plugins")
        optipatcher_asi = os.path.join(plugins_dir, "OptiPatcher.asi")
        
        if os.path.exists(optipatcher_asi):
            try:
                size = os.path.getsize(optipatcher_asi) / 1024
                details.append(f"  ✅ OptiPatcher.asi ({size:.1f} KB)")
            except:
                details.append(f"  ✅ OptiPatcher.asi")
            
            # Verificar si LoadAsiPlugins está habilitado
            if ini_exists:
                try:
                    config = configparser.ConfigParser()
                    config.read(ini_path)
                    load_asi = config.get('Plugins', 'LoadAsiPlugins', fallback='false').lower()
                    if load_asi == 'true':
                        details.append("  ✅ LoadAsiPlugins: ACTIVADO")
                    else:
                        details.append("  ⚠️ LoadAsiPlugins: DESACTIVADO (OptiPatcher no se cargará)")
                except:
                    pass
        else:
            details.append("  ℹ️ No instalado")
        
        # Diagnóstico final
        details.append("")
        details.append("═" * 60)
        details.append("📋 DIAGNÓSTICO:")
        details.append("═" * 60)
        
        if core_dll_found:
            details.append("  ✅ Archivos core: COMPLETO")
        else:
            details.append("  ❌ Archivos core: INCOMPLETO")
        
        if found_runtime or found_additional:
            details.append("  ✅ Archivos adicionales: Encontrados")
        else:
            details.append("  ⚠️ Archivos adicionales: No encontrados")
        
        # Frame Generation diagnosis (basado en configuración)
        if ini_exists:
            try:
                config = configparser.ConfigParser()
                config.read(ini_path)
                fg_type = config.get('FrameGen', 'fgtype', fallback='auto').lower()
                optifg_enabled = config.get('OptiFG', 'enabled', fallback='false').lower()
                
                if fg_type == 'optifg' and optifg_enabled == 'true':
                    details.append("  ✅ Frame Generation: Configurado (OptiFG)")
                elif fg_type == 'nukems' and found_nukem:
                    details.append("  ✅ Frame Generation: Configurado (Nukem's)")
                elif fg_type == 'nofg':
                    details.append("  ⚪ Frame Generation: Desactivado")
                else:
                    details.append("  ℹ️ Frame Generation: Modo automático")
            except:
                pass
        
        # Mostrar en messagebox
        details_text = "\n".join(details)
        messagebox.showinfo("Detalles de Instalación", details_text)
    
    def gamepad_button_press(self, button):
        """Maneja presión de botones del gamepad."""
        if button == 'A':
            # Comportamiento contextual del botón A
            if self.focus_zone == 'sidebar':
                # Estamos en sidebar: A ejecuta el botón (abre el panel) Y entra al contenido
                if self.current_focused_widget:
                    try:
                        # Invocar el botón del sidebar para abrir su panel
                        if isinstance(self.current_focused_widget, ctk.CTkButton):
                            self.current_focused_widget.invoke()
                        
                        # Luego entrar al panel central
                        self.after(50, self.enter_content_panel)
                    except Exception as e:
                        self.log('ERROR', f"Error al activar botón sidebar: {e}")
            elif self.focus_zone == 'content':
                # Estamos en contenido: A activa el widget enfocado
                if self.current_focused_widget:
                    try:
                        if isinstance(self.current_focused_widget, ctk.CTkButton):
                            self.current_focused_widget.invoke()
                        elif isinstance(self.current_focused_widget, ctk.CTkCheckBox):
                            current = self.current_focused_widget.get()
                            self.current_focused_widget.select() if not current else self.current_focused_widget.deselect()
                        elif isinstance(self.current_focused_widget, ctk.CTkRadioButton):
                            # Activar el radiobutton
                            self.current_focused_widget.invoke()
                        elif isinstance(self.current_focused_widget, ctk.CTkSlider):
                            # Toggle: activar/desactivar slider para ajuste
                            self.slider_active = not self.slider_active
                            if self.slider_active:
                                # Verde brillante cuando está activo
                                self.current_focused_widget.configure(border_color="#00FF00", border_width=3)
                            else:
                                # Volver a color de foco normal
                                self.current_focused_widget.configure(border_color=COLOR_FOCUS, border_width=2)
                        elif isinstance(self.current_focused_widget, ctk.CTkComboBox):
                            # Abrir combobox estándar si expone método interno
                            try:
                                cb = self.current_focused_widget
                                if hasattr(cb, '_open_dropdown_menu'):
                                    cb._open_dropdown_menu()
                                elif hasattr(cb, '_dropdown_callback'):
                                    cb._dropdown_callback()
                                else:
                                    cb.focus_set()
                            except Exception as e:
                                self.log('ERROR', f"Error CTkComboBox A: {e}")
                        elif isinstance(self.current_focused_widget, WideComboBox):
                            # WideComboBox personalizado: abrir o seleccionar
                            try:
                                if self.current_focused_widget.is_open():
                                    self.current_focused_widget.select_current()
                                else:
                                    self.current_focused_widget.open_dropdown()
                            except Exception as e:
                                self.log('ERROR', f"Error WideComboBox A: {e}")
                    except Exception as e:
                        self.log('ERROR', f"Error al activar widget: {e}")
        
        elif button == 'B':
            # B: cerrar dropdown WideComboBox si está abierto, si no volver al sidebar
            if self.focus_zone == 'content':
                # Si hay slider activo, desactivarlo primero
                if self.slider_active:
                    self.slider_active = False
                    return
                # Si hay WideComboBox abierto, cerrarlo
                if isinstance(self.current_focused_widget, WideComboBox):
                    try:
                        if self.current_focused_widget.is_open():
                            self.current_focused_widget.close_dropdown()
                            return
                    except Exception:
                        pass
                self.return_to_sidebar()
            # Si ya estamos en sidebar, B no hace nada (o podría cerrar la app)
        
        elif button == 'X':
            # Config rápida - ir a panel config
            self.show_panel('config')
        
        elif button == 'Y':
            # Abrir filtro
            self.open_filter()
        
        elif button == 'START':
            # Aplicar cambios
            self.apply_mod_to_selected()
    
    def enter_content_panel(self):
        """Entra del sidebar al panel central."""
        try:
            self.focus_zone = 'content'
            
            # Buscar primer widget enfocable en el panel activo
            current_panel = None
            if self.config_panel.winfo_ismapped():
                current_panel = self.config_panel
            elif self.auto_panel.winfo_ismapped():
                current_panel = self.auto_panel
            elif self.manual_panel.winfo_ismapped():
                current_panel = self.manual_panel
            elif self.settings_panel.winfo_ismapped():
                current_panel = self.settings_panel
            elif self.help_panel.winfo_ismapped():
                current_panel = self.help_panel
            
            if current_panel:
                # Buscar primer widget enfocable
                first_widget = self.find_first_focusable_widget(current_panel)
                if first_widget:
                    self.safe_focus_widget(first_widget)
                    self.log('INFO', f"Foco movido a panel central ({self.focus_zone})")
        except Exception as e:
            self.log('ERROR', f"Error al entrar al panel: {e}")
    
    def return_to_sidebar(self):
        """Vuelve del panel central al sidebar."""
        try:
            self.focus_zone = 'sidebar'
            
            # Volver a enfocar el botón activo del sidebar
            active_panel = None
            if self.config_panel.winfo_ismapped():
                active_panel = 'config'
            elif self.auto_panel.winfo_ismapped():
                active_panel = 'auto'
            elif self.manual_panel.winfo_ismapped():
                active_panel = 'manual'
            elif self.settings_panel.winfo_ismapped():
                active_panel = 'settings'
            elif self.help_panel.winfo_ismapped():
                active_panel = 'help'
            
            if active_panel and active_panel in self.nav_buttons:
                self.safe_focus_widget(self.nav_buttons[active_panel])
                self.log('INFO', f"Foco vuelto al sidebar ({self.focus_zone})")
        except Exception as e:
            self.log('ERROR', f"Error al volver al sidebar: {e}")
    
    def find_first_focusable_widget(self, parent):
        """Encuentra el primer widget enfocable en un contenedor.
        
        Args:
            parent: Widget padre donde buscar
            
        Returns:
            Primer widget enfocable o None
        """
        # Tipos de widgets que aceptan foco (incluyendo WideComboBox)
        focusable_types = (ctk.CTkButton, ctk.CTkCheckBox, ctk.CTkEntry,
                           ctk.CTkComboBox, ctk.CTkSlider, ctk.CTkRadioButton, WideComboBox)
        
        def search_recursive(widget):
            # Verificar si el widget actual es enfocable
            if isinstance(widget, focusable_types):
                return widget
            
            # Buscar en hijos
            try:
                for child in widget.winfo_children():
                    result = search_recursive(child)
                    if result:
                        return result
            except:
                pass
            
            return None
        
        return search_recursive(parent)
    
    
    def navigate_focus(self, direction):
        """Navega entre elementos enfocables con gamepad según zona actual."""
        if self.focus_zone == 'sidebar':
            # En sidebar: arriba/abajo navegan entre botones del sidebar
            if direction in ['down', 'right']:
                self._navigate_sidebar(1)
            elif direction in ['up', 'left']:
                self._navigate_sidebar(-1)
        elif self.focus_zone == 'content':
            # Si hay un slider activo, izquierda/derecha ajustan su valor
            if self.slider_active and isinstance(self.current_focused_widget, ctk.CTkSlider):
                if direction in ['left', 'right']:
                    self._adjust_slider(direction)
                    return
                # Arriba/abajo desactivan el slider y navegan
                elif direction in ['up', 'down']:
                    self.slider_active = False
                    # Continuar con navegación normal
            
            # Interceptar navegación dentro de WideComboBox abierto
            if isinstance(self.current_focused_widget, WideComboBox) and self.current_focused_widget.is_open():
                if direction in ['up', 'down']:
                    try:
                        self.current_focused_widget.navigate_options(direction)
                    except Exception as e:
                        self.log('ERROR', f"Error navegando WideComboBox: {e}")
                # Ignorar left/right mientras está abierto
                return
            # Verificar si estamos en un botón de preset
            if self.current_focused_widget and hasattr(self, 'preset_buttons'):
                if self.current_focused_widget in self.preset_buttons.values():
                    # Navegación especial para presets: izquierda/derecha entre presets
                    if direction in ['left', 'right']:
                        self._navigate_presets_horizontal(direction)
                        return
                    elif direction in ['down', 'up']:
                        # Arriba/abajo sale de los presets
                        self._navigate_content(1 if direction == 'down' else -1)
                        return
            
            # Verificar si estamos en el header del panel de auto-detección
            if (self.auto_panel.winfo_ismapped() and 
                self.current_focused_widget and 
                self._is_auto_header_button(self.current_focused_widget)):
                # Navegación especial para header de auto-detección
                if direction in ['left', 'right']:
                    self._navigate_auto_header_horizontal(direction)
                    return
                elif direction == 'down':
                    # Abajo va al primer juego del listado
                    self._focus_first_game()
                    return
                elif direction == 'up':
                    # Arriba se queda en el header o va al anterior
                    self._navigate_content(-1)
                    return
            
            # Navegación normal en contenido
            if direction in ['down', 'right']:
                self._navigate_content(1)
            elif direction in ['up', 'left']:
                self._navigate_content(-1)
    
    def _adjust_slider(self, direction):
        """Ajusta el valor de un slider activo.
        
        Args:
            direction: 'left' (decrementar) o 'right' (incrementar)
        """
        if not isinstance(self.current_focused_widget, ctk.CTkSlider):
            return
        
        slider = self.current_focused_widget
        try:
            # Obtener valores del slider
            current_value = slider.get()
            min_value = slider.cget("from_")
            max_value = slider.cget("to")
            steps = slider.cget("number_of_steps")
            
            # Calcular step size
            if steps and steps > 0:
                step_size = (max_value - min_value) / steps
            else:
                # Si no hay steps definidos, usar 1% del rango
                step_size = (max_value - min_value) * 0.01
            
            # Ajustar valor
            if direction == 'right':
                new_value = min(current_value + step_size, max_value)
            else:  # 'left'
                new_value = max(current_value - step_size, min_value)
            
            # Aplicar nuevo valor usando la variable vinculada si existe
            variable = slider.cget("variable")
            if variable:
                try:
                    variable.set(new_value)
                except Exception as var_error:
                    self.log('ERROR', f"Error actualizando variable: {var_error}")
                    # Fallback: usar set() directamente
                    slider.set(new_value)
            else:
                # Si no hay variable, usar set() directamente
                slider.set(new_value)
            
            # Forzar actualización visual
            slider.update_idletasks()
            
            # Ejecutar callback manualmente si existe
            callback = slider.cget("command")
            if callback and callable(callback):
                try:
                    callback(new_value)
                except Exception as cb_error:
                    self.log('ERROR', f"Error ejecutando callback del slider: {cb_error}")
            
        except Exception as e:
            self.log('ERROR', f"Error ajustando slider: {e}")
    
    def _navigate_sidebar(self, direction):
        """Navega entre botones del sidebar.
        
        Args:
            direction: 1 (abajo/siguiente) o -1 (arriba/anterior)
        """
        sidebar_buttons = ['config', 'auto', 'manual', 'settings', 'help']
        
        # Encontrar botón actual
        current_idx = -1
        if self.current_focused_widget:
            for i, key in enumerate(sidebar_buttons):
                if self.nav_buttons.get(key) == self.current_focused_widget:
                    current_idx = i
                    break
        
        # Si no hay widget enfocado, empezar desde el primero o último
        if current_idx == -1:
            current_idx = 0 if direction > 0 else len(sidebar_buttons) - 1
        else:
            # Calcular nuevo índice (cíclico)
            current_idx = (current_idx + direction) % len(sidebar_buttons)
        
        # Enfocar nuevo botón
        new_key = sidebar_buttons[current_idx]
        if new_key in self.nav_buttons:
            self.safe_focus_widget(self.nav_buttons[new_key])
    
    def _navigate_content(self, direction):
        """Navega entre widgets enfocables del panel actual.
        
        Args:
            direction: 1 (siguiente) o -1 (anterior)
        """
        # Obtener panel activo
        current_panel = None
        if self.config_panel.winfo_ismapped():
            current_panel = self.config_panel
        elif self.auto_panel.winfo_ismapped():
            current_panel = self.auto_panel
        elif self.manual_panel.winfo_ismapped():
            current_panel = self.manual_panel
        elif self.settings_panel.winfo_ismapped():
            current_panel = self.settings_panel
        elif self.help_panel.winfo_ismapped():
            current_panel = self.help_panel
        
        if not current_panel:
            return
        
        # Obtener lista de widgets enfocables en el panel
        focusable_widgets = self._get_focusable_widgets(current_panel)
        
        if not focusable_widgets:
            return
        
        # Encontrar índice actual
        current_idx = -1
        
        # Si estamos en un preset, buscar cualquier preset en la lista
        if self.current_focused_widget and hasattr(self, 'preset_buttons'):
            if self.current_focused_widget in self.preset_buttons.values():
                # Buscar cualquier preset en focusable_widgets (será el primero que encontramos)
                for i, widget in enumerate(focusable_widgets):
                    if widget in self.preset_buttons.values():
                        current_idx = i
                        break
        
        # Si no encontramos preset o no estamos en preset, buscar widget actual normalmente
        if current_idx == -1 and self.current_focused_widget in focusable_widgets:
            current_idx = focusable_widgets.index(self.current_focused_widget)
        
        # Calcular nuevo índice
        if current_idx == -1:
            new_idx = 0 if direction > 0 else len(focusable_widgets) - 1
        else:
            new_idx = current_idx + direction
            # Limitar a los bordes (no cíclico en contenido)
            if new_idx < 0:
                new_idx = 0
            elif new_idx >= len(focusable_widgets):
                new_idx = len(focusable_widgets) - 1
        
        # Enfocar nuevo widget
        if 0 <= new_idx < len(focusable_widgets):
            self.safe_focus_widget(focusable_widgets[new_idx])
    
    def _get_focusable_widgets(self, parent):
        """Obtiene lista ordenada de widgets enfocables en un contenedor.
        
        Args:
            parent: Widget padre donde buscar
            
        Returns:
            Lista de widgets enfocables en orden de aparición
        """
        # Añadir WideComboBox al conjunto de widgets enfocables
        focusable_types = (ctk.CTkButton, ctk.CTkCheckBox, ctk.CTkEntry,
                           ctk.CTkComboBox, ctk.CTkSlider, ctk.CTkRadioButton, WideComboBox)
        focusable_widgets = []
        preset_widgets_found = False

        def collect_recursive(widget):
            nonlocal preset_widgets_found
            # Tratar WideComboBox como un control atómico: se enfoca él, no sus hijos
            try:
                if isinstance(widget, WideComboBox):
                    if widget.winfo_ismapped():
                        focusable_widgets.append(widget)
                    return  # No descender a sus hijos (evita foco en botón flecha interno)
            except Exception:
                pass
            # Si el widget es enfocable y está visible
            if isinstance(widget, focusable_types):
                try:
                    if widget.winfo_ismapped():
                        # Si es un botón de preset y ya agregamos uno, skip (solo agregar uno para toda la fila)
                        if hasattr(self, 'preset_buttons') and widget in self.preset_buttons.values():
                            if not preset_widgets_found:
                                focusable_widgets.append(widget)
                                preset_widgets_found = True
                            return  # Saltar otros presets
                        else:
                            focusable_widgets.append(widget)
                except Exception:
                    pass
            # Buscar en hijos recursivamente
            try:
                for child in widget.winfo_children():
                    collect_recursive(child)
            except Exception:
                pass

        collect_recursive(parent)
        return focusable_widgets
    
    def _is_auto_header_button(self, widget):
        """Verifica si el widget es un botón del header de auto-detección.
        
        Args:
            widget: Widget a verificar
            
        Returns:
            True si es un botón del header
        """
        header_buttons = []
        if hasattr(self, 'scan_btn'):
            header_buttons.append(self.scan_btn)
        if hasattr(self, 'btn_filter'):
            header_buttons.append(self.btn_filter)
        if hasattr(self, 'apply_btn'):
            header_buttons.append(self.apply_btn)
        if hasattr(self, 'remove_btn'):
            header_buttons.append(self.remove_btn)
        if hasattr(self, 'open_folder_btn'):
            header_buttons.append(self.open_folder_btn)
        
        return widget in header_buttons
    
    def _navigate_auto_header_horizontal(self, direction):
        """Navega horizontalmente entre botones del header de auto-detección.
        
        Args:
            direction: 'left' o 'right'
        """
        # Orden de botones en el header
        header_buttons = []
        if hasattr(self, 'scan_btn'):
            header_buttons.append(self.scan_btn)
        if hasattr(self, 'btn_filter'):
            header_buttons.append(self.btn_filter)
        if hasattr(self, 'apply_btn'):
            header_buttons.append(self.apply_btn)
        if hasattr(self, 'remove_btn'):
            header_buttons.append(self.remove_btn)
        if hasattr(self, 'open_folder_btn'):
            header_buttons.append(self.open_folder_btn)
        
        if not header_buttons:
            return
        
        # Encontrar índice actual
        try:
            current_idx = header_buttons.index(self.current_focused_widget)
        except ValueError:
            return
        
        # Calcular nuevo índice
        if direction == 'right':
            new_idx = (current_idx + 1) % len(header_buttons)
        else:  # left
            new_idx = (current_idx - 1) % len(header_buttons)
        
        # Mover foco
        new_btn = header_buttons[new_idx]
        self.safe_focus_widget(new_btn)
    
    def _focus_first_game(self):
        """Mueve el foco al primer juego del listado de detección automática."""
        try:
            if hasattr(self, 'games_scrollable'):
                # Buscar primer checkbox de juego
                for child in self.games_scrollable.winfo_children():
                    if isinstance(child, ctk.CTkFrame):
                        # Buscar checkbox dentro del frame
                        for subchild in child.winfo_children():
                            if isinstance(subchild, ctk.CTkCheckBox):
                                self.safe_focus_widget(subchild)
                                return
        except Exception as e:
            self.log('ERROR', f"Error al enfocar primer juego: {e}")
    
    def _navigate_presets_horizontal(self, direction):
        """Navega horizontalmente entre botones de preset.
        
        Args:
            direction: 'left' o 'right'
        """
        preset_order = ["default", "performance", "balanced", "quality", "custom"]
        
        # Encontrar preset actual
        current_preset = None
        for preset_name, btn in self.preset_buttons.items():
            if btn == self.current_focused_widget:
                current_preset = preset_name
                break
        
        if current_preset:
            current_idx = preset_order.index(current_preset)
            
            if direction == 'right':
                new_idx = (current_idx + 1) % len(preset_order)
            else:  # left
                new_idx = (current_idx - 1) % len(preset_order)
            
            new_preset = preset_order[new_idx]
            new_btn = self.preset_buttons[new_preset]
            self.safe_focus_widget(new_btn)
    
    def navigate_tabs(self, direction):
        """Navega entre pestañas con bumpers (LB/RB) - funciona desde cualquier zona."""
        panels = ['config', 'auto', 'manual', 'settings', 'help']
        current = None
        
        # Encontrar panel actual
        if self.config_panel.winfo_ismapped():
            current = 'config'
        elif self.auto_panel.winfo_ismapped():
            current = 'auto'
        elif self.manual_panel.winfo_ismapped():
            current = 'manual'
        elif self.settings_panel.winfo_ismapped():
            current = 'settings'
        elif self.help_panel.winfo_ismapped():
            current = 'help'
        
        if current:
            idx = panels.index(current)
            new_idx = (idx + direction) % len(panels)
            self.show_panel(panels[new_idx])
            
            # Después de cambiar pestaña, volver al sidebar
            self.focus_zone = 'sidebar'
            if panels[new_idx] in self.nav_buttons:
                self.safe_focus_widget(self.nav_buttons[panels[new_idx]])
    
    def quick_scroll(self, delta):
        """Scroll rápido con triggers."""
        # Intentar hacer scroll en el scrollable frame activo
        try:
            if self.auto_panel.winfo_ismapped() and hasattr(self, 'games_scrollable'):
                canvas = self.games_scrollable._parent_canvas
                canvas.yview_scroll(int(delta / 50), "units")
        except Exception as e:
            pass
    
    def update_gamepad_indicator(self):
        """Actualiza indicador visual de gamepad en sidebar."""
        if self.gamepad_connected:
            self.gamepad_indicator.configure(text_color=COLOR_SUCCESS)  # Verde cuando conectado
            gamepad_name = self.gamepad.get_name() if self.gamepad else "Gamepad"
            # Truncar nombre si es muy largo
            if len(gamepad_name) > 15:
                gamepad_name = gamepad_name[:12] + "..."
            self.gamepad_status_label.configure(
                text=gamepad_name,
                text_color=COLOR_SUCCESS
            )
        else:
            self.gamepad_indicator.configure(text_color="#333333")  # Gris oscuro
            self.gamepad_status_label.configure(
                text="Desconectado",
                text_color="#666666"
            )
    
    # ==================================================================================
    # FUNCIONES HELPER PARA FEEDBACK VISUAL
    # ==================================================================================
    
    def add_hover_effect(self, widget, enter_color, leave_color, scale=1.02):
        """Añade efecto hover visual a un widget.
        
        Args:
            widget: Widget al que añadir efecto
            enter_color: Color al pasar el ratón
            leave_color: Color normal
            scale: Factor de escala (1.0 = sin escala)
        """
        original_fg = leave_color
        
        def on_enter(e):
            widget.configure(fg_color=enter_color)
            if hasattr(widget, 'cget') and 'cursor' in widget.keys():
                widget.configure(cursor="hand2")
        
        def on_leave(e):
            widget.configure(fg_color=original_fg)
        
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)
    
    def add_click_feedback(self, widget, click_color="#005080"):
        """Añade feedback visual al hacer click.
        
        Args:
            widget: Widget al que añadir efecto
            click_color: Color al hacer click
        """
        original_command = widget.cget("command") if hasattr(widget, 'cget') else None
        
        def on_click_with_feedback():
            # Flash visual
            original_color = widget.cget("fg_color")
            widget.configure(fg_color=click_color)
            self.after(100, lambda: widget.configure(fg_color=original_color))
            
            # Ejecutar comando original
            if original_command:
                if callable(original_command):
                    original_command()
        
        if hasattr(widget, 'configure') and 'command' in widget.keys():
            widget.configure(command=on_click_with_feedback)
    
    def highlight_active_nav(self, active_key):
        """Resalta el botón de navegación activo.
        
        Args:
            active_key: Key del botón activo ('config', 'auto', etc.)
        """
        for key, btn in self.nav_buttons.items():
            if key == active_key:
                btn.configure(
                    fg_color=COLOR_SELECTED,
                    border_width=2,
                    border_color=COLOR_FOCUS
                )
            else:
                btn.configure(
                    fg_color="#2b2b2b",
                    border_width=0
                )
    
    def add_focus_indicator(self, widget):
        """Añade indicador de foco para navegación por teclado/gamepad.
        
        Args:
            widget: Widget al que añadir indicador
        """
        try:
            from .components.wide_combobox import WideComboBox
        except Exception:
            WideComboBox = None
        def on_focus_in(e):
            self.current_focused_widget = widget
            if hasattr(widget, 'configure'):
                try:
                    widget.configure(border_color=COLOR_FOCUS, border_width=2)
                except:
                    pass
            # Auto-scroll para traer widget enfocado a la vista
            self.auto_scroll_to_widget(widget)
        
        def on_focus_out(e):
            # No quitar el borde si es un WideComboBox con dropdown abierto
            if WideComboBox is not None and isinstance(widget, WideComboBox):
                try:
                    if widget.is_open():
                        return "break"
                except Exception:
                    pass
            if hasattr(widget, 'configure'):
                try:
                    widget.configure(border_width=0)
                except:
                    pass
        
        if hasattr(widget, 'bind'):
            widget.bind("<FocusIn>", on_focus_in)
            widget.bind("<FocusOut>", on_focus_out)
    
    def enable_click_to_focus(self, widget):
        """Habilita foco al hacer clic en el widget.
        
        Args:
            widget: Widget al que añadir funcionalidad click-to-focus
        """
        # Los sliders NO deben tener click-to-focus directo
        # Requieren Enter/A para activarse
        if isinstance(widget, ctk.CTkSlider):
            return
            
        def on_click(e):
            try:
                # Establecer foco en el widget
                if hasattr(widget, 'focus'):
                    widget.focus()
                # Actualizar widget con foco actual
                self.current_focused_widget = widget
                # Actualizar zona de foco a 'content' si no está en sidebar
                if self.focus_zone == 'sidebar':
                    self.focus_zone = 'content'
            except Exception as ex:
                self.log('ERROR', f"Error en click-to-focus: {ex}")
        
        if hasattr(widget, 'bind'):
            widget.bind("<Button-1>", on_click, add="+")
    
    def setup_widget_focus(self, widget):
        """Configura un widget con indicador de foco y click-to-focus.
        
        Para sliders: solo añade indicador de foco (sin click-to-focus)
        Para otros widgets: añade ambos
        
        Args:
            widget: Widget a configurar
        """
        self.add_focus_indicator(widget)
        # Los sliders solo tienen indicador, no click-to-focus
        if not isinstance(widget, ctk.CTkSlider):
            self.enable_click_to_focus(widget)
    
    def auto_scroll_to_widget(self, widget):
        """Hace scroll automático para traer widget enfocado a la vista.
        
        Args:
            widget: Widget al que hacer scroll
        """
        try:
            # Determinar qué scrollable frame usar según panel activo
            scrollable = None
            
            if self.auto_panel.winfo_ismapped() and hasattr(self, 'games_scrollable'):
                scrollable = self.games_scrollable
            elif self.config_panel.winfo_ismapped():
                # Buscar scrollable frame en config panel (recursivamente)
                def find_scrollable(parent):
                    for child in parent.winfo_children():
                        if isinstance(child, ctk.CTkScrollableFrame):
                            return child
                        # Buscar recursivamente
                        result = find_scrollable(child)
                        if result:
                            return result
                    return None
                scrollable = find_scrollable(self.config_panel)
            elif self.settings_panel.winfo_ismapped():
                def find_scrollable(parent):
                    for child in parent.winfo_children():
                        if isinstance(child, ctk.CTkScrollableFrame):
                            return child
                        result = find_scrollable(child)
                        if result:
                            return result
                    return None
                scrollable = find_scrollable(self.settings_panel)
            elif self.help_panel.winfo_ismapped():
                def find_scrollable(parent):
                    for child in parent.winfo_children():
                        if isinstance(child, ctk.CTkScrollableFrame):
                            return child
                        result = find_scrollable(child)
                        if result:
                            return result
                    return None
                scrollable = find_scrollable(self.help_panel)
            
            if not scrollable:
                print("[AUTOSCROLL] ❌ No se encontró scrollable frame")
                self.log('DEBUG', "No se encontró scrollable frame")
                return
            
            print(f"[AUTOSCROLL] ✓ Scrollable encontrado: {type(scrollable).__name__}")
            
            # Obtener canvas - acceso robusto
            canvas = None
            try:
                if hasattr(scrollable, '_parent_canvas'):
                    canvas = scrollable._parent_canvas
                elif hasattr(scrollable, 'canvas'):
                    canvas = scrollable.canvas
                else:
                    # Buscar canvas entre los hijos
                    for child in scrollable.winfo_children():
                        if isinstance(child, ctk.CTkCanvas) or 'canvas' in str(type(child)).lower():
                            canvas = child
                            break
            except Exception:
                pass
            
            if not canvas:
                print("[AUTOSCROLL] ❌ No se pudo obtener el canvas del scrollable")
                self.log('DEBUG', "No se pudo obtener el canvas del scrollable")
                return
            
            # Forzar actualización de geometría
            try:
                widget.update_idletasks()
                scrollable.update_idletasks()
                canvas.update_idletasks()
            except Exception:
                pass
            
            # Calcular posición absoluta del widget
            # Usar winfo_rooty para obtener posición absoluta en pantalla
            try:
                widget_abs_y = widget.winfo_rooty()
                scrollable_abs_y = scrollable.winfo_rooty()
                widget_y = widget_abs_y - scrollable_abs_y
                widget_height = widget.winfo_height()
                
                print(f"[AUTOSCROLL] Widget absolute Y: {widget_abs_y}, Scrollable absolute Y: {scrollable_abs_y}, Relative Y: {widget_y}")
                self.log('DEBUG', f"Widget absolute Y: {widget_abs_y}, Scrollable absolute Y: {scrollable_abs_y}, Relative Y: {widget_y}")
            except Exception as e:
                print(f"[AUTOSCROLL] Error calculando posición absoluta: {e}")
                self.log('DEBUG', f"Error calculando posición absoluta: {e}")
                # Fallback al método antiguo
                widget_y = 0
                widget_height = widget.winfo_height()
                
                # Recorrer hacia arriba hasta llegar al scrollable frame
                current = widget
                while current and current != scrollable:
                    try:
                        widget_y += current.winfo_y()
                        current = current.master
                    except Exception:
                        break
            
            # Obtener región visible del canvas
            canvas_height = canvas.winfo_height()
            scroll_region_str = canvas.cget("scrollregion")
            
            if not scroll_region_str or scroll_region_str == "":
                self.log('DEBUG', "Canvas scrollregion vacío")
                return
                
            scroll_region = scroll_region_str.split()
            if len(scroll_region) < 4:
                self.log('DEBUG', f"Canvas scrollregion inválido: {scroll_region}")
                return
            
            total_height = float(scroll_region[3])
            if total_height == 0:
                self.log('DEBUG', "Total height es 0")
                return
            
            # Obtener posición actual del scroll (0.0 a 1.0)
            view = canvas.yview()
            visible_top = view[0] * total_height
            visible_bottom = view[1] * total_height
            
            # Determinar si widget está fuera de vista
            widget_top = widget_y
            widget_bottom = widget_y + widget_height
            
            # Margen de seguridad (pixels)
            margin = 100
            
            print(f"[AUTOSCROLL] Visible: {visible_top:.0f}-{visible_bottom:.0f}, Widget: {widget_top:.0f}-{widget_bottom:.0f}, Canvas H: {canvas_height}")
            self.log('DEBUG', f"Visible: {visible_top:.0f}-{visible_bottom:.0f}, Widget: {widget_top:.0f}-{widget_bottom:.0f}, Canvas H: {canvas_height}")
            
            # Si widget está arriba de la vista visible
            if widget_top < visible_top + margin:
                # Scroll hacia arriba
                target_fraction = max(0, (widget_top - margin) / total_height)
                canvas.yview_moveto(target_fraction)
                print(f"[AUTOSCROLL] ⬆️ UP: widget_top={widget_top:.0f}, target={target_fraction:.2f}")
                self.log('DEBUG', f"Auto-scroll UP: widget_top={widget_top:.0f}, target={target_fraction:.2f}")
            
            # Si widget está abajo de la vista visible
            elif widget_bottom > visible_bottom - margin:
                # Scroll hacia abajo para centrar el widget
                target_fraction = max(0, min(1.0, (widget_top - margin) / total_height))
                canvas.yview_moveto(target_fraction)
                print(f"[AUTOSCROLL] ⬇️ DOWN: widget_bottom={widget_bottom:.0f}, target={target_fraction:.2f}")
                self.log('DEBUG', f"Auto-scroll DOWN: widget_bottom={widget_bottom:.0f}, target={target_fraction:.2f}")
            else:
                print(f"[AUTOSCROLL] ✓ Widget ya está visible")
                self.log('DEBUG', "Widget ya está visible, no se necesita scroll")
            
        except Exception as e:
            self.log('DEBUG', f"Error en auto_scroll_to_widget: {e}")
            # Silenciar errores de auto-scroll para no interrumpir navegación
            pass
    
    def safe_focus_widget(self, widget):
        """Establece el foco en un widget de manera segura (compatible con CustomTkinter).
        
        Args:
            widget: Widget a enfocar
        """
        try:
            try:
                from .components.wide_combobox import WideComboBox
            except Exception:
                WideComboBox = None
            # Remover efecto visual del widget anterior
            if self.current_focused_widget and hasattr(self.current_focused_widget, 'configure'):
                try:
                    # Para botones, checkboxes, combos, etc.
                    if WideComboBox is not None and isinstance(self.current_focused_widget, WideComboBox):
                        # Si el dropdown sigue abierto, no quitar el borde
                        try:
                            if self.current_focused_widget.is_open():
                                pass
                            else:
                                self.current_focused_widget.configure(border_width=0)
                        except Exception:
                            pass
                    elif not isinstance(self.current_focused_widget, ctk.CTkRadioButton):
                        self.current_focused_widget.configure(border_width=0)
                    else:
                        # Para radiobuttons, restaurar color de texto normal
                        self.current_focused_widget.configure(text_color=("#DCE4EE", "#DCE4EE"))
                except:
                    pass
            
            # Establecer nuevo widget enfocado
            self.current_focused_widget = widget
            
            # Desactivar slider si estaba activo y cambiamos de widget
            if self.slider_active and not isinstance(widget, ctk.CTkSlider):
                self.slider_active = False
            
            # Aplicar efecto visual de foco
            if hasattr(widget, 'configure'):
                try:
                    if isinstance(widget, ctk.CTkRadioButton):
                        # Para radiobuttons, usar color de texto brillante como indicador
                        widget.configure(text_color=COLOR_FOCUS)
                    elif isinstance(widget, ctk.CTkComboBox):
                        # Para combobox estándar: solo borde visual
                        widget.configure(border_color=COLOR_FOCUS, border_width=2)
                    else:
                        # Para otros widgets, usar borde
                        widget.configure(border_color=COLOR_FOCUS, border_width=2)
                except:
                    pass
            
            # Auto-scroll si es necesario
            self.auto_scroll_to_widget(widget)
        except Exception as e:
            pass
    
    
    def set_initial_focus(self):
        """Establece el foco inicial en el botón de auto-detección del sidebar."""
        try:
            if hasattr(self, 'nav_buttons') and 'auto' in self.nav_buttons:
                self.focus_zone = 'sidebar'
                self.safe_focus_widget(self.nav_buttons['auto'])
                self.log('INFO', "Foco inicial establecido en botón de auto-detección")
        except Exception as e:
            self.log('ERROR', f"Error al establecer foco inicial: {e}")
    
    def setup_drag_scroll(self, scrollable_frame):
        """Configura drag-to-scroll en un CTkScrollableFrame.
        
        Args:
            scrollable_frame: CTkScrollableFrame al que añadir drag scroll
        """
        # BUGFIX: Acceso robusto al canvas interno de CTkScrollableFrame
        try:
            # Intentar obtener el canvas interno (puede variar entre versiones de customtkinter)
            if hasattr(scrollable_frame, '_parent_canvas'):
                canvas = scrollable_frame._parent_canvas
            elif hasattr(scrollable_frame, 'canvas'):
                canvas = scrollable_frame.canvas
            else:
                # Buscar canvas como hijo directo
                for child in scrollable_frame.winfo_children():
                    if isinstance(child, ctk.CTkCanvas) or 'canvas' in str(type(child)).lower():
                        canvas = child
                        break
                else:
                    self.log('WARNING', "No se pudo activar drag-to-scroll: canvas no encontrado")
                    return
        except Exception as e:
            self.log('WARNING', f"No se pudo configurar drag-to-scroll: {e}")
            return
        
        # Variables para tracking del drag
        drag_data = {"y": 0, "scrolling": False}
        
        def on_mouse_press(event):
            """Inicia el drag."""
            drag_data["y"] = event.y
            drag_data["scrolling"] = False
            # Cambiar cursor
            try:
                canvas.configure(cursor="hand2")
            except:
                pass
        
        def on_mouse_drag(event):
            """Maneja el movimiento durante drag."""
            if not drag_data["scrolling"]:
                # Comprobar si se ha movido suficiente para considerar drag
                if abs(event.y - drag_data["y"]) > 5:
                    drag_data["scrolling"] = True
            
            if drag_data["scrolling"]:
                # Calcular delta
                delta = drag_data["y"] - event.y
                drag_data["y"] = event.y
                
                # Scroll suavizado
                scroll_amount = delta / 3  # Ajustar sensibilidad
                try:
                    canvas.yview_scroll(int(scroll_amount), "units")
                except:
                    pass
        
        def on_mouse_release(event):
            """Finaliza el drag."""
            drag_data["scrolling"] = False
            # Restaurar cursor
            try:
                canvas.configure(cursor="")
            except:
                pass
        
        # Bind eventos al canvas interno
        try:
            canvas.bind("<Button-1>", on_mouse_press)
            canvas.bind("<B1-Motion>", on_mouse_drag)
            canvas.bind("<ButtonRelease-1>", on_mouse_release)
            self.log('INFO', "Drag-to-scroll configurado correctamente")
        except Exception as e:
            self.log('WARNING', f"Error al bindear eventos drag-to-scroll: {e}")
    
    # ==================================================================================
    # CREACIÓN DE UI
    # ==================================================================================
    
    def create_sidebar(self):
        """Crea sidebar con 4 iconos."""
        self.sidebar = ctk.CTkFrame(self, fg_color="#1a1a1a", corner_radius=0, width=160)
        self.sidebar.grid(row=0, column=0, sticky="ns")
        self.sidebar.grid_propagate(False)
        
        # Botones de navegación con iconos grandes
        self.nav_buttons = {}
        
        nav_items = [
            ("config", "⚙️", self.show_config_panel, None),
            ("auto", "", self.show_auto_panel, "auto"),
            ("manual", "📁", self.show_manual_panel, None),
            ("settings", "🔧", self.show_settings_panel, None),
            ("help", "❓", self.show_help_panel, None),
        ]
        
        for key, icon, command, icon_key in nav_items:
            # Usar imagen si está disponible, sino emoji
            if icon_key and self.icons.get(icon_key):
                btn = ctk.CTkButton(
                    self.sidebar,
                    text="",
                    image=self.icons[icon_key],
                    command=command,
                    fg_color="#2b2b2b",
                    hover_color=COLOR_SECONDARY_HOVER,
                    height=90,
                    width=140,
                    corner_radius=8,
                    border_width=0,
                    cursor="hand2"
                )
            else:
                btn = ctk.CTkButton(
                    self.sidebar,
                    text=icon,
                    command=command,
                    fg_color="#2b2b2b",
                    hover_color=COLOR_SECONDARY_HOVER,
                    height=90,
                    width=140,
                    corner_radius=8,
                    font=ctk.CTkFont(size=48),
                    border_width=0,
                    cursor="hand2"
                )
            btn.pack(padx=10, pady=10)
            self.nav_buttons[key] = btn
            
            # Añadir efectos visuales
            self.setup_widget_focus(btn)
        
        # Añadir indicador de gamepad al final
        self.gamepad_indicator_frame = ctk.CTkFrame(
            self.sidebar,
            fg_color="transparent",
            height=60
        )
        self.gamepad_indicator_frame.pack(side="bottom", fill="x", padx=10, pady=10)
        
        self.gamepad_indicator = ctk.CTkLabel(
            self.gamepad_indicator_frame,
            text="🎮",
            font=ctk.CTkFont(size=24),
            text_color="#333333"  # Gris oscuro cuando está desconectado
        )
        self.gamepad_indicator.pack()
        
        self.gamepad_status_label = ctk.CTkLabel(
            self.gamepad_indicator_frame,
            text="Desconectado",
            font=ctk.CTkFont(size=FONT_TINY),
            text_color="#666666"
        )
        self.gamepad_status_label.pack()
            
    def create_content_area(self):
        """Crea el área de contenido principal."""
        self.content_frame = ctk.CTkFrame(self, fg_color="#2b2b2b", corner_radius=10)
        self.content_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.content_frame.grid_rowconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(0, weight=1)
        
    def create_panels(self):
        """Crea todos los paneles (ocultos inicialmente)."""
        self.create_config_panel()
        self.create_auto_panel()
        self.create_manual_panel()
        self.create_settings_panel()
        self.create_help_panel()
        
    # ==================================================================================
    # PANEL 1: CONFIGURACIÓN DEL MOD
    # ==================================================================================
    
    def create_config_panel(self):
        """Panel de configuración global del mod con presets."""
        self.config_panel = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.config_panel.grid(row=0, column=0, sticky="nsew")
        self.config_panel.grid_columnconfigure(0, weight=1)
        
        # Título del app arriba
        ctk.CTkLabel(
            self.config_panel,
            text=APP_TITLE,
            font=ctk.CTkFont(size=FONT_TITLE, weight="bold"),
            text_color="#00BFFF"
        ).pack(pady=(15, 5))
        
        # Título del panel
        ctk.CTkLabel(
            self.config_panel,
            text="⚙️ CONFIGURACIÓN DEL MOD",
            font=ctk.CTkFont(size=FONT_TITLE, weight="bold")
        ).pack(pady=(5, 10))
        
        # Scrollable content principal (contendrá secciones colapsables)
        config_scroll = ctk.CTkScrollableFrame(self.config_panel, fg_color="transparent")
        config_scroll.pack(fill="both", expand=True, padx=20, pady=10)
        self.setup_drag_scroll(config_scroll)

        # === Sección 1: Configuración Básica (agrupa lo ya existente) ===
        self.basic_section = CollapsibleSection(config_scroll, title="🎮 Configuración Básica", collapsed=False)
        # No empaquetar aún - update_config_visibility() lo hará según disponibilidad de mod
        
        # Frame para mensaje "No hay mod instalado"
        self.config_no_mod_frame = ctk.CTkFrame(config_scroll, fg_color="#1a1a1a", corner_radius=8)
        
        ctk.CTkLabel(
            self.config_no_mod_frame,
            text="⚠️ OptiScaler no está instalado",
            font=ctk.CTkFont(size=FONT_SECTION, weight="bold"),
            text_color="#FFA500"
        ).pack(pady=(20, 10))
        
        ctk.CTkLabel(
            self.config_no_mod_frame,
            text="Para configurar el mod, primero necesitas descargarlo desde Ajustes",
            font=ctk.CTkFont(size=FONT_NORMAL),
            text_color="#888888"
        ).pack(pady=(0, 10))
        
        ctk.CTkButton(
            self.config_no_mod_frame,
            text="🛠️ Ir a Ajustes para descargar OptiScaler",
            command=lambda: self.show_panel("settings"),
            height=45,
            fg_color="#3a3a3a",
            hover_color="#00BFFF",
            font=ctk.CTkFont(size=FONT_NORMAL, weight="bold")
        ).pack(pady=(10, 20), padx=20, fill="x")
        
        # Frame contenedor para todas las opciones (oculto si no hay mod) ahora dentro del collapsible
        self.config_options_frame = ctk.CTkFrame(self.basic_section.content_frame, fg_color="transparent")
        self.config_options_frame.pack(fill="x")
        
        # === PRESETS RÁPIDOS ===
        presets_frame = ctk.CTkFrame(self.config_options_frame, fg_color="#1a1a1a", corner_radius=8)
        presets_frame.pack(fill="x", pady=10)
        
        # Contenedor del título y preset activo
        title_container = ctk.CTkFrame(presets_frame, fg_color="transparent")
        title_container.pack(fill="x", padx=15, pady=(10, 5))
        
        ctk.CTkLabel(
            title_container,
            text="⚡ PRESETS RÁPIDOS",
            font=ctk.CTkFont(size=FONT_SECTION, weight="bold")
        ).pack(side="left", anchor="w")
        
        # Indicador de preset activo (esquina superior derecha)
        self.active_preset_label = ctk.CTkLabel(
            title_container,
            text="Default",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#00AAFF",
            fg_color="#2a2a2a",
            corner_radius=5,
            padx=10,
            pady=4
        )
        self.active_preset_label.pack(side="right", anchor="e")
        
        # Botones de presets en una fila
        presets_btn_frame = ctk.CTkFrame(presets_frame, fg_color="transparent")
        presets_btn_frame.pack(fill="x", padx=15, pady=(5, 10))
        
        self.preset_buttons = {}
        self.preset_borders = {
            "default": ("#2196F3", 3),      # Azul
            "performance": ("#FFD600", 3),  # Amarillo
            "balanced": ("#00E676", 3),     # Verde
            "quality": ("#AB47BC", 3),      # Violeta
            "custom": ("#B0BEC5", 3)        # Gris
        }
        preset_buttons = [
            ("⚪ Default", "default"),
            ("⚡ Performance", "performance"),
            ("⚖️ Balanced", "balanced"),
            ("💎 Quality", "quality"),
            ("✏️ Custom", "custom")
        ]
        for text, preset in preset_buttons:
            btn = ctk.CTkButton(
                presets_btn_frame,
                text=text,
                command=lambda p=preset: self.apply_preset(p),
                fg_color="#3a3a3a",
                hover_color="#4a4a4a",
                height=40,
                corner_radius=8,
                border_width=0
            )
            btn.pack(side="left", padx=5, expand=True, fill="x")
            self.preset_buttons[preset] = btn
        
        # === 0. TIPO DE GPU + INFO DETECTADA ===
        gpu_frame = ctk.CTkFrame(self.config_options_frame, fg_color="#1a1a1a", corner_radius=8)
        gpu_frame.pack(fill="x", pady=10)
        
        # Título
        ctk.CTkLabel(
            gpu_frame,
            text="Tipo de GPU:",
            font=ctk.CTkFont(size=FONT_SECTION, weight="bold")
        ).pack(anchor="w", padx=15, pady=(10, 5))
        
        # GPU Detectada (info)
        gpu_names = {
            'nvidia': ('NVIDIA', '#76B900'),
            'amd': ('AMD', '#ED1C24'),
            'intel': ('Intel', '#0071C5'),
            'unknown': ('Desconocida', '#888888')
        }
        gpu_display_name, gpu_color = gpu_names.get(self.gpu_vendor, ('Desconocida', '#888888'))
        
        gpu_info_container = ctk.CTkFrame(gpu_frame, fg_color="#2a2a2a", corner_radius=6)
        gpu_info_container.pack(fill="x", padx=15, pady=(0, 10))
        
        ctk.CTkLabel(
            gpu_info_container,
            text=f"🖥️ GPU Detectada: {gpu_display_name}",
            font=ctk.CTkFont(size=FONT_NORMAL, weight="bold"),
            text_color=gpu_color
        ).pack(padx=10, pady=(8, 4), anchor="w")
        
        if self.use_dual_mod:
            mode_text = "✅ Recomendado: OptiScaler + dlssg-to-fsr3"
            mode_color = "#00FF00"
        else:
            mode_text = "ℹ️ Recomendado: Solo OptiScaler (DLSS nativo disponible)"
            mode_color = "#00BFFF"
        
        ctk.CTkLabel(
            gpu_info_container,
            text=mode_text,
            font=ctk.CTkFont(size=FONT_TINY),
            text_color=mode_color
        ).pack(padx=10, pady=(0, 8), anchor="w")
        
        # Selector Manual (Forzar tipo)
        ctk.CTkLabel(
            gpu_frame,
            text="Forzar tipo de GPU:",
            font=ctk.CTkFont(size=FONT_SMALL),
            text_color="#888888"
        ).pack(anchor="w", padx=15, pady=(5, 2))
        
        self.gpu_radio_frame = ctk.CTkFrame(gpu_frame, fg_color="transparent")
        self.gpu_radio_frame.pack(fill="x", padx=15, pady=(0, 10))
        
        self.gpu_radio_amd = ctk.CTkRadioButton(
            self.gpu_radio_frame,
            text="AMD / Intel",
            variable=self.gpu_var,
            value=1,
            font=ctk.CTkFont(size=FONT_NORMAL),
            command=self.on_gpu_type_changed
        )
        self.gpu_radio_amd.pack(side="left", padx=10)
        self.setup_widget_focus(self.gpu_radio_amd)
        
        self.gpu_radio_nvidia = ctk.CTkRadioButton(
            self.gpu_radio_frame,
            text="NVIDIA",
            variable=self.gpu_var,
            value=2,
            font=ctk.CTkFont(size=FONT_NORMAL),
            command=self.on_gpu_type_changed
        )
        self.gpu_radio_nvidia.pack(side="left", padx=10)
        self.setup_widget_focus(self.gpu_radio_nvidia)
        
        # (DLL Injection movido a sección avanzada)
        
        # === 2. REESCALADOR (UPSCALER) ===
        upscaler_frame = ctk.CTkFrame(self.config_options_frame, fg_color="#1a1a1a", corner_radius=8)
        upscaler_frame.pack(fill="x", pady=10)
        
        upscaler_title_frame = ctk.CTkFrame(upscaler_frame, fg_color="transparent")
        upscaler_title_frame.pack(fill="x", padx=15, pady=(10, 5))
        
        ctk.CTkLabel(
            upscaler_title_frame,
            text="Reescalador:",
            font=ctk.CTkFont(size=FONT_SECTION, weight="bold")
        ).pack(side="left")
        
        ctk.CTkLabel(
            upscaler_title_frame,
            text="🎮 Tecnología base",
            font=ctk.CTkFont(size=FONT_TINY),
            text_color="#888888"
        ).pack(side="left", padx=10)
        
        self.upscaler_combo = WideComboBox(
            upscaler_frame,
            variable=self.upscaler_var,
            values=["Automático", "FSR 3.1", "FSR 2.2", "XeSS", "DLSS"],
            width=300,
            font=ctk.CTkFont(size=FONT_NORMAL)
        )
        self.upscaler_combo.pack(padx=15, pady=(0, 10), fill="x")
        self.setup_widget_focus(self.upscaler_combo)
        self.upscaler_var.trace_add('write', lambda *a: (self.mark_preset_custom(), self.update_custom_state()))
        
        # === 3. MODO DE REESCALADO ===
        upscale_mode_frame = ctk.CTkFrame(self.config_options_frame, fg_color="#1a1a1a", corner_radius=8)
        upscale_mode_frame.pack(fill="x", pady=10)
        
        upscale_title_frame = ctk.CTkFrame(upscale_mode_frame, fg_color="transparent")
        upscale_title_frame.pack(fill="x", padx=15, pady=(10, 5))
        
        ctk.CTkLabel(
            upscale_title_frame,
            text="Modo de Reescalado:",
            font=ctk.CTkFont(size=FONT_SECTION, weight="bold")
        ).pack(side="left")
        
        ctk.CTkLabel(
            upscale_title_frame,
            text="📊 Performance: +60% | Quality: +20%",
            font=ctk.CTkFont(size=FONT_TINY),
            text_color="#FFAA00"
        ).pack(side="left", padx=10)
        
        self.upscale_mode_combo = WideComboBox(
            upscale_mode_frame,
            variable=self.upscale_mode_var,
            values=["Automático", "Ultra Rendimiento", "Rendimiento", "Equilibrado", "Calidad", "Ultra Calidad"],
            width=300,
            font=ctk.CTkFont(size=13)
        )
        self.upscale_mode_combo.pack(padx=15, pady=(0, 10), fill="x")
        self.setup_widget_focus(self.upscale_mode_combo)
        self.upscale_mode_var.trace_add('write', lambda *a: (self.mark_preset_custom(), self.update_custom_state()))
        
        # === 4. FRAME GENERATION ===
        fg_frame = ctk.CTkFrame(self.config_options_frame, fg_color="#1a1a1a", corner_radius=8)
        fg_frame.pack(fill="x", pady=10)
        
        fg_title_frame = ctk.CTkFrame(fg_frame, fg_color="transparent")
        fg_title_frame.pack(fill="x", padx=15, pady=(10, 5))
        
        ctk.CTkLabel(
            fg_title_frame,
            text="Frame Generation:",
            font=ctk.CTkFont(size=FONT_SECTION, weight="bold")
        ).pack(side="left")
        
        ctk.CTkLabel(
            fg_title_frame,
            text="⚡ ~+80% FPS",
            font=ctk.CTkFont(size=FONT_TINY),
            text_color="#00FF00"
        ).pack(side="left", padx=10)
        
        # Crear combobox primero (con valores por defecto)
        self.fg_combo = WideComboBox(
            fg_frame,
            variable=self.fg_mode_var,
            values=["Desactivado", "OptiFG", "FSR-FG (Nukem's DLSSG)"],
            width=300,
            font=ctk.CTkFont(size=FONT_NORMAL)
        )
        self.fg_combo.pack(padx=15, pady=(0, 10), fill="x")
        self.setup_widget_focus(self.fg_combo)
        self.fg_mode_var.trace_add('write', lambda *a: (self.mark_preset_custom(), self.update_custom_state()))
        
        # Actualizar opciones según configuración (después de crear el combobox)
        self.update_fg_options()
        
        # === 5. LÍMITE DE FPS ===
        fps_frame = ctk.CTkFrame(self.config_options_frame, fg_color="#1a1a1a", corner_radius=8)
        fps_frame.pack(fill="x", pady=10)
        
        fps_title_frame = ctk.CTkFrame(fps_frame, fg_color="transparent")
        fps_title_frame.pack(fill="x", padx=15, pady=(10, 5))
        
        ctk.CTkLabel(
            fps_title_frame,
            text="Límite de FPS:",
            font=ctk.CTkFont(size=FONT_SECTION, weight="bold")
        ).pack(side="left")
        
        self.fps_label = ctk.CTkLabel(
            fps_title_frame,
            text=f"🎯 {self.fps_limit_var.get()} FPS" if self.fps_limit_var.get() > 0 else "Sin límite",
            font=ctk.CTkFont(size=FONT_TINY),
            text_color="#00BFFF"
        )
        self.fps_label.pack(side="left", padx=10)
        
        self.fps_slider = ctk.CTkSlider(
            fps_frame,
            from_=0,
            to=300,
            number_of_steps=60,
            variable=self.fps_limit_var,
            command=self.on_fps_changed
        )
        self.fps_slider.pack(padx=15, pady=(0, 10), fill="x")
        self.setup_widget_focus(self.fps_slider)
        self.fps_limit_var.trace_add('write', lambda *a: (self.mark_preset_custom(), self.update_custom_state()))
        
        # === 6. SHARPNESS ===
        sharpness_frame = ctk.CTkFrame(self.config_options_frame, fg_color="#1a1a1a", corner_radius=8)
        sharpness_frame.pack(fill="x", pady=10)

        # === Sección 2: Configuración Avanzada ===
        self.advanced_section = CollapsibleSection(config_scroll, title="⚙️ Configuración Avanzada", collapsed=True)
        # No empaquetar aún - update_config_visibility() lo hará

        # === CONTENIDO REAL SECCIÓN AVANZADA ===
        adv_wrap = ctk.CTkFrame(self.advanced_section.content_frame, fg_color="transparent")
        adv_wrap.pack(fill="x")

        # DLL Injection (movido aquí)
        dll_frame = ctk.CTkFrame(adv_wrap, fg_color="#1a1a1a", corner_radius=8)
        dll_frame.pack(fill="x", pady=8)
        ctk.CTkLabel(
            dll_frame,
            text="🔧 DLL de Inyección",
            font=ctk.CTkFont(size=FONT_SECTION, weight="bold")
        ).pack(anchor="w", padx=15, pady=(10, 5))
        ctk.CTkLabel(
            dll_frame,
            text="⚠️ Cambia solo si el juego no carga el mod con la opción por defecto.",
            font=ctk.CTkFont(size=FONT_TINY),
            text_color="#FFAA00"
        ).pack(anchor="w", padx=15, pady=(0, 5))
        self.dll_combo = WideComboBox(
            dll_frame,
            variable=self.dll_name_var,
            values=["dxgi.dll", "d3d11.dll", "d3d12.dll", "winmm.dll"],
            width=300,
            font=ctk.CTkFont(size=FONT_NORMAL)
        )
        self.dll_combo.pack(padx=15, pady=(0, 12), fill="x")
        self.setup_widget_focus(self.dll_combo)
        self.dll_name_var.trace_add('write', lambda *a: (self._on_advanced_changed()))

        # Antialiasing control (Native AA vs OptiScaler)
        aa_frame = ctk.CTkFrame(adv_wrap, fg_color="#1a1a1a", corner_radius=8)
        aa_frame.pack(fill="x", pady=8)
        ctk.CTkLabel(
            aa_frame,
            text="🎨 Antialiasing",
            font=ctk.CTkFont(size=FONT_SECTION, weight="bold")
        ).pack(anchor="w", padx=15, pady=(10, 5))
        ctk.CTkLabel(
            aa_frame,
            text="Selecciona quién gestiona el AA (TAA/MSAA). Desactivar nativo puede reducir 'imagen plastificada'.",
            font=ctk.CTkFont(size=FONT_TINY),
            text_color="#888888",
            wraplength=850,
            justify="left"
        ).pack(anchor="w", padx=15, pady=(0, 8))
        aa_opts = ctk.CTkFrame(aa_frame, fg_color="transparent")
        aa_opts.pack(fill="x", padx=15, pady=(0, 10))
        self.aa_native_radio = ctk.CTkRadioButton(
            aa_opts,
            text="Usar AA nativo del juego",
            variable=self.native_aa_var,
            value=True,
            font=ctk.CTkFont(size=FONT_NORMAL),
            command=self._on_advanced_changed
        )
        self.aa_native_radio.pack(side="left", padx=(0, 20))
        self.setup_widget_focus(self.aa_native_radio)
        self.aa_optiscaler_radio = ctk.CTkRadioButton(
            aa_opts,
            text="OptiScaler gestiona AA",
            variable=self.native_aa_var,
            value=False,
            font=ctk.CTkFont(size=FONT_NORMAL),
            command=self._on_advanced_changed
        )
        self.aa_optiscaler_radio.pack(side="left")
        self.setup_widget_focus(self.aa_optiscaler_radio)

        # Mipmap Bias control
        mipmap_frame = ctk.CTkFrame(adv_wrap, fg_color="#1a1a1a", corner_radius=8)
        mipmap_frame.pack(fill="x", pady=8)
        ctk.CTkLabel(
            mipmap_frame,
            text="🖼️ Mipmap Bias (Nitidez Texturas)",
            font=ctk.CTkFont(size=FONT_SECTION, weight="bold")
        ).pack(anchor="w", padx=15, pady=(10, 5))
        self.mipmap_label = ctk.CTkLabel(
            mipmap_frame,
            text=f"Valor actual: {self.mipmap_bias_var.get():.1f}",
            font=ctk.CTkFont(size=FONT_TINY),
            text_color="#00BFFF"
        )
        self.mipmap_label.pack(anchor="w", padx=15)
        ctk.CTkLabel(
            mipmap_frame,
            text="Valores negativos = más nitidez. Demasiado bajo puede causar shimmer/aliasing.",
            font=ctk.CTkFont(size=FONT_TINY),
            text_color="#FFAA00"
        ).pack(anchor="w", padx=15, pady=(0,5))
        self.mipmap_slider = ctk.CTkSlider(
            mipmap_frame,
            from_=-2.0,
            to=0.0,
            number_of_steps=40,
            variable=self.mipmap_bias_var,
            command=self._on_mipmap_bias_changed
        )
        self.mipmap_slider.pack(padx=15, pady=(0, 10), fill="x")
        self.setup_widget_focus(self.mipmap_slider)
        self.mipmap_bias_var.trace_add('write', lambda *a: (self._on_advanced_changed()))

        # ===== QUALITY OVERRIDES =====
        qo_section = CollapsibleSection(
            parent=adv_wrap,
            title="📐 Quality Overrides",
            collapsed=True
        )
        qo_section.pack(fill="x", pady=8)
        
        qo_content = qo_section.content_frame
        
        # Enable checkbox
        enable_qo_check = ctk.CTkCheckBox(
            qo_content,
            text="Activar ratios de calidad personalizados",
            variable=self.quality_override_enabled_var,
            font=ctk.CTkFont(size=FONT_NORMAL),
            command=self._on_quality_override_changed
        )
        enable_qo_check.pack(anchor="w", padx=15, pady=(10, 15))
        self.setup_widget_focus(enable_qo_check)
        
        # Info text
        info_text = ctk.CTkLabel(
            qo_content,
            text="Los ratios controlan la resolución interna de renderizado. Valores más altos = menor resolución interna = mejor rendimiento pero menor calidad visual.",
            font=ctk.CTkFont(size=FONT_TINY),
            text_color="#cccccc",
            wraplength=850,
            justify="left"
        )
        info_text.pack(anchor="w", padx=15, pady=(0, 15))
        
        # Grid frame for the 4 spinboxes
        ratios_grid = ctk.CTkFrame(qo_content, fg_color="transparent")
        ratios_grid.pack(fill="x", padx=15, pady=(0, 10))
        ratios_grid.grid_columnconfigure((0, 1), weight=1)
        
        # Quality preset ratio
        quality_frame = ctk.CTkFrame(ratios_grid, fg_color="#2a2a2a", corner_radius=6)
        quality_frame.grid(row=0, column=0, padx=(0, 5), pady=5, sticky="ew")
        ctk.CTkLabel(
            quality_frame,
            text="🏆 Quality",
            font=ctk.CTkFont(size=FONT_NORMAL, weight="bold"),
            text_color="#4CAF50"
        ).pack(anchor="w", padx=10, pady=(8, 2))
        self.quality_ratio_entry = ctk.CTkEntry(
            quality_frame,
            width=100,
            textvariable=self.quality_ratio_var,
            font=ctk.CTkFont(size=FONT_NORMAL)
        )
        self.quality_ratio_entry.pack(anchor="w", padx=10, pady=(0, 8))
        self.setup_widget_focus(self.quality_ratio_entry)
        self.quality_ratio_var.trace_add('write', lambda *a: self._validate_quality_ratio('quality'))
        
        # Balanced preset ratio
        balanced_frame = ctk.CTkFrame(ratios_grid, fg_color="#2a2a2a", corner_radius=6)
        balanced_frame.grid(row=0, column=1, padx=(5, 0), pady=5, sticky="ew")
        ctk.CTkLabel(
            balanced_frame,
            text="⚖️ Balanced",
            font=ctk.CTkFont(size=FONT_NORMAL, weight="bold"),
            text_color="#2196F3"
        ).pack(anchor="w", padx=10, pady=(8, 2))
        self.balanced_ratio_entry = ctk.CTkEntry(
            balanced_frame,
            width=100,
            textvariable=self.balanced_ratio_var,
            font=ctk.CTkFont(size=FONT_NORMAL)
        )
        self.balanced_ratio_entry.pack(anchor="w", padx=10, pady=(0, 8))
        self.setup_widget_focus(self.balanced_ratio_entry)
        self.balanced_ratio_var.trace_add('write', lambda *a: self._validate_quality_ratio('balanced'))
        
        # Performance preset ratio
        performance_frame = ctk.CTkFrame(ratios_grid, fg_color="#2a2a2a", corner_radius=6)
        performance_frame.grid(row=1, column=0, padx=(0, 5), pady=5, sticky="ew")
        ctk.CTkLabel(
            performance_frame,
            text="⚡ Performance",
            font=ctk.CTkFont(size=FONT_NORMAL, weight="bold"),
            text_color="#FF9800"
        ).pack(anchor="w", padx=10, pady=(8, 2))
        self.performance_ratio_entry = ctk.CTkEntry(
            performance_frame,
            width=100,
            textvariable=self.performance_ratio_var,
            font=ctk.CTkFont(size=FONT_NORMAL)
        )
        self.performance_ratio_entry.pack(anchor="w", padx=10, pady=(0, 8))
        self.setup_widget_focus(self.performance_ratio_entry)
        self.performance_ratio_var.trace_add('write', lambda *a: self._validate_quality_ratio('performance'))
        
        # Ultra Performance preset ratio
        ultra_perf_frame = ctk.CTkFrame(ratios_grid, fg_color="#2a2a2a", corner_radius=6)
        ultra_perf_frame.grid(row=1, column=1, padx=(5, 0), pady=5, sticky="ew")
        ctk.CTkLabel(
            ultra_perf_frame,
            text="🚀 Ultra Performance",
            font=ctk.CTkFont(size=FONT_NORMAL, weight="bold"),
            text_color="#F44336"
        ).pack(anchor="w", padx=10, pady=(8, 2))
        self.ultra_perf_ratio_entry = ctk.CTkEntry(
            ultra_perf_frame,
            width=100,
            textvariable=self.ultra_perf_ratio_var,
            font=ctk.CTkFont(size=FONT_NORMAL)
        )
        self.ultra_perf_ratio_entry.pack(anchor="w", padx=10, pady=(0, 8))
        self.setup_widget_focus(self.ultra_perf_ratio_entry)
        self.ultra_perf_ratio_var.trace_add('write', lambda *a: self._validate_quality_ratio('ultra_perf'))
        
        # Warning for extreme values
        self.qo_warning_label = ctk.CTkLabel(
            qo_content,
            text="",
            font=ctk.CTkFont(size=FONT_TINY),
            text_color="#FF9800",
            wraplength=850,
            justify="left"
        )
        self.qo_warning_label.pack(anchor="w", padx=15, pady=(5, 10))

        # Btn restaurar valores por defecto avanzados
        reset_adv = ctk.CTkButton(
            adv_wrap,
            text="🔄 Restaurar valores avanzados",
            command=self._reset_advanced_defaults,
            height=34,
            fg_color="#3a3a3a",
            hover_color="#4a4a4a",
            font=ctk.CTkFont(size=FONT_SMALL, weight="bold")
        )
        reset_adv.pack(pady=(4, 10), padx=10, anchor="e")
        self.setup_widget_focus(reset_adv)

        # === Sección 3: Overlay Settings ===
        self.overlay_section = CollapsibleSection(config_scroll, title="📊 Overlay Settings", collapsed=True)
        # No empaquetar aún - update_config_visibility() lo hará
        
        overlay_wrap = ctk.CTkFrame(self.overlay_section.content_frame, fg_color="transparent")
        overlay_wrap.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Info header
        info_header = ctk.CTkFrame(overlay_wrap, fg_color="#2a2a2a", corner_radius=6)
        info_header.pack(fill="x", padx=15, pady=(10, 15))
        
        ctk.CTkLabel(
            info_header,
            text="ℹ️ El overlay muestra información en tiempo real dentro del juego (FPS, tiempos de frame, etc.)",
            font=ctk.CTkFont(size=FONT_TINY),
            text_color="#cccccc",
            wraplength=850,
            justify="left"
        ).pack(padx=10, pady=8)
        
        # Modo de Overlay
        mode_frame = ctk.CTkFrame(overlay_wrap, fg_color="transparent")
        mode_frame.pack(fill="x", padx=15, pady=(5, 10))
        
        ctk.CTkLabel(
            mode_frame,
            text="🎯 Modo de Overlay:",
            font=ctk.CTkFont(size=FONT_SECTION, weight="bold")
        ).pack(side="left")
        
        self.overlay_mode_combo = WideComboBox(
            mode_frame,
            variable=self.overlay_mode_var,
            values=["Desactivado", "Básico", "Completo"],
            width=200,
            font=ctk.CTkFont(size=FONT_NORMAL),
            max_visible_items=3  # Mostrar todas las 3 opciones sin scroll
        )
        self.overlay_mode_combo.pack(side="left", padx=10)
        self.setup_widget_focus(self.overlay_mode_combo)
        self.overlay_mode_var.trace_add('write', lambda *a: (self._on_overlay_mode_changed(), self.mark_preset_custom(), self.update_custom_state()))
        
        # Frame de métricas (solo visible cuando overlay está activo)
        self.overlay_metrics_frame = ctk.CTkFrame(overlay_wrap, fg_color="#1a1a1a", corner_radius=8)
        
        ctk.CTkLabel(
            self.overlay_metrics_frame,
            text="📈 Métricas a Mostrar:",
            font=ctk.CTkFont(size=FONT_TINY, weight="bold")
        ).pack(anchor="w", padx=10, pady=(8, 5))
        
        # Checkboxes para métricas
        self.overlay_fps_check = ctk.CTkCheckBox(
            self.overlay_metrics_frame,
            text="📊 Mostrar FPS (Frames por Segundo)",
            variable=self.overlay_show_fps_var,
            font=ctk.CTkFont(size=FONT_SMALL),
            command=self._on_overlay_metrics_changed
        )
        self.overlay_fps_check.pack(anchor="w", padx=15, pady=5)
        self.setup_widget_focus(self.overlay_fps_check)
        
        self.overlay_frametime_check = ctk.CTkCheckBox(
            self.overlay_metrics_frame,
            text="⏱️ Mostrar Frame Time (milisegundos por frame)",
            variable=self.overlay_show_frametime_var,
            font=ctk.CTkFont(size=FONT_SMALL),
            command=self._on_overlay_metrics_changed
        )
        self.overlay_frametime_check.pack(anchor="w", padx=15, pady=5)
        self.setup_widget_focus(self.overlay_frametime_check)
        
        self.overlay_messages_check = ctk.CTkCheckBox(
            self.overlay_metrics_frame,
            text="💬 Mostrar Mensajes del Sistema",
            variable=self.overlay_show_messages_var,
            font=ctk.CTkFont(size=FONT_SMALL),
            command=self._on_overlay_metrics_changed
        )
        self.overlay_messages_check.pack(anchor="w", padx=15, pady=(5, 10))
        self.setup_widget_focus(self.overlay_messages_check)
        
        # Posición del overlay
        self.position_frame = ctk.CTkFrame(overlay_wrap, fg_color="#1a1a1a", corner_radius=8)
        
        ctk.CTkLabel(
            self.position_frame,
            text="📍 Posición en Pantalla:",
            font=ctk.CTkFont(size=FONT_TINY, weight="bold")
        ).pack(anchor="w", padx=10, pady=(8, 5))
        
        positions_grid = ctk.CTkFrame(self.position_frame, fg_color="transparent")
        positions_grid.pack(padx=15, pady=(0, 10))
        
        # Grid 3x3 de posiciones
        positions = [
            ("↖️ Superior Izquierda", 0, 0),
            ("⬆️ Superior Centro", 0, 1),
            ("↗️ Superior Derecha", 0, 2),
            ("⬅️ Centro Izquierda", 1, 0),
            ("⏺️ Centro", 1, 1),
            ("➡️ Centro Derecha", 1, 2),
            ("↙️ Inferior Izquierda", 2, 0),
            ("⬇️ Inferior Centro", 2, 1),
            ("↘️ Inferior Derecha", 2, 2)
        ]
        
        for text, row, col in positions:
            rb = ctk.CTkRadioButton(
                positions_grid,
                text=text,
                variable=self.overlay_position_var,
                value=text.split(" ", 1)[1],  # Extraer "Superior Izquierda", etc.
                command=self._on_overlay_position_changed,
                font=ctk.CTkFont(size=FONT_TINY)
            )
            rb.grid(row=row, column=col, padx=5, pady=3, sticky="w")
            self.setup_widget_focus(rb)
        
        # Escala del overlay
        self.scale_frame = ctk.CTkFrame(overlay_wrap, fg_color="transparent")
        
        scale_title_frame = ctk.CTkFrame(self.scale_frame, fg_color="transparent")
        scale_title_frame.pack(fill="x", padx=15, pady=(10, 5))
        
        ctk.CTkLabel(
            scale_title_frame,
            text="🔍 Escala del Overlay:",
            font=ctk.CTkFont(size=FONT_SECTION, weight="bold")
        ).pack(side="left")
        
        self.overlay_scale_label = ctk.CTkLabel(
            scale_title_frame,
            text=f"{int(self.overlay_scale_var.get() * 100)}%",
            font=ctk.CTkFont(size=FONT_TINY),
            text_color="#00BFFF"
        )
        self.overlay_scale_label.pack(side="left", padx=10)
        
        self.overlay_scale_slider = ctk.CTkSlider(
            self.scale_frame,
            from_=0.5,
            to=2.0,
            number_of_steps=15,
            variable=self.overlay_scale_var,
            command=self._on_overlay_scale_changed
        )
        self.overlay_scale_slider.pack(fill="x", padx=15, pady=(0, 5))
        self.setup_widget_focus(self.overlay_scale_slider)
        
        ctk.CTkLabel(
            self.scale_frame,
            text="ℹ️ 50% = Muy pequeño | 100% = Normal | 200% = Muy grande",
            font=ctk.CTkFont(size=FONT_TINY-1),
            text_color="#666666"
        ).pack(anchor="w", padx=15, pady=(0, 10))
        
        # Tamaño de fuente
        self.font_frame = ctk.CTkFrame(overlay_wrap, fg_color="transparent")
        
        font_title_frame = ctk.CTkFrame(self.font_frame, fg_color="transparent")
        font_title_frame.pack(fill="x", padx=15, pady=(5, 5))
        
        ctk.CTkLabel(
            font_title_frame,
            text="🔤 Tamaño de Fuente:",
            font=ctk.CTkFont(size=FONT_SECTION, weight="bold")
        ).pack(side="left")
        
        self.overlay_font_label = ctk.CTkLabel(
            font_title_frame,
            text=f"{self.overlay_font_size_var.get()}px",
            font=ctk.CTkFont(size=FONT_TINY),
            text_color="#00BFFF"
        )
        self.overlay_font_label.pack(side="left", padx=10)
        
        self.overlay_font_slider = ctk.CTkSlider(
            self.font_frame,
            from_=10,
            to=24,
            number_of_steps=14,
            variable=self.overlay_font_size_var,
            command=self._on_overlay_font_changed
        )
        self.overlay_font_slider.pack(fill="x", padx=15, pady=(0, 5))
        self.setup_widget_focus(self.overlay_font_slider)
        
        ctk.CTkLabel(
            self.font_frame,
            text="ℹ️ Tamaño recomendado: 14px (legible en 1080p/1440p)",
            font=ctk.CTkFont(size=FONT_TINY-1),
            text_color="#666666"
        ).pack(anchor="w", padx=15, pady=(0, 10))
        
        # Actualizar visibilidad inicial del metrics_frame
        self._update_overlay_ui_visibility()

        # === Sección 4: HDR Settings ===
        self.hdr_section = CollapsibleSection(config_scroll, title="🌈 HDR Settings", collapsed=True)
        # No empaquetar aún - update_config_visibility() lo hará
        
        hdr_wrap = ctk.CTkFrame(self.hdr_section.content_frame, fg_color="transparent")
        hdr_wrap.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Auto HDR Checkbox
        self.auto_hdr_check = ctk.CTkCheckBox(
            hdr_wrap,
            text="✨ Activar Auto HDR",
            variable=self.auto_hdr_var,
            font=ctk.CTkFont(size=FONT_SMALL, weight="bold"),
            command=self._on_hdr_changed
        )
        self.auto_hdr_check.pack(anchor="w", padx=15, pady=(10, 5))
        self.setup_widget_focus(self.auto_hdr_check)
        
        # NVIDIA HDR Override Checkbox
        self.nvidia_hdr_check = ctk.CTkCheckBox(
            hdr_wrap,
            text="🎮 NVIDIA HDR Override (solo GPUs RTX)",
            variable=self.nvidia_hdr_override_var,
            font=ctk.CTkFont(size=FONT_SMALL),
            command=self._on_hdr_changed
        )
        self.nvidia_hdr_check.pack(anchor="w", padx=15, pady=5)
        self.setup_widget_focus(self.nvidia_hdr_check)
        
        # HDR RGB Max Range Slider
        hdr_slider_frame = ctk.CTkFrame(hdr_wrap, fg_color="transparent")
        hdr_slider_frame.pack(fill="x", padx=15, pady=(10, 5))
        
        hdr_title_frame = ctk.CTkFrame(hdr_slider_frame, fg_color="transparent")
        hdr_title_frame.pack(fill="x")
        
        ctk.CTkLabel(
            hdr_title_frame,
            text="💡 Luminancia Máxima (nits):",
            font=ctk.CTkFont(size=FONT_SECTION, weight="bold")
        ).pack(side="left")
        
        self.hdr_range_label = ctk.CTkLabel(
            hdr_title_frame,
            text=f"{int(self.hdr_rgb_range_var.get())} nits",
            font=ctk.CTkFont(size=FONT_TINY),
            text_color="#FFD700"
        )
        self.hdr_range_label.pack(side="left", padx=10)
        
        self.hdr_range_slider = ctk.CTkSlider(
            hdr_slider_frame,
            from_=10.0,
            to=200.0,
            number_of_steps=190,
            variable=self.hdr_rgb_range_var,
            command=self.on_hdr_range_changed
        )
        self.hdr_range_slider.pack(fill="x", pady=(5, 10))
        self.setup_widget_focus(self.hdr_range_slider)
        
        # HDR Presets
        preset_frame = ctk.CTkFrame(hdr_wrap, fg_color="#1a1a1a", corner_radius=8)
        preset_frame.pack(fill="x", padx=15, pady=(5, 10))
        
        ctk.CTkLabel(
            preset_frame,
            text="⚡ Presets Rápidos:",
            font=ctk.CTkFont(size=FONT_TINY, weight="bold")
        ).pack(anchor="w", padx=10, pady=(8, 5))
        
        presets_buttons_frame = ctk.CTkFrame(preset_frame, fg_color="transparent")
        presets_buttons_frame.pack(fill="x", padx=10, pady=(0, 8))
        
        btn_sdr = ctk.CTkButton(
            presets_buttons_frame,
            text="📺 SDR",
            width=100,
            height=28,
            command=lambda: self._apply_hdr_preset("sdr"),
            fg_color="#3a3a3a",
            hover_color="#4a4a4a",
            font=ctk.CTkFont(size=FONT_TINY)
        )
        btn_sdr.pack(side="left", padx=2)
        self.setup_widget_focus(btn_sdr)
        
        btn_hdr400 = ctk.CTkButton(
            presets_buttons_frame,
            text="🌟 HDR400",
            width=100,
            height=28,
            command=lambda: self._apply_hdr_preset("hdr400"),
            fg_color="#3a3a3a",
            hover_color="#4a4a4a",
            font=ctk.CTkFont(size=FONT_TINY)
        )
        btn_hdr400.pack(side="left", padx=2)
        self.setup_widget_focus(btn_hdr400)
        
        btn_hdr600 = ctk.CTkButton(
            presets_buttons_frame,
            text="✨ HDR600",
            width=100,
            height=28,
            command=lambda: self._apply_hdr_preset("hdr600"),
            fg_color="#3a3a3a",
            hover_color="#4a4a4a",
            font=ctk.CTkFont(size=FONT_TINY)
        )
        btn_hdr600.pack(side="left", padx=2)
        self.setup_widget_focus(btn_hdr600)
        
        btn_hdr1000 = ctk.CTkButton(
            presets_buttons_frame,
            text="💎 HDR1000+",
            width=100,
            height=28,
            command=lambda: self._apply_hdr_preset("hdr1000"),
            fg_color="#3a3a3a",
            hover_color="#4a4a4a",
            font=ctk.CTkFont(size=FONT_TINY)
        )
        btn_hdr1000.pack(side="left", padx=2)
        self.setup_widget_focus(btn_hdr1000)
        
        # Info text
        ctk.CTkLabel(
            hdr_wrap,
            text="ℹ️ SDR = sin HDR | HDR400 = 100 nits | HDR600 = 150 nits | HDR1000+ = 200 nits",
            font=ctk.CTkFont(size=FONT_TINY-1),
            text_color="#666666"
        ).pack(anchor="w", padx=15, pady=(0, 10))

        # ===== CAS SHARPENING =====
        self.cas_section = CollapsibleSection(config_scroll, title="✨ CAS Sharpening", collapsed=True)
        # No empaquetar aún - update_config_visibility() lo hará
        
        cas_wrap = ctk.CTkFrame(self.cas_section.content_frame, fg_color="transparent")
        cas_wrap.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Enable CAS checkbox
        self.cas_enabled_check = ctk.CTkCheckBox(
            cas_wrap,
            text="Activar CAS (Contrast Adaptive Sharpening)",
            variable=self.cas_enabled_var,
            font=ctk.CTkFont(size=FONT_NORMAL),
            command=self._on_cas_changed
        )
        self.cas_enabled_check.pack(anchor="w", padx=15, pady=(10, 15))
        self.setup_widget_focus(self.cas_enabled_check)
        
        # Info text explaining CAS vs RCAS
        info_frame = ctk.CTkFrame(cas_wrap, fg_color="#2a2a2a", corner_radius=6)
        info_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        ctk.CTkLabel(
            info_frame,
            text="ℹ️ Diferencias entre algoritmos:",
            font=ctk.CTkFont(size=FONT_SMALL, weight="bold"),
            text_color="#00BFFF"
        ).pack(anchor="w", padx=10, pady=(8, 5))
        
        ctk.CTkLabel(
            info_frame,
            text="• RCAS (Robust): Mejor calidad, preserva detalles finos, menos artifacts.\n• CAS (Standard): Más rápido, puede ser más agresivo con el contraste.",
            font=ctk.CTkFont(size=FONT_TINY),
            text_color="#cccccc",
            wraplength=850,
            justify="left"
        ).pack(anchor="w", padx=10, pady=(0, 8))
        
        # Radio buttons for CAS type
        cas_type_frame = ctk.CTkFrame(cas_wrap, fg_color="transparent")
        cas_type_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        ctk.CTkLabel(
            cas_type_frame,
            text="Algoritmo:",
            font=ctk.CTkFont(size=FONT_NORMAL, weight="bold")
        ).pack(anchor="w", pady=(0, 5))
        
        radio_frame = ctk.CTkFrame(cas_type_frame, fg_color="transparent")
        radio_frame.pack(fill="x")
        
        self.cas_rcas_radio = ctk.CTkRadioButton(
            radio_frame,
            text="🏆 RCAS (Recomendado)",
            variable=self.cas_type_var,
            value="RCAS",
            font=ctk.CTkFont(size=FONT_NORMAL),
            command=self._on_cas_changed
        )
        self.cas_rcas_radio.pack(side="left", padx=(0, 20))
        self.setup_widget_focus(self.cas_rcas_radio)
        
        self.cas_cas_radio = ctk.CTkRadioButton(
            radio_frame,
            text="⚡ CAS (Clásico)",
            variable=self.cas_type_var,
            value="CAS",
            font=ctk.CTkFont(size=FONT_NORMAL),
            command=self._on_cas_changed
        )
        self.cas_cas_radio.pack(side="left")
        self.setup_widget_focus(self.cas_cas_radio)
        
        # CAS Sharpness slider
        cas_sharpness_title = ctk.CTkFrame(cas_wrap, fg_color="transparent")
        cas_sharpness_title.pack(fill="x", padx=15, pady=(0, 5))
        
        ctk.CTkLabel(
            cas_sharpness_title,
            text="Intensidad CAS:",
            font=ctk.CTkFont(size=FONT_NORMAL, weight="bold")
        ).pack(side="left")
        
        self.cas_sharpness_label = ctk.CTkLabel(
            cas_sharpness_title,
            text=f"✨ {self.cas_sharpness_var.get():.2f}",
            font=ctk.CTkFont(size=FONT_TINY),
            text_color="#00BFFF"
        )
        self.cas_sharpness_label.pack(side="left", padx=10)
        
        self.cas_sharpness_slider = ctk.CTkSlider(
            cas_wrap,
            from_=0.0,
            to=1.0,
            number_of_steps=100,
            variable=self.cas_sharpness_var,
            command=self._on_cas_sharpness_changed
        )
        self.cas_sharpness_slider.pack(padx=15, pady=(0, 10), fill="x")
        self.setup_widget_focus(self.cas_sharpness_slider)
        
        # Warning about RCAS conflict
        ctk.CTkLabel(
            cas_wrap,
            text="⚠️ Nota: Si CAS está activado, el slider RCAS de la sección básica será ignorado (solo uno activo a la vez).",
            font=ctk.CTkFont(size=FONT_TINY),
            text_color="#FFA500",
            wraplength=850,
            justify="left"
        ).pack(anchor="w", padx=15, pady=(5, 10))
        
        # ===== NVNGX SPOOFING =====
        self.nvngx_section = CollapsibleSection(config_scroll, title="🎭 NVNGX Spoofing", collapsed=True)
        # No empaquetar aún - update_config_visibility() lo hará
        
        nvngx_wrap = ctk.CTkFrame(self.nvngx_section.content_frame, fg_color="transparent")
        nvngx_wrap.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Info/Warning header
        warning_frame = ctk.CTkFrame(nvngx_wrap, fg_color="#3a2a2a", corner_radius=6, border_width=2, border_color="#FFA500")
        warning_frame.pack(fill="x", padx=15, pady=(10, 15))
        
        ctk.CTkLabel(
            warning_frame,
            text="⚠️ CONFIGURACIÓN AVANZADA - Solo modificar si hay problemas",
            font=ctk.CTkFont(size=FONT_NORMAL, weight="bold"),
            text_color="#FFA500"
        ).pack(anchor="w", padx=10, pady=(8, 5))
        
        ctk.CTkLabel(
            warning_frame,
            text="Por defecto, OptiScaler engaña (spoof) a los juegos para que crean que DLSS está disponible en todas las APIs (DirectX 12/11, Vulkan).\nSolo desmarca una opción si un juego específico tiene problemas de inicialización o crashes.",
            font=ctk.CTkFont(size=FONT_TINY),
            text_color="#cccccc",
            wraplength=850,
            justify="left"
        ).pack(anchor="w", padx=10, pady=(0, 8))
        
        # Checkboxes para cada API
        ctk.CTkLabel(
            nvngx_wrap,
            text="Activar spoofing para:",
            font=ctk.CTkFont(size=FONT_NORMAL, weight="bold")
        ).pack(anchor="w", padx=15, pady=(0, 10))
        
        # DirectX 12
        self.nvngx_dx12_check = ctk.CTkCheckBox(
            nvngx_wrap,
            text="✅ DirectX 12 (Recomendado - mayoría de juegos modernos)",
            variable=self.nvngx_dx12_var,
            font=ctk.CTkFont(size=FONT_NORMAL),
            command=self._on_nvngx_changed
        )
        self.nvngx_dx12_check.pack(anchor="w", padx=15, pady=5)
        self.setup_widget_focus(self.nvngx_dx12_check)
        
        # DirectX 11
        self.nvngx_dx11_check = ctk.CTkCheckBox(
            nvngx_wrap,
            text="✅ DirectX 11 (Juegos más antiguos)",
            variable=self.nvngx_dx11_var,
            font=ctk.CTkFont(size=FONT_NORMAL),
            command=self._on_nvngx_changed
        )
        self.nvngx_dx11_check.pack(anchor="w", padx=15, pady=5)
        self.setup_widget_focus(self.nvngx_dx11_check)
        
        # Vulkan
        self.nvngx_vulkan_check = ctk.CTkCheckBox(
            nvngx_wrap,
            text="✅ Vulkan (Doom Eternal, Red Dead Redemption 2, etc.)",
            variable=self.nvngx_vulkan_var,
            font=ctk.CTkFont(size=FONT_NORMAL),
            command=self._on_nvngx_changed
        )
        self.nvngx_vulkan_check.pack(anchor="w", padx=15, pady=5)
        self.setup_widget_focus(self.nvngx_vulkan_check)
        
        # Info adicional
        ctk.CTkLabel(
            nvngx_wrap,
            text="ℹ️ Si un juego no inicia o crashea al cargar, intenta desmarcar la API correspondiente y reinstala el mod.",
            font=ctk.CTkFont(size=FONT_TINY),
            text_color="#888888",
            wraplength=850,
            justify="left"
        ).pack(anchor="w", padx=15, pady=(15, 10))
        
        # === Sección Debug y Logging (al final) ===
        self.debug_section = CollapsibleSection(config_scroll, title="🐛 Debug y Logging", collapsed=True)
        # No empaquetar aún - update_config_visibility() lo hará
        
        debug_wrap = ctk.CTkFrame(self.debug_section.content_frame, fg_color="transparent")
        debug_wrap.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Log Level Dropdown
        log_level_frame = ctk.CTkFrame(debug_wrap, fg_color="transparent")
        log_level_frame.pack(fill="x", padx=15, pady=(10, 5))
        
        ctk.CTkLabel(
            log_level_frame,
            text="📊 Nivel de Log:",
            font=ctk.CTkFont(size=FONT_SECTION, weight="bold")
        ).pack(side="left")
        
        self.log_level_combo = WideComboBox(
            log_level_frame,
            variable=self.log_level_var,
            values=["Off", "Error", "Warn", "Info", "Debug", "Trace"],
            width=200,
            font=ctk.CTkFont(size=FONT_NORMAL),
            max_visible_items=6  # Mostrar todas las 6 opciones sin scroll
        )
        self.log_level_combo.pack(side="left", padx=10)
        self.setup_widget_focus(self.log_level_combo)
        self.log_level_var.trace_add('write', lambda *a: (self._on_logging_changed(), self.mark_preset_custom(), self.update_custom_state()))
        
        # Open Console Checkbox
        self.open_console_check = ctk.CTkCheckBox(
            debug_wrap,
            text="🖥️ Abrir ventana de consola al iniciar juego",
            variable=self.open_console_var,
            font=ctk.CTkFont(size=FONT_SMALL),
            command=self._on_logging_changed
        )
        self.open_console_check.pack(anchor="w", padx=15, pady=5)
        self.setup_widget_focus(self.open_console_check)
        
        # Log to File Checkbox
        self.log_to_file_check = ctk.CTkCheckBox(
            debug_wrap,
            text="💾 Guardar logs en archivo",
            variable=self.log_to_file_var,
            font=ctk.CTkFont(size=FONT_SMALL),
            command=self._on_logging_changed
        )
        self.log_to_file_check.pack(anchor="w", padx=15, pady=5)
        self.setup_widget_focus(self.log_to_file_check)
        
        # Log Management Section
        log_mgmt_frame = ctk.CTkFrame(debug_wrap, fg_color="#1a1a1a", corner_radius=8)
        log_mgmt_frame.pack(fill="x", padx=15, pady=(10, 5))
        
        ctk.CTkLabel(
            log_mgmt_frame,
            text="📁 Gestión de Logs",
            font=ctk.CTkFont(size=FONT_TINY, weight="bold")
        ).pack(anchor="w", padx=10, pady=(8, 5))
        
        # Log location info
        logs_dir = os.path.join(get_config_dir(), "logs")
        ctk.CTkLabel(
            log_mgmt_frame,
            text=f"Ubicación: {logs_dir}",
            font=ctk.CTkFont(size=FONT_TINY-1),
            text_color="#888888"
        ).pack(anchor="w", padx=10, pady=(0, 5))
        
        # Buttons frame
        log_buttons_frame = ctk.CTkFrame(log_mgmt_frame, fg_color="transparent")
        log_buttons_frame.pack(fill="x", padx=10, pady=(0, 8))
        
        btn_open_logs = ctk.CTkButton(
            log_buttons_frame,
            text="📂 Abrir Carpeta",
            width=140,
            height=28,
            command=self._open_logs_folder,
            fg_color="#3a3a3a",
            hover_color="#4a4a4a",
            font=ctk.CTkFont(size=FONT_TINY)
        )
        btn_open_logs.pack(side="left", padx=2)
        self.setup_widget_focus(btn_open_logs)
        
        btn_clean_logs = ctk.CTkButton(
            log_buttons_frame,
            text="🗑️ Limpiar Antiguos",
            width=140,
            height=28,
            command=self._clean_old_logs,
            fg_color="#3a3a3a",
            hover_color="#4a4a4a",
            font=ctk.CTkFont(size=FONT_TINY)
        )
        btn_clean_logs.pack(side="left", padx=2)
        self.setup_widget_focus(btn_clean_logs)
        
        # Info text
        ctk.CTkLabel(
            debug_wrap,
            text="ℹ️ Los logs se guardan en la carpeta de configuración. 'Limpiar Antiguos' elimina logs de más de 7 días.",
            font=ctk.CTkFont(size=FONT_TINY-1),
            text_color="#666666",
            wraplength=850,
            justify="left"
        ).pack(anchor="w", padx=15, pady=(5, 10))
        
        sharpness_title_frame = ctk.CTkFrame(sharpness_frame, fg_color="transparent")
        sharpness_title_frame.pack(fill="x", padx=15, pady=(10, 5))
        
        ctk.CTkLabel(
            sharpness_title_frame,
            text="Sharpness (Nitidez):",
            font=ctk.CTkFont(size=FONT_SECTION, weight="bold")
        ).pack(side="left")
        
        self.sharpness_label = ctk.CTkLabel(
            sharpness_title_frame,
            text=f"✨ {self.sharpness_var.get():.2f}",
            font=ctk.CTkFont(size=FONT_TINY),
            text_color="#00BFFF"
        )
        self.sharpness_label.pack(side="left", padx=10)
        
        self.sharpness_slider = ctk.CTkSlider(
            sharpness_frame,
            from_=0.0,
            to=1.0,
            number_of_steps=100,
            variable=self.sharpness_var,
            command=self.on_sharpness_changed
        )
        self.sharpness_slider.pack(padx=15, pady=(0, 10), fill="x")
        self.setup_widget_focus(self.sharpness_slider)
        self.sharpness_var.trace_add('write', lambda *a: (self.mark_preset_custom(), self.update_custom_state()))
        
        # Aplicar focus indicators a todos los widgets enfocables del panel de configuración
        self._apply_focus_indicators_to_panel(self.config_panel)
        
        self.config_panel.grid_remove()  # Oculto inicialmente

    # ==================================================================================
    # ADVANCED SECTION HELPERS
    # ==================================================================================
    def _on_mipmap_bias_changed(self, value):
        try:
            self.mipmap_label.configure(text=f"Valor actual: {float(value):.1f}")
        except Exception:
            pass

    def _on_advanced_changed(self):
        # Actualizar config interna y persistir
        try:
            self.config['use_native_aa'] = bool(self.native_aa_var.get())
            self.config['mipmap_bias'] = float(self.mipmap_bias_var.get())
            self.config['last_spoof_name'] = self.dll_name_var.get()
            save_config(self.config)
        except Exception:
            pass
        # Marcar preset como custom y guardar snapshot
        self.mark_preset_custom()
        self.update_custom_state()

    def _reset_advanced_defaults(self):
        # Valores por defecto razonables
        self.native_aa_var.set(True)
        self.mipmap_bias_var.set(0.0)
        self.dll_name_var.set('dxgi.dll')
        self._on_advanced_changed()
    
    def _apply_focus_indicators_to_panel(self, panel):
        """Aplica indicadores de foco a todos los widgets enfocables en un panel.
        
        Args:
            panel: Panel donde buscar widgets enfocables
        """
        focusable_types = (ctk.CTkButton, ctk.CTkCheckBox, ctk.CTkEntry, 
                          ctk.CTkComboBox, ctk.CTkSlider, ctk.CTkRadioButton)
        
        def apply_recursive(widget):
            # Aplicar a widget actual si es enfocable
            if isinstance(widget, focusable_types):
                self.setup_widget_focus(widget)
            
            # Buscar en hijos recursivamente
            try:
                for child in widget.winfo_children():
                    apply_recursive(child)
            except:
                pass
        
        apply_recursive(panel)
        
    # ==================================================================================
    # PANEL 2: DETECCIÓN AUTOMÁTICA
    # ==================================================================================
    
    def create_auto_panel(self):
        """Panel de detección automática de juegos."""
        self.auto_panel = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.auto_panel.grid(row=0, column=0, sticky="nsew")
        self.auto_panel.grid_columnconfigure(0, weight=1)
        self.auto_panel.grid_rowconfigure(3, weight=1)  # Fila 3 ahora es la lista de juegos
        
        # Título del app arriba
        ctk.CTkLabel(
            self.auto_panel,
            text=APP_TITLE,
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#00BFFF"
        ).grid(row=0, column=0, pady=(15, 5))
        
        # Header con botones de acción
        auto_header = ctk.CTkFrame(self.auto_panel, fg_color="#1a1a1a", corner_radius=8)
        auto_header.grid(row=1, column=0, sticky="ew", padx=20, pady=(5, 20))
        auto_header.grid_columnconfigure(2, weight=1)
        
        # Padding interno
        header_content = ctk.CTkFrame(auto_header, fg_color="transparent")
        header_content.pack(fill="x", padx=15, pady=12)
        header_content.grid_columnconfigure(2, weight=1)
        
        # Botón escanear (inicia con lupa, cambia a rescan después)
        if self.icons.get("scan"):
            self.scan_btn = ctk.CTkButton(
                header_content,
                text="",
                image=self.icons["scan"],
                command=self.scan_games_action,
                width=80,
                height=50,
                fg_color="#3a3a3a",
                hover_color="#4a4a4a",
                corner_radius=8
            )
        else:
            self.scan_btn = ctk.CTkButton(
                header_content,
                text="🔍",
                command=self.scan_games_action,
                width=80,
                height=50,
                fg_color="#3a3a3a",
                hover_color="#4a4a4a",
                corner_radius=8,
                font=ctk.CTkFont(size=24)
            )
        self.scan_btn.grid(row=0, column=0, sticky="w", padx=(0, 10))
        self.setup_widget_focus(self.scan_btn)
        
        # Botón filtro
        if self.icons.get("filter"):
            self.btn_filter = ctk.CTkButton(
                header_content,
                text="",
                image=self.icons["filter"],
                command=self.open_filter,
                width=80,
                height=50,
                fg_color="#3a3a3a",
                hover_color="#4a4a4a",
                corner_radius=8
            )
        else:
            self.btn_filter = ctk.CTkButton(
                header_content,
                text="🔽",
                command=self.open_filter,
                width=80,
                height=50,
                fg_color="#3a3a3a",
                hover_color="#4a4a4a",
                corner_radius=8,
                font=ctk.CTkFont(size=20)
            )
        self.btn_filter.grid(row=0, column=1, sticky="w", padx=(0, 10))
        self.setup_widget_focus(self.btn_filter)
        
        # Contador
        self.games_counter_label = ctk.CTkLabel(
            header_content,
            text="0/0",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#00AAFF",
            fg_color="#2a2a2a",
            corner_radius=5,
            width=100,
            height=35
        )
        self.games_counter_label.grid(row=0, column=2, sticky="w")
        
        # Botones aplicar/eliminar
        btn_actions = ctk.CTkFrame(header_content, fg_color="transparent")
        btn_actions.grid(row=0, column=3, padx=15)
        
        self.apply_btn = ctk.CTkButton(
            btn_actions,
            text="✓ APLICAR",
            command=self.apply_to_selected,
            fg_color="#3a3a3a",
            hover_color="#4a4a4a",
            height=44,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.apply_btn.pack(side="left", padx=5)
        self.setup_widget_focus(self.apply_btn)
        
        self.remove_btn = ctk.CTkButton(
            btn_actions,
            text="❌ ELIMINAR",
            command=self.remove_from_selected,
            fg_color="#3a3a3a",
            hover_color="#4a4a4a",
            height=44,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.remove_btn.pack(side="left", padx=5)
        self.setup_widget_focus(self.remove_btn)
        
        self.open_folder_btn = ctk.CTkButton(
            btn_actions,
            text="📂 ABRIR CARPETA",
            command=self.open_selected_folders,
            fg_color="#3a3a3a",
            hover_color="#4a4a4a",
            height=44,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.open_folder_btn.pack(side="left", padx=5)
        self.setup_widget_focus(self.open_folder_btn)
        
        # Frame para barra de progreso y estado (inicialmente oculto)
        # Mejora #7: Altura variable (empezamos con altura compacta)
        self.progress_frame = ctk.CTkFrame(self.auto_panel, fg_color="#1a1a1a", corner_radius=8)
        self.progress_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 15))
        self.progress_frame.grid_columnconfigure(0, weight=1)
        self.progress_frame.grid_remove()  # Ocultar inicialmente
        
        # Frame interno para contenido (permite controlar padding)
        # Mejora #9: Variable para el padding actual
        self.progress_padding_normal = 12
        self.progress_padding_compact = 6
        
        progress_content = ctk.CTkFrame(self.progress_frame, fg_color="transparent")
        progress_content.grid(row=0, column=0, sticky="ew", padx=15, pady=self.progress_padding_normal)
        progress_content.grid_columnconfigure(0, weight=1)
        
        # Guardar referencia para poder cambiar padding
        self.progress_content = progress_content
        
        # Header con label de estado y botón cerrar
        header_frame = ctk.CTkFrame(progress_content, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        header_frame.grid_columnconfigure(0, weight=1)
        
        # Label de estado
        self.status_label = ctk.CTkLabel(
            header_frame,
            text="",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#00BFFF"
        )
        self.status_label.grid(row=0, column=0, sticky="w")
        
        # Mejora #5: Botón para ocultar la barra manualmente
        self.hide_progress_btn = ctk.CTkButton(
            header_frame,
            text="✕",
            width=25,
            height=25,
            corner_radius=12,
            fg_color="#2a2a2a",
            hover_color="#ff4444",
            command=self.hide_progress,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.hide_progress_btn.grid(row=0, column=1, padx=(10, 0))
        
        # Barra de progreso
        # Mejora #3: Color dinámico (se cambiará según estado)
        self.progress_bar = ctk.CTkProgressBar(
            progress_content,
            mode="determinate",
            height=20,
            corner_radius=10,
            progress_color="#00BFFF"  # Color por defecto (azul)
        )
        self.progress_bar.grid(row=1, column=0, sticky="ew")
        self.progress_bar.set(0)
        
        # Variables para mejoras
        self.progress_animation_running = False  # Para animación fade
        self.progress_start_time = None  # Para calcular tiempo estimado
        self.progress_items_processed = 0  # Para calcular velocidad
        
        # Mejora #3: Variables para resumen detallado
        self.last_operation_results = {
            'success': [],  # Lista de juegos exitosos
            'failed': [],   # Lista de juegos fallidos con razón
            'operation': '' # Tipo de operación (escaneo/instalación/desinstalación)
        }
        
        # Mejora #5: Diccionario para referencias de frames de juegos (preview en tiempo real)
        self.game_frames = {}  # {game_path: {'frame': frame, 'status_label': label}}
        
        # Hacer la barra clicable para mostrar detalles
        self.status_label.bind("<Button-1>", lambda e: self.show_operation_details())
        
        # Lista de juegos
        self.games_scrollable = ctk.CTkScrollableFrame(
            self.auto_panel,
            fg_color="transparent"
        )
        self.games_scrollable.grid(row=3, column=0, sticky="nsew", padx=20, pady=(0, 20))
        self.games_scrollable.grid_columnconfigure(0, weight=1)
        
        # Añadir drag-to-scroll
        self.setup_drag_scroll(self.games_scrollable)
        
        # Mensaje inicial
        # Mensaje inicial con icono rescan.png si está disponible
        self.no_games_label = ctk.CTkLabel(
            self.games_scrollable,
            text="No se encontraron juegos\n\nHaz clic en la rueda para escanear",
            font=ctk.CTkFont(size=14),
            text_color="#888888"
        )
        self.no_games_label.pack(pady=50)
        
        # Aplicar focus indicators a todos los widgets enfocables del panel de auto-detección
        self._apply_focus_indicators_to_panel(self.auto_panel)
        
        self.auto_panel.grid_remove()  # Oculto inicialmente
        
    # ==================================================================================
    # PANEL 3: RUTA MANUAL
    # ==================================================================================
    
    def create_manual_panel(self):
        """Panel de ruta manual."""
        self.manual_panel = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.manual_panel.grid(row=0, column=0, sticky="nsew")
        self.manual_panel.grid_columnconfigure(0, weight=1)
        
        # Título del app arriba
        ctk.CTkLabel(
            self.manual_panel,
            text=APP_TITLE,
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#00BFFF"
        ).pack(pady=(15, 5))
        
        # Título del panel
        ctk.CTkLabel(
            self.manual_panel,
            text="📂 RUTA MANUAL",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(pady=(5, 20))
        
        # Contenido
        manual_content = ctk.CTkFrame(
            self.manual_panel,
            fg_color="#1a1a1a",
            corner_radius=10,
            border_width=2,
            border_color="#2a2a2a"
        )
        manual_content.pack(fill="both", expand=True, padx=30, pady=10)
        
        # Instrucciones
        ctk.CTkLabel(
            manual_content,
            text="Selecciona la carpeta del juego manualmente:",
            font=ctk.CTkFont(size=14),
            text_color="#CCCCCC"
        ).pack(pady=(20, 10))
        
        # Path display
        path_frame = ctk.CTkFrame(
            manual_content,
            fg_color="#0a0a0a",
            corner_radius=5,
            border_width=1,
            border_color="#333333"
        )
        path_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(
            path_frame,
            textvariable=self.manual_path_var,
            font=ctk.CTkFont(size=12),
            text_color="#AAAAAA",
            wraplength=500
        ).pack(pady=15, padx=15)
        
        # Botón examinar
        browse_btn = ctk.CTkButton(
            manual_content,
            text="📁 EXAMINAR CARPETA",
            command=self.browse_folder,
            font=ctk.CTkFont(size=16, weight="bold"),
            height=55,
            fg_color="#3a3a3a",
            hover_color="#4a4a4a",
            corner_radius=8
        )
        browse_btn.pack(pady=20)
        
        # Status
        self.manual_status_label = ctk.CTkLabel(
            manual_content,
            textvariable=self.manual_status_var,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.manual_status_label.pack(pady=10)
        
        # Botones aplicar/eliminar
        buttons_frame = ctk.CTkFrame(manual_content, fg_color="transparent")
        buttons_frame.pack(pady=(20, 30))
        
        self.manual_apply_btn = ctk.CTkButton(
            buttons_frame,
            text="✅ APLICAR MOD",
            command=self.apply_manual,
            font=ctk.CTkFont(size=16, weight="bold"),
            height=55,
            width=200,
            fg_color="#3a3a3a",
            hover_color="#4a4a4a",
            corner_radius=8,
            state="disabled"
        )
        self.manual_apply_btn.pack(side="left", padx=10)
        
        self.manual_uninstall_btn = ctk.CTkButton(
            buttons_frame,
            text="❌ ELIMINAR MOD",
            command=self.uninstall_manual,
            font=ctk.CTkFont(size=16, weight="bold"),
            height=55,
            width=200,
            fg_color="#3a3a3a",
            hover_color="#4a4a4a",
            corner_radius=8,
            state="disabled"
        )
        self.manual_uninstall_btn.pack(side="left", padx=10)
        
        # Aplicar focus indicators al panel manual
        self._apply_focus_indicators_to_panel(self.manual_panel)
        
        self.manual_panel.grid_remove()  # Oculto inicialmente
        
    # ==================================================================================
    # PANEL 4: AJUSTES DE LA APP
    # ==================================================================================
    
    def create_settings_panel(self):
        """Panel de ajustes de la aplicación."""
        self.settings_panel = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.settings_panel.grid(row=0, column=0, sticky="nsew")
        
        # Título del app arriba
        ctk.CTkLabel(
            self.settings_panel,
            text=APP_TITLE,
            font=ctk.CTkFont(size=FONT_TITLE, weight="bold"),
            text_color="#00BFFF"
        ).pack(pady=(15, 5))
        
        # Título del panel
        ctk.CTkLabel(
            self.settings_panel,
            text="⚙️ AJUSTES DE LA APP",
            font=ctk.CTkFont(size=FONT_TITLE, weight="bold")
        ).pack(pady=(5, 20))
        
        # Scrollable content
        settings_scroll = ctk.CTkScrollableFrame(self.settings_panel, fg_color="transparent")
        settings_scroll.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        self.setup_drag_scroll(settings_scroll)
        
        # === INFO GPU DETECTADA (ARRIBA DE TODO) ===
        gpu_info_frame = ctk.CTkFrame(settings_scroll, fg_color="#1a1a1a", corner_radius=8)
        gpu_info_frame.pack(fill="x", pady=10)
        
        gpu_names = {
            'nvidia': ('NVIDIA', '#76B900'),
            'amd': ('AMD', '#ED1C24'),
            'intel': ('Intel', '#0071C5'),
            'unknown': ('Desconocida', '#888888')
        }
        gpu_display_name, gpu_color = gpu_names.get(self.gpu_vendor, ('Desconocida', '#888888'))
        
        ctk.CTkLabel(
            gpu_info_frame,
            text=f"🖥️ GPU Detectada: {gpu_display_name}",
            font=ctk.CTkFont(size=FONT_SECTION, weight="bold"),
            text_color=gpu_color
        ).pack(padx=15, pady=(10, 5), anchor="w")
        
        # Explicación según tipo de GPU
        if self.use_dual_mod:
            mode_text = "✅ Configuración recomendada: OptiScaler + dlssg-to-fsr3"
            mode_detail = "Tu GPU necesita ambos mods para Frame Generation"
            mode_color = "#00FF00"
        else:
            mode_text = "ℹ️ Configuración recomendada: OptiScaler"
            mode_detail = "Tu GPU NVIDIA tiene DLSS nativo, solo necesitas OptiScaler para upscaling adicional"
            mode_color = "#00BFFF"
        
        ctk.CTkLabel(
            gpu_info_frame,
            text=mode_text,
            font=ctk.CTkFont(size=FONT_NORMAL, weight="bold"),
            text_color=mode_color
        ).pack(padx=15, pady=(0, 2), anchor="w")
        
        ctk.CTkLabel(
            gpu_info_frame,
            text=mode_detail,
            font=ctk.CTkFont(size=FONT_TINY),
            text_color="#888888"
        ).pack(padx=15, pady=(0, 10), anchor="w")
        
        # === TEMA ===
        # Tema Oscuro forzado (Claro está roto, se implementará en futuro)
        theme_frame = ctk.CTkFrame(settings_scroll, fg_color="#1a1a1a", corner_radius=8)
        theme_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(
            theme_frame,
            text="Tema:",
            font=ctk.CTkFont(size=FONT_SECTION, weight="bold")
        ).pack(anchor="w", padx=15, pady=(10, 5))
        
        ctk.CTkLabel(
            theme_frame,
            text="🌙 Modo Oscuro (activo)",
            font=ctk.CTkFont(size=FONT_NORMAL),
            text_color="#00BFFF"
        ).pack(anchor="w", padx=15, pady=(0, 10))
        
        # === ESCALA ===
        scale_frame = ctk.CTkFrame(settings_scroll, fg_color="#1a1a1a", corner_radius=8)
        scale_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(
            scale_frame,
            text="Escala UI:",
            font=ctk.CTkFont(size=FONT_SECTION, weight="bold")
        ).pack(anchor="w", padx=15, pady=(10, 5))
        
        WideComboBox(
            scale_frame,
            values=["80%", "90%", "100%", "110%", "120%"],
            variable=self.scale_var,
            width=300,
            font=ctk.CTkFont(size=FONT_NORMAL),
            command=lambda v: self.on_scale_changed()
        ).pack(fill="x", padx=15, pady=(0, 10))
        
        # === GESTIÓN DE MODS ===
        mod_frame = ctk.CTkFrame(settings_scroll, fg_color="#1a1a1a", corner_radius=8)
        mod_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(
            mod_frame,
            text="📥 Gestión de Mods",
            font=ctk.CTkFont(size=FONT_SECTION, weight="bold")
        ).pack(anchor="w", padx=15, pady=(10, 5))
        
        # OptiScaler
        optiscaler_label_text = "OptiScaler (Upscaling) - REQUERIDO"
        ctk.CTkLabel(
            mod_frame,
            text=optiscaler_label_text,
            font=ctk.CTkFont(size=FONT_NORMAL, weight="bold"),
            text_color="#00BFFF"
        ).pack(anchor="w", padx=15, pady=(10, 2))
        
        ctk.CTkLabel(
            mod_frame,
            text="✅ Necesario para todas las GPUs - Proporciona FSR 3.1, XeSS y mejoras",
            font=ctk.CTkFont(size=FONT_TINY),
            text_color="#888888"
        ).pack(anchor="w", padx=15, pady=(0, 5))
        
        ctk.CTkButton(
            mod_frame,
            text="⬇️ Descargar / Gestionar OptiScaler",
            command=self.open_optiscaler_downloader,
            height=40,
            fg_color="#3a3a3a",
            hover_color="#4a4a4a",
            font=ctk.CTkFont(size=FONT_NORMAL, weight="bold")
        ).pack(fill="x", padx=15, pady=5)
        
        # Selector de versión OptiScaler
        version_frame = ctk.CTkFrame(mod_frame, fg_color="transparent")
        version_frame.pack(fill="x", padx=15, pady=(5, 5))
        
        ctk.CTkLabel(
            version_frame,
            text="Versión activa:",
            font=ctk.CTkFont(size=FONT_SMALL),
            text_color="#888888"
        ).pack(side="left", padx=(0, 10))
        
        # Obtener versiones y establecer valor inicial
        optiscaler_versions = self.get_downloaded_optiscaler_versions()
        default_optiscaler = optiscaler_versions[0] if optiscaler_versions else "Sin versiones descargadas"
        
        self.optiscaler_version_var = ctk.StringVar(value=default_optiscaler)
        self.optiscaler_version_combo = WideComboBox(
            version_frame,
            variable=self.optiscaler_version_var,
            values=optiscaler_versions,
            width=250,
            font=ctk.CTkFont(size=FONT_NORMAL)
        )
        self.optiscaler_version_combo.pack(side="left", fill="x", expand=True)

        # Botón de carpeta personalizada
        ctk.CTkButton(
            mod_frame,
            text="📂 Usar carpeta personalizada...",
            command=self.select_custom_mod_folder,
            height=30,
            fg_color="#2a2a2a",
            hover_color="#3a3a3a",
            font=ctk.CTkFont(size=11)
        ).pack(fill="x", padx=15, pady=(2, 5))
        
        # === OptiPatcher (Plugin ASI) ===
        ctk.CTkLabel(
            mod_frame,
            text="OptiPatcher (Plugin ASI)",
            font=ctk.CTkFont(size=FONT_NORMAL, weight="bold"),
            text_color="#00BFFF"
        ).pack(anchor="w", padx=15, pady=(15, 2))
        
        ctk.CTkLabel(
            mod_frame,
            text="🔧 Plugin que mejora compatibilidad eliminando necesidad de spoofing",
            font=ctk.CTkFont(size=FONT_TINY),
            text_color="#888888"
        ).pack(anchor="w", padx=15, pady=(0, 5))
        
        # Checkbox para habilitar/deshabilitar
        self.optipatcher_enabled_var = ctk.BooleanVar(value=True)
        self.optipatcher_check = ctk.CTkCheckBox(
            mod_frame,
            text="✅ Instalar OptiPatcher automáticamente (Recomendado)",
            variable=self.optipatcher_enabled_var,
            font=ctk.CTkFont(size=FONT_SMALL),
            command=self._on_optipatcher_changed
        )
        self.optipatcher_check.pack(anchor="w", padx=15, pady=5)
        self.setup_widget_focus(self.optipatcher_check)
        
        # Frame horizontal para versión y botones
        optipatcher_controls = ctk.CTkFrame(mod_frame, fg_color="transparent")
        optipatcher_controls.pack(fill="x", padx=15, pady=(5, 5))
        
        # Label de estado/versión (ocupa espacio flexible)
        self.optipatcher_status_label = ctk.CTkLabel(
            optipatcher_controls,
            text="📦 Plugin no descargado",
            font=ctk.CTkFont(size=FONT_SMALL),
            text_color="#FFA500",
            anchor="w"
        )
        self.optipatcher_status_label.pack(side="left", fill="x", expand=True)
        
        # Botón de verificar/descargar (cambia dinámicamente)
        self.optipatcher_action_btn = ctk.CTkButton(
            optipatcher_controls,
            text="🔄 Buscar actualizaciones",
            command=self.check_optipatcher_updates,
            height=30,
            width=160,
            fg_color="#2a2a2a",
            hover_color="#3a3a3a",
            font=ctk.CTkFont(size=FONT_TINY)
        )
        self.optipatcher_action_btn.pack(side="left", padx=5)
        
        # Botón GitHub
        ctk.CTkButton(
            optipatcher_controls,
            text="🔗 GitHub",
            command=lambda: webbrowser.open("https://github.com/optiscaler/OptiPatcher/releases"),
            height=30,
            width=80,
            fg_color="#2a2a2a",
            hover_color="#3a3a3a",
            font=ctk.CTkFont(size=FONT_TINY)
        ).pack(side="left")
        
        # Variable para guardar info de última release
        self.optipatcher_latest_release = None
        
        # Actualizar estado al iniciar
        self.after(100, self.update_optipatcher_status)
        
        # Info expandible
        optipatcher_info_frame = ctk.CTkFrame(mod_frame, fg_color="#0a0a0a", corner_radius=6)
        optipatcher_info_frame.pack(fill="x", padx=15, pady=(0, 5))
        
        info_text = (
            "✅ Soporta 171+ juegos (Wukong, Stalker 2, Hogwarts Legacy, etc.)\n"
            "✅ Elimina errores 'D3D12 not supported' en Intel Arc\n"
            "✅ Mejora estabilidad en GPUs AMD/Intel\n"
            "✅ No modifica archivos del juego (parches en memoria)"
        )
        
        ctk.CTkLabel(
            optipatcher_info_frame,
            text=info_text,
            font=ctk.CTkFont(size=FONT_TINY-1),
            text_color="#aaaaaa",
            justify="left"
        ).pack(anchor="w", padx=10, pady=5)
        
        # dlssg-to-fsr3 - Mostrar si es necesario
        if self.use_dual_mod:
            nukem_label_text = "dlssg-to-fsr3 (Frame Generation) - REQUERIDO"
            nukem_status_text = "✅ Necesario para Frame Generation en AMD/Intel/NVIDIA no-RTX40"
            nukem_color = "#FF6B35"
        else:
            nukem_label_text = "dlssg-to-fsr3 (Frame Generation) - OPCIONAL"
            nukem_status_text = "ℹ️ No necesario - Tu GPU NVIDIA ya tiene DLSS Frame Generation nativo"
            nukem_color = "#888888"
        
        ctk.CTkLabel(
            mod_frame,
            text=nukem_label_text,
            font=ctk.CTkFont(size=FONT_NORMAL, weight="bold"),
            text_color=nukem_color
        ).pack(anchor="w", padx=15, pady=(10, 2))
        
        ctk.CTkLabel(
            mod_frame,
            text=nukem_status_text,
            font=ctk.CTkFont(size=FONT_TINY),
            text_color="#888888"
        ).pack(anchor="w", padx=15, pady=(0, 5))
        
        # Link a Nexus Mods
        ctk.CTkLabel(
            mod_frame,
            text="💡 Los binarios están en Nexus Mods:",
            font=ctk.CTkFont(size=FONT_TINY),
            text_color="#888888"
        ).pack(anchor="w", padx=15, pady=(5, 2))
        
        nexus_btn = ctk.CTkButton(
            mod_frame,
            text="🔗 Descargar desde Nexus Mods",
            command=self.open_nexus_mods,
            height=30,
            fg_color="#2a2a2a",
            hover_color="#3a3a3a",
            font=ctk.CTkFont(size=FONT_SMALL)
        )
        nexus_btn.pack(fill="x", padx=15, pady=(0, 10))
        
        # Campo de ruta + botón examinar
        ctk.CTkLabel(
            mod_frame,
            text="Ruta de la carpeta descargada:",
            font=ctk.CTkFont(size=FONT_SMALL),
            text_color="#888888"
        ).pack(anchor="w", padx=15, pady=(5, 2))
        
        path_frame = ctk.CTkFrame(mod_frame, fg_color="transparent")
        path_frame.pack(fill="x", padx=15, pady=(0, 10))
        
        # Campo de texto para la ruta
        self.nukem_path_var = ctk.StringVar(value=self.config.get("nukem_mod_path", ""))
        self.nukem_path_entry = ctk.CTkEntry(
            path_frame,
            textvariable=self.nukem_path_var,
            placeholder_text="Pega aquí la ruta o usa el botón Examinar",
            font=ctk.CTkFont(size=FONT_SMALL),
            fg_color="#2a2a2a",
            height=35
        )
        self.nukem_path_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        # Botón examinar
        ctk.CTkButton(
            path_frame,
            text="🔍 Examinar",
            command=self.browse_nukem_folder,
            height=35,
            width=100,
            fg_color="#3a3a3a",
            hover_color="#4a4a4a",
            font=ctk.CTkFont(size=FONT_SMALL)
        ).pack(side="left")
        
        # Carpeta de mods
        ctk.CTkButton(
            mod_frame,
            text="📂 Abrir carpeta de mods...",
            command=self.open_mod_folder,
            height=35,
            fg_color="#2a2a2a",
            hover_color="#3a3a3a"
        ).pack(fill="x", padx=15, pady=(10, 10))
        
        # === CARPETAS DE ESCANEO ===
        scan_frame = ctk.CTkFrame(settings_scroll, fg_color="#1a1a1a", corner_radius=8)
        scan_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(
            scan_frame,
            text="Carpetas de Escaneo",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=15, pady=(10, 5))
        
        ctk.CTkButton(
            scan_frame,
            text="📁 Gestionar Carpetas de Juegos...",
            command=self.manage_scan_folders,
            height=40,
            fg_color="#3a3a3a",
            hover_color="#4a4a4a",
            font=ctk.CTkFont(size=13, weight="bold")
        ).pack(fill="x", padx=15, pady=(5, 10))
        
        # === REGISTRO ===
        log_frame = ctk.CTkFrame(settings_scroll, fg_color="#1a1a1a", corner_radius=8)
        log_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(
            log_frame,
            text="Registro de Operaciones",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=15, pady=(10, 5))
        
        ctk.CTkButton(
            log_frame,
            text="💾 Guardar Log",
            command=self.save_log,
            height=40,
            fg_color="#3a3a3a",
            hover_color="#4a4a4a",
            font=ctk.CTkFont(size=13, weight="bold")
        ).pack(fill="x", padx=15, pady=(0, 10))
        
        # Aplicar focus indicators al panel de ajustes
        self._apply_focus_indicators_to_panel(self.settings_panel)
        
        self.settings_panel.grid_remove()  # Oculto inicialmente
        
    # ==================================================================================
    # PANEL 5: AYUDA
    # ==================================================================================
    
    def create_help_panel(self):
        """Panel de ayuda completo."""
        self.help_panel = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.help_panel.grid(row=0, column=0, sticky="nsew")
        self.help_panel.grid_columnconfigure(0, weight=1)
        self.help_panel.grid_rowconfigure(1, weight=1)
        
        # Título
        ctk.CTkLabel(
            self.help_panel,
            text=APP_TITLE,
            font=ctk.CTkFont(size=FONT_TITLE, weight="bold"),
            text_color="#00BFFF"
        ).grid(row=0, column=0, pady=(15, 5))
        
        # Scrollable content
        help_scroll = ctk.CTkScrollableFrame(self.help_panel, fg_color="transparent")
        help_scroll.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        self.setup_drag_scroll(help_scroll)
        
        # === SECCIÓN: CONTROLES DE TECLADO ===
        keyboard_frame = ctk.CTkFrame(help_scroll, fg_color="#1a1a1a", corner_radius=8)
        keyboard_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(
            keyboard_frame,
            text="⌨️ CONTROLES DE TECLADO",
            font=ctk.CTkFont(size=FONT_SECTION, weight="bold"),
            text_color=COLOR_PRIMARY
        ).pack(anchor="w", padx=15, pady=(15, 10))
        
        keyboard_controls = [
            ("Tab / Shift+Tab", "Navegar entre elementos"),
            ("Enter / Espacio", "Activar botón o checkbox"),
            ("Flechas ↑↓", "Navegar en listas y combos"),
            ("Ctrl + A", "Seleccionar todos los juegos"),
            ("Ctrl + D", "Deseleccionar todos"),
            ("Ctrl + F", "Abrir filtro de juegos"),
            ("F5", "Reescanear juegos"),
            ("Esc", "Cerrar ventanas modales"),
        ]
        
        for key, desc in keyboard_controls:
            control_row = ctk.CTkFrame(keyboard_frame, fg_color="#2a2a2a", corner_radius=5)
            control_row.pack(fill="x", padx=15, pady=3)
            
            ctk.CTkLabel(
                control_row,
                text=key,
                font=ctk.CTkFont(size=FONT_NORMAL, weight="bold"),
                text_color=COLOR_PRIMARY,
                width=150,
                anchor="w"
            ).pack(side="left", padx=10, pady=8)
            
            ctk.CTkLabel(
                control_row,
                text=desc,
                font=ctk.CTkFont(size=FONT_NORMAL),
                text_color="#CCCCCC",
                anchor="w"
            ).pack(side="left", fill="x", expand=True, padx=10, pady=8)
        
        ctk.CTkLabel(
            keyboard_frame,
            text=" ",
            font=ctk.CTkFont(size=6)
        ).pack(pady=5)
        
        # === SECCIÓN: CONTROLES DE GAMEPAD ===
        gamepad_frame = ctk.CTkFrame(help_scroll, fg_color="#1a1a1a", corner_radius=8)
        gamepad_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(
            gamepad_frame,
            text="🎮 CONTROLES DE GAMEPAD",
            font=ctk.CTkFont(size=FONT_SECTION, weight="bold"),
            text_color=COLOR_PRIMARY
        ).pack(anchor="w", padx=15, pady=(15, 10))
        
        gamepad_controls = [
            ("D-Pad / Stick Izq.", "Navegar entre elementos"),
            ("Botón A", "Seleccionar / Confirmar"),
            ("Botón B", "Volver / Cancelar"),
            ("Botón X", "Abrir configuración rápida"),
            ("Botón Y", "Abrir filtro"),
            ("LB / RB", "Cambiar entre pestañas"),
            ("LT / RT", "Scroll rápido en listas"),
            ("Start", "Aplicar cambios"),
            ("Select", "Abrir ayuda"),
        ]
        
        for key, desc in gamepad_controls:
            control_row = ctk.CTkFrame(gamepad_frame, fg_color="#2a2a2a", corner_radius=5)
            control_row.pack(fill="x", padx=15, pady=3)
            
            ctk.CTkLabel(
                control_row,
                text=key,
                font=ctk.CTkFont(size=FONT_NORMAL, weight="bold"),
                text_color=COLOR_SUCCESS,
                width=180,
                anchor="w"
            ).pack(side="left", padx=10, pady=8)
            
            ctk.CTkLabel(
                control_row,
                text=desc,
                font=ctk.CTkFont(size=FONT_NORMAL),
                text_color="#CCCCCC",
                anchor="w"
            ).pack(side="left", fill="x", expand=True, padx=10, pady=8)
        
        ctk.CTkLabel(
            gamepad_frame,
            text="💡 El gamepad se detecta automáticamente al conectarse",
            font=ctk.CTkFont(size=FONT_SMALL),
            text_color="#888888"
        ).pack(anchor="w", padx=15, pady=(5, 10))
        
        # === SECCIÓN: FAQs ===
        faq_frame = ctk.CTkFrame(help_scroll, fg_color="#1a1a1a", corner_radius=8)
        faq_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(
            faq_frame,
            text="❓ PREGUNTAS FRECUENTES",
            font=ctk.CTkFont(size=FONT_SECTION, weight="bold"),
            text_color=COLOR_PRIMARY
        ).pack(anchor="w", padx=15, pady=(15, 10))
        
        faqs = [
            ("¿Qué es OptiScaler?", 
             "Mod que mejora el upscaling en juegos, añadiendo FSR 3.1, XeSS y optimizaciones."),
            ("¿Necesito ambos mods?", 
             "GPUs AMD/Intel necesitan OptiScaler + dlssg-to-fsr3 para Frame Generation. NVIDIA solo OptiScaler."),
            ("¿El mod funciona en todos los juegos?", 
             "Funciona en juegos con DLSS, FSR o XeSS nativo. No todos los juegos son compatibles."),
            ("¿Puedo usar diferentes versiones del mod?", 
             "Sí, puedes descargar múltiples versiones y cambiar entre ellas en Ajustes."),
            ("¿Los cambios afectan solo al juego seleccionado?", 
             "La configuración global se aplica a todos los juegos donde instales el mod."),
            ("¿Qué hago si el juego no arranca?", 
             "Prueba cambiar la DLL de inyección (dxgi.dll, d3d11.dll, d3d12.dll) o desinstala el mod."),
            ("¿Cómo añado carpetas personalizadas para escanear?", 
             "Ve a Ajustes → Gestionar Carpetas de Juegos. Puedes añadir cualquier carpeta con juegos."),
            ("¿Funciona con juegos de Xbox/Windows Store?", 
             "Sí, la app detecta automáticamente juegos de Xbox Game Pass y Windows Store."),
            ("¿Qué son los WideComboBox con autoscroll?", 
             "Menús desplegables optimizados para navegación con gamepad que hacen scroll automático."),
            ("¿Cómo funciona el Overlay de FPS? (NUEVO v2.4)", 
             "El overlay muestra FPS, Frame Time y mensajes del sistema directamente en el juego sin necesidad de RTSS u otros programas. Configura modo (Básico/Completo), posición (9 ubicaciones), escala (50%-200%) y tamaño de fuente (10-24px) en la sección Configuración del Mod."),
        ]
        
        for i, (question, answer) in enumerate(faqs):
            faq_item = ctk.CTkFrame(faq_frame, fg_color="#2a2a2a", corner_radius=5)
            faq_item.pack(fill="x", padx=15, pady=5)
            
            ctk.CTkLabel(
                faq_item,
                text=f"Q: {question}",
                font=ctk.CTkFont(size=FONT_NORMAL, weight="bold"),
                text_color=COLOR_WARNING,
                anchor="w",
                wraplength=950
            ).pack(anchor="w", padx=15, pady=(10, 5))
            
            ctk.CTkLabel(
                faq_item,
                text=f"A: {answer}",
                font=ctk.CTkFont(size=FONT_NORMAL),
                text_color="#CCCCCC",
                anchor="w",
                wraplength=950
            ).pack(anchor="w", padx=15, pady=(0, 10))
        
        ctk.CTkLabel(
            faq_frame,
            text=" ",
            font=ctk.CTkFont(size=6)
        ).pack(pady=5)
        
        # === SECCIÓN: CONFIGURACIÓN AVANZADA ===
        config_help_frame = ctk.CTkFrame(help_scroll, fg_color="#1a1a1a", corner_radius=8)
        config_help_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(
            config_help_frame,
            text="⚙️ OPCIONES DE CONFIGURACIÓN",
            font=ctk.CTkFont(size=FONT_SECTION, weight="bold"),
            text_color=COLOR_PRIMARY
        ).pack(anchor="w", padx=15, pady=(15, 10))
        
        config_options = [
            ("DLL de Inyección", 
             "dxgi.dll: Funciona en la mayoría de juegos (prueba primero esta). d3d11.dll: Para juegos DirectX 11. d3d12.dll: Para juegos DirectX 12. winmm.dll: Alternativa si las demás fallan."),
            ("Reescalador (Upscaler)", 
             "Automático: El mod detecta el mejor upscaler. FSR 3.1: Mejor para AMD, funciona en todas las GPUs. XeSS: Optimizado para Intel Arc. DLSS: Solo para GPUs NVIDIA con tensor cores."),
            ("Modo de Reescalado", 
             "Ultra Rendimiento: +60% FPS, menor calidad visual. Rendimiento: +40% FPS, calidad aceptable. Equilibrado: Balance entre FPS y calidad. Calidad: +20% FPS, mejor imagen. Ultra Calidad: Mínima mejora de FPS, máxima calidad."),
            ("Frame Generation", 
             "Desactivado: Sin generación de frames. OptiFG: Frame Gen nativo de OptiScaler (~+80% FPS). FSR-FG: Usa mod de Nukem (requiere dlssg-to-fsr3 instalado). AMD/Intel necesitan ambos mods para FG. NVIDIA solo necesita OptiScaler."),
            ("Límite de FPS", 
             "0: Sin límite (usa todo el rendimiento de GPU). 30-60 FPS: Para mejor duración de batería. 90-120 FPS: Para pantallas de alta frecuencia. 144+ FPS: Para monitores gaming."),
            ("Sharpness (Nitidez)", 
             "0.0-0.3: Imagen suave, menos artefactos. 0.5: Balance recomendado. 0.7-1.0: Imagen muy nítida, puede crear artefactos. Ajusta según preferencia visual."),
            ("📊 Overlay Settings (NUEVO v2.4)", 
             "Desactivado: Sin overlay en juego. Básico: Muestra solo FPS (bajo impacto). Completo: FPS + Frame Time + Mensajes del sistema. Personaliza posición (9 ubicaciones), escala (50%-200%) y tamaño de fuente (10-24px). Perfecto para monitorear rendimiento sin programas externos."),
            ("🔧 OptiPatcher (Plugin - NUEVO v2.4)", 
             "Plugin ASI que mejora compatibilidad en 171+ juegos. Elimina necesidad de spoofing y parches en memoria sin modificar archivos. Soluciona errores 'D3D12 not supported' en Intel Arc. Mejora estabilidad en AMD/Intel. Instalación automática recomendada. Soporta: Wukong, Stalker 2, Hogwarts Legacy, FF7 Rebirth y muchos más."),
            ("🌈 HDR Settings", 
             "Auto HDR: Activa automáticamente el espacio de color HDR. NVIDIA Override: Fuerza configuración HDR en GPUs NVIDIA. Max Range: Controla el rango dinámico (nits). Requiere monitor HDR compatible."),
            ("🐛 Debug/Logging", 
             "Off/Error: Sin logs o solo errores críticos. Warn/Info: Logs informativos para troubleshooting. Debug/Trace: Logs detallados para reportar bugs. Consola: Abre ventana de consola en tiempo real. Log a archivo: Guarda logs en disco."),
            ("🎯 Quality Overrides", 
             "Permite personalizar los ratios de cada modo de calidad. Quality: 1.3-1.7x (más calidad). Balanced: 1.5-2.0x (equilibrado). Performance: 1.7-2.3x (más FPS). Ultra Perf: 2.5-3.5x (máximo FPS). Desactiva para usar valores por defecto del mod."),
            ("✨ CAS Sharpening", 
             "RCAS: Algoritmo de nitidez robusto (recomendado). CAS: Contrast Adaptive Sharpening (alternativa). Motion Sharpness: Ajusta nitidez según movimiento de cámara. Contrast Boost: Aumenta nitidez en áreas de alto contraste. Valor: 0.0-1.3 intensidad del efecto."),
            ("🎭 NVNGX Spoofing", 
             "Permite que GPUs AMD/Intel usen características de NVIDIA. DX12/DX11/Vulkan: Activa spoofing por API gráfica. Necesario para Frame Generation en GPUs no-NVIDIA. Todo activado por defecto (recomendado)."),
        ]
        
        for option, desc in config_options:
            option_item = ctk.CTkFrame(config_help_frame, fg_color="#2a2a2a", corner_radius=5)
            option_item.pack(fill="x", padx=15, pady=5)
            
            ctk.CTkLabel(
                option_item,
                text=f"🔧 {option}",
                font=ctk.CTkFont(size=FONT_NORMAL, weight="bold"),
                text_color=COLOR_PRIMARY,
                anchor="w"
            ).pack(anchor="w", padx=15, pady=(10, 5))
            
            ctk.CTkLabel(
                option_item,
                text=desc,
                font=ctk.CTkFont(size=FONT_NORMAL),
                text_color="#CCCCCC",
                anchor="w",
                wraplength=950,
                justify="left"
            ).pack(anchor="w", padx=15, pady=(0, 10))
        
        ctk.CTkLabel(
            config_help_frame,
            text=" ",
            font=ctk.CTkFont(size=6)
        ).pack(pady=5)
        
        # === SECCIÓN: ABOUT ===
        about_frame = ctk.CTkFrame(help_scroll, fg_color="#1a1a1a", corner_radius=8)
        about_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(
            about_frame,
            text="ℹ️ ACERCA DE",
            font=ctk.CTkFont(size=FONT_SECTION, weight="bold"),
            text_color=COLOR_PRIMARY
        ).pack(anchor="w", padx=15, pady=(15, 10))
        
        about_text = f"""Gestor Automatizado de OptiScaler V{APP_VERSION}
        
Aplicación para gestionar e instalar mods de upscaling en juegos de PC.

🔧 Desarrollado para handheld PCs (Steam Deck, ROG Ally, Legion Go, etc.)
📦 Integra OptiScaler (cdozdil) y dlssg-to-fsr3 (Nukem9)
🎮 Soporte completo de gamepad y controles táctiles
🚀 Escaneo automático de juegos en Steam, Epic Games, Xbox y carpetas personalizadas

Versión: {APP_VERSION}
Licencia: Open Source
        """
        
        ctk.CTkLabel(
            about_frame,
            text=about_text,
            font=ctk.CTkFont(size=FONT_NORMAL),
            text_color="#CCCCCC",
            anchor="w",
            justify="left"
        ).pack(anchor="w", padx=15, pady=(0, 10))
        
        # Enlaces
        links_frame = ctk.CTkFrame(about_frame, fg_color="#2a2a2a", corner_radius=5)
        links_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        ctk.CTkButton(
            links_frame,
            text="📖 OptiScaler GitHub",
            command=lambda: self.open_url("https://github.com/cdozdil/OptiScaler"),
            height=35,
            fg_color="#3a3a3a",
            hover_color="#4a4a4a",
            font=ctk.CTkFont(size=FONT_NORMAL)
        ).pack(fill="x", padx=10, pady=5)
        
        ctk.CTkButton(
            links_frame,
            text="📖 dlssg-to-fsr3 GitHub",
            command=lambda: self.open_url("https://github.com/Nukem9/dlssg-to-fsr3"),
            height=35,
            fg_color="#3a3a3a",
            hover_color="#4a4a4a",
            font=ctk.CTkFont(size=FONT_NORMAL)
        ).pack(fill="x", padx=10, pady=5)
        
        # Aplicar focus indicators al panel de ayuda
        self._apply_focus_indicators_to_panel(self.help_panel)
        
        self.help_panel.grid_remove()  # Oculto inicialmente
        
    # ==================================================================================
    # NAVEGACIÓN
    # ==================================================================================
    
    def show_panel(self, panel_name):
        """Muestra un panel y oculta los demás."""
        # Ocultar todos
        for panel in [self.config_panel, self.auto_panel, self.manual_panel, 
                      self.settings_panel, self.help_panel]:
            panel.grid_remove()
        
        # Resetear botones
        for btn in self.nav_buttons.values():
            btn.configure(border_width=0, border_color="")
        
        # Mostrar el solicitado
        panel_map = {
            "config": self.config_panel,
            "auto": self.auto_panel,
            "manual": self.manual_panel,
            "settings": self.settings_panel,
            "help": self.help_panel
        }
        
        if panel_name in panel_map:
            panel_map[panel_name].grid()
            self.nav_buttons[panel_name].configure(border_width=3, border_color="#00BFFF")
            
            # Actualizar combos de versión si es el panel de settings
            if panel_name == "settings":
                self.update_version_combos()
            
            # Actualizar visibilidad de opciones si es config
            if panel_name == "config":
                self.update_config_visibility()
            
            # Resaltar botón activo
            self.highlight_active_nav(panel_name)
            
            # Mantener foco en sidebar al cambiar de panel (navegación lógica)
            if hasattr(self, 'focus_zone'):
                self.focus_zone = 'sidebar'
                if panel_name in self.nav_buttons:
                    self.safe_focus_widget(self.nav_buttons[panel_name])
            
    def show_config_panel(self):
        self.show_panel("config")
        
    def show_auto_panel(self):
        self.show_panel("auto")
        
    def show_manual_panel(self):
        self.show_panel("manual")
        
    def show_settings_panel(self):
        self.show_panel("settings")
        
    def show_help_panel(self):
        self.show_panel("help")
        
    # ==================================================================================
    # FUNCIONES DE ACCIÓN
    # ==================================================================================
    
    def apply_preset(self, preset):
        """Aplica un preset de configuración rápida."""
        presets = {
            "performance": {
                "fg_mode": "OptiFG",
                "upscale_mode": "Rendimiento",
                "upscaler": "FSR 3.1",
                "sharpness": 0.3,
                "fps_limit": 0,
                # HDR: Desactivado en modo Performance para máximo rendimiento
                "auto_hdr": False,
                "nvidia_hdr_override": False,
                "hdr_rgb_range": 100.0,
                # Logging: Mínimo en Performance
                "log_level": "Error",
                "open_console": False,
                "log_to_file": False,
                # Quality Overrides: Desactivado
                "quality_override_enabled": False,
                "quality_ratio": 1.5,
                "balanced_ratio": 1.7,
                "performance_ratio": 2.0,
                "ultra_perf_ratio": 3.0,
                # CAS: Activado con sharpening bajo
                "cas_enabled": True,
                "cas_type": "RCAS",
                "cas_sharpness": 0.3,
                # NVNGX: Todo activado
                "nvngx_dx12": True,
                "nvngx_dx11": True,
                "nvngx_vulkan": True,
                # Overlay: Básico con FPS en Performance
                "overlay_mode": "Básico",
                "overlay_show_fps": True,
                "overlay_show_frametime": False,
                "overlay_show_messages": False,
                "overlay_position": "Superior Derecha",
                "overlay_scale": 0.8,
                "overlay_font_size": 12
            },
            "balanced": {
                "fg_mode": "OptiFG",
                "upscale_mode": "Equilibrado",
                "upscaler": "Automático",
                "sharpness": 0.5,
                "fps_limit": 0,
                # HDR: Activado con configuración estándar
                "auto_hdr": True,
                "nvidia_hdr_override": False,
                "hdr_rgb_range": 100.0,
                # Logging: Info level
                "log_level": "Info",
                "open_console": False,
                "log_to_file": True,
                # Quality Overrides: Desactivado
                "quality_override_enabled": False,
                "quality_ratio": 1.5,
                "balanced_ratio": 1.7,
                "performance_ratio": 2.0,
                "ultra_perf_ratio": 3.0,
                # CAS: Activado con sharpening medio
                "cas_enabled": True,
                "cas_type": "RCAS",
                "cas_sharpness": 0.5,
                # NVNGX: Todo activado
                "nvngx_dx12": True,
                "nvngx_dx11": True,
                "nvngx_vulkan": True,
                # Overlay: Completo en Balanced
                "overlay_mode": "Completo",
                "overlay_show_fps": True,
                "overlay_show_frametime": True,
                "overlay_show_messages": True,
                "overlay_position": "Superior Izquierda",
                "overlay_scale": 1.0,
                "overlay_font_size": 14
            },
            "quality": {
                "fg_mode": "Desactivado",
                "upscale_mode": "Calidad",
                "upscaler": "XeSS",
                "sharpness": 0.7,
                "fps_limit": 0,
                # HDR: Activado con configuración alta
                "auto_hdr": True,
                "nvidia_hdr_override": True,
                "hdr_rgb_range": 150.0,
                # Logging: Debug level
                "log_level": "Debug",
                "open_console": False,
                "log_to_file": True,
                # Quality Overrides: Desactivado (usar nativo)
                "quality_override_enabled": False,
                "quality_ratio": 1.5,
                "balanced_ratio": 1.7,
                "performance_ratio": 2.0,
                "ultra_perf_ratio": 3.0,
                # CAS: Desactivado en Quality (usar nativo)
                "cas_enabled": False,
                "cas_type": "RCAS",
                "cas_sharpness": 0.5,
                # NVNGX: Todo activado
                "nvngx_dx12": True,
                "nvngx_dx11": True,
                "nvngx_vulkan": True,
                # Overlay: Desactivado en Quality para máxima calidad
                "overlay_mode": "Desactivado",
                "overlay_show_fps": True,
                "overlay_show_frametime": True,
                "overlay_show_messages": True,
                "overlay_position": "Superior Izquierda",
                "overlay_scale": 1.0,
                "overlay_font_size": 14
            },
            "default": {
                "fg_mode": "Desactivado",
                "upscale_mode": "Automático",
                "upscaler": "Automático",
                "sharpness": 0.5,
                "fps_limit": 0,
                # HDR: Activado por defecto
                "auto_hdr": True,
                "nvidia_hdr_override": False,
                "hdr_rgb_range": 100.0,
                # Logging: Info level
                "log_level": "Info",
                "open_console": False,
                "log_to_file": True,
                # Quality Overrides: Desactivado
                "quality_override_enabled": False,
                "quality_ratio": 1.5,
                "balanced_ratio": 1.7,
                "performance_ratio": 2.0,
                "ultra_perf_ratio": 3.0,
                # CAS: Desactivado por defecto
                "cas_enabled": False,
                "cas_type": "RCAS",
                "cas_sharpness": 0.5,
                # NVNGX: Todo activado
                "nvngx_dx12": True,
                "nvngx_dx11": True,
                "nvngx_vulkan": True,
                # Overlay: Desactivado por defecto
                "overlay_mode": "Desactivado",
                "overlay_show_fps": True,
                "overlay_show_frametime": True,
                "overlay_show_messages": True,
                "overlay_position": "Superior Izquierda",
                "overlay_scale": 1.0,
                "overlay_font_size": 14
            },
            "custom": {
                # No cambia nada, solo para referencia
            }
        }
        
        # Visual feedback: reset all, highlight only the active with its color
        for key, btn in self.preset_buttons.items():
            if key == preset:
                color, width = self.preset_borders.get(key, ("#00BFFF", 3))
                btn.configure(border_width=width, border_color=color)
            else:
                btn.configure(border_width=0)

        if preset in presets and preset != "custom":
            # Suprimir cambio automático a Custom mientras actualizamos variables
            self._suppress_custom = True
            config = presets[preset]
            
            # Variables básicas
            self.fg_mode_var.set(config["fg_mode"])
            self.upscale_mode_var.set(config["upscale_mode"])
            self.upscaler_var.set(config["upscaler"])
            self.sharpness_var.set(config["sharpness"])
            self.fps_limit_var.set(config["fps_limit"])
            
            # HDR Settings
            self.auto_hdr_var.set(config.get("auto_hdr", True))
            self.nvidia_hdr_override_var.set(config.get("nvidia_hdr_override", False))
            self.hdr_rgb_range_var.set(config.get("hdr_rgb_range", 100.0))
            
            # Debug/Logging
            self.log_level_var.set(config.get("log_level", "Info"))
            self.open_console_var.set(config.get("open_console", False))
            self.log_to_file_var.set(config.get("log_to_file", True))
            
            # OptiPatcher
            self.optipatcher_enabled_var.set(config.get("optipatcher_enabled", True))
            
            # Quality Overrides
            self.quality_override_enabled_var.set(config.get("quality_override_enabled", False))
            self.quality_ratio_var.set(config.get("quality_ratio", 1.5))
            self.balanced_ratio_var.set(config.get("balanced_ratio", 1.7))
            self.performance_ratio_var.set(config.get("performance_ratio", 2.0))
            self.ultra_perf_ratio_var.set(config.get("ultra_perf_ratio", 3.0))
            
            # CAS Sharpening
            self.cas_enabled_var.set(config.get("cas_enabled", False))
            self.cas_type_var.set(config.get("cas_type", "RCAS"))
            self.cas_sharpness_var.set(config.get("cas_sharpness", 0.5))
            
            # NVNGX Spoofing
            self.nvngx_dx12_var.set(config.get("nvngx_dx12", True))
            self.nvngx_dx11_var.set(config.get("nvngx_dx11", True))
            self.nvngx_vulkan_var.set(config.get("nvngx_vulkan", True))
            
            # Overlay Settings
            self.overlay_mode_var.set(config.get("overlay_mode", "Desactivado"))
            self.overlay_show_fps_var.set(config.get("overlay_show_fps", True))
            self.overlay_show_frametime_var.set(config.get("overlay_show_frametime", True))
            self.overlay_show_messages_var.set(config.get("overlay_show_messages", True))
            self.overlay_position_var.set(config.get("overlay_position", "Superior Izquierda"))
            self.overlay_scale_var.set(config.get("overlay_scale", 1.0))
            self.overlay_font_size_var.set(config.get("overlay_font_size", 14))

            # Actualizar labels
            self.on_sharpness_changed(config["sharpness"])
            self.on_fps_changed(config["fps_limit"])

            # Actualizar indicador de preset activo
            preset_names = {
                "default": "Default",
                "performance": "⚡ Performance",
                "balanced": "⚖️ Balanced",
                "quality": "💎 Quality"
            }
            self.active_preset_label.configure(text=preset_names.get(preset, "Custom"))

            self.log('INFO', f"✓ Preset '{preset}' aplicado")
            self._suppress_custom = False
        elif preset == "custom":
            # Restaurar última configuración personalizada si existe
            if getattr(self, 'custom_preset_state', None):
                self._suppress_custom = True
                state = self.custom_preset_state
                
                # Variables básicas
                if 'fg_mode' in state: self.fg_mode_var.set(state['fg_mode'])
                if 'upscale_mode' in state: self.upscale_mode_var.set(state['upscale_mode'])
                if 'upscaler' in state: self.upscaler_var.set(state['upscaler'])
                if 'sharpness' in state: self.sharpness_var.set(state['sharpness']); self.on_sharpness_changed(state['sharpness'])
                if 'fps_limit' in state: self.fps_limit_var.set(state['fps_limit']); self.on_fps_changed(state['fps_limit'])
                if 'dll_name' in state: self.dll_name_var.set(state['dll_name'])
                
                # HDR Settings
                if 'auto_hdr' in state: self.auto_hdr_var.set(state['auto_hdr'])
                if 'nvidia_hdr_override' in state: self.nvidia_hdr_override_var.set(state['nvidia_hdr_override'])
                if 'hdr_rgb_range' in state: self.hdr_rgb_range_var.set(state['hdr_rgb_range'])
                
                # Debug/Logging
                if 'log_level' in state: self.log_level_var.set(state['log_level'])
                if 'open_console' in state: self.open_console_var.set(state['open_console'])
                if 'log_to_file' in state: self.log_to_file_var.set(state['log_to_file'])
                
                # Quality Overrides
                if 'quality_override_enabled' in state: self.quality_override_enabled_var.set(state['quality_override_enabled'])
                if 'quality_ratio' in state: self.quality_ratio_var.set(state['quality_ratio'])
                if 'balanced_ratio' in state: self.balanced_ratio_var.set(state['balanced_ratio'])
                if 'performance_ratio' in state: self.performance_ratio_var.set(state['performance_ratio'])
                if 'ultra_perf_ratio' in state: self.ultra_perf_ratio_var.set(state['ultra_perf_ratio'])
                
                # CAS Sharpening
                if 'cas_enabled' in state: self.cas_enabled_var.set(state['cas_enabled'])
                if 'cas_type' in state: self.cas_type_var.set(state['cas_type'])
                if 'cas_sharpness' in state: self.cas_sharpness_var.set(state['cas_sharpness'])
                
                # NVNGX Spoofing
                if 'nvngx_dx12' in state: self.nvngx_dx12_var.set(state['nvngx_dx12'])
                if 'nvngx_dx11' in state: self.nvngx_dx11_var.set(state['nvngx_dx11'])
                if 'nvngx_vulkan' in state: self.nvngx_vulkan_var.set(state['nvngx_vulkan'])
                
                # Overlay Settings
                if 'overlay_mode' in state: self.overlay_mode_var.set(state['overlay_mode'])
                if 'overlay_show_fps' in state: self.overlay_show_fps_var.set(state['overlay_show_fps'])
                if 'overlay_show_frametime' in state: self.overlay_show_frametime_var.set(state['overlay_show_frametime'])
                if 'overlay_show_messages' in state: self.overlay_show_messages_var.set(state['overlay_show_messages'])
                if 'overlay_position' in state: self.overlay_position_var.set(state['overlay_position'])
                if 'overlay_scale' in state: self.overlay_scale_var.set(state['overlay_scale'])
                if 'overlay_font_size' in state: self.overlay_font_size_var.set(state['overlay_font_size'])
                
                self._suppress_custom = False
            self.active_preset_label.configure(text="✏️ Custom")
            self.log('INFO', "Modo personalizado activado (estado restaurado)")
        
    def scan_games_action(self, silent=False):
        """Ejecuta escaneo de juegos en hilo separado.
        
        Args:
            silent: Si es True, actualiza la lista sin modificar la barra de progreso
        """
        # BUGFIX: Protección contra race condition si se presiona botón durante scan
        if hasattr(self, '_scan_in_progress') and self._scan_in_progress:
            self.log('WARNING', "⏳ Escaneo ya en progreso, espera a que termine")
            return
            
        self.log('INFO', "Iniciando escaneo de juegos...")
        self._scan_in_progress = True
        
        # Deshabilitar botón durante escaneo
        self.scan_btn.configure(state="disabled")
        if self.icons.get("rescan"):
            self.scan_btn.configure(text="")
        else:
            self.scan_btn.configure(text="⏳")
        
        # Mostrar barra de progreso solo si no es silencioso
        if not silent:
            self.show_progress()  # Usar función con animación
            self.status_label.configure(text="🔍 Escaneando juegos...", text_color="#00BFFF")
            self.progress_bar.set(0)
            # Mejora #6: Mejorar animación indeterminada
            self.progress_bar.configure(mode="indeterminate")
            # Mejora #3: Color azul durante progreso
            self.set_progress_color("#00BFFF")
            self.progress_bar.start()
            
            # Mejora #4: Animación del botón de escaneo
            self.scan_animation_running = True
            self.animate_scan_button()
        
        def scan_thread():
            try:
                # Invalidar cache para forzar rescan
                invalidate_scan_cache()
                
                # Obtener carpetas personalizadas del config
                custom_folders = self.config.get("custom_game_folders", [])
                
                # Ejecutar scan
                games_list = scan_games(self.log, custom_folders=custom_folders, use_cache=False)
                
                # Actualizar GUI en hilo principal
                self.after(0, lambda: self.update_games_list(games_list, silent=silent))
                
            except Exception as e:
                self.log('ERROR', f"Error durante escaneo: {e}")
                if not silent:
                    self.after(0, lambda: self.show_status_error(f"Error al escanear: {e}"))
            finally:
                # Restaurar botón
                def restore_button():
                    # Mejora #4: Detener animación
                    self.scan_animation_running = False
                    self._scan_in_progress = False  # BUGFIX: Liberar flag de progreso
                    if self.icons.get("rescan"):
                        self.scan_btn.configure(state="normal", text="", image=self.icons["rescan"])
                    else:
                        self.scan_btn.configure(state="normal", text="🔄")
                self.after(0, restore_button)
        
        threading.Thread(target=scan_thread, daemon=True).start()
    
    def animate_scan_button(self):
        """Mejora #4: Anima el botón de escaneo con emojis rotatorios."""
        if not hasattr(self, 'scan_animation_running') or not self.scan_animation_running:
            return
        
        # Secuencia de animación
        if not hasattr(self, 'scan_animation_frame'):
            self.scan_animation_frame = 0
        
        animation_frames = ["🔄", "🔃", "⟳", "⟲"]
        
        # Si no hay icono, usar emoji animado
        if not self.icons.get("rescan"):
            current_frame = animation_frames[self.scan_animation_frame % len(animation_frames)]
            self.scan_btn.configure(text=current_frame)
            self.scan_animation_frame += 1
        
        # Continuar animación cada 200ms
        if self.scan_animation_running:
            self.after(200, self.animate_scan_button)
    
    def update_game_status_realtime(self, game_path, status_text, status_color, force=False):
        """Mejora #5: Actualiza el estado de un juego en la lista en tiempo real.
        
        Args:
            game_path: Ruta del juego
            status_text: Texto del estado a mostrar
            status_color: Color del texto
            force: Si True, no re-detecta el estado, usa los valores pasados
        """
        if game_path in self.game_frames:
            frame_data = self.game_frames[game_path]
            status_label = frame_data['status_label']
            game_frame = frame_data['frame']
            
            # Re-computar badge actualizado con detector SOLO si no es forzado
            if not force:
                try:
                    badge_info = get_version_badge_info(game_path, OPTISCALER_DIR)
                    status_text = badge_info['badge_text']
                    status_color = badge_info['badge_color']
                except Exception:
                    pass  # Usar valores pasados como fallback
            
            # Actualizar label de estado
            status_label.configure(text=status_text, text_color=status_color)
            
            # Efecto de resaltado temporal
            original_color = game_frame.cget("fg_color")
            game_frame.configure(fg_color="#2a4a2a" if "✅" in status_text else "#4a2a2a")
            
            # Volver al color original después de 1 segundo
            self.after(1000, lambda: game_frame.configure(fg_color=original_color))
    
    def update_games_list(self, games_list, silent=False):
        """Actualiza la lista visual de juegos.
        
        Args:
            games_list: Lista de juegos encontrados
            silent: Si es True, no actualiza la barra de progreso
        """
        # Actualizar datos
        self.games_data.clear()
        self.selected_games.clear()
        
        for game_path, game_name, mod_status, exe_name, platform in games_list:
            self.games_data[game_path] = (game_name, mod_status, exe_name, platform)
        
        # Aplicar filtros (mostrará todos si no hay filtros activos)
        self.apply_game_filters()
        
        self.log('INFO', f"Escaneo completado: {len(games_list)} juegos encontrados")
        
            # Actualizar barra de progreso solo si no es silencioso
        if not silent:
            # Detener animación y mostrar resultado completo en la barra de progreso
            self.progress_bar.stop()  # Detener animación indeterminada
            self.progress_bar.configure(mode="determinate")
            self.progress_bar.set(1.0)  # 100% completado
            # Mejora #3: Color verde para éxito
            self.set_progress_color("#00FF88")
            self.status_label.configure(
                text=f"✅ Escaneo completado: {len(games_list)} juegos encontrados",
                text_color="#00FF88"
            )
            # Mejora #9: Cambiar a modo compacto al terminar
            self.after(1000, self.set_progress_mode_compact)
            # La barra permanece visible mostrando el último estado
    
    def toggle_game_selection(self, game_path, var):
        """Maneja selección/deselección de juegos."""
        if var.get():
            self.selected_games.add(game_path)
        else:
            self.selected_games.discard(game_path)
        
        # Actualizar contador formato X/Y
        selected_count = len(self.selected_games)
        total_count = len(self.games_data)
        self.games_counter_label.configure(text=f"{selected_count}/{total_count}")
    
    def hide_progress(self):
        """Oculta la barra de progreso con animación fade-out."""
        # Mejora #1: Animación fade-out
        self.progress_frame.grid_remove()
        self.status_label.configure(text_color="#00BFFF")  # Resetear color
        self.progress_bar.configure(progress_color="#00BFFF")  # Resetear color de barra
    
    def show_progress(self):
        """Muestra la barra de progreso con animación fade-in."""
        # Mejora #1: Animación fade-in
        if not self.progress_frame.winfo_ismapped():
            self.progress_frame.grid()
        # Mejora #9: Cambiar a modo expandido cuando está activa
        self.set_progress_mode_expanded()
    
    def set_progress_mode_compact(self):
        """Mejora #9: Cambia la barra a modo compacto (altura reducida)."""
        self.progress_content.grid_configure(pady=self.progress_padding_compact)
    
    def set_progress_mode_expanded(self):
        """Mejora #9: Cambia la barra a modo expandido (altura normal)."""
        self.progress_content.grid_configure(pady=self.progress_padding_normal)
    
    def set_progress_color(self, color):
        """Cambia el color de la barra de progreso.
        
        Mejora #3: Colores dinámicos
        - Verde (#00FF88): Éxito
        - Azul (#00BFFF): En progreso
        - Naranja (#FFA500): Advertencia
        - Rojo (#FF4444): Error
        """
        self.progress_bar.configure(progress_color=color)
    
    def show_status_error(self, message):
        """Muestra un error en la barra de estado."""
        self.show_progress()
        self.progress_bar.configure(mode="determinate")
        self.progress_bar.set(0)
        self.progress_bar.stop()
        # Mejora #3: Color rojo para errores
        self.set_progress_color("#FF4444")
        self.status_label.configure(text=f"❌ {message}", text_color="#FF4444")
        # La barra permanece visible mostrando el error
    
    def update_progress(self, current, total, message, show_time=False):
        """Actualiza la barra de progreso con valores específicos.
        
        Mejora #2: Porcentaje visual
        Mejora #4: Tiempo estimado
        """
        if total > 0:
            progress = current / total
            percentage = int(progress * 100)
            
            # Mejora #2: Añadir porcentaje al mensaje
            display_message = f"{message} ({percentage}%)"
            
            # Mejora #4: Calcular tiempo estimado
            if show_time and hasattr(self, 'progress_start_time') and self.progress_start_time:
                elapsed_time = time.time() - self.progress_start_time
                if current > 0:
                    avg_time_per_item = elapsed_time / current
                    remaining_items = total - current
                    estimated_remaining = int(avg_time_per_item * remaining_items)
                    
                    if estimated_remaining > 0:
                        display_message += f" - ~{estimated_remaining}s restantes"
            
            self.progress_bar.configure(mode="determinate")
            self.progress_bar.set(progress)
            self.status_label.configure(text=display_message, text_color="#00BFFF")
            
            # Mejora #3: Color azul durante progreso
            self.set_progress_color("#00BFFF")
    
    def show_operation_details(self):
        """Mejora #3: Muestra ventana con detalles de la última operación."""
        if not self.last_operation_results['operation']:
            return  # No hay operación reciente
        
        # Crear ventana de detalles
        details_window = ctk.CTkToplevel(self)
        details_window.title(f"📊 Detalles de {self.last_operation_results['operation']}")
        details_window.geometry("600x500")
        details_window.transient(self)
        details_window.grab_set()
        
        # Título
        ctk.CTkLabel(
            details_window,
            text=f"📊 RESULTADOS DE {self.last_operation_results['operation'].upper()}",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#00BFFF"
        ).pack(pady=(20, 10))
        
        # Frame scrollable para resultados
        scroll_frame = ctk.CTkScrollableFrame(details_window, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Sección de exitosos
        success_list = self.last_operation_results['success']
        if success_list:
            ctk.CTkLabel(
                scroll_frame,
                text=f"✅ EXITOSOS ({len(success_list)})",
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color="#00FF88",
                anchor="w"
            ).pack(fill="x", pady=(5, 5))
            
            for game_name in success_list:
                game_frame = ctk.CTkFrame(scroll_frame, fg_color="#1a3a1a", corner_radius=5)
                game_frame.pack(fill="x", pady=2, padx=10)
                ctk.CTkLabel(
                    game_frame,
                    text=f"  ✓ {game_name}",
                    font=ctk.CTkFont(size=12),
                    text_color="#00FF88",
                    anchor="w"
                ).pack(fill="x", padx=10, pady=5)
        
        # Sección de fallidos
        failed_list = self.last_operation_results['failed']
        if failed_list:
            ctk.CTkLabel(
                scroll_frame,
                text=f"❌ FALLIDOS ({len(failed_list)})",
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color="#FF4444",
                anchor="w"
            ).pack(fill="x", pady=(15, 5))
            
            for game_name, reason in failed_list:
                game_frame = ctk.CTkFrame(scroll_frame, fg_color="#3a1a1a", corner_radius=5)
                game_frame.pack(fill="x", pady=2, padx=10)
                ctk.CTkLabel(
                    game_frame,
                    text=f"  ✗ {game_name}",
                    font=ctk.CTkFont(size=12, weight="bold"),
                    text_color="#FF4444",
                    anchor="w"
                ).pack(fill="x", padx=10, pady=(5, 2))
                ctk.CTkLabel(
                    game_frame,
                    text=f"    Razón: {reason}",
                    font=ctk.CTkFont(size=10),
                    text_color="#AAAAAA",
                    anchor="w"
                ).pack(fill="x", padx=10, pady=(0, 5))
        
        # Mensaje si todo OK
        if success_list and not failed_list:
            ctk.CTkLabel(
                scroll_frame,
                text="🎉 ¡Todas las operaciones se completaron exitosamente!",
                font=ctk.CTkFont(size=12),
                text_color="#00FF88"
            ).pack(pady=20)
        
        # Botón cerrar
        ctk.CTkButton(
            details_window,
            text="Cerrar",
            command=details_window.destroy,
            width=150,
            height=35,
            fg_color="#3a3a3a",
            hover_color="#4a4a4a"
        ).pack(pady=(10, 20))
        
    def open_filter(self):
        """Abre modal de filtrado de juegos."""
        # Crear ventana modal
        filter_window = ctk.CTkToplevel(self)
        filter_window.title("🔍 Filtrar Juegos")
        filter_window.geometry("500x450")
        filter_window.resizable(False, False)
        
        # Centrar ventana
        filter_window.transient(self)
        filter_window.grab_set()
        
        # Título
        ctk.CTkLabel(
            filter_window,
            text="🔍 FILTRAR JUEGOS",
            font=ctk.CTkFont(size=FONT_TITLE, weight="bold"),
            text_color=COLOR_PRIMARY
        ).pack(pady=(20, 10))
        
        # Frame principal
        main_frame = ctk.CTkFrame(filter_window, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # === FILTRO POR PLATAFORMA ===
        platform_frame = ctk.CTkFrame(main_frame, fg_color="#1a1a1a", corner_radius=8)
        platform_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(
            platform_frame,
            text="Plataforma:",
            font=ctk.CTkFont(size=FONT_SECTION, weight="bold")
        ).pack(anchor="w", padx=15, pady=(10, 5))
        
        platform_combo = WideComboBox(
            platform_frame,
            variable=self.filter_platform,
            values=["Todas", "Steam", "Epic Games", "Xbox", "Custom"],
            width=300,
            font=ctk.CTkFont(size=FONT_NORMAL)
        )
        platform_combo.pack(padx=15, pady=(0, 10), fill="x")
        
        # === FILTRO POR ESTADO DEL MOD ===
        status_frame = ctk.CTkFrame(main_frame, fg_color="#1a1a1a", corner_radius=8)
        status_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(
            status_frame,
            text="Estado del Mod:",
            font=ctk.CTkFont(size=FONT_SECTION, weight="bold")
        ).pack(anchor="w", padx=15, pady=(10, 5))
        
        status_combo = WideComboBox(
            status_frame,
            variable=self.filter_mod_status,
            values=["Todos", "Instalado", "No instalado"],
            width=300,
            font=ctk.CTkFont(size=FONT_NORMAL)
        )
        status_combo.pack(padx=15, pady=(0, 10), fill="x")
        
        # === BÚSQUEDA POR NOMBRE ===
        search_frame = ctk.CTkFrame(main_frame, fg_color="#1a1a1a", corner_radius=8)
        search_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(
            search_frame,
            text="Buscar por nombre:",
            font=ctk.CTkFont(size=FONT_SECTION, weight="bold")
        ).pack(anchor="w", padx=15, pady=(10, 5))
        
        search_entry = ctk.CTkEntry(
            search_frame,
            textvariable=self.filter_search,
            placeholder_text="Escribe el nombre del juego...",
            font=ctk.CTkFont(size=FONT_NORMAL),
            height=35
        )
        search_entry.pack(padx=15, pady=(0, 10), fill="x")
        
        # === BOTONES ===
        buttons_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        buttons_frame.pack(fill="x", pady=(10, 0))
        
        def apply_filters():
            """Aplica los filtros seleccionados."""
            self.active_filters = {
                "platform": self.filter_platform.get(),
                "mod_status": self.filter_mod_status.get(),
                "search": self.filter_search.get().lower().strip()
            }
            self.apply_game_filters()
            filter_window.destroy()
        
        def clear_filters():
            """Limpia todos los filtros."""
            self.filter_platform.set("Todas")
            self.filter_mod_status.set("Todos")
            self.filter_search.set("")
            self.active_filters = {"platform": "Todas", "mod_status": "Todos", "search": ""}
            self.apply_game_filters()
            filter_window.destroy()
        
        # Botón Aplicar
        apply_btn = ctk.CTkButton(
            buttons_frame,
            text="✅ Aplicar Filtros",
            command=apply_filters,
            height=40,
            fg_color=COLOR_PRIMARY,
            hover_color=COLOR_PRIMARY_HOVER,
            font=ctk.CTkFont(size=FONT_NORMAL, weight="bold")
        )
        apply_btn.pack(side="left", padx=5, fill="x", expand=True)
        
        # Botón Limpiar
        clear_btn = ctk.CTkButton(
            buttons_frame,
            text="🔄 Limpiar Filtros",
            command=clear_filters,
            height=40,
            fg_color=COLOR_SECONDARY,
            hover_color=COLOR_SECONDARY_HOVER,
            font=ctk.CTkFont(size=FONT_NORMAL, weight="bold")
        )
        clear_btn.pack(side="left", padx=5, fill="x", expand=True)
        
        # Botón Cancelar
        cancel_btn = ctk.CTkButton(
            buttons_frame,
            text="❌ Cancelar",
            command=filter_window.destroy,
            height=40,
            fg_color="#3a3a3a",
            hover_color="#4a4a4a",
            font=ctk.CTkFont(size=FONT_NORMAL, weight="bold")
        )
        cancel_btn.pack(side="left", padx=5, fill="x", expand=True)
        
        # Focus en búsqueda
        search_entry.focus()
    
    def apply_game_filters(self):
        """Aplica los filtros activos a la lista de juegos."""
        # Limpiar lista actual
        for widget in self.games_scrollable.winfo_children():
            widget.destroy()
        
        # Obtener todos los juegos
        all_games = list(self.games_data.items())
        
        # Aplicar filtros
        filtered_games = []
        for game_path, (game_name, mod_status, exe_name, platform) in all_games:
            # Filtro de plataforma
            if self.active_filters["platform"] != "Todas":
                if self.active_filters["platform"] != platform:
                    continue
            
            # Filtro de estado del mod
            if self.active_filters["mod_status"] != "Todos":
                is_installed = "✅" in mod_status
                if self.active_filters["mod_status"] == "Instalado" and not is_installed:
                    continue
                if self.active_filters["mod_status"] == "No instalado" and is_installed:
                    continue
            
            # Filtro de búsqueda
            if self.active_filters["search"]:
                if self.active_filters["search"] not in game_name.lower():
                    continue
            
            filtered_games.append((game_path, game_name, mod_status, exe_name, platform))
        
        # Recrear lista de juegos filtrada
        # Mejora #5: Limpiar referencias antiguas
        self.game_frames.clear()
        
        for game_path, game_name, mod_status, exe_name, platform in filtered_games:
            # Frame para cada juego con efecto hover
            game_frame = ctk.CTkFrame(
                self.games_scrollable,
                fg_color="#1a1a1a",
                corner_radius=5,
                cursor="hand2"
            )
            game_frame.pack(fill="x", padx=5, pady=3)
            
            # Checkbox
            var = ctk.BooleanVar(value=game_path in self.selected_games)
            check = ctk.CTkCheckBox(
                game_frame,
                text="",
                variable=var,
                width=20,
                command=lambda p=game_path, v=var: self.toggle_game_selection(p, v)
            )
            check.pack(side="left", padx=5)
            
            # Nombre del juego
            name_label = ctk.CTkLabel(
                game_frame,
                text=game_name,
                anchor="w",
                font=ctk.CTkFont(size=FONT_NORMAL),
                cursor="hand2"
            )
            name_label.pack(side="left", fill="x", expand=True, padx=5)
            
            # Estado del mod - mejorado con detección de versión
            try:
                from pathlib import Path
                badge_info = get_version_badge_info(game_path, OPTISCALER_DIR)
                mod_status_text = badge_info['badge_text']
                status_color = badge_info['badge_color']
            except Exception:
                # Fallback al método anterior si falla detección
                status_color = "#00ff00" if "✅" in mod_status else "#888888"
                mod_status_text = mod_status
            
            status_label = ctk.CTkLabel(
                game_frame,
                text=mod_status_text,
                text_color=status_color,
                font=ctk.CTkFont(size=FONT_SMALL),
                anchor="e",
                cursor="hand2"
            )
            status_label.pack(side="right", padx=5)
            
            # FEATURE: Click en estado muestra detalles de instalación
            # Capturamos variables como argumentos por defecto para evitar que todos los
            # handlers apunten al último juego (late binding en closures dentro de loops)
            def show_mod_details(event=None, _p=game_path, _n=game_name, _s=mod_status_text):
                try:
                    self.show_installation_details(_p, _n, _s)
                except Exception as e:
                    self.log('ERROR', f"Error mostrando detalles: {e}")
                    messagebox.showerror("Error", f"No se pudieron cargar los detalles:\n{e}")
            
            status_label.bind("<Button-1>", show_mod_details)
            # Agregar efecto hover
            def on_enter(e, label=status_label):
                label.configure(font=ctk.CTkFont(size=FONT_SMALL, underline=True))
            def on_leave(e, label=status_label):
                label.configure(font=ctk.CTkFont(size=FONT_SMALL, underline=False))
            status_label.bind("<Enter>", on_enter)
            status_label.bind("<Leave>", on_leave)
            
            # Mejora #5: Guardar referencias para actualización en tiempo real
            self.game_frames[game_path] = {
                'frame': game_frame,
                'status_label': status_label,
                'name': game_name
            }
    
    def check_optiscaler_available(self):
        """Verifica si OptiScaler está descargado.
        
        Returns:
            bool: True si está disponible, False si no
        """
        import glob
        
        # Buscar carpetas de OptiScaler en OPTISCALER_DIR
        optiscaler_patterns = [
            os.path.join(OPTISCALER_DIR, "OptiScaler*"),
            os.path.join(OPTISCALER_DIR, "optiscaler*")
        ]
        
        for pattern in optiscaler_patterns:
            matches = glob.glob(pattern)
            if matches:
                # Verificar que tenga archivos del mod
                for match in matches:
                    if os.path.isdir(match):
                        # Buscar archivos .dll característicos
                        dll_files = glob.glob(os.path.join(match, "*.dll"))
                        if dll_files:
                            return True
        
        return False
    
    def get_optiscaler_source_dir(self):
        """Obtiene la carpeta de OptiScaler según la versión seleccionada.
        
        Returns:
            str|None: Ruta a la carpeta del mod o None si no se encuentra
        """
        import glob
        
        selected_version = self.optiscaler_version_var.get()
        
        # Si es versión custom
        if selected_version.startswith("[Custom]"):
            folder_name = selected_version.replace("[Custom] ", "")
            custom_path = os.path.join(OPTISCALER_DIR, folder_name)
            if os.path.exists(custom_path):
                return custom_path
        
        # Buscar por nombre de versión
        patterns = [
            os.path.join(OPTISCALER_DIR, f"*{selected_version}*"),
            os.path.join(OPTISCALER_DIR, f"OptiScaler_{selected_version}"),
            os.path.join(OPTISCALER_DIR, f"OptiScaler*{selected_version}*")
        ]
        
        for pattern in patterns:
            matches = glob.glob(pattern)
            if matches and os.path.isdir(matches[0]):
                return matches[0]
        
        # Si no se encuentra, usar la primera disponible
        all_optiscaler = glob.glob(os.path.join(OPTISCALER_DIR, "OptiScaler*"))
        if all_optiscaler:
            return all_optiscaler[0]
        
        return None
    
    def get_nukem_source_dir(self):
        """Obtiene la carpeta de dlssg-to-fsr3 desde el campo de ruta.
        
        Returns:
            str|None: Ruta a la carpeta del mod o None si no se encuentra
        """
        # Leer la ruta del campo de texto
        nukem_path = self.nukem_path_var.get().strip()
        
        # Si hay una ruta y existe, usarla
        if nukem_path and os.path.exists(nukem_path):
            # Verificar que tenga archivos .dll
            dll_files = [f for f in os.listdir(nukem_path) if f.endswith('.dll')]
            if dll_files:
                return nukem_path
        
        # Si no hay ruta válida, retornar None
        return None
        
    def apply_to_selected(self):
        """Aplica el mod a los juegos seleccionados."""
        if not self.selected_games:
            self.show_progress()
            # Mejora #3: Color naranja para advertencia
            self.set_progress_color("#FFA500")
            self.status_label.configure(text="⚠️ No hay juegos seleccionados", text_color="#FFA500")
            self.progress_bar.set(0)
            return
        
        # Verificar que OptiScaler esté descargado
        if not self.check_optiscaler_available():
            response = messagebox.askyesnocancel(
                "OptiScaler no encontrado",
                "No se encontró OptiScaler descargado.\n\n"
                "¿Deseas ir al panel de Ajustes para descargarlo?"
            )
            if response:  # Yes
                self.show_panel("settings")
            return
        
        # Confirmar
        count = len(self.selected_games)
        if not messagebox.askyesno(
            "Confirmar",
            f"¿Instalar OptiScaler en {count} juego(s)?"
        ):
            return
        
        # Mostrar barra de progreso
        self.show_progress()
        self.progress_bar.configure(mode="determinate")
        self.progress_bar.set(0)
        # Mejora #3: Color azul durante instalación
        self.set_progress_color("#00BFFF")
        
        # Mejora #4: Iniciar contador de tiempo
        self.progress_start_time = time.time()
        
        self.apply_btn.configure(state="disabled", text="⏳ Instalando...")
        
        def install_thread():
            success_count = 0
            fail_count = 0
            total = len(self.selected_games)
            current = 0
            
            # Mejora #3: Limpiar resultados anteriores
            self.last_operation_results = {
                'success': [],
                'failed': [],
                'operation': 'Instalación'
            }
            
            for game_path in self.selected_games:
                try:
                    game_name, _, exe_name, _ = self.games_data[game_path]
                    current += 1
                    
                    # Mejora #2 y #4: Actualizar progreso con porcentaje y tiempo estimado
                    self.after(0, lambda c=current, t=total, n=game_name: 
                              self.update_progress(c, t, f"⚙️ Instalando {c}/{t}: {n[:30]}{'...' if len(n) > 30 else ''}", show_time=True))
                    
                    # Obtener carpeta de OptiScaler
                    mod_source_dir = self.get_optiscaler_source_dir()
                    if not mod_source_dir:
                        fail_count += 1
                        self.log('ERROR', f"❌ {game_name}: No se encontró la carpeta de OptiScaler")
                        continue
                    
                    # BUGFIX: Verificar si realmente necesita Nukem (solo si fg_mode == "FSR-FG (Nukem's DLSSG)")
                    fg_mode = self.fg_mode_var.get()
                    needs_nukem = fg_mode == "FSR-FG (Nukem's DLSSG)"
                    
                    if needs_nukem:
                        # Obtener carpeta de Nukem/dlssg-to-fsr3
                        nukem_source_dir = self.get_nukem_source_dir()
                        if not nukem_source_dir:
                            fail_count += 1
                            self.log('ERROR', f"❌ {game_name}: No se encontró dlssg-to-fsr3. Descárgalo desde Ajustes.")
                            continue
                        
                        # Obtener configuraciones del GUI
                        gpu_choice = self.gpu_var.get()
                        upscaler = self.upscaler_var.get()
                        upscale_mode = self.upscale_mode_var.get()
                        dll_name = self.dll_name_var.get()
                        sharpness = float(self.sharpness_var.get())
                        overlay = self.overlay_var.get() == "Activado"
                        mb = self.mb_var.get() == "Activado"
                        
                        result = install_combined_mods(
                            optiscaler_source_dir=mod_source_dir,
                            nukem_source_dir=nukem_source_dir,
                            target_dir=game_path,
                            log_func=self.log,
                            spoof_dll_name=dll_name,
                            gpu_choice=gpu_choice,
                            fg_mode_selected=fg_mode,
                            upscaler_selected=upscaler,
                            upscale_mode_selected=upscale_mode,
                            sharpness_selected=sharpness,
                            overlay_selected=overlay,
                            mb_selected=mb,
                            install_nukem=True
                        )
                    else:
                        # Obtener configuraciones del GUI
                        gpu_choice = self.gpu_var.get()
                        fg_mode = self.fg_mode_var.get()
                        upscaler = self.upscaler_var.get()
                        upscale_mode = self.upscale_mode_var.get()
                        dll_name = self.dll_name_var.get()
                        sharpness = float(self.sharpness_var.get())
                        overlay = self.overlay_var.get() == "Activado"
                        mb = self.mb_var.get() == "Activado"
                        
                        result = inject_fsr_mod(
                            mod_source_dir=mod_source_dir,
                            target_dir=game_path,
                            log_func=self.log,
                            spoof_dll_name=dll_name,
                            gpu_choice=gpu_choice,
                            fg_mode_selected=fg_mode,
                            upscaler_selected=upscaler,
                            upscale_mode_selected=upscale_mode,
                            sharpness_selected=sharpness,
                            overlay_selected=overlay,
                            mb_selected=mb,
                            auto_hdr=self.auto_hdr_var.get(),
                            nvidia_hdr_override=self.nvidia_hdr_override_var.get(),
                            hdr_rgb_range=self.hdr_rgb_range_var.get(),
                            log_level=self.log_level_var.get(),
                            open_console=self.open_console_var.get(),
                            log_to_file=self.log_to_file_var.get(),
                            quality_override_enabled=self.quality_override_enabled_var.get(),
                            quality_ratio=self.quality_ratio_var.get(),
                            balanced_ratio=self.balanced_ratio_var.get(),
                            performance_ratio=self.performance_ratio_var.get(),
                            ultra_perf_ratio=self.ultra_perf_ratio_var.get(),
                            cas_enabled=self.cas_enabled_var.get(),
                            cas_type=self.cas_type_var.get(),
                            cas_sharpness=self.cas_sharpness_var.get(),
                            nvngx_dx12=self.nvngx_dx12_var.get(),
                            nvngx_dx11=self.nvngx_dx11_var.get(),
                            nvngx_vulkan=self.nvngx_vulkan_var.get(),
                            overlay_mode=self.overlay_mode_var.get(),
                            overlay_show_fps=self.overlay_show_fps_var.get(),
                            overlay_show_frametime=self.overlay_show_frametime_var.get(),
                            overlay_show_messages=self.overlay_show_messages_var.get(),
                            overlay_position=self.overlay_position_var.get(),
                            overlay_scale=self.overlay_scale_var.get(),
                            overlay_font_size=self.overlay_font_size_var.get()
                        )
                    
                    if result:
                        # Instalar OptiPatcher si está habilitado
                        if self.optipatcher_enabled_var.get():
                            optipatcher_asi = MOD_SOURCE_DIR / "OptiPatcher" / "OptiPatcher.asi"
                            if optipatcher_asi.exists():
                                self.log('INFO', f"Instalando OptiPatcher en {game_name}...")
                                optipatcher_result = install_optipatcher(
                                    target_dir=game_path,
                                    optipatcher_asi_path=str(optipatcher_asi),
                                    log_func=self.log
                                )
                                if not optipatcher_result:
                                    self.log('WARN', f"OptiPatcher no se pudo instalar en {game_name}")
                            else:
                                self.log('WARN', f"OptiPatcher.asi no encontrado. Usa 'Buscar actualizaciones' para descargarlo.")
                        
                        success_count += 1
                        self.log('OK', f"✅ {game_name}: Instalado correctamente")
                        # Mejora #3: Guardar en lista de exitosos
                        self.last_operation_results['success'].append(game_name)
                        # Mejora #5: Actualizar estado en tiempo real (re-detectar)
                        self.after(0, lambda p=game_path: self.update_game_status_realtime(p, "✅ OptiScaler (Upscaling)", "#00FF88", force=False))
                    else:
                        fail_count += 1
                        self.log('ERROR', f"❌ {game_name}: Fallo en instalación")
                        # Mejora #3: Guardar en lista de fallidos
                        self.last_operation_results['failed'].append((game_name, "Fallo en instalación"))
                        # Mejora #5: Actualizar estado en tiempo real (forzar error, no re-detectar)
                        self.after(0, lambda p=game_path: self.update_game_status_realtime(p, "❌ Fallo", "#FF4444", force=True))
                        
                except Exception as e:
                    fail_count += 1
                    self.log('ERROR', f"❌ Error en {game_path}: {e}")
                    # Mejora #3: Guardar en lista de fallidos
                    game_name = self.games_data.get(game_path, ("Juego desconocido", None, None, None))[0]
                    self.last_operation_results['failed'].append((game_name, str(e)))
                    # Actualizar UI con error (forzar, no re-detectar)
                    self.after(0, lambda p=game_path: self.update_game_status_realtime(p, "❌ Error", "#FF4444", force=True))
            
            # Mostrar resultado en la barra de estado
            def finish_install():
                self.apply_btn.configure(state="normal", text="✓ APLICAR")
                self.progress_bar.set(1.0)
                if fail_count == 0:
                    # Mejora #3: Color verde para éxito
                    self.set_progress_color("#00FF88")
                    self.status_label.configure(
                        text=f"✅ Instalación completada: {success_count} juego(s) instalado(s) (clic para detalles)",
                        text_color="#00FF88",
                        cursor="hand2"  # Cursor de mano para indicar que es clicable
                    )
                else:
                    # Mejora #3: Color naranja para advertencia
                    self.set_progress_color("#FFA500")
                    self.status_label.configure(
                        text=f"⚠️ Completado: {success_count} exitosos, {fail_count} fallidos (clic para detalles)",
                        text_color="#FFA500",
                        cursor="hand2"
                    )
                # La barra permanece visible mostrando el último estado
                # Mejora #9: Cambiar a modo compacto al terminar
                self.after(1500, self.set_progress_mode_compact)
            
            self.after(0, finish_install)
            
            # Rescanear para actualizar estados (silenciosamente)
            self.after(1000, lambda: self.scan_games_action(silent=True))
        
        threading.Thread(target=install_thread, daemon=True).start()
        
    def remove_from_selected(self):
        """Elimina el mod de los juegos seleccionados."""
        if not self.selected_games:
            self.show_progress()
            # Mejora #3: Color naranja para advertencia
            self.set_progress_color("#FFA500")
            self.status_label.configure(text="⚠️ No hay juegos seleccionados", text_color="#FFA500")
            self.progress_bar.set(0)
            return
        
        count = len(self.selected_games)
        if not messagebox.askyesno(
            "Confirmar",
            f"¿Desinstalar OptiScaler de {count} juego(s)?"
        ):
            return
        
        # Mostrar barra de progreso
        self.show_progress()
        self.progress_bar.configure(mode="determinate")
        self.progress_bar.set(0)
        # Mejora #3: Color azul durante desinstalación
        self.set_progress_color("#00BFFF")
        
        # Mejora #4: Iniciar contador de tiempo
        self.progress_start_time = time.time()
        
        self.remove_btn.configure(state="disabled", text="⏳ Desinstalando...")
        
        def uninstall_thread():
            success_count = 0
            fail_count = 0
            total = len(self.selected_games)
            current = 0
            
            # Mejora #3: Limpiar resultados anteriores
            self.last_operation_results = {
                'success': [],
                'failed': [],
                'operation': 'Desinstalación'
            }
            
            for game_path in self.selected_games:
                try:
                    game_name, _, _, _ = self.games_data[game_path]
                    current += 1
                    
                    # Mejora #2 y #4: Actualizar progreso con porcentaje y tiempo estimado
                    self.after(0, lambda c=current, t=total, n=game_name: 
                              self.update_progress(c, t, f"🗑️ Desinstalando {c}/{t}: {n[:30]}{'...' if len(n) > 30 else ''}", show_time=True))
                    
                    result = uninstall_fsr_mod(game_path, self.log)
                    
                    # Desinstalar OptiPatcher también
                    uninstall_optipatcher(game_path, self.log)
                    
                    if result:
                        success_count += 1
                        self.log('OK', f"✅ {game_name}: Desinstalado")
                        # Mejora #3: Guardar en lista de exitosos
                        self.last_operation_results['success'].append(game_name)
                        # Mejora #5: Actualizar estado en tiempo real (re-detectar)
                        self.after(0, lambda p=game_path: self.update_game_status_realtime(p, "⭕ Ausente", "#888888", force=False))
                    else:
                        fail_count += 1
                        self.log('ERROR', f"❌ {game_name}: Fallo en desinstalación")
                        # Mejora #3: Guardar en lista de fallidos
                        self.last_operation_results['failed'].append((game_name, "Fallo en desinstalación"))
                        # Mejora #5: Actualizar estado en tiempo real (forzar error)
                        self.after(0, lambda p=game_path: self.update_game_status_realtime(p, "❌ Error desinst.", "#FF4444", force=True))
                        
                except Exception as e:
                    fail_count += 1
                    self.log('ERROR', f"❌ Error en {game_path}: {e}")
                    # Mejora #3: Guardar en lista de fallidos
                    game_name = self.games_data.get(game_path, ("Juego desconocido", None, None, None))[0]
                    self.last_operation_results['failed'].append((game_name, str(e)))
                    # Actualizar UI con error (forzar)
                    self.after(0, lambda p=game_path: self.update_game_status_realtime(p, "❌ Error", "#FF4444", force=True))
            
            # Mostrar resultado en la barra de estado
            def finish_uninstall():
                self.remove_btn.configure(state="normal", text="❌ ELIMINAR")
                self.progress_bar.set(1.0)
                if fail_count == 0:
                    # Mejora #3: Color verde para éxito
                    self.set_progress_color("#00FF88")
                    self.status_label.configure(
                        text=f"✅ Desinstalación completada: {success_count} juego(s) limpiado(s) (clic para detalles)",
                        text_color="#00FF88",
                        cursor="hand2"
                    )
                else:
                    # Mejora #3: Color naranja para advertencia
                    self.set_progress_color("#FFA500")
                    self.status_label.configure(
                        text=f"⚠️ Completado: {success_count} exitosos, {fail_count} fallidos (clic para detalles)",
                        text_color="#FFA500",
                        cursor="hand2"
                    )
                # La barra permanece visible mostrando el último estado
                # Mejora #9: Cambiar a modo compacto al terminar
                self.after(1500, self.set_progress_mode_compact)
            
            self.after(0, finish_uninstall)
            
            # Rescanear para actualizar estados (silenciosamente)
            self.after(1000, lambda: self.scan_games_action(silent=True))
        
        threading.Thread(target=uninstall_thread, daemon=True).start()
    
    def open_selected_folders(self):
        """Abre las carpetas de los juegos seleccionados en el explorador."""
        if not self.selected_games:
            messagebox.showwarning("Sin selección", "No hay juegos seleccionados")
            return
        
        import subprocess
        opened_count = 0
        
        for game_path in self.selected_games:
            try:
                if os.path.exists(game_path):
                    # Abrir explorador de Windows en la carpeta
                    subprocess.Popen(f'explorer "{game_path}"')
                    opened_count += 1
                else:
                    self.log('WARN', f"⚠️ Carpeta no encontrada: {game_path}")
            except Exception as e:
                self.log('ERROR', f"❌ Error abriendo {game_path}: {e}")
        
        if opened_count > 0:
            self.log('OK', f"✅ {opened_count} carpeta(s) abierta(s)")
        
    def browse_folder(self):
        """Selecciona carpeta de juego manualmente."""
        folder = filedialog.askdirectory(title="Seleccionar carpeta del juego")
        if folder:
            self.manual_path_var.set(folder)
            self.manual_apply_btn.configure(state="normal")
            self.manual_uninstall_btn.configure(state="normal")
            
            # Verificar estado del mod en esa carpeta
            from ..core.scanner import check_mod_status
            status = check_mod_status(folder)
            self.manual_status_var.set(f"Estado actual: {status}")
            
    def apply_manual(self):
        """Aplica mod a la ruta manual."""
        folder = self.manual_path_var.get()
        if not folder or folder == "Ninguna carpeta seleccionada":
            messagebox.showwarning("Error", "Selecciona una carpeta primero")
            return
        
        # Verificar que OptiScaler esté descargado
        if not self.check_optiscaler_available():
            response = messagebox.askyesnocancel(
                "OptiScaler no encontrado",
                "No se encontró OptiScaler descargado.\n\n"
                "¿Deseas ir al panel de Ajustes para descargarlo?"
            )
            if response:  # Yes
                self.show_panel("settings")
            return
        
        if not messagebox.askyesno("Confirmar", f"¿Instalar OptiScaler en:\n{folder}?"):
            return
        
        self.manual_apply_btn.configure(state="disabled", text="⏳ Instalando...")
        
        def install_thread():
            try:
                # Obtener carpeta de OptiScaler
                mod_source_dir = self.get_optiscaler_source_dir()
                if not mod_source_dir:
                    self.after(0, lambda: messagebox.showerror("Error", "No se encontró la carpeta de OptiScaler"))
                    return
                
                # BUGFIX: Verificar si realmente necesita Nukem (solo si fg_mode == "FSR-FG (Nukem's DLSSG)")
                fg_mode = self.fg_mode_var.get()
                needs_nukem = fg_mode == "FSR-FG (Nukem's DLSSG)"
                
                if needs_nukem:
                    # Obtener carpeta de Nukem/dlssg-to-fsr3
                    nukem_source_dir = self.get_nukem_source_dir()
                    if not nukem_source_dir:
                        self.after(0, lambda: messagebox.showerror("Error", "No se encontró dlssg-to-fsr3.\nDescárgalo desde el panel de Ajustes."))
                        return
                    
                    # Obtener configuraciones del GUI
                    gpu_choice = self.gpu_var.get()
                    upscaler = self.upscaler_var.get()
                    upscale_mode = self.upscale_mode_var.get()
                    dll_name = self.dll_name_var.get()
                    sharpness = float(self.sharpness_var.get())
                    overlay = self.overlay_var.get() == "Activado"
                    mb = self.mb_var.get() == "Activado"
                    
                    result = install_combined_mods(
                        optiscaler_source_dir=mod_source_dir,
                        nukem_source_dir=nukem_source_dir,
                        target_dir=folder,
                        log_func=self.log,
                        spoof_dll_name=dll_name,
                        gpu_choice=gpu_choice,
                        fg_mode_selected=fg_mode,
                        upscaler_selected=upscaler,
                        upscale_mode_selected=upscale_mode,
                        sharpness_selected=sharpness,
                        overlay_selected=overlay,
                        mb_selected=mb,
                        install_nukem=True
                    )
                else:
                    # Obtener configuraciones del GUI
                    gpu_choice = self.gpu_var.get()
                    fg_mode = self.fg_mode_var.get()
                    upscaler = self.upscaler_var.get()
                    upscale_mode = self.upscale_mode_var.get()
                    dll_name = self.dll_name_var.get()
                    sharpness = float(self.sharpness_var.get())
                    overlay = self.overlay_var.get() == "Activado"
                    mb = self.mb_var.get() == "Activado"
                    
                    result = inject_fsr_mod(
                        mod_source_dir=mod_source_dir,
                        target_dir=folder,
                        log_func=self.log,
                        spoof_dll_name=dll_name,
                        gpu_choice=gpu_choice,
                        fg_mode_selected=fg_mode,
                        upscaler_selected=upscaler,
                        upscale_mode_selected=upscale_mode,
                        sharpness_selected=sharpness,
                        overlay_selected=overlay,
                        mb_selected=mb,
                        auto_hdr=self.auto_hdr_var.get(),
                        nvidia_hdr_override=self.nvidia_hdr_override_var.get(),
                        hdr_rgb_range=self.hdr_rgb_range_var.get(),
                        log_level=self.log_level_var.get(),
                        open_console=self.open_console_var.get(),
                        log_to_file=self.log_to_file_var.get(),
                        quality_override_enabled=self.quality_override_enabled_var.get(),
                        quality_ratio=self.quality_ratio_var.get(),
                        balanced_ratio=self.balanced_ratio_var.get(),
                        performance_ratio=self.performance_ratio_var.get(),
                        ultra_perf_ratio=self.ultra_perf_ratio_var.get(),
                        cas_enabled=self.cas_enabled_var.get(),
                        cas_type=self.cas_type_var.get(),
                        cas_sharpness=self.cas_sharpness_var.get(),
                        nvngx_dx12=self.nvngx_dx12_var.get(),
                        nvngx_dx11=self.nvngx_dx11_var.get(),
                        nvngx_vulkan=self.nvngx_vulkan_var.get(),
                        overlay_mode=self.overlay_mode_var.get(),
                        overlay_show_fps=self.overlay_show_fps_var.get(),
                        overlay_show_frametime=self.overlay_show_frametime_var.get(),
                        overlay_show_messages=self.overlay_show_messages_var.get(),
                        overlay_position=self.overlay_position_var.get(),
                        overlay_scale=self.overlay_scale_var.get(),
                        overlay_font_size=self.overlay_font_size_var.get()
                    )
                
                if result:
                    self.after(0, lambda: messagebox.showinfo("Éxito", "Mod instalado correctamente"))
                    from ..core.scanner import check_mod_status
                    status = check_mod_status(folder)
                    self.after(0, lambda: self.manual_status_var.set(f"Estado actual: {status}"))
                else:
                    self.after(0, lambda: messagebox.showerror("Error", "Error al instalar el mod"))
                    
            except Exception as e:
                self.log('ERROR', f"Error en instalación manual: {e}")
                self.after(0, lambda: messagebox.showerror("Error", f"Error:\n{e}"))
            finally:
                self.after(0, lambda: self.manual_apply_btn.configure(state="normal", text="✅ APLICAR MOD"))
        
        threading.Thread(target=install_thread, daemon=True).start()
            
    def uninstall_manual(self):
        """Desinstala mod de la ruta manual."""
        folder = self.manual_path_var.get()
        if not folder or folder == "Ninguna carpeta seleccionada":
            messagebox.showwarning("Error", "Selecciona una carpeta primero")
            return
        
        if not messagebox.askyesno("Confirmar", f"¿Desinstalar OptiScaler de:\n{folder}?"):
            return
        
        self.manual_uninstall_btn.configure(state="disabled", text="⏳ Desinstalando...")
        
        def uninstall_thread():
            try:
                result = uninstall_fsr_mod(folder, self.log)
                
                # Desinstalar OptiPatcher también
                uninstall_optipatcher(folder, self.log)
                
                if result:
                    self.after(0, lambda: messagebox.showinfo("Éxito", "Mod desinstalado correctamente"))
                    self.after(0, lambda: self.manual_status_var.set("Estado actual: ❌ AUSENTE"))
                else:
                    self.after(0, lambda: messagebox.showerror("Error", "Error al desinstalar"))
                    
            except Exception as e:
                self.log('ERROR', f"Error en desinstalación manual: {e}")
                self.after(0, lambda: messagebox.showerror("Error", f"Error:\n{e}"))
            finally:
                self.after(0, lambda: self.manual_uninstall_btn.configure(state="normal", text="🗑️ DESINSTALAR"))
        
        threading.Thread(target=uninstall_thread, daemon=True).start()
        
    def on_theme_changed(self, choice):
        """Cambia el tema de la aplicación."""
        theme_map = {"Claro": "light", "Oscuro": "dark", "Sistema": "system"}
        ctk.set_appearance_mode(theme_map.get(choice, "dark"))
        self.config["theme"] = choice
        save_config(self.config)
        
    def on_scale_changed(self, choice):
        """Cambia la escala de la interfaz."""
        messagebox.showinfo("Escala", f"Escala {choice} (función en desarrollo)")
    
    def on_gpu_type_changed(self):
        """Se ejecuta cuando el usuario cambia manualmente el tipo de GPU."""
        self.update_fg_options()
        self.log('INFO', f"Tipo de GPU cambiado manualmente a: {'AMD/Intel' if self.gpu_var.get() == 1 else 'NVIDIA'}")
    
    def on_fps_changed(self, value):
        """Actualiza el label cuando cambia el slider de FPS."""
        fps_value = int(float(value))
        if fps_value == 0:
            self.fps_label.configure(text="Sin límite")
        else:
            self.fps_label.configure(text=f"🎯 {fps_value} FPS")
        self.config["fps_limit"] = fps_value
        save_config(self.config)
    
    def on_sharpness_changed(self, value):
        """Actualiza el label cuando cambia el slider de sharpness."""
        sharpness_value = float(value)
        self.sharpness_label.configure(text=f"✨ {sharpness_value:.2f}")
        self.config["sharpness"] = sharpness_value
        save_config(self.config)
    
    def on_hdr_range_changed(self, value):
        """Actualiza el label cuando cambia el slider de HDR RGB Range."""
        range_value = int(float(value))
        self.hdr_range_label.configure(text=f"{range_value} nits")
        self.config["hdr_rgb_range"] = range_value
        save_config(self.config)
    
    # ==================================================================================
    # OVERLAY SETTINGS CALLBACKS
    # ==================================================================================
    
    def _on_overlay_mode_changed(self, *args):
        """Callback cuando cambia el modo de overlay."""
        self.config["overlay_mode"] = self.overlay_mode_var.get()
        save_config(self.config)
        self._update_overlay_ui_visibility()
        self.log('INFO', f"Modo de overlay cambiado a: {self.overlay_mode_var.get()}")
    
    def _on_overlay_metrics_changed(self):
        """Callback cuando cambian las métricas a mostrar."""
        self.config["overlay_show_fps"] = self.overlay_show_fps_var.get()
        self.config["overlay_show_frametime"] = self.overlay_show_frametime_var.get()
        self.config["overlay_show_messages"] = self.overlay_show_messages_var.get()
        save_config(self.config)
        self.mark_preset_custom()
        self.update_custom_state()
    
    def _on_overlay_position_changed(self):
        """Callback cuando cambia la posición del overlay."""
        self.config["overlay_position"] = self.overlay_position_var.get()
        save_config(self.config)
        self.mark_preset_custom()
        self.update_custom_state()
    
    def _on_overlay_scale_changed(self, value):
        """Callback cuando cambia la escala del overlay."""
        try:
            self.overlay_scale_label.configure(text=f"{int(float(value) * 100)}%")
            self.config["overlay_scale"] = float(value)
            save_config(self.config)
            self.mark_preset_custom()
            self.update_custom_state()
        except Exception:
            pass
    
    def _on_overlay_font_changed(self, value):
        """Callback cuando cambia el tamaño de fuente del overlay."""
        try:
            font_size = int(float(value))
            self.overlay_font_label.configure(text=f"{font_size}px")
            self.config["overlay_font_size"] = font_size
            save_config(self.config)
            self.mark_preset_custom()
            self.update_custom_state()
        except Exception:
            pass
    
    def _update_overlay_ui_visibility(self):
        """Actualiza la visibilidad de las opciones de overlay según el modo seleccionado."""
        mode = self.overlay_mode_var.get()
        
        if mode == "Desactivado":
            # Ocultar todo excepto el dropdown de modo
            if hasattr(self, 'overlay_metrics_frame'):
                self.overlay_metrics_frame.pack_forget()
            if hasattr(self, 'position_frame'):
                self.position_frame.pack_forget()
            if hasattr(self, 'scale_frame'):
                self.scale_frame.pack_forget()
            if hasattr(self, 'font_frame'):
                self.font_frame.pack_forget()
        else:
            # Mostrar opciones según el modo
            if hasattr(self, 'overlay_metrics_frame'):
                self.overlay_metrics_frame.pack(fill="x", padx=15, pady=(5, 10))
            if hasattr(self, 'position_frame'):
                self.position_frame.pack(fill="x", padx=15, pady=(5, 10))
            if hasattr(self, 'scale_frame'):
                self.scale_frame.pack(fill="x", pady=(5, 5))
            if hasattr(self, 'font_frame'):
                self.font_frame.pack(fill="x", pady=(5, 10))
            
            # En modo "Básico", solo mostrar FPS
            if mode == "Básico":
                self.overlay_show_fps_var.set(True)
                self.overlay_show_frametime_var.set(False)
                self.overlay_show_messages_var.set(False)
                # Deshabilitar checkboxes de frametime y messages
                if hasattr(self, 'overlay_frametime_check'):
                    self.overlay_frametime_check.configure(state="disabled")
                if hasattr(self, 'overlay_messages_check'):
                    self.overlay_messages_check.configure(state="disabled")
            elif mode == "Completo":
                # Habilitar todos los checkboxes
                if hasattr(self, 'overlay_frametime_check'):
                    self.overlay_frametime_check.configure(state="normal")
                if hasattr(self, 'overlay_messages_check'):
                    self.overlay_messages_check.configure(state="normal")
    
    # ==================================================================================
    # HDR SETTINGS CALLBACKS
    # ==================================================================================
    
    def _on_hdr_changed(self):
        """Callback cuando cambian las opciones de HDR."""
        self.config["auto_hdr"] = self.auto_hdr_var.get()
        self.config["nvidia_hdr_override"] = self.nvidia_hdr_override_var.get()
        save_config(self.config)
        self.mark_preset_custom()
        self.update_custom_state()
    
    def _apply_hdr_preset(self, preset_name):
        """Aplica un preset rápido de HDR."""
        presets = {
            "sdr": {"auto_hdr": False, "nvidia_override": False, "rgb_range": 80.0},
            "hdr400": {"auto_hdr": True, "nvidia_override": False, "rgb_range": 100.0},
            "hdr600": {"auto_hdr": True, "nvidia_override": False, "rgb_range": 150.0},
            "hdr1000": {"auto_hdr": True, "nvidia_override": False, "rgb_range": 200.0}
        }
        
        if preset_name in presets:
            preset = presets[preset_name]
            self.auto_hdr_var.set(preset["auto_hdr"])
            self.nvidia_hdr_override_var.set(preset["nvidia_override"])
            self.hdr_rgb_range_var.set(preset["rgb_range"])
            self._on_hdr_changed()
            self.on_hdr_range_changed(preset["rgb_range"])
    
    def _on_logging_changed(self, *args):
        """Callback cuando cambian las opciones de logging."""
        self.config["log_level"] = self.log_level_var.get()
        self.config["open_console"] = self.open_console_var.get()
        self.config["log_to_file"] = self.log_to_file_var.get()
        save_config(self.config)
    
    def _on_optipatcher_changed(self, *args):
        """Callback cuando cambia el estado de OptiPatcher."""
        self.config["optipatcher_enabled"] = self.optipatcher_enabled_var.get()
        save_config(self.config)
        self.log('INFO', f"OptiPatcher {'habilitado' if self.optipatcher_enabled_var.get() else 'deshabilitado'}")
    
    def update_optipatcher_status(self):
        """Actualiza el label de estado con versión instalada"""
        try:
            optipatcher_dir = MOD_SOURCE_DIR / "OptiPatcher"
            optipatcher_asi = optipatcher_dir / "OptiPatcher.asi"
            version_file = optipatcher_dir / "version.txt"
            
            if optipatcher_asi.exists():
                # Obtener fecha de modificación
                timestamp = optipatcher_asi.stat().st_mtime
                date_str = datetime.fromtimestamp(timestamp).strftime("%d/%m/%Y")
                file_size_kb = optipatcher_asi.stat().st_size / 1024
                
                # Intentar leer versión desde archivo
                version_str = None
                if version_file.exists():
                    try:
                        with open(version_file, 'r', encoding='utf-8') as f:
                            version_str = f.readline().strip()
                    except:
                        pass
                
                if version_str:
                    self.optipatcher_status_label.configure(
                        text=f"📦 Versión {version_str} del {date_str} ({file_size_kb:.0f} KB)",
                        text_color="#4CAF50"
                    )
                else:
                    self.optipatcher_status_label.configure(
                        text=f"📦 Descargado el {date_str} ({file_size_kb:.0f} KB)",
                        text_color="#4CAF50"
                    )
            else:
                self.optipatcher_status_label.configure(
                    text="📦 Plugin no descargado",
                    text_color="#FFA500"
                )
        except Exception as e:
            self.optipatcher_status_label.configure(
                text="⚠️ Error verificando estado",
                text_color="#FF5555"
            )
    
    def check_optipatcher_updates(self):
        """Verifica si hay actualizaciones disponibles de OptiPatcher"""
        def check_in_thread():
            try:
                from src.core.github import GitHubClient
                
                # Obtener última release
                github_client = GitHubClient(repo_type="optipatcher")
                releases = github_client.get_releases()
                
                if not releases:
                    self.after(0, lambda: self._restore_button_state())
                    self.after(0, lambda: messagebox.showinfo(
                        "OptiPatcher",
                        "No se pudieron obtener las releases de GitHub.\n\n"
                        "Verifica tu conexión a internet."
                    ))
                    return
                
                latest = releases[0]
                version = latest.get("tag_name", "unknown")
                published = latest.get("published_at", "")
                
                if published:
                    try:
                        date_obj = datetime.strptime(published, "%Y-%m-%dT%H:%M:%SZ")
                        date_str = date_obj.strftime("%d/%m/%Y")
                    except:
                        date_str = published.split("T")[0]
                else:
                    date_str = "Desconocida"
                
                # Guardar info de release
                self.optipatcher_latest_release = latest
                
                # Verificar si ya está descargado
                optipatcher_asi = MOD_SOURCE_DIR / "OptiPatcher" / "OptiPatcher.asi"
                
                if optipatcher_asi.exists():
                    # Comparar fechas
                    local_timestamp = optipatcher_asi.stat().st_mtime
                    local_date = datetime.fromtimestamp(local_timestamp)
                    
                    try:
                        remote_date = datetime.strptime(published, "%Y-%m-%dT%H:%M:%SZ")
                        
                        if remote_date > local_date:
                            # Hay actualización disponible
                            self.after(0, lambda v=version, d=date_str: self._show_update_available(v, d))
                        else:
                            # Ya está actualizado
                            self.after(0, lambda: self._restore_button_state())
                            self.after(0, lambda v=version, d=date_str: messagebox.showinfo(
                                "OptiPatcher",
                                f"✅ Ya tienes la última versión\n\n"
                                f"Versión: {v}\n"
                                f"Fecha: {d}"
                            ))
                    except:
                        # Si hay error comparando, ofrecer descargar
                        self.after(0, lambda v=version, d=date_str: self._show_update_available(v, d))
                else:
                    # No está descargado, cambiar botón a descargar
                    self.after(0, lambda v=version, d=date_str: self._show_download_option(v, d))
                    
            except Exception as e:
                self.after(0, lambda: self._restore_button_state())
                self.after(0, lambda err=str(e): messagebox.showerror(
                    "Error",
                    f"Error verificando actualizaciones:\n{err}"
                ))
        
        # Mostrar que está verificando
        self.optipatcher_action_btn.configure(text="⏳ Verificando...", state="disabled")
        
        # Ejecutar en thread
        thread = threading.Thread(target=check_in_thread, daemon=True)
        thread.start()
    
    def _restore_button_state(self):
        """Restaura el botón a su estado inicial"""
        self.optipatcher_action_btn.configure(
            text="🔄 Buscar actualizaciones",
            state="normal",
            command=self.check_optipatcher_updates
        )
    
    def _show_update_available(self, version, date_str):
        """Cambia el botón a modo descarga de actualización"""
        self.optipatcher_action_btn.configure(
            text="⬇️ Descargar actualización",
            state="normal",
            command=self.download_optipatcher_update
        )
        
    def _show_update_available(self, version, date_str):
        """Cambia el botón a modo descarga de actualización"""
        self.optipatcher_action_btn.configure(
            text="⬇️ Descargar actualización",
            state="normal",
            command=self.download_optipatcher_update
        )
        
        messagebox.showinfo(
            "Actualización disponible",
            f"🆕 Nueva versión de OptiPatcher\n\n"
            f"Versión: {version}\n"
            f"Fecha: {date_str}\n\n"
            f"Haz clic en 'Descargar actualización' para obtenerla."
        )
    
    def _show_download_option(self, version, date_str):
        """Cambia el botón a modo descarga inicial"""
        self.optipatcher_action_btn.configure(
            text="⬇️ Descargar OptiPatcher",
            state="normal",
            command=self.download_optipatcher_update
        )
        
        messagebox.showinfo(
            "OptiPatcher",
            f"📦 OptiPatcher {version}\n"
            f"Publicado: {date_str}\n\n"
            f"Haz clic en 'Descargar OptiPatcher' para descargarlo."
        )
    
    def download_optipatcher_update(self):
        """Descarga la última versión de OptiPatcher"""
        if not self.optipatcher_latest_release:
            messagebox.showerror("Error", "No hay información de release disponible.")
            return
        
        def download_in_thread():
            try:
                from src.core.github import GitHubClient
                
                self.after(0, lambda: self.log("🔄 Descargando OptiPatcher..."))
                
                # Definir ruta de destino
                optipatcher_dir = MOD_SOURCE_DIR / "OptiPatcher"
                optipatcher_asi = optipatcher_dir / "OptiPatcher.asi"
                
                github_client = GitHubClient(repo_type="optipatcher")
                result = github_client.download_optipatcher(destination_path=str(optipatcher_asi))
                
                if result:
                    self.after(0, lambda: self.log("✅ OptiPatcher descargado correctamente"))
                    self.after(0, self.update_optipatcher_status)
                    self.after(0, self._restore_button_state)
                    self.after(0, lambda: messagebox.showinfo(
                        "Descarga completada",
                        "✅ OptiPatcher descargado correctamente\n\n"
                        "Se instalará automáticamente al instalar OptiScaler en tus juegos."
                    ))
                else:
                    self.after(0, lambda: self.log("❌ Error descargando OptiPatcher"))
                    self.after(0, self._restore_button_state)
                    self.after(0, lambda: messagebox.showerror(
                        "Error",
                        "No se pudo descargar OptiPatcher.\n\n"
                        "Puedes descargarlo manualmente desde GitHub."
                    ))
                    
            except Exception as e:
                self.after(0, lambda: self.log(f"❌ Error: {str(e)}"))
                self.after(0, self._restore_button_state)
                self.after(0, lambda err=str(e): messagebox.showerror(
                    "Error",
                    f"Error durante la descarga:\n{err}\n\n"
                    "Puedes descargar manualmente desde GitHub."
                ))
        
        # Cambiar botón a descargando
        self.optipatcher_action_btn.configure(text="⏳ Descargando...", state="disabled")
        
        # Ejecutar descarga
        thread = threading.Thread(target=download_in_thread, daemon=True)
        thread.start()
    
    def _open_logs_folder(self):
        """Abre la carpeta de logs en el explorador."""
        logs_dir = os.path.join(get_config_dir(), "logs")
        
        # Crear carpeta si no existe
        if not os.path.exists(logs_dir):
            os.makedirs(logs_dir, exist_ok=True)
        
        # Abrir en explorador
        try:
            if platform.system() == "Windows":
                os.startfile(logs_dir)
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", logs_dir])
            else:  # Linux
                subprocess.run(["xdg-open", logs_dir])
            self.log('INFO', f"Carpeta de logs abierta: {logs_dir}")
        except Exception as e:
            self.log('ERROR', f"Error al abrir carpeta de logs: {e}")
            messagebox.showerror("Error", f"No se pudo abrir la carpeta de logs:\n{e}")
    
    def _clean_old_logs(self):
        """Elimina logs de más de 7 días."""
        import time
        from pathlib import Path
        
        logs_dir = Path(get_config_dir()) / "logs"
        
        if not logs_dir.exists():
            messagebox.showinfo("Info", "No hay carpeta de logs para limpiar.")
            return
        
        try:
            # Obtener fecha límite (7 días atrás)
            seven_days_ago = time.time() - (7 * 24 * 60 * 60)
            deleted_count = 0
            
            # Buscar y eliminar archivos .log antiguos
            for log_file in logs_dir.glob("*.log"):
                if log_file.stat().st_mtime < seven_days_ago:
                    log_file.unlink()
                    deleted_count += 1
                    self.log('INFO', f"Log antiguo eliminado: {log_file.name}")
            
            if deleted_count > 0:
                messagebox.showinfo(
                    "Limpieza Completada",
                    f"Se eliminaron {deleted_count} archivo(s) de log antiguos."
                )
                self.log('OK', f"Limpieza de logs: {deleted_count} archivos eliminados")
            else:
                messagebox.showinfo(
                    "Sin archivos antiguos",
                    "No se encontraron logs de más de 7 días."
                )
                self.log('INFO', "Limpieza de logs: no hay archivos antiguos")
        
        except Exception as e:
            self.log('ERROR', f"Error al limpiar logs: {e}")
            messagebox.showerror("Error", f"Error al limpiar logs:\n{e}")
    
    def _on_quality_override_changed(self):
        """Callback cuando cambia el estado de Quality Overrides."""
        enabled = self.quality_override_enabled_var.get()
        
        # Guardar en config
        self.config["quality_override_enabled"] = enabled
        self.config["quality_ratio"] = self.quality_ratio_var.get()
        self.config["balanced_ratio"] = self.balanced_ratio_var.get()
        self.config["performance_ratio"] = self.performance_ratio_var.get()
        self.config["ultra_perf_ratio"] = self.ultra_perf_ratio_var.get()
        save_config(self.config)
        
        self.log('INFO', f"Quality Overrides {'activado' if enabled else 'desactivado'}")
        self._on_advanced_changed()
    
    def _validate_quality_ratio(self, preset_name):
        """Valida y actualiza el ratio de calidad. Muestra warning si es extremo."""
        ratio_vars = {
            'quality': self.quality_ratio_var,
            'balanced': self.balanced_ratio_var,
            'performance': self.performance_ratio_var,
            'ultra_perf': self.ultra_perf_ratio_var
        }
        
        var = ratio_vars.get(preset_name)
        if not var:
            return
        
        try:
            value = var.get()
            
            # Validar rango (0.5 - 4.0)
            if value < 0.5:
                var.set(0.5)
                value = 0.5
            elif value > 4.0:
                var.set(4.0)
                value = 4.0
            
            # Actualizar config
            config_key = f"{preset_name}_ratio" if preset_name != 'ultra_perf' else 'ultra_perf_ratio'
            self.config[config_key] = value
            save_config(self.config)
            
            # Mostrar warning si valores extremos
            all_ratios = [v.get() for v in ratio_vars.values()]
            if any(r < 1.0 for r in all_ratios):
                self.qo_warning_label.configure(
                    text="⚠️ Ratios < 1.0 pueden causar mayor resolución interna (más carga GPU, posibles artifacts)."
                )
            elif any(r > 3.5 for r in all_ratios):
                self.qo_warning_label.configure(
                    text="⚠️ Ratios > 3.5 pueden causar pérdida significativa de calidad visual."
                )
            else:
                self.qo_warning_label.configure(text="")
            
            self._on_advanced_changed()
        
        except Exception as e:
            self.log('ERROR', f"Error validando ratio {preset_name}: {e}")
    
    def _on_cas_changed(self):
        """Callback cuando cambia la configuración de CAS."""
        enabled = self.cas_enabled_var.get()
        cas_type = self.cas_type_var.get()
        sharpness = self.cas_sharpness_var.get()
        
        # Guardar en config
        self.config["cas_enabled"] = enabled
        self.config["cas_type"] = cas_type
        self.config["cas_sharpness"] = sharpness
        save_config(self.config)
        
        self.log('INFO', f"CAS {'activado' if enabled else 'desactivado'} - Tipo: {cas_type}, Intensidad: {sharpness:.2f}")
        self.mark_preset_custom()
        self.update_custom_state()
    
    def _on_cas_sharpness_changed(self, value):
        """Actualiza el label cuando cambia el slider de CAS sharpness."""
        try:
            self.cas_sharpness_label.configure(text=f"✨ {float(value):.2f}")
            self.config["cas_sharpness"] = float(value)
            save_config(self.config)
            self.mark_preset_custom()
            self.update_custom_state()
        except Exception as e:
            self.log('ERROR', f"Error actualizando CAS sharpness: {e}")
    
    def _on_nvngx_changed(self):
        """Callback cuando cambia la configuración de NVNGX spoofing."""
        dx12 = self.nvngx_dx12_var.get()
        dx11 = self.nvngx_dx11_var.get()
        vulkan = self.nvngx_vulkan_var.get()
        
        # Guardar en config
        self.config["nvngx_dx12"] = dx12
        self.config["nvngx_dx11"] = dx11
        self.config["nvngx_vulkan"] = vulkan
        save_config(self.config)
        
        status = []
        if dx12: status.append("DX12")
        if dx11: status.append("DX11")
        if vulkan: status.append("Vulkan")
        
        self.log('INFO', f"NVNGX Spoofing activado para: {', '.join(status) if status else 'Ninguna API'}")
        self.mark_preset_custom()
        self.update_custom_state()
    
    def update_fg_options(self):
        """Actualiza las opciones de Frame Generation según GPU y mods instalados."""
        if not hasattr(self, 'fg_combo'):
            return
        
        # Verificar si dlssg-to-fsr3 está configurado en ajustes
        nukem_configured = False
        if hasattr(self, 'nukem_path_var'):
            # Si ya existe la variable, usarla
            nukem_path = self.nukem_path_var.get().strip()
            nukem_configured = bool(nukem_path and os.path.exists(nukem_path))
        else:
            # Si aún no existe (primera carga), leer del config
            nukem_path = self.config.get("nukem_mod_path", "").strip()
            nukem_configured = bool(nukem_path and os.path.exists(nukem_path))
        
        # Opciones base (siempre disponibles con OptiScaler)
        options = ["Desactivado", "OptiFG"]
        
        # Añadir FSR-FG solo si está configurado en ajustes
        if nukem_configured:
            options.append("FSR-FG (Nukem's DLSSG)")
        
        # Actualizar combobox
        self.fg_combo.configure(values=options)
        
        # Si la opción actual no está disponible, cambiar a "Desactivado"
        current_value = self.fg_mode_var.get()
        if current_value not in options:
            self.fg_mode_var.set("Desactivado")
        
        # Deshabilitar opciones según GPU si es NVIDIA
        if self.gpu_var.get() == 2:  # NVIDIA
            # DLSS solo funciona en NVIDIA, otros upscalers funcionan en todas
            if hasattr(self, 'upscaler_combo'):
                # No bloqueamos nada para NVIDIA, todo funciona
                pass
        else:  # AMD/Intel
            # DLSS no funciona en AMD/Intel, bloquear si está seleccionado
            if hasattr(self, 'upscaler_combo'):
                current_upscaler = self.upscaler_var.get()
                if current_upscaler == "DLSS":
                    self.upscaler_var.set("Automático")
                    self.log('WARN', "DLSS no está disponible en GPUs AMD/Intel. Cambiado a Automático.")
        
    def open_optiscaler_downloader(self):
        """Abre el gestor de descarga de OptiScaler."""
        DownloadWindow(self, "optiscaler")
        
    def open_nukem_downloader(self):
        """Abre el gestor de descarga de dlssg-to-fsr3."""
        DownloadWindow(self, "nukem")
        
    def open_mod_folder(self):
        """Abre la carpeta de mods en el explorador."""
        import subprocess
        if os.path.exists(MOD_SOURCE_DIR):
            subprocess.Popen(f'explorer "{MOD_SOURCE_DIR}"')
        else:
            messagebox.showwarning("Carpeta no encontrada", f"La carpeta de mods no existe:\n{MOD_SOURCE_DIR}")
    
    def get_downloaded_optiscaler_versions(self):
        """Obtiene lista de versiones de OptiScaler descargadas.
        
        Returns:
            list: Lista de versiones disponibles
        """
        import glob
        
        if not os.path.exists(OPTISCALER_DIR):
            return ["Sin versiones descargadas"]
        
        # Buscar carpetas de OptiScaler
        optiscaler_folders = glob.glob(os.path.join(OPTISCALER_DIR, "OptiScaler*"))
        
        if not optiscaler_folders:
            return ["Sin versiones descargadas"]
        
        versions = []
        for folder in optiscaler_folders:
            folder_name = os.path.basename(folder)
            versions.append(folder_name)
        
        # Ordenar por versión (más reciente primero)
        versions.sort(reverse=True)
        
        return versions
    
    def update_version_combos(self):
        """Actualiza los valores de los combos de versión."""
        try:
            # Actualizar OptiScaler
            optiscaler_versions = self.get_downloaded_optiscaler_versions()
            self.optiscaler_version_combo.configure(values=optiscaler_versions)
            if optiscaler_versions and (self.optiscaler_version_var.get() not in optiscaler_versions):
                self.optiscaler_version_var.set(optiscaler_versions[0])
            
            # Para dlssg-to-fsr3, ya no hay combo de versiones (se usa campo de ruta)
            
            self.log('INFO', 'Selectores de versión actualizados')
        except Exception as e:
            self.log('ERROR', f'Error al actualizar selectores de versión: {e}')

    def refresh_optiscaler_versions(self):
        """Alias más semántico usado tras una actualización para refrescar combos."""
        self.update_version_combos()
    
    def update_config_visibility(self):
        """Actualiza la visibilidad de las opciones de configuración según si hay mod instalado."""
        # Verificar si hay OptiScaler instalado
        has_optiscaler = self.check_optiscaler_available()
        
        if has_optiscaler:
            # Mostrar secciones colapsables en el orden correcto, ocultar mensaje
            self.config_no_mod_frame.pack_forget()
            if hasattr(self, 'basic_section'):
                self.basic_section.pack(fill="x", pady=5)
            if hasattr(self, 'advanced_section'):
                self.advanced_section.pack(fill="x", pady=5)
            if hasattr(self, 'overlay_section'):
                self.overlay_section.pack(fill="x", pady=5)
            if hasattr(self, 'hdr_section'):
                self.hdr_section.pack(fill="x", pady=5)
            if hasattr(self, 'cas_section'):
                self.cas_section.pack(fill="x", pady=5)
            if hasattr(self, 'nvngx_section'):
                self.nvngx_section.pack(fill="x", pady=5)
            if hasattr(self, 'debug_section'):
                self.debug_section.pack(fill="x", pady=5)
        else:
            # Ocultar todas las secciones, mostrar solo mensaje
            if hasattr(self, 'basic_section'):
                self.basic_section.pack_forget()
            if hasattr(self, 'advanced_section'):
                self.advanced_section.pack_forget()
            if hasattr(self, 'overlay_section'):
                self.overlay_section.pack_forget()
            if hasattr(self, 'hdr_section'):
                self.hdr_section.pack_forget()
            if hasattr(self, 'debug_section'):
                self.debug_section.pack_forget()
            if hasattr(self, 'cas_section'):
                self.cas_section.pack_forget()
            if hasattr(self, 'nvngx_section'):
                self.nvngx_section.pack_forget()
            self.config_no_mod_frame.pack(fill="x", pady=20, padx=20)
    
    def select_custom_mod_folder(self):
        """Permite seleccionar una carpeta personalizada de mod."""
        from tkinter import filedialog
        
        folder = filedialog.askdirectory(
            title="Seleccionar carpeta de OptiScaler personalizada",
            initialdir=MOD_SOURCE_DIR if os.path.exists(MOD_SOURCE_DIR) else None
        )
        
        if not folder:
            return
        
        # Verificar que tenga archivos .dll (validación básica)
        dll_files = [f for f in os.listdir(folder) if f.endswith('.dll')]
        
        if not dll_files:
            messagebox.showwarning(
                "Carpeta inválida",
                "La carpeta seleccionada no contiene archivos .dll de OptiScaler"
            )
            return
        
        # Guardar en configuración
        self.config["custom_mod_folder"] = folder
        save_config(self.config)
        
        # Actualizar combo
        folder_name = os.path.basename(folder)
        current_values = list(self.optiscaler_version_combo.cget("values"))
        if folder_name not in current_values:
            current_values.append(f"[Custom] {folder_name}")
            self.optiscaler_version_combo.configure(values=current_values)
        
        self.optiscaler_version_var.set(f"[Custom] {folder_name}")
        
        messagebox.showinfo(
            "Carpeta configurada",
            f"Se usará la carpeta personalizada:\n{folder}"
        )
    
    def browse_nukem_folder(self):
        """Permite seleccionar la carpeta de dlssg-to-fsr3 descargada desde Nexus Mods."""
        from tkinter import filedialog
        
        folder = filedialog.askdirectory(
            title="Seleccionar carpeta de dlssg-to-fsr3 descargada desde Nexus Mods",
            initialdir=MOD_SOURCE_DIR if os.path.exists(MOD_SOURCE_DIR) else None
        )
        
        if not folder:
            return
        
        # Verificar que tenga archivos .dll (validación básica)
        dll_files = [f for f in os.listdir(folder) if f.endswith('.dll')]
        
        if not dll_files:
            messagebox.showwarning(
                "Carpeta inválida",
                "La carpeta seleccionada no contiene archivos .dll de dlssg-to-fsr3.\n\n"
                "Asegúrate de seleccionar la carpeta que contiene los archivos del mod descargado desde Nexus Mods."
            )
            return
        
        # Actualizar el campo de texto y guardar en config
        self.nukem_path_var.set(folder)
        self.config["nukem_mod_path"] = folder
        save_config(self.config)
        
        # Actualizar opciones de Frame Generation
        self.update_fg_options()
        
        self.log(f"✅ Carpeta de dlssg-to-fsr3 configurada: {folder}")
        messagebox.showinfo(
            "Carpeta configurada",
            f"Se usará la carpeta de dlssg-to-fsr3:\n{folder}"
        )
    
    def select_custom_nukem_folder(self):
        """Permite seleccionar una carpeta personalizada de dlssg-to-fsr3."""
        from tkinter import filedialog
        
        folder = filedialog.askdirectory(
            title="Seleccionar carpeta de dlssg-to-fsr3 personalizada",
            initialdir=MOD_SOURCE_DIR if os.path.exists(MOD_SOURCE_DIR) else None
        )
        
        if not folder:
            return
        
        # Verificar que tenga archivos .dll (validación básica)
        dll_files = [f for f in os.listdir(folder) if f.endswith('.dll')]
        
        if not dll_files:
            messagebox.showwarning(
                "Carpeta inválida",
                "La carpeta seleccionada no contiene archivos .dll de dlssg-to-fsr3"
            )
            return
        
        # Guardar en configuración
        self.config["custom_nukem_folder"] = folder
        save_config(self.config)
        
        # Actualizar combo
        folder_name = os.path.basename(folder)
        current_values = list(self.nukem_version_combo.cget("values"))
        if folder_name not in current_values:
            current_values.append(f"[Custom] {folder_name}")
            self.nukem_version_combo.configure(values=current_values)
        
        self.nukem_version_var.set(f"[Custom] {folder_name}")
        
        messagebox.showinfo(
            "Carpeta configurada",
            f"Se usará la carpeta personalizada para dlssg-to-fsr3:\n{folder}"
        )
    
    def open_nexus_mods(self):
        """Abre el enlace de Nexus Mods para dlssg-to-fsr3."""
        import webbrowser
        webbrowser.open("https://www.nexusmods.com/site/mods/738")
        self.log("🔗 Abriendo Nexus Mods en el navegador...")
        
    def manage_scan_folders(self):
        """Gestiona carpetas personalizadas de escaneo."""
        from tkinter import filedialog
        
        # Crear ventana modal
        folder_window = ctk.CTkToplevel(self)
        folder_window.title("📁 Gestionar Carpetas de Escaneo")
        folder_window.geometry("700x500")
        folder_window.resizable(False, False)
        
        # Centrar ventana
        folder_window.transient(self)
        folder_window.grab_set()
        
        # Título
        ctk.CTkLabel(
            folder_window,
            text="📁 CARPETAS PERSONALIZADAS DE ESCANEO",
            font=ctk.CTkFont(size=FONT_TITLE, weight="bold"),
            text_color=COLOR_PRIMARY
        ).pack(pady=(20, 10))
        
        # Descripción
        ctk.CTkLabel(
            folder_window,
            text="Añade carpetas adicionales donde buscar juegos instalados.\nEstas carpetas se escanearán junto con Steam, Epic y Xbox.",
            font=ctk.CTkFont(size=FONT_NORMAL),
            text_color="#AAAAAA"
        ).pack(pady=(0, 15))
        
        # Frame principal
        main_frame = ctk.CTkFrame(folder_window, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Lista de carpetas (scrollable)
        list_frame = ctk.CTkFrame(main_frame, fg_color="#1a1a1a", corner_radius=8)
        list_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        ctk.CTkLabel(
            list_frame,
            text="Carpetas actuales:",
            font=ctk.CTkFont(size=FONT_SECTION, weight="bold")
        ).pack(anchor="w", padx=15, pady=(10, 5))
        
        # Scrollable frame para las carpetas
        folders_scroll = ctk.CTkScrollableFrame(list_frame, fg_color="#2b2b2b", height=250)
        folders_scroll.pack(fill="both", expand=True, padx=15, pady=(0, 10))
        
        # Obtener carpetas actuales del config
        custom_folders = self.config.get("custom_game_folders", [])
        
        # Variable para trackear cambios
        folders_modified = {"changed": False}
        
        def refresh_folder_list():
            """Actualiza la lista visual de carpetas."""
            # Limpiar lista
            for widget in folders_scroll.winfo_children():
                widget.destroy()
            
            # Mostrar carpetas
            if not custom_folders:
                ctk.CTkLabel(
                    folders_scroll,
                    text="📂 No hay carpetas personalizadas añadidas",
                    font=ctk.CTkFont(size=FONT_NORMAL),
                    text_color="#666666"
                ).pack(pady=20)
            else:
                for i, folder_path in enumerate(custom_folders):
                    folder_frame = ctk.CTkFrame(folders_scroll, fg_color="#1a1a1a", corner_radius=5)
                    folder_frame.pack(fill="x", pady=3, padx=5)
                    
                    # Path
                    path_label = ctk.CTkLabel(
                        folder_frame,
                        text=folder_path,
                        anchor="w",
                        font=ctk.CTkFont(size=FONT_NORMAL)
                    )
                    path_label.pack(side="left", fill="x", expand=True, padx=10, pady=8)
                    
                    # Botón eliminar
                    del_btn = ctk.CTkButton(
                        folder_frame,
                        text="✕",
                        width=40,
                        height=30,
                        fg_color=COLOR_SECONDARY,
                        hover_color=COLOR_SECONDARY_HOVER,
                        font=ctk.CTkFont(size=16, weight="bold"),
                        command=lambda idx=i: remove_folder(idx)
                    )
                    del_btn.pack(side="right", padx=5)
        
        def add_folder():
            """Abre diálogo para añadir carpeta."""
            folder_path = filedialog.askdirectory(
                title="Seleccionar carpeta de juegos",
                initialdir=os.path.expanduser("~")
            )
            
            if folder_path:
                # Normalizar path
                folder_path = os.path.normpath(folder_path)
                
                # Verificar que no esté duplicada
                if folder_path in custom_folders:
                    messagebox.showwarning("Carpeta duplicada", "Esta carpeta ya está en la lista")
                    return
                
                # Añadir
                custom_folders.append(folder_path)
                folders_modified["changed"] = True
                refresh_folder_list()
                self.log('INFO', f"Carpeta añadida: {folder_path}")
        
        def remove_folder(index):
            """Elimina una carpeta de la lista."""
            if 0 <= index < len(custom_folders):
                removed = custom_folders.pop(index)
                folders_modified["changed"] = True
                refresh_folder_list()
                self.log('INFO', f"Carpeta eliminada: {removed}")
        
        def save_and_close():
            """Guarda los cambios y cierra la ventana."""
            if folders_modified["changed"]:
                # Guardar en config
                self.config["custom_game_folders"] = custom_folders
                save_config(self.config)
                self.log('OK', f"Carpetas guardadas: {len(custom_folders)} carpeta(s)")
                messagebox.showinfo("Guardado", f"Se han guardado {len(custom_folders)} carpeta(s) personalizada(s).\n\nPresiona el botón de escaneo para buscar juegos en estas carpetas.")
            folder_window.destroy()
        
        # Mostrar carpetas iniciales
        refresh_folder_list()
        
        # Botones de acción
        buttons_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        buttons_frame.pack(fill="x", pady=(10, 0))
        
        # Botón añadir
        add_btn = ctk.CTkButton(
            buttons_frame,
            text="➕ Añadir Carpeta",
            command=add_folder,
            height=40,
            fg_color="#3a3a3a",
            hover_color="#4a4a4a",
            font=ctk.CTkFont(size=FONT_NORMAL, weight="bold")
        )
        add_btn.pack(side="left", padx=5, fill="x", expand=True)
        
        # Botón guardar
        save_btn = ctk.CTkButton(
            buttons_frame,
            text="✓ Guardar y Cerrar",
            command=save_and_close,
            height=40,
            fg_color=COLOR_PRIMARY,
            hover_color=COLOR_PRIMARY_HOVER,
            font=ctk.CTkFont(size=FONT_NORMAL, weight="bold")
        )
        save_btn.pack(side="left", padx=5, fill="x", expand=True)
        
        # Botón cancelar
        cancel_btn = ctk.CTkButton(
            buttons_frame,
            text="✕ Cancelar",
            command=folder_window.destroy,
            height=40,
            fg_color=COLOR_SECONDARY,
            hover_color=COLOR_SECONDARY_HOVER,
            font=ctk.CTkFont(size=FONT_NORMAL, weight="bold")
        )
        cancel_btn.pack(side="left", padx=5, fill="x", expand=True)
        
    def save_log(self):
        """Guarda el log en un archivo."""
        from tkinter import filedialog
        import shutil
        
        try:
            # Obtener el archivo de log actual del LogManager
            current_log_file = self.log_manager.logger.handlers[0].baseFilename
            
            # Sugerir nombre de archivo con timestamp
            from datetime import datetime
            default_name = f"gestor_optiscaler_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            
            # Abrir diálogo para guardar
            save_path = filedialog.asksaveasfilename(
                title="Guardar Log",
                defaultextension=".txt",
                initialfile=default_name,
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
            )
            
            if save_path:
                # Copiar el archivo de log
                shutil.copy2(current_log_file, save_path)
                messagebox.showinfo("Éxito", f"Log guardado en:\n{save_path}")
                self.log('OK', f"Log guardado en: {save_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar el log:\n{e}")
            self.log('ERROR', f"Error al guardar log: {e}")
    
    def open_url(self, url):
        """Abre una URL en el navegador predeterminado.
        
        Args:
            url: URL a abrir
        """
        import webbrowser
        try:
            webbrowser.open(url)
            self.log('INFO', f"Abriendo URL: {url}")
        except Exception as e:
            self.log('ERROR', f"Error al abrir URL: {e}")
            messagebox.showerror("Error", f"No se pudo abrir el enlace:\n{url}")
    
    def show_welcome_if_needed(self):
        """Muestra el tutorial de bienvenida si es la primera vez."""
        config_path = APP_DIR / "injector_config.json"
        if should_show_tutorial(config_path):
            self.show_welcome_tutorial()
    
    def check_app_updates(self):
        """Verifica si hay actualizaciones de la aplicación disponibles."""
        self.log("INFO", "Verificando actualizaciones de la aplicación...")
        check_app_updates_async(self)
    
    def show_welcome_tutorial(self):
        """Muestra la ventana de tutorial de bienvenida."""
        config_path = APP_DIR / "injector_config.json"
        WelcomeTutorial(self, config_path)
        
    def on_closing(self):
        """Maneja el cierre de la aplicación."""
        # Detener gamepad thread
        self.gamepad_running = False
        if self.gamepad_thread and self.gamepad_thread.is_alive():
            self.gamepad_thread.join(timeout=1)
        
        # Cerrar pygame
        try:
            pygame.quit()
        except:
            pass
        
        # Guardar configuración básica
        self.config["gpu_choice"] = self.gpu_var.get()
        self.config["fg_mode"] = self.fg_mode_var.get()
        self.config["upscale_mode"] = self.upscale_mode_var.get()
        self.config["last_spoof_name"] = self.dll_name_var.get()
        
        # Guardar HDR Settings
        self.config["auto_hdr"] = self.auto_hdr_var.get()
        self.config["nvidia_hdr_override"] = self.nvidia_hdr_override_var.get()
        self.config["hdr_rgb_range"] = self.hdr_rgb_range_var.get()
        
        # Guardar Debug/Logging
        self.config["log_level"] = self.log_level_var.get()
        self.config["open_console"] = self.open_console_var.get()
        self.config["log_to_file"] = self.log_to_file_var.get()
        
        # Guardar Quality Overrides
        self.config["quality_override_enabled"] = self.quality_override_enabled_var.get()
        self.config["quality_ratio"] = self.quality_ratio_var.get()
        self.config["balanced_ratio"] = self.balanced_ratio_var.get()
        self.config["performance_ratio"] = self.performance_ratio_var.get()
        self.config["ultra_perf_ratio"] = self.ultra_perf_ratio_var.get()
        
        # Guardar CAS Sharpening
        self.config["cas_enabled"] = self.cas_enabled_var.get()
        self.config["cas_type"] = self.cas_type_var.get()
        self.config["cas_sharpness"] = self.cas_sharpness_var.get()
        
        # Guardar NVNGX Spoofing
        self.config["nvngx_dx12"] = self.nvngx_dx12_var.get()
        self.config["nvngx_dx11"] = self.nvngx_dx11_var.get()
        self.config["nvngx_vulkan"] = self.nvngx_vulkan_var.get()
        
        # Guardar Overlay Settings
        self.config["overlay_mode"] = self.overlay_mode_var.get()
        self.config["overlay_show_fps"] = self.overlay_show_fps_var.get()
        self.config["overlay_show_frametime"] = self.overlay_show_frametime_var.get()
        self.config["overlay_show_messages"] = self.overlay_show_messages_var.get()
        self.config["overlay_position"] = self.overlay_position_var.get()
        self.config["overlay_scale"] = self.overlay_scale_var.get()
        self.config["overlay_font_size"] = self.overlay_font_size_var.get()
        
        save_config(self.config)
        
        if messagebox.askokcancel("Salir", "¿Seguro que quieres salir?"):
            self.quit()


class DownloadWindow(ctk.CTkToplevel):
    """Ventana para descargar y gestionar versiones de mods."""
    
    def __init__(self, parent, mod_type="optiscaler"):
        super().__init__(parent)
        
        self.parent = parent
        self.mod_type = mod_type
        
        # Configuración ventana
        titles = {
            "optiscaler": "Descargar OptiScaler",
            "nukem": "Descargar dlssg-to-fsr3"
        }
        self.title(titles.get(mod_type, "Descargar Mod"))
        self.geometry("700x500")
        self.resizable(False, False)
        
        # Aplicar tema oscuro
        self.configure(fg_color="#2b2b2b")
        
        # Centrar ventana
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (700 // 2)
        y = (self.winfo_screenheight() // 2) - (500 // 2)
        self.geometry(f"+{x}+{y}")
        
        # GitHub client
        self.github_client = GitHubClient(
            logger=parent.log,
            repo_type=mod_type
        )
        
        # Variables
        self.releases = []
        self.selected_release = None
        
        # Crear UI
        self.create_ui()
        
        # Protocolo de cierre - actualizar combos al cerrar
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Cargar releases
        self.load_releases()
        
        # Modal
        self.transient(parent)
        self.grab_set()
        
    def create_ui(self):
        """Crea la interfaz de la ventana."""
        # Header
        header = ctk.CTkFrame(self, fg_color="#1a1a1a", height=60)
        header.pack(fill="x", padx=10, pady=10)
        header.pack_propagate(False)
        
        icons = {"optiscaler": "⬆️", "nukem": "🎮"}
        names = {"optiscaler": "OptiScaler", "nukem": "dlssg-to-fsr3"}
        
        ctk.CTkLabel(
            header,
            text=f"{icons.get(self.mod_type, '📦')} {names.get(self.mod_type, 'Mod')}",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(side="left", padx=15)
        
        # Botón actualizar con icono (desactivado en .exe por problemas con PyInstaller)
        if not getattr(sys, 'frozen', False):
            try:
                from PIL import Image
                rescan_icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "icons", "rescan.png")
                rescan_img = ctk.CTkImage(
                    light_image=Image.open(rescan_icon_path),
                    dark_image=Image.open(rescan_icon_path),
                    size=(24, 24)
                )
                refresh_btn = ctk.CTkButton(
                    header,
                    text="",
                    image=rescan_img,
                    command=self.load_releases,
                    width=45,
                    height=40,
                    fg_color="#3a3a3a",
                    hover_color="#4a4a4a"
                )
            except:
                # Fallback si no se encuentra el icono
                refresh_btn = ctk.CTkButton(
                    header,
                    text="🔄",
                    command=self.load_releases,
                    width=45,
                    height=40,
                    fg_color="#3a3a3a",
                    hover_color="#4a4a4a",
                    font=ctk.CTkFont(size=18)
                )
        else:
            # En .exe siempre usar emoji
            refresh_btn = ctk.CTkButton(
                header,
                text="🔄",
                command=self.load_releases,
                width=45,
                height=40,
                fg_color="#3a3a3a",
                hover_color="#4a4a4a",
                font=ctk.CTkFont(size=18)
            )
        
        refresh_btn.pack(side="right", padx=10)
        
        # Lista de releases
        list_frame = ctk.CTkFrame(self, fg_color="transparent")
        list_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        ctk.CTkLabel(
            list_frame,
            text="Versiones disponibles:",
            font=ctk.CTkFont(size=13, weight="bold")
        ).pack(anchor="w", pady=(0, 5))
        
        self.releases_listbox = ctk.CTkScrollableFrame(list_frame, fg_color="#2b2b2b")
        self.releases_listbox.pack(fill="both", expand=True)
        
        # Barra de progreso
        self.progress_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.progress_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        self.progress_bar = ctk.CTkProgressBar(
            self.progress_frame,
            fg_color="#2b2b2b",
            progress_color="#00BFFF"
        )
        self.progress_bar.pack(fill="x", pady=5)
        self.progress_bar.set(0)
        
        self.progress_label = ctk.CTkLabel(
            self.progress_frame,
            text="",
            font=ctk.CTkFont(size=11),
            text_color="#888888"
        )
        self.progress_label.pack()
        
        # Botones
        buttons_frame = ctk.CTkFrame(self, fg_color="transparent")
        buttons_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        ctk.CTkButton(
            buttons_frame,
            text="Cerrar",
            command=self.on_closing,
            height=35,
            fg_color="#3a3a3a",
            hover_color="#4a4a4a"
        ).pack(fill="x")
        
    def load_releases(self):
        """Carga lista de releases desde GitHub."""
        self.progress_label.configure(text="Cargando releases...")
        
        def load_thread():
            try:
                releases = self.github_client.get_releases(use_cache=False)
                self.after(0, lambda: self.populate_releases(releases))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror(
                    "Error",
                    f"Error al cargar releases:\n{e}"
                ))
                self.after(0, lambda: self.progress_label.configure(text="Error al cargar releases"))
        
        threading.Thread(target=load_thread, daemon=True).start()
        
    def populate_releases(self, releases):
        """Puebla la lista de releases."""
        self.releases = releases
        
        # Limpiar lista
        for widget in self.releases_listbox.winfo_children():
            widget.destroy()
        
        if not releases:
            ctk.CTkLabel(
                self.releases_listbox,
                text="No se encontraron releases",
                text_color="#888888"
            ).pack(pady=20)
            self.progress_label.configure(text="")
            return
        
        # Añadir releases
        for release in releases:
            self.create_release_item(release)
        
        self.progress_label.configure(text=f"{len(releases)} versiones disponibles")
        
    def create_release_item(self, release):
        """Crea un item de release en la lista."""
        frame = ctk.CTkFrame(self.releases_listbox, fg_color="#1a1a1a", corner_radius=5)
        frame.pack(fill="x", padx=5, pady=3)
        
        # Info
        info_frame = ctk.CTkFrame(frame, fg_color="transparent")
        info_frame.pack(side="left", fill="x", expand=True, padx=10, pady=8)
        
        # Nombre y tag
        name = release.get('name', release.get('tag_name', 'Unknown'))
        tag = release.get('tag_name', '')
        
        ctk.CTkLabel(
            info_frame,
            text=f"📦 {name}",
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w"
        ).pack(anchor="w")
        
        # Fecha
        published = release.get('published_at', '')
        if published:
            from datetime import datetime
            try:
                date = datetime.strptime(published, '%Y-%m-%dT%H:%M:%SZ')
                date_str = date.strftime('%d/%m/%Y')
            except:
                date_str = published[:10]
                
            ctk.CTkLabel(
                info_frame,
                text=f"📅 {date_str}",
                font=ctk.CTkFont(size=11),
                text_color="#888888",
                anchor="w"
            ).pack(anchor="w")
        
        # Verificar si ya está descargado
        is_downloaded = self.check_if_downloaded(name, tag)
        
        # Botones frame
        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.pack(side="right", padx=10, pady=8)
        
        if is_downloaded:
            # Botón eliminar (X roja)
            delete_btn = ctk.CTkButton(
                btn_frame,
                text="✖",
                command=lambda r=release, n=name: self.delete_release(r, n),
                width=50,
                height=40,
                fg_color="#AA0000",
                hover_color="#CC0000",
                font=ctk.CTkFont(size=18, weight="bold")
            )
            delete_btn.pack()
        else:
            # Botón descargar (flecha hacia abajo)
            download_btn = ctk.CTkButton(
                btn_frame,
                text="⬇",
                command=lambda r=release: self.download_release(r),
                width=50,
                height=40,
                fg_color="#3a3a3a",
                hover_color="#00BFFF",
                font=ctk.CTkFont(size=18, weight="bold")
            )
            download_btn.pack()
    
    def check_if_downloaded(self, name, tag):
        """Verifica si un release ya está descargado.
        
        Args:
            name: Nombre del release
            tag: Tag del release
            
        Returns:
            bool: True si está descargado
        """
        import glob
        
        # Para dlssg-to-fsr3, buscar carpeta con el tag
        if self.mod_type == "nukem":
            if not os.path.exists(DLSSG_TO_FSR3_DIR):
                return False
            # Buscar carpeta específica para esta versión
            tag_clean = tag.replace('v', '').replace('V', '')
            nukem_path = os.path.join(DLSSG_TO_FSR3_DIR, f"dlssg-to-fsr3_{tag_clean}")
            if os.path.exists(nukem_path) and os.path.isdir(nukem_path):
                # Verificar que tenga archivos dentro
                files = os.listdir(nukem_path)
                return len(files) > 0
            return False
        
        # Para OptiScaler, buscar por tag o nombre
        if not os.path.exists(OPTISCALER_DIR):
            return False
        # Buscar carpetas que contengan el tag (ej: "0.7.9" en "OptiScaler_0.7.9")
        tag_clean = tag.replace('v', '').replace('V', '')
        
        patterns = [
            os.path.join(OPTISCALER_DIR, f"*{tag_clean}*"),
            os.path.join(OPTISCALER_DIR, f"*{tag}*"),
        ]
        
        for pattern in patterns:
            matches = glob.glob(pattern)
            for match in matches:
                if os.path.isdir(match):
                    return True
        
        return False
        
    def select_release(self, release):
        """Selecciona un release para descargar."""
        self.selected_release = release
        name = release.get('name', release.get('tag_name', 'Unknown'))
        self.progress_label.configure(text=f"Seleccionado: {name}")
        self.download_btn.configure(state="normal")
    
    def download_release(self, release):
        """Descarga un release específico.
        
        Args:
            release: Información del release a descargar
        """
        self.selected_release = release
        name = release.get('name', release.get('tag_name', 'Unknown'))
        
        if not messagebox.askyesno(
            "Confirmar descarga",
            f"¿Descargar {name}?"
        ):
            return
        
        self.progress_bar.set(0)
        self.progress_label.configure(text=f"Descargando {name}...")
        
        def progress_callback(downloaded, total, complete, message):
            if complete:
                self.after(0, lambda: self.progress_bar.set(1.0))
                self.after(0, lambda: self.progress_label.configure(text=message))
                # Recargar lista para mostrar botón de eliminar
                self.after(1000, self.load_releases)
            else:
                progress = downloaded / total if total > 0 else 0
                self.after(0, lambda: self.progress_bar.set(progress))
                self.after(0, lambda: self.progress_label.configure(text=message or f"{progress:.1%}"))
        
        def download_thread():
            try:
                # Verificar y descargar 7-Zip si es necesario (solo para OptiScaler)
                if self.mod_type == "optiscaler":
                    from ..core.installer import check_and_download_7zip
                    
                    self.after(0, lambda: self.progress_label.configure(text="Verificando 7-Zip..."))
                    
                    if not check_and_download_7zip(self.parent.log):
                        raise Exception("No se pudo obtener 7-Zip. La extracción podría fallar.")
                
                if self.mod_type == "nukem":
                    # Usar carpeta con versión específica en DLSSG_TO_FSR3_DIR
                    tag = release.get('tag_name', '')
                    tag_clean = tag.replace('v', '').replace('V', '')
                    extract_dir = os.path.join(DLSSG_TO_FSR3_DIR, f"dlssg-to-fsr3_{tag_clean}")
                    self.github_client.download_nukem_release(
                        release,
                        extract_dir,
                        progress_callback
                    )
                else:
                    # OptiScaler se descarga a OPTISCALER_DIR
                    self.github_client.download_release(
                        release,
                        progress_callback
                    )
                
                self.after(0, lambda: messagebox.showinfo(
                    "Éxito",
                    f"{name} descargado correctamente"
                ))
                
            except Exception as e:
                self.after(0, lambda: messagebox.showerror(
                    "Error",
                    f"Error durante la descarga:\n{e}"
                ))
                self.after(0, lambda: self.progress_label.configure(text="Error en descarga"))
        
        threading.Thread(target=download_thread, daemon=True).start()
    
    def delete_release(self, release, name):
        """Elimina un release descargado.
        
        Args:
            release: Información del release
            name: Nombre del release
        """
        if not messagebox.askyesno(
            "Confirmar eliminación",
            f"¿Eliminar {name}?"
        ):
            return
        
        import glob
        import shutil
        
        tag = release.get('tag_name', '')
        tag_clean = tag.replace('v', '').replace('V', '')
        
        deleted = False
        
        # Para dlssg-to-fsr3 - usar carpeta con versión en DLSSG_TO_FSR3_DIR
        if self.mod_type == "nukem":
            nukem_path = os.path.join(DLSSG_TO_FSR3_DIR, f"dlssg-to-fsr3_{tag_clean}")
            if os.path.exists(nukem_path):
                try:
                    shutil.rmtree(nukem_path)
                    self.parent.log('OK', f"Eliminado: {nukem_path}")
                    deleted = True
                except Exception as e:
                    self.parent.log('ERROR', f"Error al eliminar {nukem_path}: {e}")
        else:
            # Para OptiScaler, buscar por tag en OPTISCALER_DIR
            patterns = [
                os.path.join(OPTISCALER_DIR, f"*{tag_clean}*"),
                os.path.join(OPTISCALER_DIR, f"*{tag}*"),
            ]
            
            for pattern in patterns:
                matches = glob.glob(pattern)
                for match in matches:
                    try:
                        if os.path.isdir(match):
                            shutil.rmtree(match)
                            self.parent.log('OK', f"Eliminado: {match}")
                            deleted = True
                    except Exception as e:
                        self.parent.log('ERROR', f"Error al eliminar {match}: {e}")
        
        if deleted:
            messagebox.showinfo("Éxito", f"{name} eliminado correctamente")
            # Recargar lista para mostrar botón de descargar
            self.load_releases()
        else:
            messagebox.showwarning("Aviso", f"No se encontró {name} para eliminar")
    
    def on_closing(self):
        """Maneja el cierre de la ventana y actualiza los combos de versión."""
        try:
            self.parent.log('INFO', 'Cerrando gestor de descargas, actualizando versiones...')
            # Actualizar los combos de versión en la ventana principal
            self.parent.update_version_combos()
        except Exception as e:
            self.parent.log('ERROR', f'Error al actualizar al cerrar: {e}')
        finally:
            # Cerrar la ventana
            self.destroy()
        
    def download_selected(self):
        """Descarga el release seleccionado (DEPRECADO - Ya no se usa)."""
        pass


# ==================================================================================
# SISTEMA DE AUTO-ACTUALIZACIÓN DE LA APLICACIÓN
# ==================================================================================

def check_app_updates_async(app_instance):
    """Verifica actualizaciones en thread separado."""
    import threading
    from ..core.app_updater import check_for_updates
    
    def check_thread():
        try:
            result = check_for_updates(logger=app_instance.log)
            
            if result:
                latest_version, release_info = result
                # Mostrar ventana de actualización en el hilo principal
                app_instance.after(0, lambda: show_update_dialog(app_instance, latest_version, release_info))
        except Exception as e:
            app_instance.log("ERROR", f"Error verificando actualizaciones de la app: {e}")
    
    thread = threading.Thread(target=check_thread, daemon=True)
    thread.start()


def show_update_dialog(app_instance, latest_version: str, release_info: dict):
    """Muestra el diálogo de actualización."""
    from ..config.constants import APP_VERSION
    from .components.windows.update_window import UpdateWindow
    
    def on_update_accepted():
        """Callback cuando el usuario acepta actualizar."""
        download_and_install_app_update(app_instance, release_info)
    
    UpdateWindow(
        app_instance,
        current_version=APP_VERSION,
        latest_version=latest_version,
        release_info=release_info,
        update_callback=on_update_accepted
    )


def download_and_install_app_update(app_instance, release_info: dict):
    """Descarga e instala la actualización de la aplicación."""
    from tkinter import messagebox
    import threading
    from ..core.app_updater import download_and_install_update
    
    def download_thread():
        try:
            app_instance.log("INFO", "Iniciando descarga de actualización...")
            
            success = download_and_install_update(
                release_info,
                logger=app_instance.log,
                progress_callback=None  # Podemos añadir barra de progreso si queremos
            )
            
            if success:
                app_instance.log("OK", "Actualización descargada. Cerrando aplicación...")
                # Cerrar la aplicación
                app_instance.after(1000, lambda: app_instance.quit())
            else:
                app_instance.after(0, lambda: messagebox.showerror(
                    "Error",
                    "No se pudo descargar la actualización.\n\n"
                    "Puedes descargarla manualmente desde GitHub."
                ))
        except Exception as e:
            app_instance.log("ERROR", f"Error durante la actualización: {e}")
            app_instance.after(0, lambda: messagebox.showerror(
                "Error",
                f"Error durante la actualización:\n{str(e)}\n\n"
                "Puedes descargar manualmente desde GitHub."
            ))
    
    thread = threading.Thread(target=download_thread, daemon=True)
    thread.start()


if __name__ == "__main__":
    app = GamingApp()
    app.mainloop()

