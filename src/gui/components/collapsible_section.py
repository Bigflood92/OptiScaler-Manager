import customtkinter as ctk

class CollapsibleSection(ctk.CTkFrame):
    """Sección colapsable reutilizable para agrupar opciones.

    Características:
    - Header con botón que alterna mostrar/ocultar contenido.
    - Indicador visual (▶ / ▼) en el título.
    - Permite añadir cualquier widget dentro de `content_frame`.
    - Estado accesible vía `is_collapsed`.
    - Método `set_collapsed(state: bool)` para control externo.
    """
    def __init__(self, parent, title: str, collapsed: bool = False, *args, **kwargs):
        super().__init__(parent, fg_color="#1a1a1a", corner_radius=8, *args, **kwargs)

        self._raw_title = title
        self.is_collapsed = collapsed

        # Header
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(fill="x", padx=10, pady=(8, 4))

        self.toggle_btn = ctk.CTkButton(
            self.header_frame,
            text=self._compose_title(),
            command=self.toggle,
            fg_color="#2b2b2b",
            hover_color="#3a3a3a",
            corner_radius=6,
            height=32,
            font=ctk.CTkFont(size=15, weight="bold"),
        )
        self.toggle_btn.pack(fill="x")

        # Contenido
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        if not self.is_collapsed:
            self.content_frame.pack(fill="x", expand=False, padx=10, pady=(0, 10))

    def _compose_title(self) -> str:
        prefix = "▶" if self.is_collapsed else "▼"
        # Evitar duplicar indicadores si ya vienen en el título
        base = self._raw_title
        for mark in ("▶", "▼"):
            if base.startswith(mark):
                base = base[1:].strip()
        return f"{prefix} {base}".strip()

    def toggle(self):
        self.set_collapsed(not self.is_collapsed)

    def set_collapsed(self, state: bool):
        if state == self.is_collapsed:
            return
        self.is_collapsed = state
        if self.is_collapsed:
            self.content_frame.pack_forget()
        else:
            self.content_frame.pack(fill="x", expand=False, padx=10, pady=(0, 10))
        self.toggle_btn.configure(text=self._compose_title())

    def add_widget(self, widget, **pack_kwargs):
        """Helper para añadir widgets directamente al contenido.
        Usa pack por simplicidad. El caller puede gestionar layout complejo.
        """
        widget.pack(**pack_kwargs)

__all__ = ["CollapsibleSection"]
