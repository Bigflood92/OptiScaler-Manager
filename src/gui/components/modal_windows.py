"""Ventanas modales para la interfaz gráfica."""

import customtkinter as ctk
from .navigation import NavigableMixin

class CustomSelectWindow(ctk.CTkToplevel, NavigableMixin):
    """Ventana modal para selección de opciones."""
    
    def __init__(self, parent, title, options, current_value, log_func, callback):
        super().__init__(parent)
        self.init_navigation()
        
        self.title(title)
        self.log_func = log_func
        self.callback = callback
        self.options = options
        self.selected_value = current_value
        
        # UI Setup
        self.setup_ui()
        self.setup_navigation_bindings()
        
        # Centra la ventana
        window_width = 400
        window_height = min(600, len(options) * 40 + 100)
        
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (window_width // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (window_height // 2)
        
        self.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
    def setup_ui(self):
        """Configura la interfaz de usuario."""
        # Frame principal con scroll
        self.main_frame = ctk.CTkScrollableFrame(self)
        self.main_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        
        # Grid configuration
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Crear botones de opción
        self.navigable_widgets = [[]]
        
        for option in self.options:
            btn = ctk.CTkButton(
                self.main_frame,
                text=option,
                command=lambda o=option: self.on_select(o),
                height=35
            )
            btn.grid(sticky="ew", pady=(0, 5))
            self.navigable_widgets[0].append(btn)
            
            if option == self.selected_value:
                self.focused_indices = [0, len(self.navigable_widgets[0])-1]
        
        # Actualizar el foco visual inicial
        self.after(50, self.update_focus_visuals)

    def on_select(self, value=None):
        """Maneja la selección de una opción."""
        if value is None:
            value = self.options[self.focused_indices[1]]
        self.selected_value = value
        self.destroy()

    def on_cancel(self):
        """Cancela la selección."""
        self.selected_value = None
        self.destroy()

class GameConfigWindow(ctk.CTkToplevel, NavigableMixin):
    """Ventana modal para configuración de juego."""
    
    def __init__(self, parent, game_path, game_name, current_config, log_func):
        super().__init__(parent)
        self.init_navigation()
        
        self.game_path = game_path
        self.log_func = log_func
        self.master = parent
        self.is_closing = False
        self.child_popup = None
        
        self.title(f"Configuración de: {game_name.split(']')[-1].strip()}")
        
        # Setup UI
        self.setup_ui(current_config)
        self.setup_navigation_bindings()
        
        # Bind de teclas
        self.bind("<Escape>", lambda e: self.on_cancel_and_close())

    def setup_ui(self, current_config):
        """Configura la interfaz de usuario."""
        # Setup widgets aquí...
        # Lista de navegación
        self.navigable_widgets = [
            [self.r_gpu_amd, self.r_gpu_nvidia],
            [self.btn_dll_select],
            [self.btn_fg_select],
            [self.btn_upscale_select],
            [self.slider_sharpness],
            [self.switch_overlay, self.switch_motion_blur],
            [self.btn_cancel, self.btn_save]
        ]
        
        # Actualizar foco inicial
        self.after(50, self.update_focus_visuals)

class ModDownloaderWindow(ctk.CTkToplevel, NavigableMixin):
    """Ventana modal para descarga de mods."""
    
    def __init__(self, parent, log_func):
        super().__init__(parent)
        self.init_navigation()
        
        self.log_func = log_func
        self.master = parent
        self.title("Gestor de Descargas de OptiScaler")
        
        # Setup UI
        self.setup_ui()
        self.setup_navigation_bindings()
        
        # Bind de teclas
        self.bind("<Escape>", lambda e: self.destroy())

    def setup_ui(self):
        """Configura la interfaz de usuario."""
        # Setup widgets aquí...
        # Lista de navegación
        self.navigable_widgets = [
            [self.btn_close],
            [self.btn_refresh]
        ]
        
        # Actualizar foco inicial
        self.after(50, self.update_focus_visuals)
        
        # Cargar datos
        self.after(100, self.on_refresh_clicked)