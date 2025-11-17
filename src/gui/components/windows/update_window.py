"""
Ventana de actualización de la aplicación.
"""

import customtkinter as ctk
from tkinter import messagebox
import threading
import webbrowser


class UpdateWindow(ctk.CTkToplevel):
    """Ventana modal para notificar actualizaciones de la aplicación."""
    
    def __init__(self, parent, current_version: str, latest_version: str, release_info: dict, update_callback):
        """
        Args:
            parent: Ventana padre
            current_version: Versión actual instalada
            latest_version: Última versión disponible
            release_info: Diccionario con información del release
            update_callback: Función a llamar cuando se acepta actualizar
        """
        super().__init__(parent)
        
        self.parent = parent
        self.current_version = current_version
        self.latest_version = latest_version
        self.release_info = release_info
        self.update_callback = update_callback
        self.result = None
        
        # Configuración de ventana
        self.title("🔄 Actualización Disponible")
        self.geometry("600x450")
        self.resizable(False, False)
        
        # Centrar en pantalla
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (600 // 2)
        y = (self.winfo_screenheight() // 2) - (450 // 2)
        self.geometry(f"600x450+{x}+{y}")
        
        # Hacer modal
        self.transient(parent)
        self.grab_set()
        
        self.setup_ui()
        
    def setup_ui(self):
        """Configura la interfaz de usuario."""
        # Frame principal
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Título
        title_label = ctk.CTkLabel(
            main_frame,
            text="🆕 Nueva Versión Disponible",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(pady=(0, 15))
        
        # Frame de versiones
        version_frame = ctk.CTkFrame(main_frame, fg_color="#1a1a1a", corner_radius=10)
        version_frame.pack(fill="x", pady=(0, 15))
        
        # Versión actual
        current_label = ctk.CTkLabel(
            version_frame,
            text=f"Versión Actual: {self.current_version}",
            font=ctk.CTkFont(size=14),
            text_color="#888888"
        )
        current_label.pack(pady=(10, 5))
        
        # Nueva versión
        new_label = ctk.CTkLabel(
            version_frame,
            text=f"Nueva Versión: {self.latest_version}",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#4CAF50"
        )
        new_label.pack(pady=(5, 10))
        
        # Notas del release
        notes_label = ctk.CTkLabel(
            main_frame,
            text="📝 Notas del Release:",
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w"
        )
        notes_label.pack(anchor="w", pady=(10, 5))
        
        # TextBox scrollable con notas (más pequeño)
        notes_text = ctk.CTkTextbox(
            main_frame,
            height=120,
            font=ctk.CTkFont(size=11),
            wrap="word"
        )
        notes_text.pack(fill="both", expand=True, pady=(0, 15))
        
        # Insertar notas del release
        release_body = self.release_info.get("body", "Sin notas de release disponibles.")
        notes_text.insert("1.0", release_body)
        notes_text.configure(state="disabled")
        
        # Frame de botones
        buttons_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        buttons_frame.pack(fill="x")
        
        # Botón de GitHub
        github_btn = ctk.CTkButton(
            buttons_frame,
            text="🔗 Ver en GitHub",
            command=self._open_github,
            width=140,
            height=35,
            fg_color="#2a2a2a",
            hover_color="#3a3a3a",
            font=ctk.CTkFont(size=13)
        )
        github_btn.pack(side="left", padx=(0, 5))
        
        # Botón Cerrar
        close_btn = ctk.CTkButton(
            buttons_frame,
            text="❌ Cerrar",
            command=self._close,
            width=140,
            height=35,
            fg_color="#2a2a2a",
            hover_color="#3a3a3a",
            font=ctk.CTkFont(size=13)
        )
        close_btn.pack(side="left", padx=5)
        
        # Botón Descargar y Actualizar (destacado)
        update_btn = ctk.CTkButton(
            buttons_frame,
            text="⬇️ Descargar y Actualizar",
            command=self._start_update,
            width=200,
            height=35,
            fg_color="#4CAF50",
            hover_color="#45a049",
            font=ctk.CTkFont(size=13, weight="bold")
        )
        update_btn.pack(side="right")
        
    def _open_github(self):
        """Abre la página de releases en GitHub."""
        html_url = self.release_info.get("html_url", "https://github.com/Bigflood92/OptiScaler-Manager/releases")
        webbrowser.open(html_url)
        
    def _close(self):
        """Cierra la ventana sin actualizar."""
        self.result = False
        self.grab_release()
        self.destroy()
        
    def _start_update(self):
        """Inicia el proceso de actualización."""
        self.result = True
        self.grab_release()
        self.destroy()
        
        # Llamar al callback de actualización
        if self.update_callback:
            self.update_callback()
