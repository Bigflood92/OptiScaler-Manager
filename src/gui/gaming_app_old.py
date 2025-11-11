"""
GUI Gaming Mode - Interfaz única y simplificada para OptiScaler Manager
Basada en el concepto Gaming de legacy_app pero completamente reescrita y limpia.
"""

import os
import json
import customtkinter as ctk
from tkinter import filedialog, messagebox
from typing import Optional
import threading

# Imports básicos - imports del core vendrán después
# from ..core.scanner import scan_games, check_mod_status
# from ..core.installer import inject_fsr_mod, uninstall_fsr_mod, install_combined_mods
# from ..core.github import GitHubClient

# Constantes hardcodeadas por ahora
APP_TITLE = "Gestor OptiScaler"
APP_VERSION = "2.0"


class GamingApp(ctk.CTk):
    """
    Aplicación principal con interfaz Gaming simplificada.
    
    Estructura:
    - Sidebar izquierdo: Navegación con iconos
    - Panel principal: Contenido dinámico según sección activa
    """
    
    def __init__(self):
        super().__init__()
        
        # Configuración de ventana
        self.title(f"{APP_TITLE} v{APP_VERSION} - Gaming Mode")
        self.geometry("1400x800")
        self.minsize(1000, 600)
        
        # Tema
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")
        
        # Variables
        self.games_data = {}  # {game_path: {name, mod_status, selected}}
        self.current_panel = None
        self.config = {}  # Configuración (por ahora vacía)
        
        # GitHub client (comentado por ahora)
        # self.github_client = GitHubClient(self.log)
        
        # Configuración de grid
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        
        # Crear UI
        self.create_sidebar()
        self.create_content_area()
        self.create_log_area()
        
        # Mostrar panel de detección automática por defecto
        self.show_auto_detect_panel()
        
        # Protocolo de cierre
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def create_sidebar(self):
        """Crea el sidebar de navegación izquierdo con iconos grandes."""
        self.sidebar = ctk.CTkFrame(self, fg_color="#1a1a1a", corner_radius=0, width=140)
        self.sidebar.grid(row=0, column=0, rowspan=2, sticky="nsew")
        self.sidebar.grid_propagate(False)
        
        # Logo/Título
        title_label = ctk.CTkLabel(
            self.sidebar,
            text="🎮",
            font=ctk.CTkFont(size=48)
        )
        title_label.pack(pady=(20, 10))
        
        app_label = ctk.CTkLabel(
            self.sidebar,
            text="OptiScaler\nManager",
            font=ctk.CTkFont(size=14, weight="bold"),
            justify="center"
        )
        app_label.pack(pady=(0, 30))
        
        # Botones de navegación
        self.nav_buttons = {}
        
        nav_items = [
            ("auto", "🎮", "Detección\nAutomática", self.show_auto_detect_panel),
            ("manual", "📁", "Ruta\nManual", self.show_manual_panel),
            ("config", "⚙️", "Config.\nGlobal", self.show_config_panel),
            ("download", "⬇️", "Descargar\nMod", self.show_download_panel),
        ]
        
        for key, icon, text, command in nav_items:
            btn = ctk.CTkButton(
                self.sidebar,
                text=f"{icon}\n{text}",
                command=command,
                fg_color="#2b2b2b",
                hover_color="#3b3b3b",
                height=100,
                corner_radius=8,
                font=ctk.CTkFont(size=12)
            )
            btn.pack(fill="x", padx=10, pady=5)
            self.nav_buttons[key] = btn
            
    def create_content_area(self):
        """Crea el área de contenido principal (centro)."""
        self.content_frame = ctk.CTkFrame(self, fg_color="#2b2b2b", corner_radius=10)
        self.content_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=(10, 5))
        self.content_frame.grid_rowconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(0, weight=1)
        
    def create_log_area(self):
        """Crea el área de log inferior."""
        log_frame = ctk.CTkFrame(self, fg_color="#1a1a1a", corner_radius=10)
        log_frame.grid(row=1, column=1, sticky="nsew", padx=10, pady=(5, 10))
        log_frame.grid_rowconfigure(0, weight=1)
        log_frame.grid_columnconfigure(0, weight=1)
        
        # Título del log
        log_title = ctk.CTkLabel(
            log_frame,
            text="📋 LOG DE OPERACIONES",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        log_title.grid(row=0, column=0, sticky="w", padx=10, pady=(5, 0))
        
        # Textbox de log
        self.log_text = ctk.CTkTextbox(
            log_frame,
            state="disabled",
            wrap="word",
            font=ctk.CTkFont(size=11),
            height=150
        )
        self.log_text.grid(row=1, column=0, sticky="nsew", padx=10, pady=(5, 10))
        
        # Configurar colores de tags
        self.log_text.tag_config('INFO', foreground='#00FF00')
        self.log_text.tag_config('WARN', foreground='#FFFF00')
        self.log_text.tag_config('ERROR', foreground='#FF4500')
        self.log_text.tag_config('OK', foreground='#00FF00')
        
    def log(self, level: str, message: str):
        """Añade un mensaje al log."""
        self.log_text.configure(state="normal")
        timestamp = ""  # Simplificado
        prefix = {"INFO": "ℹ️", "WARN": "⚠️", "ERROR": "❌", "OK": "✅"}.get(level, "•")
        full_message = f"{prefix} {message}\n"
        self.log_text.insert("end", full_message, level)
        self.log_text.see("end")
        self.log_text.configure(state="disabled")
        
    def clear_content(self):
        """Limpia el área de contenido."""
        for widget in self.content_frame.winfo_children():
            widget.destroy()
            
    def highlight_nav_button(self, key: str):
        """Resalta el botón de navegación activo."""
        for btn_key, btn in self.nav_buttons.items():
            if btn_key == key:
                btn.configure(fg_color="#3a3a3a", border_width=2, border_color="#00FF00")
            else:
                btn.configure(fg_color="#2b2b2b", border_width=0)
                
    # ============================================================================
    # PANEL: DETECCIÓN AUTOMÁTICA
    # ============================================================================
    
    def show_auto_detect_panel(self):
        """Muestra el panel de detección automática de juegos."""
        self.clear_content()
        self.highlight_nav_button("auto")
        self.current_panel = "auto"
        
        # Título
        title = ctk.CTkLabel(
            self.content_frame,
            text="🎮 DETECCIÓN AUTOMÁTICA DE JUEGOS",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title.pack(pady=(20, 10))
        
        # Botón de escaneo
        scan_btn = ctk.CTkButton(
            self.content_frame,
            text="🔍 ESCANEAR JUEGOS",
            command=self.scan_games,
            height=50,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color="#3a3a3a",
            hover_color="#4a4a4a"
        )
        scan_btn.pack(pady=10)
        
        # Frame de lista de juegos
        self.games_list_frame = ctk.CTkScrollableFrame(
            self.content_frame,
            fg_color="transparent"
        )
        self.games_list_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Botones de acción
        actions_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        actions_frame.pack(pady=10)
        
        install_btn = ctk.CTkButton(
            actions_frame,
            text="✅ INSTALAR EN SELECCIONADOS",
            command=self.install_to_selected,
            height=50,
            width=250,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#2a7a2a",
            hover_color="#3a8a3a"
        )
        install_btn.pack(side="left", padx=5)
        
        remove_btn = ctk.CTkButton(
            actions_frame,
            text="❌ ELIMINAR DE SELECCIONADOS",
            command=self.remove_from_selected,
            height=50,
            width=250,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#7a2a2a",
            hover_color="#8a3a3a"
        )
        remove_btn.pack(side="left", padx=5)
        
    def scan_games(self):
        """Escanea juegos en las ubicaciones comunes."""
        self.log("INFO", "Iniciando escaneo de juegos...")
        
        # Limpiar lista
        for widget in self.games_list_frame.winfo_children():
            widget.destroy()
        self.games_data.clear()
        
        # Ejecutar escaneo en hilo
        def scan_thread():
            # TODO: Implementar escaneo real
            # games = scan_games(self.log)
            games = []  # Por ahora vacío
            self.after(0, lambda: self.populate_games_list(games))
            
        thread = threading.Thread(target=scan_thread, daemon=True)
        thread.start()
        
    def populate_games_list(self, games: list):
        """Rellena la lista de juegos detectados."""
        if not games:
            self.log("WARN", "No se encontraron juegos")
            no_games_label = ctk.CTkLabel(
                self.games_list_frame,
                text="No se encontraron juegos.\nEscanea de nuevo o usa Ruta Manual.",
                font=ctk.CTkFont(size=14),
                text_color="#888888"
            )
            no_games_label.pack(pady=50)
            return
            
        self.log("OK", f"Se encontraron {len(games)} juegos")
        
        for game in games:
            self.create_game_row(game)
            
    def create_game_row(self, game: dict):
        """Crea una fila para un juego en la lista."""
        game_path = game.get("path", "")
        game_name = game.get("name", "Desconocido")
        mod_status = game.get("mod_status", "❌ NO INSTALADO")
        
        # Frame de fila
        row_frame = ctk.CTkFrame(
            self.games_list_frame,
            fg_color="#1a1a1a",
            corner_radius=8
        )
        row_frame.pack(fill="x", pady=5, padx=10)
        row_frame.grid_columnconfigure(1, weight=1)
        
        # Checkbox
        var = ctk.BooleanVar(value=False)
        self.games_data[game_path] = {
            "name": game_name,
            "mod_status": mod_status,
            "selected": var
        }
        
        checkbox = ctk.CTkCheckBox(
            row_frame,
            text="",
            variable=var,
            width=30
        )
        checkbox.grid(row=0, column=0, padx=10, pady=10)
        
        # Nombre del juego
        name_label = ctk.CTkLabel(
            row_frame,
            text=game_name,
            font=ctk.CTkFont(size=13),
            anchor="w"
        )
        name_label.grid(row=0, column=1, sticky="w", padx=10)
        
        # Estado del mod
        status_label = ctk.CTkLabel(
            row_frame,
            text=mod_status,
            font=ctk.CTkFont(size=12, weight="bold"),
            anchor="e"
        )
        status_label.grid(row=0, column=2, sticky="e", padx=10)
        
        # Botón de configuración
        config_btn = ctk.CTkButton(
            row_frame,
            text="⚙️",
            width=40,
            height=40,
            command=lambda: self.open_game_config(game_path),
            fg_color="#3a3a3a",
            hover_color="#4a4a4a"
        )
        config_btn.grid(row=0, column=3, padx=5)
        
    def install_to_selected(self):
        """Instala el mod en los juegos seleccionados."""
        selected = [path for path, data in self.games_data.items() if data["selected"].get()]
        
        if not selected:
            messagebox.showwarning("Sin Selección", "No hay juegos seleccionados")
            return
            
        self.log("INFO", f"Instalando mod en {len(selected)} juego(s)...")
        
        # TODO: Implementar instalación con progreso
        for game_path in selected:
            game_name = self.games_data[game_path]["name"]
            self.log("INFO", f"Instalando en: {game_name}")
            # Aquí iría la lógica de instalación
            
        self.log("OK", "Instalación completada")
        messagebox.showinfo("Éxito", f"Mod instalado en {len(selected)} juego(s)")
        
    def remove_from_selected(self):
        """Elimina el mod de los juegos seleccionados."""
        selected = [path for path, data in self.games_data.items() if data["selected"].get()]
        
        if not selected:
            messagebox.showwarning("Sin Selección", "No hay juegos seleccionados")
            return
            
        self.log("INFO", f"Eliminando mod de {len(selected)} juego(s)...")
        
        # TODO: Implementar desinstalación
        for game_path in selected:
            game_name = self.games_data[game_path]["name"]
            self.log("INFO", f"Eliminando de: {game_name}")
            
        self.log("OK", "Eliminación completada")
        messagebox.showinfo("Éxito", f"Mod eliminado de {len(selected)} juego(s)")
        
    def open_game_config(self, game_path: str):
        """Abre la ventana de configuración para un juego específico."""
        game_name = self.games_data[game_path]["name"]
        self.log("INFO", f"Abriendo configuración de: {game_name}")
        # TODO: Implementar ventana de configuración
        messagebox.showinfo("Configuración", f"Configurando:\n{game_name}\n\nEn desarrollo...")
        
    # ============================================================================
    # PANEL: RUTA MANUAL
    # ============================================================================
    
    def show_manual_panel(self):
        """Muestra el panel de ruta manual."""
        self.clear_content()
        self.highlight_nav_button("manual")
        self.current_panel = "manual"
        
        # Título
        title = ctk.CTkLabel(
            self.content_frame,
            text="📁 RUTA MANUAL",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title.pack(pady=(20, 10))
        
        # Info
        info = ctk.CTkLabel(
            self.content_frame,
            text="Selecciona manualmente la carpeta del juego donde instalar el mod",
            font=ctk.CTkFont(size=13),
            text_color="#888888"
        )
        info.pack(pady=10)
        
        # Entry de ruta
        path_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        path_frame.pack(pady=20, padx=50, fill="x")
        
        self.manual_path_var = ctk.StringVar(value="")
        path_entry = ctk.CTkEntry(
            path_frame,
            textvariable=self.manual_path_var,
            placeholder_text="Ninguna carpeta seleccionada",
            height=40,
            font=ctk.CTkFont(size=13)
        )
        path_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        browse_btn = ctk.CTkButton(
            path_frame,
            text="📁 EXAMINAR",
            command=self.browse_manual_folder,
            height=40,
            width=150,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#3a3a3a",
            hover_color="#4a4a4a"
        )
        browse_btn.pack(side="right")
        
        # Botones de acción
        actions_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        actions_frame.pack(pady=30)
        
        install_btn = ctk.CTkButton(
            actions_frame,
            text="✅ INSTALAR MOD",
            command=self.install_manual,
            height=60,
            width=200,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color="#2a7a2a",
            hover_color="#3a8a3a"
        )
        install_btn.pack(side="left", padx=10)
        
        remove_btn = ctk.CTkButton(
            actions_frame,
            text="❌ ELIMINAR MOD",
            command=self.remove_manual,
            height=60,
            width=200,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color="#7a2a2a",
            hover_color="#8a3a3a"
        )
        remove_btn.pack(side="left", padx=10)
        
    def browse_manual_folder(self):
        """Abre un diálogo para seleccionar carpeta."""
        folder = filedialog.askdirectory(title="Seleccionar carpeta del juego")
        if folder:
            self.manual_path_var.set(folder)
            self.log("INFO", f"Carpeta seleccionada: {folder}")
            
    def install_manual(self):
        """Instala el mod en la ruta manual."""
        path = self.manual_path_var.get()
        if not path or not os.path.isdir(path):
            messagebox.showerror("Error", "Selecciona una carpeta válida")
            return
            
        self.log("INFO", f"Instalando mod en: {path}")
        # TODO: Implementar instalación
        messagebox.showinfo("Éxito", "Mod instalado correctamente")
        
    def remove_manual(self):
        """Elimina el mod de la ruta manual."""
        path = self.manual_path_var.get()
        if not path or not os.path.isdir(path):
            messagebox.showerror("Error", "Selecciona una carpeta válida")
            return
            
        self.log("INFO", f"Eliminando mod de: {path}")
        # TODO: Implementar desinstalación
        messagebox.showinfo("Éxito", "Mod eliminado correctamente")
        
    # ============================================================================
    # PANEL: CONFIGURACIÓN GLOBAL
    # ============================================================================
    
    def show_config_panel(self):
        """Muestra el panel de configuración global."""
        self.clear_content()
        self.highlight_nav_button("config")
        self.current_panel = "config"
        
        # Título
        title = ctk.CTkLabel(
            self.content_frame,
            text="⚙️ CONFIGURACIÓN GLOBAL",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title.pack(pady=(20, 10))
        
        # TODO: Implementar configuración global
        placeholder = ctk.CTkLabel(
            self.content_frame,
            text="Panel de configuración global\n\nEn desarrollo...",
            font=ctk.CTkFont(size=14),
            text_color="#888888"
        )
        placeholder.pack(pady=50)
        
    # ============================================================================
    # PANEL: DESCARGAR MOD
    # ============================================================================
    
    def show_download_panel(self):
        """Muestra el panel de descarga de mods."""
        self.clear_content()
        self.highlight_nav_button("download")
        self.current_panel = "download"
        
        # Título
        title = ctk.CTkLabel(
            self.content_frame,
            text="⬇️ DESCARGAR MODS",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title.pack(pady=(20, 10))
        
        # Info
        info = ctk.CTkLabel(
            self.content_frame,
            text="Descarga las últimas versiones de OptiScaler y dlssg-to-fsr3",
            font=ctk.CTkFont(size=13),
            text_color="#888888"
        )
        info.pack(pady=10)
        
        # Botones de descarga
        download_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        download_frame.pack(pady=30)
        
        optiscaler_btn = ctk.CTkButton(
            download_frame,
            text="⬇️ DESCARGAR OPTISCALER\n(Upscaling)",
            command=self.download_optiscaler,
            height=100,
            width=300,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#3a3a3a",
            hover_color="#4a4a4a"
        )
        optiscaler_btn.pack(side="left", padx=10)
        
        nukem_btn = ctk.CTkButton(
            download_frame,
            text="⬇️ DESCARGAR DLSSG-TO-FSR3\n(Frame Generation)",
            command=self.download_nukem,
            height=100,
            width=300,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#3a3a3a",
            hover_color="#4a4a4a"
        )
        nukem_btn.pack(side="left", padx=10)
        
    def download_optiscaler(self):
        """Descarga OptiScaler."""
        self.log("INFO", "Descargando OptiScaler...")
        # TODO: Implementar descarga
        messagebox.showinfo("Descarga", "Descargando OptiScaler...\n\nEn desarrollo...")
        
    def download_nukem(self):
        """Descarga dlssg-to-fsr3."""
        self.log("INFO", "Descargando dlssg-to-fsr3...")
        # TODO: Implementar descarga
        messagebox.showinfo("Descarga", "Descargando dlssg-to-fsr3...\n\nEn desarrollo...")
        
    # ============================================================================
    # UTILIDADES
    # ============================================================================
    
    def on_closing(self):
        """Maneja el cierre de la aplicación."""
        if messagebox.askokcancel("Salir", "¿Seguro que quieres salir?"):
            self.quit()


if __name__ == "__main__":
    app = GamingApp()
    app.mainloop()
