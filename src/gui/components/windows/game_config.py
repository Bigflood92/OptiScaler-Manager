"""Ventana de configuración específica de juego."""

import customtkinter as ctk
from tkinter import messagebox
import traceback

from ....core.installer import (
    read_optiscaler_ini,
    update_optiscaler_ini
)
from ...components.navigation import NavigableMixin
from ...components.popups.custom_select import CustomSelectWindow
from ....config.settings import (
    FG_OPTIONS,
    UPSCALER_OPTIONS,
    UPSCALE_OPTIONS,
    SPOOFING_DLL_NAMES,
    FG_MODE_MAP, FG_MODE_MAP_INVERSE,
    UPSCALER_MAP, UPSCALER_MAP_INVERSE,
    UPSCALE_MODE_MAP, UPSCALE_MODE_MAP_INVERSE
)


class GameConfigWindow(ctk.CTkToplevel, NavigableMixin):
    """Ventana modal para configuración específica de un juego."""
    
    def __init__(self, parent, game_path, game_name, log_func):
        """Inicializa la ventana de configuración.
        
        Args:
            parent: Ventana padre
            game_path (str): Ruta al directorio del juego
            game_name (str): Nombre del juego para mostrar
            log_func (callable): Función para registrar mensajes
        """
        super().__init__(parent)
        self.init_navigation()
        
        self.game_path = game_path
        self.log_func = log_func
        self.master = parent
        self.is_closing = False
        self.child_popup = None
        
        self.title(f"Configuración de: {game_name.split(']')[-1].strip()}")
        
        # Cargar config actual
        try:
            current_config = read_optiscaler_ini(game_path, log_func)
        except Exception as e:
            self.log_func('ERROR', f"Error al leer configuración: {e}")
            traceback.print_exc()
            current_config = None
        
        # UI Setup
        self.setup_ui(current_config)
        self.setup_navigation_bindings()
        
        # Modal
        self.transient(parent)
        self.grab_set()
        
        # Centrar ventana
        window_width = 600
        window_height = 550
        
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (window_width // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (window_height // 2)
        
        self.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # Bindings
        self.bind("<Escape>", lambda e: self.on_cancel_and_close())
        
        # Focus
        self.after(100, self.focus_force)
        
    def setup_ui(self, current_config):
        """Configura la interfaz de usuario.
        
        Args:
            current_config (dict): Configuración actual del juego
        """
        if not current_config:
            current_config = {
                "gpu_choice": 2,  # NVIDIA por defecto
                "fg_mode": "Automático",
                "upscaler": "Automático",
                "upscale_mode": "Automático",
                "sharpness": 0.8,
                "overlay": False,
                "motion_blur": True
            }
        
        # Variables
        self.gpu_choice = ctk.IntVar(value=current_config["gpu_choice"])
        self.spoof_dll_name = ctk.StringVar(value="dxgi.dll")
        # Map codes (from INI) to human-friendly labels when needed
        fg_display = FG_MODE_MAP_INVERSE.get(current_config.get("fg_mode", "auto"), "Automático")
        upscaler_display = UPSCALER_MAP_INVERSE.get(current_config.get("upscaler", "auto"), "Automático")
        upscale_display = UPSCALE_MODE_MAP_INVERSE.get(current_config.get("upscale_mode", "auto"), "Automático")

        self.fg_mode = ctk.StringVar(value=fg_display)
        self.upscaler = ctk.StringVar(value=upscaler_display)
        self.upscale_mode = ctk.StringVar(value=upscale_display)
        self.sharpness = ctk.DoubleVar(value=current_config["sharpness"])
        self.overlay = ctk.BooleanVar(value=current_config["overlay"])
        self.motion_blur = ctk.BooleanVar(value=current_config["motion_blur"])
        
        # Frame principal
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Grid configuration
        main_frame.grid_columnconfigure(2, weight=1)
        
        current_row = 0
        
        # --- GPU Choice ---
        ctk.CTkLabel(
            main_frame,
            text="Tipo de GPU:",
            font=ctk.CTkFont(size=12, weight="bold")
        ).grid(row=current_row, column=0, sticky="w", pady=5)
        
        gpu_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        gpu_frame.grid(row=current_row, column=2, sticky="w")
        
        self.r_gpu_amd = ctk.CTkRadioButton(
            gpu_frame, text="AMD / Intel",
            variable=self.gpu_choice, value=1
        )
        self.r_gpu_amd.pack(side="left", padx=10)
        
        self.r_gpu_nvidia = ctk.CTkRadioButton(
            gpu_frame, text="NVIDIA",
            variable=self.gpu_choice, value=2
        )
        self.r_gpu_nvidia.pack(side="left", padx=10)
        current_row += 1
        
        # --- DLL Choice ---
        ctk.CTkLabel(
            main_frame,
            text="DLL de Inyección:",
            font=ctk.CTkFont(size=12, weight="bold")
        ).grid(row=current_row, column=0, sticky="w", pady=5)
        
        self.btn_dll_select = ctk.CTkButton(
            main_frame,
            text=f"{self.spoof_dll_name.get()} ▾",
            command=self.open_dll_select
        )
        self.btn_dll_select.grid(
            row=current_row, column=2,
            sticky="ew", pady=5
        )
        current_row += 1
        
        # --- Frame Generation ---
        ctk.CTkLabel(
            main_frame,
            text="Modo Frame Gen:",
            font=ctk.CTkFont(size=12, weight="bold")
        ).grid(row=current_row, column=0, sticky="w", pady=5)
        
        self.btn_fg_select = ctk.CTkButton(
            main_frame,
            text=f"{self.fg_mode.get()} ▾",
            command=self.open_fg_select
        )
        self.btn_fg_select.grid(
            row=current_row, column=2,
            sticky="ew", pady=5
        )
        current_row += 1

        # --- Upscaler Backend (Reescalador) ---
        ctk.CTkLabel(
            main_frame,
            text="Reescalador:",
            font=ctk.CTkFont(size=12, weight="bold")
        ).grid(row=current_row, column=0, sticky="w", pady=5)

        self.btn_upscaler_select = ctk.CTkButton(
            main_frame,
            text=f"{self.upscaler.get()} ▾",
            command=self.open_upscaler_select
        )
        self.btn_upscaler_select.grid(
            row=current_row, column=2,
            sticky="ew", pady=5
        )
        current_row += 1
        
        # --- Upscale Mode ---
        ctk.CTkLabel(
            main_frame,
            text="Modo Reescalado:",
            font=ctk.CTkFont(size=12, weight="bold")
        ).grid(row=current_row, column=0, sticky="w", pady=5)
        
        self.btn_upscale_select = ctk.CTkButton(
            main_frame,
            text=f"{self.upscale_mode.get()} ▾",
            command=self.open_upscale_select
        )
        self.btn_upscale_select.grid(
            row=current_row, column=2,
            sticky="ew", pady=5
        )
        current_row += 1
        
        # --- Sharpness ---
        ctk.CTkLabel(
            main_frame,
            text="Nitidez:",
            font=ctk.CTkFont(size=12, weight="bold")
        ).grid(row=current_row, column=0, sticky="w", pady=5)
        
        sharpness_frame = ctk.CTkFrame(
            main_frame, fg_color="transparent"
        )
        sharpness_frame.grid(
            row=current_row, column=2,
            sticky="ew", pady=5
        )
        sharpness_frame.grid_columnconfigure(0, weight=1)
        
        self.slider_sharpness = ctk.CTkSlider(
            sharpness_frame,
            from_=0.0, to=2.0,
            variable=self.sharpness
        )
        self.slider_sharpness.grid(
            row=0, column=0,
            sticky="ew", padx=(0,10)
        )
        
        self.label_sharpness = ctk.CTkLabel(
            sharpness_frame,
            text=f"{self.sharpness.get():.2f}",
            width=40
        )
        self.label_sharpness.grid(row=0, column=1)
        
        self.sharpness.trace_add(
            "write",
            lambda *args: self.label_sharpness.configure(
                text=f"{self.sharpness.get():.2f}"
            )
        )
        current_row += 1
        
        # --- Toggles ---
        toggle_frame = ctk.CTkFrame(
            main_frame, fg_color="transparent"
        )
        toggle_frame.grid(
            row=current_row, column=2,
            sticky="w", pady=5
        )
        
        self.switch_overlay = ctk.CTkSwitch(
            toggle_frame,
            text="Mostrar Overlay",
            variable=self.overlay
        )
        self.switch_overlay.pack(side="left", padx=10)
        
        self.switch_motion_blur = ctk.CTkSwitch(
            toggle_frame,
            text="Desactivar Motion Blur",
            variable=self.motion_blur
        )
        self.switch_motion_blur.pack(side="left", padx=10)
        current_row += 1
        
        # Botones inferiores
        button_frame = ctk.CTkFrame(
            main_frame, fg_color="transparent"
        )
        button_frame.grid(
            row=current_row, column=0,
            columnspan=3, sticky="ew",
            pady=(20,0)
        )
        button_frame.grid_columnconfigure((0,1), weight=1)
        
        self.btn_cancel = ctk.CTkButton(
            button_frame,
            text="Cancelar",
            command=self.on_cancel_and_close,
            fg_color="gray30",
            hover_color="gray40"
        )
        self.btn_cancel.grid(
            row=0, column=0,
            sticky="e", padx=5
        )
        
        self.btn_save = ctk.CTkButton(
            button_frame,
            text="Guardar",
            command=self.on_save_and_close,
            fg_color="#00BFFF",
            hover_color="#008CBA"
        )
        self.btn_save.grid(
            row=0, column=1,
            sticky="w", padx=5
        )
        
        # Lista de navegación
        self.navigable_widgets = [
            [self.r_gpu_amd, self.r_gpu_nvidia],
            [self.btn_dll_select],
            [self.btn_fg_select],
            [self.btn_upscaler_select],
            [self.btn_upscale_select],
            [self.slider_sharpness],
            [self.switch_overlay, self.switch_motion_blur],
            [self.btn_cancel, self.btn_save]
        ]
        
        # Foco inicial
        self.after(50, self.update_focus_visuals)
    
    def open_dll_select(self):
        """Abre selector de DLL de inyección."""
        if self.child_popup:
            self.child_popup.focus_force()
            return
            
        def on_select(value):
            if value:
                self.spoof_dll_name.set(value)
                self.btn_dll_select.configure(text=f"{value} ▾")
            self.child_popup = None
            self.focus_force()
        
        self.child_popup = CustomSelectWindow(
            self, "DLL de Inyección",
            SPOOFING_DLL_NAMES, on_select
        )
    
    def open_fg_select(self):
        """Abre selector de modo Frame Generation."""
        if self.child_popup:
            self.child_popup.focus_force()
            return
            
        def on_select(value):
            if value:
                self.fg_mode.set(value)
                self.btn_fg_select.configure(text=f"{value} ▾")
            self.child_popup = None
            self.focus_force()
        
        self.child_popup = CustomSelectWindow(
            self, "Modo Frame Generation",
            FG_OPTIONS, on_select
        )
    
    def open_upscale_select(self):
        """Abre selector de modo Upscaling."""
        if self.child_popup:
            self.child_popup.focus_force()
            return
            
        def on_select(value):
            if value:
                self.upscale_mode.set(value)
                self.btn_upscale_select.configure(text=f"{value} ▾")
            self.child_popup = None
            self.focus_force()
        
        self.child_popup = CustomSelectWindow(
            self, "Modo Reescalado",
            UPSCALE_OPTIONS, on_select
        )

    def open_upscaler_select(self):
        """Abre selector de Reescalador (backend de upscaling)."""
        if self.child_popup:
            self.child_popup.focus_force()
            return

        def on_select(value):
            if value:
                self.upscaler.set(value)
                self.btn_upscaler_select.configure(text=f"{value} ▾")
            self.child_popup = None
            self.focus_force()

        self.child_popup = CustomSelectWindow(
            self, "Reescalador",
            UPSCALER_OPTIONS, on_select
        )
    
    def on_save_and_close(self):
        """Guarda la configuración y cierra."""
        try:
            # Map human-friendly labels to INI codes
            fg_code = FG_MODE_MAP.get(self.fg_mode.get(), 'auto')
            upscaler_code = UPSCALER_MAP.get(self.upscaler.get(), 'auto')
            upscale_code = UPSCALE_MODE_MAP.get(self.upscale_mode.get(), 'auto')
            result = update_optiscaler_ini(
                self.game_path,
                self.gpu_choice.get(),
                fg_code,
                upscaler_code,
                upscale_code,
                self.sharpness.get(),
                self.overlay.get(),
                self.motion_blur.get(),
                self.log_func
            )
            
            if result:
                self.destroy()
            else:
                messagebox.showerror(
                    "Error",
                    "No se pudo guardar la configuración.",
                    parent=self
                )
                
        except Exception as e:
            self.log_func('ERROR', f"Error al guardar: {e}")
            messagebox.showerror(
                "Error",
                f"Error al guardar: {e}",
                parent=self
            )
    
    def on_cancel_and_close(self):
        """Cierra sin guardar."""
        self.destroy()