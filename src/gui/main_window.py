"""Ventana principal de la aplicación."""

import pygame
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
from .widgets.tabs import (
    TabGamesPanel,
    TabModsPanel,
    TabSettingsPanel,
    TabHelpPanel
)
from .components.navigation import NavigableMixin
from ..core.settings import APP_VERSION, APP_TITLE

class MainWindow(ctk.CTk, NavigableMixin):
    """Ventana principal que contiene los tabs y la lógica de GUI principal."""
    
    def __init__(self):
        """Inicializa la ventana principal y sus componentes."""
        super().__init__()
        
        # Configuración de ventana
        self.title(f"{APP_TITLE} {APP_VERSION}")
        self.geometry("1400x800")
        self.minsize(900, 600)
        
        # Grid configuration
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        
        # Estilo por defecto
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")
        
        # Crea sidebar con botones de navegación
        self.setup_navigation()
        
        # Crea los tabs
        self.setup_tabs()
        
        # Bind de eventos
        self.bind("<Control-q>", self.handle_close)
        self.protocol("WM_DELETE_WINDOW", self.handle_close)
        
        # Selecciona el primer tab por defecto
        self.select_tab(0)

    def setup_navigation(self):
        """Configura la barra lateral de navegación."""
        self.navigation_frame = ctk.CTkFrame(self, corner_radius=0)
        self.navigation_frame.grid(row=0, column=0, sticky="nsew")
        self.navigation_frame.grid_rowconfigure(4, weight=1)
        
        # Logo/título
        self.logo_label = ctk.CTkLabel(
            self.navigation_frame, text=APP_TITLE,
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        
        # Botones de navegación
        self.nav_buttons = []
        
        # Juegos
        self.nav_btn_games = ctk.CTkButton(
            self.navigation_frame,
            corner_radius=0,
            height=40,
            border_spacing=10,
            text="1. Seleccionar Juego",
            fg_color="transparent",
            text_color=("gray10", "gray90"),
            hover_color=("gray70", "gray30"),
            anchor="w",
            command=lambda: self.select_tab(0)
        )
        self.nav_btn_games.grid(row=1, column=0, sticky="ew")
        self.nav_buttons.append(self.nav_btn_games)
        
        # Mods
        self.nav_btn_mods = ctk.CTkButton(
            self.navigation_frame,
            corner_radius=0,
            height=40,
            border_spacing=10,
            text="2. Gestionar Mods",
            fg_color="transparent",
            text_color=("gray10", "gray90"),
            hover_color=("gray70", "gray30"),
            anchor="w",
            command=lambda: self.select_tab(1)
        )
        self.nav_btn_mods.grid(row=2, column=0, sticky="ew")
        self.nav_buttons.append(self.nav_btn_mods)
        
        # Ajustes
        self.nav_btn_settings = ctk.CTkButton(
            self.navigation_frame,
            corner_radius=0,
            height=40,
            border_spacing=10,
            text="⚙️ Ajustes",
            fg_color="transparent",
            text_color=("gray10", "gray90"),
            hover_color=("gray70", "gray30"),
            anchor="w",
            command=lambda: self.select_tab(2)
        )
        self.nav_btn_settings.grid(row=3, column=0, sticky="ew")
        self.nav_buttons.append(self.nav_btn_settings)
        
        # Ayuda (al final)
        self.nav_btn_help = ctk.CTkButton(
            self.navigation_frame,
            corner_radius=0,
            height=40,
            border_spacing=10,
            text="❓ Ayuda",
            fg_color="transparent",
            text_color=("gray10", "gray90"),
            hover_color=("gray70", "gray30"),
            anchor="w",
            command=lambda: self.select_tab(3)
        )
        self.nav_btn_help.grid(row=5, column=0, sticky="ew", pady=(0, 10))
        self.nav_buttons.append(self.nav_btn_help)

    def setup_tabs(self):
        """Crea y configura los paneles de tabs."""
        # Frame contenedor
        self.tabs_frame = ctk.CTkFrame(self, corner_radius=0)
        self.tabs_frame.grid(row=0, column=1, sticky="nsew")
        
        # Pestañas
        self.tabs = []
        
        # Tab de juegos
        self.tab_games = TabGamesPanel(self.tabs_frame, self)
        self.tab_games.grid(row=0, column=0, sticky="nsew")
        self.tabs.append(self.tab_games)
        
        # Tab de mods
        self.tab_mods = TabModsPanel(self.tabs_frame, self)
        self.tab_mods.grid(row=0, column=0, sticky="nsew")
        self.tabs.append(self.tab_mods)
        
        # Tab de ajustes
        self.tab_settings = TabSettingsPanel(self.tabs_frame, self)
        self.tab_settings.grid(row=0, column=0, sticky="nsew")
        self.tabs.append(self.tab_settings)
        
        # Tab de ayuda
        self.tab_help = TabHelpPanel(self.tabs_frame)
        self.tab_help.grid(row=0, column=0, sticky="nsew")
        self.tabs.append(self.tab_help)
        
        # Grid configuration del frame contenedor
        self.tabs_frame.grid_rowconfigure(0, weight=1)
        self.tabs_frame.grid_columnconfigure(0, weight=1)

    def select_tab(self, tab_index):
        """
        Cambia al tab especificado y actualiza los botones de navegación.
        
        Args:
            tab_index (int): Índice del tab a mostrar (0-3)
        """
        # Oculta todos los tabs
        for tab in self.tabs:
            tab.grid_remove()
        
        # Resetea el color de los botones
        for btn in self.nav_buttons:
            btn.configure(fg_color="transparent")
        
        # Muestra el tab seleccionado
        self.tabs[tab_index].grid()
        
        # Marca el botón activo
        self.nav_buttons[tab_index].configure(fg_color="gray30")
        
        # Focus en el widget principal del tab si existe
        if hasattr(self.tabs[tab_index], "focus_main_widget"):
            self.tabs[tab_index].focus_main_widget()

    def handle_close(self, event=None):
        """Manejador del evento de cierre de ventana."""
        if messagebox.askokcancel("Salir", "¿Seguro que quieres salir?"):
            self.quit()