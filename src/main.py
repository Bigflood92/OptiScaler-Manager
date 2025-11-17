"""Punto de entrada principal de la aplicación."""

import os
import sys

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
from src.core.utils import is_admin, run_as_admin
from src.config.paths import initialize_directories


def main():
    """Función principal que inicia la aplicación."""
    # Inicializar estructura de directorios
    initialize_directories()
    
    # SKIP_ADMIN: Variable de entorno para omitir verificación (solo para desarrollo/debug)
    skip_admin_check = os.environ.get('SKIP_ADMIN_CHECK', '0') == '1'
    
    if skip_admin_check:
        print("[DEBUG] SKIP_ADMIN_CHECK activado - omitiendo verificación de permisos")
    else:
        # Verifica permisos de administrador y relanza si falta elevación
        admin_status = is_admin()
        print(f"[DEBUG] is_admin() = {admin_status}")
        
        if not admin_status:
            print("[UAC] No se detectan privilegios de administrador. Intentando elevar...")
            elevated = run_as_admin()
            print(f"[DEBUG] run_as_admin() = {elevated}")
            if elevated:
                print("[UAC] Elevación solicitada. Cerrando proceso actual.")
                return 0  # El nuevo proceso elevado continuará.
            else:
                print("[UAC] Falló la elevación automática. Ejecuta manualmente 'Ejecutar como administrador'.")
                return 1
        
        print("[DEBUG] Continuando con privilegios de administrador...")
    
    # Iniciar aplicación
    try:
        from src.gui.gaming_app import GamingApp
        app = GamingApp()
        app.mainloop()
        return 0
    except Exception as e:
        print(f"Error al iniciar aplicación: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())