"""
Ventana de bienvenida y tutorial para nuevos usuarios.
"""
import customtkinter as ctk
from typing import Callable, Optional
import json
from pathlib import Path


class WelcomeTutorial(ctk.CTkToplevel):
    """Ventana de tutorial/bienvenida para el primer inicio."""
    
    def __init__(self, parent, config_path: Path, on_close: Optional[Callable] = None):
        super().__init__(parent)
        
        self.config_path = config_path
        self.on_close_callback = on_close
        self.current_page = 0
        
        # Configuración de la ventana
        self.title("¡Bienvenido a OptiScaler Manager! 🎮")
        self.geometry("700x500")
        self.resizable(False, False)
        
        # Centrar ventana
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (700 // 2)
        y = (self.winfo_screenheight() // 2) - (500 // 2)
        self.geometry(f"700x500+{x}+{y}")
        
        # Modal
        self.transient(parent)
        self.grab_set()
        self.focus_set()
        
        # Contenido de las páginas del tutorial
        self.pages = [
            {
                "title": "¡Bienvenido! 🎉",
                "content": """OptiScaler Manager v2.1.0

Gestor automatizado para inyectar FSR 3.1/4.0, XeSS y DLSS 
en tus juegos favoritos.

¿Qué hace esta aplicación?
• Detecta automáticamente juegos instalados
• Instala mods de OptiScaler con un clic
• Configura presets de rendimiento optimizados
• Gestiona versiones de OptiScaler desde GitHub

¡Haz clic en "Siguiente" para comenzar el tutorial!
                """,
                "emoji": "🎮"
            },
            {
                "title": "Paso 1: Configurar Carpetas 📁",
                "content": """Antes de empezar, añade tus carpetas de juegos:

1. Ve a la pestaña "Ajustes de la App"
2. En "Carpetas Personalizadas", haz clic en "Añadir Carpeta"
3. Selecciona carpetas donde tengas juegos instalados
   Ejemplo: D:\\Juegos, C:\\Program Files\\Epic Games

4. Haz clic en "🔍 Escanear" para detectar juegos

Nota: La app ya detecta Steam, Epic, Xbox Game Pass y GOG 
automáticamente, pero puedes añadir carpetas personalizadas.
                """,
                "emoji": "📁"
            },
            {
                "title": "Paso 2: Seleccionar Juegos ✅",
                "content": """Instalar mods en tus juegos es muy fácil:

1. En la pestaña "Juegos Detectados", verás todos tus juegos
2. Marca los checkboxes de los juegos donde quieras el mod
3. Usa la función de búsqueda para encontrar juegos rápido
4. Puedes hacer drag-to-scroll en la lista

Consejo: Puedes seleccionar múltiples juegos y aplicar 
la configuración a todos a la vez.
                """,
                "emoji": "✅"
            },
            {
                "title": "Paso 3: Configurar Mod ⚙️",
                "content": """Personaliza el mod según tu hardware:

Presets Rápidos:
• Performance: Máximo FPS (FSR 3.1 + Frame Gen)
• Balanced: Equilibrio calidad/rendimiento
• Quality: Mejor calidad visual (XeSS)

Configuración Manual:
• GPU: AMD/Intel o NVIDIA
• Upscaler: FSR 3.1, FSR 4.0, XeSS, DLSS
• Frame Generation: Activado/Desactivado
• Nitidez: Ajusta con el slider (0.0 - 1.0)

Si no sabes qué elegir, usa el preset "Balanced".
                """,
                "emoji": "⚙️"
            },
            {
                "title": "Paso 4: Aplicar e Instalar 🚀",
                "content": """¡Listo para instalar!

1. Revisa tu configuración en el panel derecho
2. Haz clic en "✅ APLICAR A SELECCIONADOS"
3. La aplicación copiará los archivos necesarios
4. Verás una notificación de éxito

Para desinstalar:
• Marca los juegos
• Haz clic en "❌ ELIMINAR DE SELECCIONADOS"

Nota: Requiere permisos de administrador para copiar 
archivos en carpetas protegidas de juegos.
                """,
                "emoji": "🚀"
            },
            {
                "title": "Panel de Ayuda 💡",
                "content": """¿Necesitas ayuda? Usa el panel de ayuda integrado:

• Haz clic en el botón "❓" en la parte superior
• Verás todos los controles disponibles
• Soporte para teclado y gamepad
• Atajos útiles para navegación rápida

Controles útiles:
• Ctrl + F: Buscar juegos
• Ctrl + A: Seleccionar todos
• Gamepad: Navega con D-Pad y botones

¡Ya estás listo para empezar! 🎉
                """,
                "emoji": "💡"
            }
        ]
        
        self.setup_ui()
        
    def setup_ui(self):
        """Configura la interfaz de usuario."""
        # Frame principal
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Header con emoji
        self.emoji_label = ctk.CTkLabel(
            main_frame,
            text=self.pages[0]["emoji"],
            font=("Segoe UI Emoji", 60)
        )
        self.emoji_label.pack(pady=(0, 10))
        
        # Título
        self.title_label = ctk.CTkLabel(
            main_frame,
            text=self.pages[0]["title"],
            font=("Segoe UI", 24, "bold")
        )
        self.title_label.pack(pady=(0, 20))
        
        # Frame de contenido con scroll
        content_frame = ctk.CTkFrame(main_frame)
        content_frame.pack(fill="both", expand=True, pady=(0, 20))
        
        self.content_text = ctk.CTkTextbox(
            content_frame,
            font=("Segoe UI", 13),
            wrap="word",
            activate_scrollbars=True
        )
        self.content_text.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Indicador de página
        self.page_indicator = ctk.CTkLabel(
            main_frame,
            text=f"Página 1 de {len(self.pages)}",
            font=("Segoe UI", 11),
            text_color="gray"
        )
        self.page_indicator.pack(pady=(0, 10))
        
        # Frame de botones
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=(0, 10))
        
        # Checkbox "No volver a mostrar"
        self.dont_show_var = ctk.BooleanVar(value=False)
        self.dont_show_check = ctk.CTkCheckBox(
            button_frame,
            text="No volver a mostrar en el inicio",
            variable=self.dont_show_var,
            font=("Segoe UI", 12)
        )
        self.dont_show_check.pack(side="left")
        
        # Botones de navegación
        btn_container = ctk.CTkFrame(button_frame, fg_color="transparent")
        btn_container.pack(side="right")
        
        self.prev_btn = ctk.CTkButton(
            btn_container,
            text="← Anterior",
            command=self.previous_page,
            width=100,
            state="disabled"
        )
        self.prev_btn.pack(side="left", padx=5)
        
        self.next_btn = ctk.CTkButton(
            btn_container,
            text="Siguiente →",
            command=self.next_page,
            width=100
        )
        self.next_btn.pack(side="left", padx=5)
        
        self.close_btn = ctk.CTkButton(
            btn_container,
            text="Cerrar",
            command=self.close_tutorial,
            width=100,
            fg_color="gray",
            hover_color="darkgray"
        )
        self.close_btn.pack(side="left", padx=5)
        
        # Cargar primera página
        self.load_page(0)
        
    def load_page(self, page_index: int):
        """Carga una página específica del tutorial."""
        if 0 <= page_index < len(self.pages):
            page = self.pages[page_index]
            
            # Actualizar emoji y título
            self.emoji_label.configure(text=page["emoji"])
            self.title_label.configure(text=page["title"])
            
            # Actualizar contenido
            self.content_text.delete("1.0", "end")
            self.content_text.insert("1.0", page["content"].strip())
            
            # Actualizar indicador de página
            self.page_indicator.configure(text=f"Página {page_index + 1} de {len(self.pages)}")
            
            # Actualizar estado de botones
            self.prev_btn.configure(state="normal" if page_index > 0 else "disabled")
            self.next_btn.configure(
                text="Finalizar ✓" if page_index == len(self.pages) - 1 else "Siguiente →"
            )
            
            self.current_page = page_index
            
    def next_page(self):
        """Ir a la siguiente página."""
        if self.current_page < len(self.pages) - 1:
            self.load_page(self.current_page + 1)
        else:
            self.close_tutorial()
            
    def previous_page(self):
        """Ir a la página anterior."""
        if self.current_page > 0:
            self.load_page(self.current_page - 1)
            
    def close_tutorial(self):
        """Cerrar el tutorial y guardar preferencias."""
        if self.dont_show_var.get():
            self.save_preference()
        
        if self.on_close_callback:
            self.on_close_callback()
        
        self.grab_release()
        self.destroy()
        
    def save_preference(self):
        """Guarda la preferencia de no mostrar el tutorial."""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            else:
                config = {}
            
            config['show_welcome_tutorial'] = False
            
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"Error guardando preferencia de tutorial: {e}")


def should_show_tutorial(config_path: Path) -> bool:
    """Verifica si se debe mostrar el tutorial."""
    try:
        if not config_path.exists():
            return True
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        return config.get('show_welcome_tutorial', True)
    except:
        return True
