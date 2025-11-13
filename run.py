"""
Punto de entrada principal para Gestor OptiScaler
Usado por Nuitka para compilar el ejecutable
"""
import sys
import os

# Asegurar que el directorio actual esté en el path
if __name__ == '__main__':
    # Importar y ejecutar main
    from src.main import main
    main()
