"""Componente de navegación para la interfaz gráfica."""

import customtkinter as ctk
try:
    import pygame  # Opcional: solo si hay soporte de mando
except Exception:  # pragma: no cover
    pygame = None

class NavigableMixin:
    """Mixin que agrega funcionalidad de navegación 2D a cualquier ventana."""
    
    def init_navigation(self):
        """Inicializa el sistema de navegación."""
        self.navigable_widgets = []
        self.focused_indices = [0, 0]
        self.focus_color = ("#CCCCCC", "#999999")
        
    def move_focus(self, direction): # 'up', 'down', 'left', 'right'
        """Mueve el foco entre los widgets navegables."""
        if not self.navigable_widgets: return
        
        current_row, current_col = self.focused_indices
        max_row = len(self.navigable_widgets) - 1
        
        if direction == 'down':
            if current_row < max_row:
                current_row += 1
                # Mantener la columna si es posible, sino ir a la última columna disponible
                current_col = min(current_col, len(self.navigable_widgets[current_row]) - 1)
        elif direction == 'up':
            if current_row > 0:
                current_row -= 1
                # Mantener la columna si es posible, sino ir a la última columna disponible
                current_col = min(current_col, len(self.navigable_widgets[current_row]) - 1)
        elif direction == 'left':
            if current_col > 0:
                current_col -= 1
        elif direction == 'right':
            max_col = len(self.navigable_widgets[current_row]) - 1
            if current_col < max_col:
                current_col += 1
                
        self.focused_indices = [current_row, current_col]
        self.update_focus_visuals()

    def update_focus_visuals(self):
        """Actualiza la visualización del foco en los widgets."""
        for r_idx, row in enumerate(self.navigable_widgets):
            for c_idx, widget in enumerate(row):
                is_focused = (r_idx == self.focused_indices[0] and c_idx == self.focused_indices[1])
                try:
                    if is_focused:
                        # Algunos widgets (p.ej. CTkRadioButton) no soportan border_width
                        if isinstance(widget, ctk.CTkRadioButton):
                            widget.configure(border_color=self.focus_color)
                        else:
                            widget.configure(border_color=self.focus_color, border_width=2)
                        # Scroll si el widget está en un frame con scroll
                        if hasattr(widget.master, '_scroll_to_widget'):
                            widget.master._scroll_to_widget(widget)
                    else:
                        if not isinstance(widget, ctk.CTkRadioButton):
                            widget.configure(border_width=0)
                except Exception:
                    # No romper navegación por widgets que no soporten estas props
                    pass
                    
    def activate_focused_widget(self):
        """Activa el widget que tiene el foco actual."""
        try:
            current_row, current_col = self.focused_indices
            widget = self.navigable_widgets[current_row][current_col]
            # Intentar invocar acción del widget de forma robusta
            if isinstance(widget, (ctk.CTkButton, ctk.CTkRadioButton, ctk.CTkSwitch, ctk.CTkCheckBox)):
                invoked = False
                # 1) Si el widget expone .invoke(), úsalo
                invoke_fn = getattr(widget, "invoke", None)
                if callable(invoke_fn):
                    try:
                        invoke_fn()
                        invoked = True
                    except Exception:
                        invoked = False
                if not invoked:
                    # 2) Intentar obtener el comando configurado y llamarlo
                    try:
                        cmd = widget.cget("command") if hasattr(widget, "cget") else None
                        if callable(cmd):
                            cmd()
                            invoked = True
                    except Exception:
                        invoked = False
                if not invoked:
                    # 3) Fallback: enfocarlo para que reciba Enter si aplica
                    widget.focus_set()
            elif isinstance(widget, ctk.CTkSlider):
                widget.focus_set()
        except Exception as e:
            if hasattr(self, 'log_func'):
                self.log_func('ERROR', f"Error al activar widget: {e}")

    def setup_navigation_bindings(self):
        """Configura los bindings de teclado para navegación y clicks a foco."""
        self.bind("<Return>", lambda e: self.activate_focused_widget())
        self.bind("<Up>", lambda e: self.move_focus('up'))
        self.bind("<Down>", lambda e: self.move_focus('down'))
        self.bind("<Left>", lambda e: self._handle_horizontal('left'))
        self.bind("<Right>", lambda e: self._handle_horizontal('right'))
        # Vincular clicks para actualizar foco visual
        self._bind_click_to_navigables()

    def _bind_click_to_navigables(self):
        """Añade binding de click a todos los widgets navegables para actualizar foco."""
        try:
            for r_idx, row in enumerate(self.navigable_widgets):
                for c_idx, widget in enumerate(row):
                    # Botones y toggles: click debe mover el foco a este widget
                    if isinstance(widget, (ctk.CTkButton, ctk.CTkRadioButton, ctk.CTkSwitch, ctk.CTkCheckBox, ctk.CTkSlider)):
                        widget.bind(
                            "<Button-1>",
                            lambda e, ri=r_idx, ci=c_idx: self._set_focus_indices(ri, ci),
                            add="+",
                        )
        except Exception:
            pass

    def _set_focus_indices(self, row_idx, col_idx):
        """Actualiza los índices de foco y refresca visuals."""
        self.focused_indices = [row_idx, col_idx]
        self.update_focus_visuals()

    def _handle_horizontal(self, direction: str):
        """Si el widget enfocado es un slider, ajusta su valor; si no, mueve foco."""
        try:
            current_row, current_col = self.focused_indices
            widget = self.navigable_widgets[current_row][current_col]
            if isinstance(widget, ctk.CTkSlider):
                # Ajuste de paso
                try:
                    # Determinar rango y paso
                    from_ = float(widget.cget("from")) if hasattr(widget, "cget") else 0.0
                    to_ = float(widget.cget("to")) if hasattr(widget, "cget") else 1.0
                    value = float(widget.get())
                    step = (to_ - from_) / 50.0  # 50 pasos por rango
                    if direction == 'left':
                        value = max(from_, value - step)
                    else:
                        value = min(to_, value + step)
                    widget.set(value)
                    widget.focus_set()
                except Exception:
                    pass
            else:
                # Movimiento de foco horizontal normal
                self.move_focus(direction)
        except Exception:
            # En caso de fallo, intenta movimiento normal
            self.move_focus(direction)
        
    def handle_controller_event(self, event):
        """Maneja los eventos del controlador."""
        if pygame is None:
            return
        if event.type == pygame.JOYHATMOTION:
            if event.hat == 0:
                hat_x, hat_y = event.value
                if hat_y == 1: self.move_focus('up')
                elif hat_y == -1: self.move_focus('down')
                elif hat_x == -1: self.move_focus('left')
                elif hat_x == 1: self.move_focus('right')
        elif event.type == pygame.JOYBUTTONDOWN:
            if event.button == 0: # A
                self.activate_focused_widget()