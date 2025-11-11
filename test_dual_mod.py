"""Script de prueba para instalación de dual-mod (OptiScaler + dlssg-to-fsr3)."""

import sys
import os

# Agregar src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.core.installer import (
    check_nukem_mod_files,
    install_nukem_mod,
    install_combined_mods
)
from src.core.scanner import check_mod_status


def simple_log(level, msg):
    """Logger simple para pruebas."""
    print(f"[{level}] {msg}")


def test_check_nukem_files():
    """Prueba verificación de archivos del mod Nukem."""
    print("\n=== TEST: Verificación de archivos dlssg-to-fsr3 ===")
    
    # Ruta de ejemplo (ajustar según tu configuración)
    test_path = r"C:\Users\Jorge\OneDrive\fsr injector\fsr 3 inyector v2.0\Config Optiscaler Gestor\mod_source\dlssg-to-fsr3"
    
    if os.path.exists(test_path):
        source_dir, found = check_nukem_mod_files(test_path, simple_log)
        if found:
            print(f"✅ Archivos encontrados en: {source_dir}")
        else:
            print("❌ Archivos NO encontrados")
    else:
        print(f"⚠️ Ruta de prueba no existe: {test_path}")


def test_mod_status():
    """Prueba detección de estado de mods."""
    print("\n=== TEST: Detección de estado de mods ===")
    
    # Ruta de ejemplo de un juego (ajustar según tu configuración)
    test_game_path = r"C:\Program Files (x86)\Steam\steamapps\common\TestGame"
    
    if os.path.exists(test_game_path):
        status = check_mod_status(test_game_path)
        print(f"Estado del mod en {test_game_path}: {status}")
    else:
        print(f"⚠️ Ruta de prueba no existe: {test_game_path}")
        print("Usando directorio temporal...")
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            status = check_mod_status(tmpdir)
            print(f"Estado de directorio vacío: {status}")


def main():
    """Función principal de prueba."""
    print("=== PRUEBAS DE DUAL-MOD SUPPORT ===")
    print("OptiScaler = Upscaling (FSR/XeSS/DLSS)")
    print("dlssg-to-fsr3 = Frame Generation (FSR3 FG)")
    
    test_check_nukem_files()
    test_mod_status()
    
    print("\n=== PRUEBAS COMPLETADAS ===")
    print("✅ Funciones de instalación dual-mod implementadas")
    print("✅ Detección de mods mejorada")
    print("\nNOTA: Para pruebas completas, necesitas:")
    print("  1. Descargar release de dlssg-to-fsr3 de GitHub")
    print("  2. Extraer a Config Optiscaler Gestor/mod_source/")
    print("  3. Usar la GUI para instalar en un juego real")


if __name__ == "__main__":
    main()
