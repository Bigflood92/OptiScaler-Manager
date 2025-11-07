"""Punto de entrada principal de la aplicación.

Este archivo intentará cargar la GUI original (monolito) desde
`baks/fsr_injector_original.py` si existe. Esto permite mantener la
interfaz EXACTA que tenías antes mientras trabajamos sobre la nueva
estructura modular. Si no se encuentra el backup, se usa la GUI
modular en `src.gui.main_window.MainWindow`.
"""

import os
import sys
import importlib.util

# Ensure the project root directory is in Python path
def setup_path():
    """Add project root directory to Python path."""
    # If running as script (__file__ is main.py)
    if os.path.basename(__file__) == "main.py":
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    # If running as module (__file__ is in src/)
    else:
        project_root = os.path.dirname(os.path.dirname(__file__))
    
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    return project_root

# Setup path before imports
project_root = setup_path()

# Now we can import our modules
from .core.utils import is_admin


def _load_legacy_app(path):
    """Carga dinámicamente el módulo Python desde la ruta `path` y
    devuelve la clase `FSRInjectorApp` si existe, o None.
    """
    if not os.path.exists(path):
        return None
    try:
        spec = importlib.util.spec_from_file_location("fsr_injector_original", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return getattr(module, 'FSRInjectorApp', None)
    except Exception as e:
        print(f"Fallo al cargar GUI legacy desde {path}: {e}")
        return None


def main():
    """Función principal que inicia la aplicación.

    Verifica los permisos de administrador y lanza la GUI. Si el backup
    monolítico está presente, intenta ejecutar exactamente esa GUI
    (Option B) para mantener comportamiento idéntico al original.
    """
    # Verifica permisos de administrador
    if not is_admin():
        print("El programa requiere permisos de administrador.")
        print("Por favor, ejecutar como administrador.")
        return 1

    # Primero intentar importar la versión migrada/expuesta en src.gui.legacy_app
    try:
        from .gui import legacy_app
        LegacyAppClass = getattr(legacy_app, 'FSRInjectorApp', None)
        if LegacyAppClass is not None:
            app = LegacyAppClass()
            # IMPORTANTE: ejecutar el loop de la app; de lo contrario el proceso termina inmediatamente
            try:
                app.mainloop()
            except AttributeError:
                # Por compatibilidad con posibles implementaciones que ya hacen mainloop() en __init__
                pass
            return 0
    except ImportError as e:
        # Falló la importación desde .gui.legacy_app, intentaremos cargar desde el backup
        print(f"Intento de cargar legacy desde .gui.legacy_app falló: {e}")
        # continuar al fallback que carga el baks/ archivo directamente
        pass

    # Intentar cargar GUI legacy directamente desde el backup (antiguo comportamiento)
    backup_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'baks', 'fsr_injector_original.py')
    backup_path = os.path.normpath(os.path.abspath(backup_path))
    LegacyAppClass = _load_legacy_app(backup_path)
    if LegacyAppClass is not None:
        try:
            app = LegacyAppClass()
            app.mainloop()
            return 0
        except Exception as e:
            print(f"Error al ejecutar GUI legacy (backup): {e}")
            # Caeremos al fallback modular

    # Fallback: usar GUI modular si la legacy no está disponible o falla
    try:
        from .gui.main_window import MainWindow
        app = MainWindow()
        app.mainloop()
        return 0
    except Exception as e:
        print(f"Error al iniciar la GUI modular: {e}")
        return 2


if __name__ == "__main__":
    sys.exit(main())