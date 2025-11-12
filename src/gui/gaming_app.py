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
import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading
import pygame
import time

# Imports de módulos core
from ..core.scanner import scan_games, invalidate_scan_cache
from ..core.config_manager import load_config, save_config
from ..core.installer import inject_fsr_mod, uninstall_fsr_mod, install_combined_mods
from ..core.utils import detect_gpu_vendor, should_use_dual_mod
from ..core.github import GitHubClient
from ..utils.logging import LogManager
from ..config.paths import MOD_SOURCE_DIR, OPTISCALER_DIR, DLSSG_TO_FSR3_DIR, SEVEN_ZIP_PATH, APP_DIR
from .components.windows.welcome_tutorial import WelcomeTutorial, should_show_tutorial

# Constantes
APP_TITLE = "GESTOR AUTOMATIZADO DE OPTISCALER V2.0"
APP_VERSION = "2.2.0"

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
    """Aplicación Gaming Mode - Interfaz completa."""
    
    def __init__(self):
        super().__init__()
        
        # Configuración ventana
        self.title(f"GESTOR AUTOMATIZADO DE OPTISCALER V2.0")
        self.geometry("1400x800")
        self.minsize(1000, 600)
        
        # Tema
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")
        
        # Logger
        self.log_manager = LogManager()
        self.log = lambda level, msg: self.log_manager.log_to_ui(level, msg)
        
        # Variable para tracking de widget enfocado
        self.current_focused_widget = None
        
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
        
        # Cargar iconos
        self.load_icons()
        
        # Inicializar sistema de gamepad
        self.gamepad_connected = False
        self.gamepad = None
        self.gamepad_thread = None
        self.gamepad_running = False
        self.init_gamepad()
        
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
        
        # Mostrar tutorial de bienvenida si es la primera vez
        self.after(500, self.show_welcome_if_needed)
    
    def load_icons(self):
        """Carga todos los iconos de la aplicación."""
        self.icons = {}
        
        # Desactivar iconos PNG en ejecutables compilados (problema con PyInstaller)
        if getattr(sys, 'frozen', False):
            self.log('INFO', "Ejecutando como .exe - usando solo emojis (sin iconos PNG)")
            return
        
        # Solo cargar iconos PNG cuando se ejecuta como script Python
        try:
            from PIL import Image
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
        """Procesa inputs del gamepad."""
        if not self.gamepad_connected or not self.gamepad:
            return
        
        try:
            pygame.event.pump()
            
            # === NAVEGACIÓN CON D-PAD / STICK ===
            # D-Pad arriba o stick arriba
            if self.gamepad.get_hat(0)[1] == 1 or self.gamepad.get_axis(1) < -0.5:
                self.navigate_focus('up')
            # D-Pad abajo o stick abajo
            elif self.gamepad.get_hat(0)[1] == -1 or self.gamepad.get_axis(1) > 0.5:
                self.navigate_focus('down')
            # D-Pad izquierda o stick izquierda
            elif self.gamepad.get_hat(0)[0] == -1 or self.gamepad.get_axis(0) < -0.5:
                self.navigate_focus('left')
            # D-Pad derecha o stick derecha
            elif self.gamepad.get_hat(0)[0] == 1 or self.gamepad.get_axis(0) > 0.5:
                self.navigate_focus('right')
            
            # === BOTONES DE ACCIÓN ===
            # Botón A (0) - Confirmar/Seleccionar
            if self.gamepad.get_button(0):
                self.gamepad_button_press('A')
                time.sleep(0.2)  # Debounce
            
            # Botón B (1) - Cancelar/Volver
            if self.gamepad.get_button(1):
                self.gamepad_button_press('B')
                time.sleep(0.2)
            
            # Botón X (2) - Config rápida
            if self.gamepad.get_button(2):
                self.gamepad_button_press('X')
                time.sleep(0.2)
            
            # Botón Y (3) - Filtro
            if self.gamepad.get_button(3):
                self.gamepad_button_press('Y')
                time.sleep(0.2)
            
            # === BUMPERS - CAMBIAR PESTAÑAS ===
            # LB (4) - Pestaña anterior
            if self.gamepad.get_button(4):
                self.navigate_tabs(-1)
                time.sleep(0.3)
            
            # RB (5) - Pestaña siguiente
            if self.gamepad.get_button(5):
                self.navigate_tabs(1)
                time.sleep(0.3)
            
            # === TRIGGERS - SCROLL RÁPIDO ===
            # LT (eje 2) - Scroll arriba
            if self.gamepad.get_axis(2) > 0.5:
                self.quick_scroll(-200)
            
            # RT (eje 5) - Scroll abajo
            if self.gamepad.get_axis(5) > 0.5:
                self.quick_scroll(200)
            
            # === BOTONES ESPECIALES ===
            # Start (7) - Aplicar cambios
            if self.gamepad.get_button(7):
                self.gamepad_button_press('START')
                time.sleep(0.3)
            
            # Select/Back (6) - Ayuda
            if self.gamepad.get_button(6):
                self.show_panel('help')
                time.sleep(0.3)
            
        except Exception as e:
            self.log('ERROR', f"Error procesando gamepad: {e}")
        
        # Continuar loop si gamepad sigue conectado
        if self.gamepad_connected:
            self.after(50, self.process_gamepad_input)  # 20 FPS polling
    
    def gamepad_button_press(self, button):
        """Maneja presión de botones del gamepad."""
        if button == 'A':
            # Activar widget enfocado
            if self.current_focused_widget:
                try:
                    if isinstance(self.current_focused_widget, ctk.CTkButton):
                        self.current_focused_widget.invoke()
                    elif isinstance(self.current_focused_widget, ctk.CTkCheckBox):
                        current = self.current_focused_widget.get()
                        self.current_focused_widget.select() if not current else self.current_focused_widget.deselect()
                except Exception as e:
                    self.log('ERROR', f"Error al activar widget: {e}")
        
        elif button == 'B':
            # Volver/Cancelar - ir a panel auto
            self.show_panel('auto')
        
        elif button == 'X':
            # Config rápida - ir a panel config
            self.show_panel('config')
        
        elif button == 'Y':
            # Abrir filtro
            self.open_filter()
        
        elif button == 'START':
            # Aplicar cambios
            self.apply_mod_to_selected()
    
    def navigate_focus(self, direction):
        """Navega entre elementos enfocables con gamepad."""
        # Generar evento Tab o Shift+Tab según dirección
        if direction in ['down', 'right']:
            # Simular Tab
            self.event_generate('<Tab>')
        elif direction in ['up', 'left']:
            # Simular Shift+Tab
            self.event_generate('<Shift-Tab>')
    
    def navigate_tabs(self, direction):
        """Navega entre pestañas con bumpers."""
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
            if hasattr(widget, 'configure'):
                try:
                    widget.configure(border_width=0)
                except:
                    pass
        
        if hasattr(widget, 'bind'):
            widget.bind("<FocusIn>", on_focus_in)
            widget.bind("<FocusOut>", on_focus_out)
    
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
                # Buscar scrollable frame en config panel
                for child in self.config_panel.winfo_children():
                    if isinstance(child, ctk.CTkScrollableFrame):
                        scrollable = child
                        break
            elif self.settings_panel.winfo_ismapped():
                for child in self.settings_panel.winfo_children():
                    if isinstance(child, ctk.CTkScrollableFrame):
                        scrollable = child
                        break
            elif self.help_panel.winfo_ismapped():
                for child in self.help_panel.winfo_children():
                    if isinstance(child, ctk.CTkScrollableFrame):
                        scrollable = child
                        break
            
            if not scrollable:
                return
            
            # Obtener canvas y posiciones
            canvas = scrollable._parent_canvas
            
            # Obtener coordenadas del widget en el canvas
            widget_y = widget.winfo_y()
            widget_height = widget.winfo_height()
            
            # Obtener región visible del canvas
            canvas_height = canvas.winfo_height()
            scroll_region = canvas.cget("scrollregion").split()
            if len(scroll_region) < 4:
                return
            
            total_height = float(scroll_region[3])
            
            # Obtener posición actual del scroll (0.0 a 1.0)
            view = canvas.yview()
            visible_top = view[0] * total_height
            visible_bottom = view[1] * total_height
            
            # Determinar si widget está fuera de vista
            widget_top = widget_y
            widget_bottom = widget_y + widget_height
            
            # Margen de seguridad (pixels)
            margin = 50
            
            # Si widget está arriba de la vista visible
            if widget_top < visible_top + margin:
                # Scroll hacia arriba
                target_fraction = max(0, (widget_top - margin) / total_height)
                canvas.yview_moveto(target_fraction)
            
            # Si widget está abajo de la vista visible
            elif widget_bottom > visible_bottom - margin:
                # Scroll hacia abajo
                target_fraction = min(1.0, (widget_bottom - canvas_height + margin) / total_height)
                canvas.yview_moveto(target_fraction)
            
        except Exception as e:
            # Silenciar errores de auto-scroll para no interrumpir navegación
            pass
    
    def setup_drag_scroll(self, scrollable_frame):
        """Configura drag-to-scroll en un CTkScrollableFrame.
        
        Args:
            scrollable_frame: CTkScrollableFrame al que añadir drag scroll
        """
        # Variables para tracking del drag
        drag_data = {"y": 0, "scrolling": False}
        
        def on_mouse_press(event):
            """Inicia el drag."""
            drag_data["y"] = event.y
            drag_data["scrolling"] = False
            # Cambiar cursor
            scrollable_frame._parent_canvas.configure(cursor="hand2")
        
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
                
                # Obtener canvas interno del scrollable frame
                canvas = scrollable_frame._parent_canvas
                
                # Scroll suavizado
                scroll_amount = delta / 3  # Ajustar sensibilidad
                canvas.yview_scroll(int(scroll_amount), "units")
        
        def on_mouse_release(event):
            """Finaliza el drag."""
            drag_data["scrolling"] = False
            # Restaurar cursor
            scrollable_frame._parent_canvas.configure(cursor="")
        
        # Bind eventos al canvas interno
        canvas = scrollable_frame._parent_canvas
        canvas.bind("<Button-1>", on_mouse_press)
        canvas.bind("<B1-Motion>", on_mouse_drag)
        canvas.bind("<ButtonRelease-1>", on_mouse_release)
    
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
            self.add_focus_indicator(btn)
        
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
            text="GESTOR AUTOMATIZADO DE OPTISCALER V2.0",
            font=ctk.CTkFont(size=FONT_TITLE, weight="bold"),
            text_color="#00BFFF"
        ).pack(pady=(15, 5))
        
        # Título del panel
        ctk.CTkLabel(
            self.config_panel,
            text="⚙️ CONFIGURACIÓN DEL MOD",
            font=ctk.CTkFont(size=FONT_TITLE, weight="bold")
        ).pack(pady=(5, 10))
        
        # Scrollable content
        config_scroll = ctk.CTkScrollableFrame(self.config_panel, fg_color="transparent")
        config_scroll.pack(fill="both", expand=True, padx=20, pady=10)
        
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
        
        # Frame contenedor para todas las opciones (oculto si no hay mod)
        self.config_options_frame = ctk.CTkFrame(config_scroll, fg_color="transparent")
        
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
                corner_radius=8
            )
            btn.pack(side="left", padx=5, expand=True, fill="x")
        
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
        
        self.gpu_radio_nvidia = ctk.CTkRadioButton(
            self.gpu_radio_frame,
            text="NVIDIA",
            variable=self.gpu_var,
            value=2,
            font=ctk.CTkFont(size=FONT_NORMAL),
            command=self.on_gpu_type_changed
        )
        self.gpu_radio_nvidia.pack(side="left", padx=10)
        
        # === 1. DLL DE INYECCIÓN ===
        dll_frame = ctk.CTkFrame(self.config_options_frame, fg_color="#1a1a1a", corner_radius=8)
        dll_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(
            dll_frame,
            text="DLL de Inyección:",
            font=ctk.CTkFont(size=FONT_SECTION, weight="bold")
        ).pack(anchor="w", padx=15, pady=(10, 5))
        
        self.dll_combo = ctk.CTkComboBox(
            dll_frame,
            variable=self.dll_name_var,
            values=["dxgi.dll", "d3d11.dll", "d3d12.dll", "winmm.dll"],
            font=ctk.CTkFont(size=FONT_NORMAL),
            width=300
        )
        self.dll_combo.pack(padx=15, pady=(0, 10), fill="x")
        
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
        
        self.upscaler_combo = ctk.CTkComboBox(
            upscaler_frame,
            variable=self.upscaler_var,
            values=["Automático", "FSR 3.1", "FSR 2.2", "XeSS", "DLSS"],
            font=ctk.CTkFont(size=FONT_NORMAL),
            width=300
        )
        self.upscaler_combo.pack(padx=15, pady=(0, 10), fill="x")
        
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
        
        self.upscale_mode_combo = ctk.CTkComboBox(
            upscale_mode_frame,
            variable=self.upscale_mode_var,
            values=["Automático", "Ultra Rendimiento", "Rendimiento", "Equilibrado", "Calidad", "Ultra Calidad"],
            font=ctk.CTkFont(size=13),
            width=300
        )
        self.upscale_mode_combo.pack(padx=15, pady=(0, 10), fill="x")
        
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
        self.fg_combo = ctk.CTkComboBox(
            fg_frame,
            variable=self.fg_mode_var,
            values=["Desactivado", "OptiFG", "FSR-FG (Nukem's DLSSG)"],
            font=ctk.CTkFont(size=FONT_NORMAL),
            width=300
        )
        self.fg_combo.pack(padx=15, pady=(0, 10), fill="x")
        
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
        
        # === 6. SHARPNESS ===
        sharpness_frame = ctk.CTkFrame(self.config_options_frame, fg_color="#1a1a1a", corner_radius=8)
        sharpness_frame.pack(fill="x", pady=10)
        
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
        
        self.config_panel.grid_remove()  # Oculto inicialmente
        
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
            text="GESTOR AUTOMATIZADO DE OPTISCALER V2.0",
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
            text="GESTOR AUTOMATIZADO DE OPTISCALER V2.0",
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
            text="GESTOR AUTOMATIZADO DE OPTISCALER V2.0",
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
        theme_frame = ctk.CTkFrame(settings_scroll, fg_color="#1a1a1a", corner_radius=8)
        theme_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(
            theme_frame,
            text="Tema:",
            font=ctk.CTkFont(size=FONT_SECTION, weight="bold")
        ).pack(anchor="w", padx=15, pady=(10, 5))
        
        ctk.CTkComboBox(
            theme_frame,
            values=["Claro", "Oscuro", "Sistema"],
            variable=self.theme_var,
            command=self.on_theme_changed,
            font=ctk.CTkFont(size=FONT_NORMAL)
        ).pack(fill="x", padx=15, pady=(0, 10))
        
        # === ESCALA ===
        scale_frame = ctk.CTkFrame(settings_scroll, fg_color="#1a1a1a", corner_radius=8)
        scale_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(
            scale_frame,
            text="Escala UI:",
            font=ctk.CTkFont(size=FONT_SECTION, weight="bold")
        ).pack(anchor="w", padx=15, pady=(10, 5))
        
        ctk.CTkComboBox(
            scale_frame,
            values=["80%", "90%", "100%", "110%", "120%"],
            variable=self.scale_var,
            command=self.on_scale_changed,
            font=ctk.CTkFont(size=FONT_NORMAL)
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
        self.optiscaler_version_combo = ctk.CTkComboBox(
            version_frame,
            variable=self.optiscaler_version_var,
            values=optiscaler_versions,
            state="readonly",
            width=250,
            fg_color="#2a2a2a",
            button_color="#3a3a3a",
            button_hover_color="#4a4a4a",
            dropdown_fg_color="#2a2a2a"
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
            text="GESTOR AUTOMATIZADO DE OPTISCALER V2.0",
            font=ctk.CTkFont(size=FONT_TITLE, weight="bold"),
            text_color="#00BFFF"
        ).grid(row=0, column=0, pady=(15, 5))
        
        # Scrollable content
        help_scroll = ctk.CTkScrollableFrame(self.help_panel, fg_color="transparent")
        help_scroll.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        
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
        
        about_text = """Gestor Automatizado de OptiScaler V2.0
        
Aplicación para gestionar e instalar mods de upscaling en juegos de PC.

🔧 Desarrollado para handheld PCs (Steam Deck, ROG Ally, Legion Go, etc.)
📦 Integra OptiScaler (cdozdil) y dlssg-to-fsr3 (Nukem9)
🎮 Soporte completo de gamepad y controles táctiles
🚀 Escaneo automático de juegos en Steam, Epic Games y carpetas personalizadas

Versión: 2.0
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
                "fps_limit": 0
            },
            "balanced": {
                "fg_mode": "OptiFG",
                "upscale_mode": "Equilibrado",
                "upscaler": "Automático",
                "sharpness": 0.5,
                "fps_limit": 0
            },
            "quality": {
                "fg_mode": "Desactivado",
                "upscale_mode": "Calidad",
                "upscaler": "XeSS",
                "sharpness": 0.7,
                "fps_limit": 0
            },
            "default": {
                "fg_mode": "Desactivado",
                "upscale_mode": "Automático",
                "upscaler": "Automático",
                "sharpness": 0.5,
                "fps_limit": 0
            },
            "custom": {
                # No cambia nada, solo para referencia
            }
        }
        
        if preset in presets and preset != "custom":
            config = presets[preset]
            self.fg_mode_var.set(config["fg_mode"])
            self.upscale_mode_var.set(config["upscale_mode"])
            self.upscaler_var.set(config["upscaler"])
            self.sharpness_var.set(config["sharpness"])
            self.fps_limit_var.set(config["fps_limit"])
            
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
        elif preset == "custom":
            self.active_preset_label.configure(text="✏️ Custom")
            self.log('INFO', "Modo personalizado activado")
        
    def scan_games_action(self, silent=False):
        """Ejecuta escaneo de juegos en hilo separado.
        
        Args:
            silent: Si es True, actualiza la lista sin modificar la barra de progreso
        """
        self.log('INFO', "Iniciando escaneo de juegos...")
        
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
    
    def update_game_status_realtime(self, game_path, status_text, status_color):
        """Mejora #5: Actualiza el estado de un juego en la lista en tiempo real."""
        if game_path in self.game_frames:
            frame_data = self.game_frames[game_path]
            status_label = frame_data['status_label']
            game_frame = frame_data['frame']
            
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
        
        platform_combo = ctk.CTkComboBox(
            platform_frame,
            variable=self.filter_platform,
            values=["Todas", "Steam", "Epic Games", "Custom"],
            font=ctk.CTkFont(size=FONT_NORMAL),
            width=300
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
        
        status_combo = ctk.CTkComboBox(
            status_frame,
            variable=self.filter_mod_status,
            values=["Todos", "Instalado", "No instalado"],
            font=ctk.CTkFont(size=FONT_NORMAL),
            width=300
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
            
            # Estado del mod
            status_color = "#00ff00" if "✅" in mod_status else "#888888"
            status_label = ctk.CTkLabel(
                game_frame,
                text=mod_status,
                text_color=status_color,
                font=ctk.CTkFont(size=FONT_SMALL),
                anchor="e",
                cursor="hand2"
            )
            status_label.pack(side="right", padx=5)
            
            # Mejora #5: Guardar referencias para actualización en tiempo real
            self.game_frames[game_path] = {
                'frame': game_frame,
                'status_label': status_label,
                'name': game_name
            }
            
            # Hacer toda la fila clickable
            def make_row_clickable(frame, checkbox, path, variable):
                def on_row_click(e):
                    variable.set(not variable.get())
                    self.toggle_game_selection(path, variable)
                
                def on_enter(e):
                    frame.configure(fg_color="#2a2a2a")
                
                def on_leave(e):
                    frame.configure(fg_color="#1a1a1a")
                
                frame.bind("<Button-1>", on_row_click)
                frame.bind("<Enter>", on_enter)
                frame.bind("<Leave>", on_leave)
                
                for child in frame.winfo_children():
                    if child != checkbox:
                        child.bind("<Button-1>", on_row_click)
            
            make_row_clickable(game_frame, check, game_path, var)
        
        # Actualizar contador
        filtered_count = len(filtered_games)
        selected_in_filtered = len([g for g in filtered_games if g[0] in self.selected_games])
        self.games_counter_label.configure(text=f"{selected_in_filtered}/{filtered_count}")
        
        # Mensaje si no hay resultados
        if not filtered_games:
            no_results = ctk.CTkLabel(
                self.games_scrollable,
                text="❌ No se encontraron juegos con los filtros aplicados",
                font=ctk.CTkFont(size=FONT_NORMAL),
                text_color="#888888"
            )
            no_results.pack(pady=50)
    
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
                    
                    # Usar dual-mod si GPU es AMD/Intel (detección automática)
                    if self.use_dual_mod:
                        # Obtener carpeta de Nukem/dlssg-to-fsr3
                        nukem_source_dir = self.get_nukem_source_dir()
                        if not nukem_source_dir:
                            fail_count += 1
                            self.log('ERROR', f"❌ {game_name}: No se encontró dlssg-to-fsr3. Descárgalo desde Ajustes.")
                            continue
                        
                        # Obtener configuraciones del GUI
                        gpu_choice = self.gpu_var.get()
                        fg_mode = self.fg_mode_var.get()
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
                            mb_selected=mb
                        )
                    
                    if result:
                        success_count += 1
                        self.log('OK', f"✅ {game_name}: Instalado correctamente")
                        # Mejora #3: Guardar en lista de exitosos
                        self.last_operation_results['success'].append(game_name)
                        # Mejora #5: Actualizar estado en tiempo real
                        self.after(0, lambda p=game_path: self.update_game_status_realtime(p, "✅ OptiScaler (Upscaling)", "#00FF88"))
                    else:
                        fail_count += 1
                        self.log('ERROR', f"❌ {game_name}: Fallo en instalación")
                        # Mejora #3: Guardar en lista de fallidos
                        self.last_operation_results['failed'].append((game_name, "Fallo en instalación"))
                        # Mejora #5: Actualizar estado en tiempo real
                        self.after(0, lambda p=game_path: self.update_game_status_realtime(p, "❌ Error", "#FF4444"))
                        
                except Exception as e:
                    fail_count += 1
                    self.log('ERROR', f"❌ Error en {game_path}: {e}")
                    # Mejora #3: Guardar en lista de fallidos
                    game_name = self.games_data.get(game_path, ("Juego desconocido", None, None, None))[0]
                    self.last_operation_results['failed'].append((game_name, str(e)))
            
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
                    
                    if result:
                        success_count += 1
                        self.log('OK', f"✅ {game_name}: Desinstalado")
                        # Mejora #3: Guardar en lista de exitosos
                        self.last_operation_results['success'].append(game_name)
                        # Mejora #5: Actualizar estado en tiempo real
                        self.after(0, lambda p=game_path: self.update_game_status_realtime(p, "⭕ Ausente", "#888888"))
                    else:
                        fail_count += 1
                        self.log('ERROR', f"❌ {game_name}: Fallo en desinstalación")
                        # Mejora #3: Guardar en lista de fallidos
                        self.last_operation_results['failed'].append((game_name, "Fallo en desinstalación"))
                        # Mejora #5: Actualizar estado en tiempo real
                        self.after(0, lambda p=game_path: self.update_game_status_realtime(p, "❌ Error", "#FF4444"))
                        
                except Exception as e:
                    fail_count += 1
                    self.log('ERROR', f"❌ Error en {game_path}: {e}")
                    # Mejora #3: Guardar en lista de fallidos
                    game_name = self.games_data.get(game_path, ("Juego desconocido", None, None, None))[0]
                    self.last_operation_results['failed'].append((game_name, str(e)))
            
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
                
                # Usar dual-mod si GPU es AMD/Intel (detección automática)
                if self.use_dual_mod:
                    # Obtener carpeta de Nukem/dlssg-to-fsr3
                    nukem_source_dir = self.get_nukem_source_dir()
                    if not nukem_source_dir:
                        self.after(0, lambda: messagebox.showerror("Error", "No se encontró dlssg-to-fsr3.\nDescárgalo desde el panel de Ajustes."))
                        return
                    
                    # Obtener configuraciones del GUI
                    gpu_choice = self.gpu_var.get()
                    fg_mode = self.fg_mode_var.get()
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
                        mb_selected=mb
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
    
    def update_config_visibility(self):
        """Actualiza la visibilidad de las opciones de configuración según si hay mod instalado."""
        # Verificar si hay OptiScaler instalado
        has_optiscaler = self.check_optiscaler_available()
        
        if has_optiscaler:
            # Mostrar opciones, ocultar mensaje
            self.config_no_mod_frame.pack_forget()
            self.config_options_frame.pack(fill="both", expand=True)
        else:
            # Ocultar opciones, mostrar mensaje
            self.config_options_frame.pack_forget()
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
        messagebox.showinfo("Carpetas", "Gestión de carpetas personalizadas en desarrollo")
        
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
        
        # Guardar configuración
        self.config["gpu_choice"] = self.gpu_var.get()
        self.config["fg_mode"] = self.fg_mode_var.get()
        self.config["upscale_mode"] = self.upscale_mode_var.get()
        self.config["last_spoof_name"] = self.dll_name_var.get()
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


if __name__ == "__main__":
    app = GamingApp()
    app.mainloop()
