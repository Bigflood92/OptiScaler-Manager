"""Script de debug para verificar rutas en Nuitka onefile."""
import os
import sys
from pathlib import Path

# Escribir a archivo en lugar de consola
output_file = "debug_paths_output.txt"
with open(output_file, "w", encoding="utf-8") as f:
    f.write("=== DEBUG DE RUTAS ===\n")
    f.write(f"sys.frozen: {hasattr(sys, 'frozen')}\n")
    f.write(f"sys.executable: {sys.executable}\n")
    f.write(f"sys.argv[0]: {sys.argv[0]}\n")
    f.write(f"os.path.abspath(sys.argv[0]): {os.path.abspath(sys.argv[0])}\n")
    f.write(f"__file__: {__file__ if '__file__' in globals() else 'N/A'}\n")

    f.write("\n=== VARIABLES DE ENTORNO NUITKA ===\n")
    for key in os.environ:
        if 'NUITKA' in key.upper():
            f.write(f"{key}: {os.environ[key]}\n")

    f.write("\n=== CÁLCULO DE BASE_DIR ===\n")
    if hasattr(sys, 'frozen'):
        f.write("Detectado: Ejecutable compilado (frozen)\n")
        if 'NUITKA_ONEFILE_PARENT' in os.environ:
            base_dir = Path(os.environ['NUITKA_ONEFILE_PARENT'])
            f.write(f"Usando NUITKA_ONEFILE_PARENT: {base_dir}\n")
        elif hasattr(sys, '_MEIPASS'):
            base_dir = Path(os.path.dirname(sys.executable))
            f.write(f"Usando PyInstaller (_MEIPASS): {base_dir}\n")
        else:
            base_dir = Path(os.path.dirname(sys.executable))
            f.write(f"Usando fallback (sys.executable): {base_dir}\n")
    else:
        f.write("Detectado: Script Python normal\n")
        base_dir = Path(os.path.dirname(__file__))
        f.write(f"Usando __file__: {base_dir}\n")

    f.write(f"\nBASE_DIR final: {base_dir}\n")
    f.write(f"Config Optiscaler Gestor estaría en: {base_dir / 'Config Optiscaler Gestor'}\n")

print(f"Debug info guardado en: {os.path.abspath(output_file)}")
