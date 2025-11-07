"""Ventana de selección personalizada para opciones."""

import customtkinter as ctk
from ...components.navigation import NavigableMixin

class CustomSelectWindow(ctk.CTkToplevel, NavigableMixin):
    """Ventana modal para selección de opciones."""
    
    def __init__(self, parent, title, options, callback):
        """Inicializa la ventana de selección.
        
        Args:
            parent: Ventana padre
            title (str): Título de la ventana
            options (list): Lista de opciones a mostrar
            callback (callable): Función a llamar con la opción seleccionada
        """
        super().__init__(parent)
        self.init_navigation()
        
        self.title(title)
        self.callback = callback
        self.options = options
        self.selected_value = None
        
        # UI Setup
        self.setup_ui()
        self.setup_navigation_bindings()
        
        # Centra la ventana
        window_width = 400
        window_height = min(600, len(options) * 40 + 100)
        
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (window_width // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (window_height // 2)
        
        self.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # Modal
        self.transient(parent)
        self.grab_set()
        self.focus_force()
        
        # Bindings
        self.bind("<Escape>", lambda e: self.on_cancel())
        self.bind("<Return>", lambda e: self.on_select())
        
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
            
            # Si es el valor actual, marca el foco inicial
            if option == self.selected_value:
                self.focused_indices = [0, len(self.navigable_widgets[0])-1]
        
        # Actualizar el foco visual inicial
        self.after(50, self.update_focus_visuals)

    def on_select(self, value=None):
        """Maneja la selección de una opción."""
        if value is None:
            value = self.options[self.focused_indices[1]]
        self.selected_value = value
        if self.callback:
            self.callback(value)
        self.destroy()

    def on_cancel(self):
        """Cancela la selección."""
        self.selected_value = None
        if self.callback:
            self.callback(None)
        self.destroy()