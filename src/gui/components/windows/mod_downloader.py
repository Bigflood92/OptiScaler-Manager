"""Ventana de descarga y configuración de mods."""

import os
import threading
import webbrowser
import customtkinter as ctk
from tkinter import messagebox

from ....core.installer import (
    check_and_download_7zip,
    download_mod_release,
    fetch_github_releases
)
from ...components.navigation import NavigableMixin


class ModDownloaderWindow(ctk.CTkToplevel, NavigableMixin):
    """Ventana modal para descargar y gestionar mods."""
    
    def __init__(self, parent, log_func):
        """Inicializa la ventana de descarga.
        
        Args:
            parent: Ventana padre
            log_func (callable): Función para registrar mensajes
        """
        super().__init__(parent)
        self.init_navigation()
        
        self.title("Gestor de Descargas de OptiScaler")
        self.geometry("650x450")
        self.minsize(600, 400)
        
        self.log_func = log_func
        self.master = parent
        self.current_download = None
        self.releases = []
        
        # UI Setup
        self.setup_ui()
        self.setup_navigation_bindings()
        
        # Modal
        self.transient(parent)
        self.grab_set()
        
        # Bindings
        self.bind("<Escape>", lambda e: self.destroy())
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Focus
        self.after(100, self.focus_force)
        
        # Cargar datos
        self.after(100, self.on_refresh_clicked)

    def setup_ui(self):
        """Configura la interfaz de usuario."""
        # Grid configuration
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Frame superior (botones)
        top_frame = ctk.CTkFrame(self, fg_color="transparent")
        top_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10,0))
        top_frame.grid_columnconfigure(2, weight=1)
        
        # Botones superiores
        self.btn_refresh = ctk.CTkButton(
            top_frame, text="🔄 Refrescar", 
            command=self.on_refresh_clicked,
            width=100
        )
        self.btn_refresh.grid(row=0, column=0, padx=5)
        
        self.btn_github = ctk.CTkButton(
            top_frame, text="GitHub ↗", 
            command=self.open_github_releases,
            width=100
        )
        self.btn_github.grid(row=0, column=1, padx=5)
        
        self.btn_close = ctk.CTkButton(
            top_frame, text="✖ Cerrar",
            command=self.destroy,
            fg_color="gray30",
            hover_color="gray40",
            width=100
        )
        self.btn_close.grid(row=0, column=3, padx=5)
        
        # Lista de releases
        self.releases_frame = ctk.CTkScrollableFrame(
            self, label_text="Versiones Disponibles"
        )
        self.releases_frame.grid(
            row=1, column=0, sticky="nsew",
            padx=10, pady=10
        )
        
        # Barra de progreso
        self.progress_bar = ctk.CTkProgressBar(self)
        self.progress_bar.grid(
            row=2, column=0, sticky="ew",
            padx=10, pady=(0,10)
        )
        self.progress_bar.set(0)
        
        # Estado de descarga
        self.status_label = ctk.CTkLabel(
            self, text="", height=20
        )
        self.status_label.grid(
            row=3, column=0, sticky="ew",
            padx=10, pady=(0,10)
        )
        
        # Lista de navegación
        self.navigable_widgets = [
            [self.btn_refresh, self.btn_github, self.btn_close]
        ]

    def on_refresh_clicked(self):
        """Refresca la lista de releases disponibles."""
        self.status_label.configure(text="Buscando versiones...")
        self.releases = fetch_github_releases(self.log_func)
        
        # Limpiar lista actual
        for widget in self.releases_frame.winfo_children():
            widget.destroy()
        
        if not self.releases:
            self.status_label.configure(
                text="No se pudo obtener la lista de versiones."
            )
            return
            
        # Añadir releases a la lista
        release_buttons = []
        for release in self.releases:
            # Crear frame para cada release
            release_frame = ctk.CTkFrame(
                self.releases_frame,
                fg_color="transparent"
            )
            release_frame.pack(fill="x", pady=(0,5))
            release_frame.grid_columnconfigure(0, weight=1)
            
            # Botón principal con nombre/versión
            btn = ctk.CTkButton(
                release_frame,
                text=f"{release['name']} ({release['tag_name']})",
                command=lambda r=release: self.on_release_clicked(r)
            )
            btn.grid(row=0, column=0, sticky="ew", padx=(0,5))
            release_buttons.append(btn)
            
            # Etiqueta de fecha
            date_label = ctk.CTkLabel(
                release_frame,
                text=release['published_at'].split('T')[0],
                width=80
            )
            date_label.grid(row=0, column=1)
        
        # Actualizar lista de navegación
        self.navigable_widgets.append(release_buttons)
        self.status_label.configure(
            text=f"Se encontraron {len(self.releases)} versiones."
        )

    def on_release_clicked(self, release):
        """Inicia la descarga de una release.
        
        Args:
            release (dict): Datos de la release a descargar
        """
        # Verificar 7z.exe
        if not check_and_download_7zip(self.log_func, self):
            return
            
        # No permitir múltiples descargas
        if self.current_download and self.current_download.is_alive():
            messagebox.showwarning(
                "Descarga en Progreso",
                "Ya hay una descarga en curso. Espere a que termine.",
                parent=self
            )
            return
            
        # Iniciar descarga en segundo plano
        self.current_download = threading.Thread(
            target=download_mod_release,
            args=(release, self.update_progress, self.log_func),
            daemon=True
        )
        self.current_download.start()

    def update_progress(self, current, total, done, status_text):
        """Actualiza la barra de progreso y estado.
        
        Args:
            current (int): Bytes descargados
            total (int): Tamaño total en bytes
            done (bool): True si la descarga terminó
            status_text (str): Texto de estado a mostrar
        """
        if total > 0:
            progress = current / total
            self.progress_bar.set(progress)
            
        if status_text:
            self.status_label.configure(text=status_text)
            
        if done and self.master:
            self.master.autodetect_mod_source()

    def open_github_releases(self):
        """Abre la página de releases en GitHub."""
        webbrowser.open_new_tab(
            "https://github.com/optiscaler/OptiScaler/releases"
        )

    def on_close(self):
        """Maneja el cierre de la ventana."""
        if self.current_download and self.current_download.is_alive():
            if messagebox.askyesno(
                "Descarga en Progreso",
                "Hay una descarga en curso. ¿Seguro que quiere cerrar?",
                parent=self
            ):
                self.destroy()
        else:
            self.destroy()