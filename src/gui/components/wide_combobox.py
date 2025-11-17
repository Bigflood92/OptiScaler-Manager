import customtkinter as ctk

class WideComboBox(ctk.CTkFrame):
    """ComboBox personalizado con dropdown que siempre iguala el ancho del propio widget.
    Interfaz mínima compatible con CTkComboBox (get, set, configure, variable, values).
    """
    def __init__(self, master, values, variable: ctk.StringVar, width=300, height=28,
                 font=None, command=None, max_visible_items=8, **kwargs):
        super().__init__(master, width=width, height=height, fg_color="#151515", corner_radius=4, **kwargs)
        self._values = list(values)
        self._variable = variable or ctk.StringVar()
        if variable is None:
            self._variable = ctk.StringVar(value=self._values[0] if self._values else "")
        self._command = command
        self._dropdown = None
        self._scrollable_frame = None
        self._open = False
        self._font = font or ctk.CTkFont(size=13)
        self._option_buttons = []
        self._current_index = 0
        self._max_visible_items = max_visible_items  # Parámetro configurable

        self.grid_propagate(False)
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        # Contenedor interno con borde (focus ring)
        self._content = ctk.CTkFrame(self, fg_color="#151515", corner_radius=4)
        # Pequeño margen para que el borde no se recorte por el contenedor padre
        self._content.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)
        self._content.grid_propagate(False)
        self._content.columnconfigure(0, weight=1)
        self._content.columnconfigure(1, weight=0)

        # Label de texto seleccionado
        self._label = ctk.CTkLabel(self._content, text=self._variable.get(), anchor="w", font=self._font, padx=8)
        self._label.grid(row=0, column=0, sticky="nsew")

        # Botón flecha
        self._arrow_btn = ctk.CTkButton(self._content, text="▾", width=32, fg_color="#222", hover_color="#333",
                                        command=self.open_dropdown, font=self._font)
        self._arrow_btn.grid(row=0, column=1, sticky="ns")

        # Trace variable externa -> actualizar label
        self._variable.trace_add('write', lambda *a: self._label.configure(text=self._variable.get()))

        # Click en la zona de texto también abre
        self._label.bind("<Button-1>", lambda e: self.open_dropdown())

        # Unificar foco: redirigir foco de hijos al frame principal
        self._arrow_btn.bind("<FocusIn>", lambda e: self.focus_set())
        self._label.bind("<FocusIn>", lambda e: self.focus_set())
        # Indicador visual de foco único
        self.bind("<FocusIn>", self._on_focus_in)
        self.bind("<FocusOut>", self._on_focus_out)

    def _on_focus_in(self, e=None):
        try:
            self._content.configure(border_color="#00BFFF", border_width=3)
            # Remover borde de botón interno si lo tuviera
            try:
                self._arrow_btn.configure(border_width=0)
            except Exception:
                pass
        except Exception:
            pass

    def _on_focus_out(self, e=None):
        # Mantener el borde si el dropdown está abierto; evita que otro handler lo borre
        if self._open:
            return "break"
        try:
            self._content.configure(border_width=0)
        except Exception:
            pass

    # --- API mínima ---
    def get(self):
        return self._variable.get()

    def set(self, value):
        if value in self._values:
            self._variable.set(value)
            if self._command:
                try:
                    self._command(value)
                except Exception:
                    pass

    def configure(self, **kwargs):
        """Override seguro sin recursión para permitir borde y otros kwargs.
        Evita llamar self.configure dentro, usa siempre super().configure.
        """
        # Extraer parámetros de borde si presentes y reenviar juntos
        bc = kwargs.get('border_color', None)
        bw = kwargs.get('border_width', None)
        try:
            super().configure(**kwargs)
        except Exception:
            # Intento granular si alguno falla
            for k,v in list(kwargs.items()):
                try:
                    super().configure(**{k:v})
                except Exception:
                    pass
        # Aplicar borde explícito si fue solicitado (CTkFrame soporta border_color/border_width)
        if bc is not None or bw is not None:
            patch = {}
            if bc is not None:
                patch['border_color'] = bc
            if bw is not None:
                patch['border_width'] = bw
            try:
                super().configure(**patch)
            except Exception:
                pass

    # Exponer variable y values como atributos para compatibilidad
    @property
    def variable(self):
        return self._variable

    @property
    def values(self):
        return self._values

    # --- Dropdown management ---
    def open_dropdown(self):
        if self._open:
            self.close_dropdown()
            return
        self._open = True
        # Crear toplevel como menú
        self._dropdown = ctk.CTkToplevel(self)
        self._dropdown.overrideredirect(True)
        self._dropdown.attributes('-topmost', True)
        # Posicionar justo debajo
        self.update_idletasks()
        x = self.winfo_rootx()
        y = self.winfo_rooty() + self.winfo_height()
        w = self.winfo_width()
        
        # Altura máxima del dropdown (mostrar hasta self._max_visible_items opciones, luego scroll)
        item_height = 28
        max_dropdown_height = min(len(self._values) * item_height, self._max_visible_items * item_height)
        
        self._dropdown.geometry(f"{w}x{max_dropdown_height}+{x}+{y}")
        
        # Usar CTkFrame normal si todas las opciones caben, CTkScrollableFrame si no
        needs_scroll = len(self._values) > self._max_visible_items
        
        if needs_scroll:
            self._scrollable_frame = ctk.CTkScrollableFrame(
                self._dropdown, 
                fg_color="#1e1e1e",
                width=w-4,
                height=max_dropdown_height
            )
        else:
            self._scrollable_frame = ctk.CTkFrame(
                self._dropdown, 
                fg_color="#1e1e1e",
                width=w-4,
                height=max_dropdown_height
            )
        self._scrollable_frame.pack(fill="both", expand=True)

        self._option_buttons = []
        # Inicializar índice según valor actual
        if self.get() in self._values:
            self._current_index = self._values.index(self.get())
        else:
            self._current_index = 0
        
        # Ajustar ancho de botones según si hay scroll o no
        button_width = w - 20 if needs_scroll else w - 10
        
        for i, val in enumerate(self._values):
            btn = ctk.CTkButton(
                self._scrollable_frame,
                text=val,
                anchor="w",
                width=button_width,
                fg_color="#262626",
                hover_color="#333",
                font=self._font,
                command=lambda v=val: self._select_value(v)
            )
            # Sin padding lateral para que el borde ocupe todo el ancho visible
            btn.pack(fill="x", padx=0, pady=1)
            self._option_buttons.append(btn)
        self._update_option_focus()
        # Key bindings para navegación teclado
        try:
            self._dropdown.bind("<Up>", lambda e: (self.navigate_options('up'), 'break'))
            self._dropdown.bind("<Down>", lambda e: (self.navigate_options('down'), 'break'))
            self._dropdown.bind("<Return>", lambda e: (self.select_current(), 'break'))
            self._dropdown.bind("<Escape>", lambda e: (self.close_dropdown(), 'break'))
        except Exception:
            pass

        # Cerrar si se hace clic fuera
        self._dropdown.bind("<FocusOut>", lambda e: self.close_dropdown())
        self._dropdown.focus_force()
        # Asegurar borde de foco permanece mientras menú abierto
        self._on_focus_in()

    def _select_value(self, value):
        self.set(value)
        self.close_dropdown()

    # --- Navegación interna ---
    def _update_option_focus(self):
        try:
            for idx, btn in enumerate(self._option_buttons):
                if idx == self._current_index:
                    btn.configure(
                        fg_color="#004e7a",  # fondo de opción activa
                        border_color="#00BFFF",
                        border_width=2
                    )
                else:
                    btn.configure(fg_color="#262626", border_width=0)
            # Autoscroll: asegurar que el botón activo sea visible
            self._scroll_to_current()
        except Exception:
            pass

    def _scroll_to_current(self):
        """Hace scroll automático para mantener la opción actual visible en el CTkScrollableFrame."""
        if not self._option_buttons or not self._dropdown:
            return
        try:
            current_btn = self._option_buttons[self._current_index]
            # Forzar actualización de geometría
            self._scrollable_frame.update_idletasks()
            
            # Obtener la posición Y del botón dentro del scrollable frame
            btn_y = current_btn.winfo_y()
            btn_height = current_btn.winfo_height()
            
            # Obtener el canvas interno del CTkScrollableFrame
            canvas = None
            for child in self._scrollable_frame.winfo_children():
                if isinstance(child, ctk.CTkCanvas) or str(type(child).__name__) == 'Canvas':
                    canvas = child
                    break
            
            if canvas:
                # Calcular la posición relativa del botón en el canvas
                # CTkScrollableFrame usa un canvas interno con scroll
                visible_height = self._scrollable_frame.winfo_height()
                
                # Scroll para centrar el elemento actual
                scroll_position = (btn_y + btn_height / 2 - visible_height / 2) / (len(self._option_buttons) * 28)
                scroll_position = max(0, min(1, scroll_position))
                
                # Aplicar scroll
                canvas.yview_moveto(scroll_position)
        except Exception as e:
            pass

    def navigate_options(self, direction):
        if not self._open or not self._option_buttons:
            return
        if direction == 'up' and self._current_index > 0:
            self._current_index -= 1
        elif direction == 'down' and self._current_index < len(self._option_buttons) - 1:
            self._current_index += 1
        self._update_option_focus()

    def select_current(self):
        if self._open and 0 <= self._current_index < len(self._values):
            self._select_value(self._values[self._current_index])

    def is_open(self):
        return self._open

    def close_dropdown(self):
        if self._dropdown is not None:
            try:
                self._dropdown.destroy()
            except Exception:
                pass
        self._dropdown = None
        self._open = False
        # Recuperar el foco al control y mantener borde
        try:
            self.focus_set()
            self._on_focus_in()
        except Exception:
            pass

    # Para integración con lógica existente que busca _dropdown_menu
    @property
    def _dropdown_menu(self):
        return self._dropdown

    def destroy(self):
        self.close_dropdown()
        super().destroy()
