"""Widgets para la interfaz gráfica de usuario."""

import os
import json
import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
from ..components.navigation import NavigableMixin
from src.core.settings import (
    HELP_TEXT_GAMES,
    HELP_TEXT_MODS,
    HELP_TEXT_SETTINGS,
    HELP_TEXT_HELP
)

class BaseTab(ctk.CTkFrame, NavigableMixin):
    """Clase base para los tabs de la aplicación."""

    def __init__(self, parent, main_window=None):
        """
        Inicializa el tab base.
        
        Args:
            parent: Widget padre de Tkinter
            main_window: Referencia a la ventana principal (opcional)
        """
        super().__init__(parent)
        self.init_navigation()
        self.main_window = main_window
        
        # Grid configuration
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Setup de navegación
        self.setup_navigation_bindings()

    def focus_main_widget(self):
        """
        Define el widget que debe recibir el foco al activar el tab.
        Debe ser implementado por las subclases.
        """
        pass

class TabGamesPanel(BaseTab):
    """Tab para la selección y detección de juegos."""
    
    def __init__(self, parent, main_window):
        """Inicializa el tab de juegos."""
        super().__init__(parent, main_window)

        # Contenedor principal
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        
        # Grid configuration del contenedor
        self.main_frame.grid_rowconfigure(1, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)
        
        # Título y ayuda
        title_frame = ctk.CTkFrame(self.main_frame)
        title_frame.grid(row=0, column=0, padx=10, pady=(10,5), sticky="ew")
        
        title_label = ctk.CTkLabel(
            title_frame,
            text="Selecciona el juego para inyectar FSR",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.grid(row=0, column=0, padx=10, pady=10)
        
        help_label = ctk.CTkLabel(
            self.main_frame,
            text=HELP_TEXT_GAMES,
            wraplength=800,
            justify="left"
        )
        help_label.grid(row=1, column=0, padx=10, pady=5, sticky="nw")

    def focus_main_widget(self):
        """Da foco al primer widget relevante del tab."""
        pass

class TabModsPanel(BaseTab):
    """Tab para la gestión de mods y archivos DLL."""
    
    def __init__(self, parent, main_window):
        """Inicializa el tab de mods."""
        super().__init__(parent, main_window)

        # Contenedor principal
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        
        # Grid configuration del contenedor
        self.main_frame.grid_rowconfigure(1, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)
        
        # Título y ayuda
        title_frame = ctk.CTkFrame(self.main_frame)
        title_frame.grid(row=0, column=0, padx=10, pady=(10,5), sticky="ew")
        
        title_label = ctk.CTkLabel(
            title_frame,
            text="Gestiona los mods y archivos DLL",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.grid(row=0, column=0, padx=10, pady=10)
        
        help_label = ctk.CTkLabel(
            self.main_frame,
            text=HELP_TEXT_MODS,
            wraplength=800,
            justify="left"
        )
        help_label.grid(row=1, column=0, padx=10, pady=5, sticky="nw")

    def focus_main_widget(self):
        """Da foco al primer widget relevante del tab."""
        pass

class TabSettingsPanel(BaseTab):
    """Tab para configuración y ajustes."""
    
    def __init__(self, parent, main_window):
        """Inicializa el tab de ajustes."""
        super().__init__(parent, main_window)

        # Contenedor principal
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        
        # Grid configuration del contenedor
        self.main_frame.grid_rowconfigure(1, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)
        
        # Título y ayuda
        title_frame = ctk.CTkFrame(self.main_frame)
        title_frame.grid(row=0, column=0, padx=10, pady=(10,5), sticky="ew")
        
        title_label = ctk.CTkLabel(
            title_frame,
            text="Configuración y ajustes",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.grid(row=0, column=0, padx=10, pady=10)
        
        help_label = ctk.CTkLabel(
            self.main_frame,
            text=HELP_TEXT_SETTINGS,
            wraplength=800,
            justify="left"
        )
        help_label.grid(row=1, column=0, padx=10, pady=5, sticky="nw")

    def focus_main_widget(self):
        """Da foco al primer widget relevante del tab."""
        pass

class TabHelpPanel(BaseTab):
    """Tab de ayuda y documentación."""
    
    def __init__(self, parent, main_window=None):
        """Inicializa el tab de ayuda."""
        super().__init__(parent, main_window)

        # Contenedor principal
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        
        # Grid configuration del contenedor
        self.main_frame.grid_rowconfigure(1, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)
        
        # Título y ayuda
        title_frame = ctk.CTkFrame(self.main_frame)
        title_frame.grid(row=0, column=0, padx=10, pady=(10,5), sticky="ew")
        
        title_label = ctk.CTkLabel(
            title_frame,
            text="Ayuda y documentación",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.grid(row=0, column=0, padx=10, pady=10)
        
        help_label = ctk.CTkLabel(
            self.main_frame,
            text=HELP_TEXT_HELP,
            wraplength=800,
            justify="left"
        )
        help_label.grid(row=1, column=0, padx=10, pady=5, sticky="nw")

    def focus_main_widget(self):
        """Da foco al primer widget relevante del tab."""
        pass