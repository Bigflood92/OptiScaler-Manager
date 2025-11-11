"""Test para verificar la nueva estructura de directorios."""

from src.config.paths import (
    BASE_DIR,
    APP_DIR,
    MOD_SOURCE_DIR,
    OPTISCALER_DIR,
    DLSSG_TO_FSR3_DIR,
    SEVEN_ZIP_PATH,
    CONFIG_FILE,
    GAMES_CACHE_FILE,
    RELEASES_CACHE_FILE,
    initialize_directories
)

def test_paths():
    print("=== Estructura de directorios ===")
    print(f"BASE_DIR: {BASE_DIR}")
    print(f"APP_DIR: {APP_DIR}")
    print(f"MOD_SOURCE_DIR: {MOD_SOURCE_DIR}")
    print(f"OPTISCALER_DIR: {OPTISCALER_DIR}")
    print(f"DLSSG_TO_FSR3_DIR: {DLSSG_TO_FSR3_DIR}")
    print(f"SEVEN_ZIP_PATH: {SEVEN_ZIP_PATH}")
    print()
    print("=== Archivos de configuración ===")
    print(f"CONFIG_FILE: {CONFIG_FILE}")
    print(f"GAMES_CACHE_FILE: {GAMES_CACHE_FILE}")
    print(f"RELEASES_CACHE_FILE: {RELEASES_CACHE_FILE}")
    print()
    print("=== Inicializando directorios ===")
    initialize_directories()
    print("✓ Directorios creados correctamente")
    
    # Verificar que existen
    import os
    dirs_to_check = [
        APP_DIR,
        MOD_SOURCE_DIR,
        OPTISCALER_DIR,
        DLSSG_TO_FSR3_DIR
    ]
    
    print()
    print("=== Verificando directorios ===")
    for dir_path in dirs_to_check:
        exists = os.path.exists(dir_path)
        status = "✓" if exists else "✗"
        print(f"{status} {dir_path}")

if __name__ == "__main__":
    test_paths()
