# Script de prueba: parchea is_admin() para permitir arrancar la GUI en este entorno de test.
# No modifica archivos fuente permanentes.
import traceback

try:
    import importlib.util
    import os
    import sys

    # Add project root to path
    project_root = os.path.dirname(os.path.abspath(__file__))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    # Import core utils from the src package
    utils = importlib.import_module('src.core.utils')
    _orig_is_admin = getattr(utils, 'is_admin', None)
    utils.is_admin = lambda: True

    main_mod = importlib.import_module('src.main')
    exit_code = main_mod.main()
    print('main() returned', exit_code)

except Exception as e:
    print('Error al ejecutar main con is_admin parcheado:')
    traceback.print_exc()

finally:
    # Restaurar (si fue importado)
    try:
        if 'utils' in locals() and _orig_is_admin is not None:
            utils.is_admin = _orig_is_admin
    except Exception:
        pass
