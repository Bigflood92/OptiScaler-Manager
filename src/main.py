"""Punto de entrada principal de la aplicación.

Modo de ejecución:
 - Por defecto se fuerza la GUI modular (más ligera y rápida).
 - Si estableces la variable de entorno OPTISCALER_USE_LEGACY=1
     se intentará cargar la GUI legacy para compatibilidad.
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
from .core.utils import is_admin, run_as_admin
from .config.paths import initialize_directories
import time


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
    # Inicializar estructura de directorios
    initialize_directories()
    
    # Verifica permisos de administrador y relanza si falta elevación
    if not is_admin():
        print("[UAC] No se detectan privilegios de administrador. Intentando elevar...")
        elevated = run_as_admin()
        if elevated:
            print("[UAC] Elevación solicitada. Cerrando proceso actual.")
            return 0  # El nuevo proceso elevado continuará.
        else:
            print("[UAC] Falló la elevación automática. Ejecuta manualmente 'Ejecutar como administrador'.")
            return 1
    # Perfilado opcional
    profile = os.environ.get("OPTISCALER_PROFILE") == "1"
    t0 = time.perf_counter()

    # GUI Gaming (nueva y simplificada) - POR DEFECTO
    # Para usar legacy: set OPTISCALER_USE_LEGACY=1
    use_legacy = os.environ.get("OPTISCALER_USE_LEGACY") == "1"
    
    if not use_legacy:
        # GUI Gaming Mode (Nueva)
        try:
            from .gui.gaming_app import GamingApp
            if profile:
                t1 = time.perf_counter()
            app = GamingApp()
            if profile:
                t2 = time.perf_counter()
                log_path = os.path.join(project_root, "profile_startup.log")
                with open(log_path, "a", encoding="utf-8") as f:
                    f.write(f"imports: {(t1-t0)*1000:.1f} ms | gaming_app init: {(t2-t1)*1000:.1f} ms\n")
            app.mainloop()
            return 0
        except Exception as e:
            print(f"Error al iniciar Gaming App: {e}")
            import traceback
            traceback.print_exc()
            # Fallback a legacy si falla
            use_legacy = True
    
    if use_legacy:
        # Fallback: GUI Legacy
        try:
            from .gui import legacy_app
            LegacyAppClass = getattr(legacy_app, 'FSRInjectorApp', None)
            if LegacyAppClass is not None:
                app = LegacyAppClass()
                try:
                    app.mainloop()
                except AttributeError:
                    pass
                return 0
        except ImportError as e:
            print(f"Error al cargar legacy: {e}")
            return 2


if __name__ == "__main__":
    sys.exit(main())