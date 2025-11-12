"""Script de arranque que configura PYTHONPATH y ejecuta main.py"""
import os
import sys
import subprocess

# Añadir el directorio raíz del proyecto al PYTHONPATH
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Importar y ejecutar main
from src.main import main

if __name__ == "__main__":
    sys.exit(main())