"""Shim entrypoint

El original `fsr_injector.py` ha sido archivado en `baks/fsr_injector_original.py`.
Este pequeño shim delega al entrypoint modular en `src.main` para mantener compatibilidad.
"""
import sys

try:
    # Import y delegación al entrypoint modular
    from src.main import main
except Exception as e:
    print("Error al importar el entrypoint modular (src.main):", e)
    raise


def shim_main():
    print("Notice: original monolith moved to baks/fsr_injector_original.py")
    print("Launching modular application (src.main)")
    return main()


if __name__ == "__main__":
    sys.exit(shim_main())
