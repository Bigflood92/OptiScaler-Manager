"""
Ejemplo de uso del IconManager
================================

Este archivo muestra cómo usar el sistema de gestión de iconos en la aplicación.
"""

# 1. IMPORTAR EL GESTOR
from src.gui.icon_manager import get_icon_manager

# 2. INICIALIZAR (solo una vez, generalmente en __init__ de la clase principal)
icons = get_icon_manager(use_custom_icons=False)  # False = usa emojis
# icons = get_icon_manager(use_custom_icons=True)  # True = usa PNG si existen

# 3. USO EN BOTONES

# Ejemplo A: Botón con emoji (método actual)
btn_help = ctk.CTkButton(
    parent_frame, 
    text=icons.get_icon("help", size="large"),  # Obtiene "?"
    command=some_function,
    width=50, 
    height=50,
    font=ctk.CTkFont(size=icons.get_emoji_size("large"))  # 28px
)

# Ejemplo B: Botón con emoji + texto
download_icon = icons.get_icon("download", size="medium")  # Obtiene "⬇️"
btn_download = ctk.CTkButton(
    parent_frame,
    text=f"{download_icon} Descargar Mod",  # "⬇️ Descargar Mod"
    command=download_function,
    font=ctk.CTkFont(size=13, weight="bold")
)

# Ejemplo C: Botón con imagen personalizada (cuando PNG existen)
# Este código funciona automáticamente cuando:
# - use_custom_icons=True
# - Existe el archivo icons/launch.png
launch_icon = icons.get_icon("game_launch", size="large", as_image=True)
btn_launch = ctk.CTkButton(
    parent_frame,
    text="",  # Vacío cuando se usa imagen
    image=launch_icon if isinstance(launch_icon, ctk.CTkImage) else None,
    # Si no hay imagen, usa emoji como fallback:
    text=launch_icon if not isinstance(launch_icon, ctk.CTkImage) else "",
    command=launch_function,
    width=50,
    height=50
)

# 4. INDICADORES DE ESTADO CON COLORES

# Obtener color según estado
status_color = icons.get_status_color("ok")      # "#00FF00" (verde)
status_color = icons.get_status_color("error")   # "#FF0000" (rojo)
status_color = icons.get_status_color("none")    # "gray"

status_label = ctk.CTkLabel(
    parent_frame,
    text=icons.get_icon("status_ok"),  # "●"
    text_color=icons.get_status_color("ok"),
    font=ctk.CTkFont(size=24)
)

# 5. TAMAÑOS DE EMOJIS DISPONIBLES

small_size = icons.get_emoji_size("small")    # 20px
medium_size = icons.get_emoji_size("medium")  # 24px
large_size = icons.get_emoji_size("large")    # 28px
xlarge_size = icons.get_emoji_size("xlarge")  # 32px

# 6. LISTA COMPLETA DE ICONOS DISPONIBLES

"""
Interfaz General:
- "help" → ?
- "gaming_mode" → 🎮
- "download" → ⬇️
- "folder_open" → 📂
- "folder_file" → 📁

Modo Gaming - Navegación:
- "nav_config" → ⚙️
- "nav_auto" → 🎯
- "nav_manual" → 📁
- "nav_settings" → 🔧

Modo Gaming - Acciones:
- "game_config" → ⚙️
- "game_folder" → 📁
- "game_launch" → 🚀
- "apply_mod" → ✔️
- "exit_gaming" → ←

Otros:
- "add" → ➕
- "rescan" → 🔄
- "status_ok" → ●
- "status_error" → ●
- "status_none" → ●
"""

# 7. ACTIVAR/DESACTIVAR ICONOS PERSONALIZADOS EN RUNTIME

# Activar iconos PNG (requiere PIL/Pillow)
icons.enable_custom_icons()

# Volver a emojis
icons.disable_custom_icons()

# 8. AJUSTAR TAMAÑO DE UN ICONO ESPECÍFICO

# Redimensionar el icono "game_launch" a 64x64
icons.set_icon_size("game_launch", 64, 64)

# 9. EJEMPLO COMPLETO: BOTÓN CON FALLBACK AUTOMÁTICO

def create_smart_button(parent, icon_name, text="", **kwargs):
    """
    Crea un botón que usa PNG si existe, si no, emoji.
    """
    icon = icons.get_icon(icon_name, size="large", as_image=True)
    
    # Si es CTkImage, es una imagen PNG
    if isinstance(icon, ctk.CTkImage):
        return ctk.CTkButton(
            parent,
            image=icon,
            text=text,
            compound="left",  # Imagen a la izquierda del texto
            **kwargs
        )
    else:
        # Es un emoji string
        full_text = f"{icon} {text}" if text else icon
        return ctk.CTkButton(
            parent,
            text=full_text,
            font=ctk.CTkFont(size=icons.get_emoji_size("large")),
            **kwargs
        )

# Uso:
btn = create_smart_button(
    parent_frame,
    icon_name="game_launch",
    text="Lanzar",
    command=launch_game,
    width=100,
    height=40
)
