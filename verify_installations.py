"""
Script para verificar instalaciones de OptiScaler en tus juegos
Detecta juegos y verifica la presencia de carpeta D3D12_Optiscaler
"""
import os
import sys
from pathlib import Path

# Configurar PYTHONPATH
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
os.chdir(project_root)

try:
    # Importar usando la ruta completa desde la raíz
    import importlib.util
    
    # Cargar scanner
    scanner_path = project_root / "src" / "core" / "scanner.py"
    spec = importlib.util.spec_from_file_location("scanner", scanner_path)
    scanner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(scanner)
    
    # Cargar mod_detector
    mod_detector_path = project_root / "src" / "core" / "mod_detector.py"
    spec = importlib.util.spec_from_file_location("mod_detector", mod_detector_path)
    mod_detector = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod_detector)
    
    # Cargar constants
    constants_path = project_root / "src" / "core" / "constants.py"
    spec = importlib.util.spec_from_file_location("constants", constants_path)
    constants = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(constants)
    
    scan_dynamic_games = scanner.scan_dynamic_games
    get_version_badge_info = mod_detector.get_version_badge_info
    OPTISCALER_DIR = constants.OPTISCALER_DIR
    
    print("=" * 100)
    print("VERIFICACION DE INSTALACIONES DE OPTISCALER")
    print("=" * 100)
    
    # Detectar juegos
    print("\nDetectando juegos instalados...")
    
    # Función simple de logging
    def log_func(level, msg):
        pass  # Silenciar logs durante detección
    
    games = scan_dynamic_games(log_func=log_func)
    
    print(f"Se encontraron {len(games)} juegos")
    
    # Filtrar solo juegos con OptiScaler instalado
    print("\nVerificando instalaciones de OptiScaler...")
    print("=" * 100)
    
    installed_count = 0
    
    for game_path, game_name, mod_status, exe_name, platform in games:
        # Solo mostrar juegos con OptiScaler instalado
        if "OptiScaler" in mod_status or "OK" in mod_status:
            installed_count += 1
            
            print(f"\n{'=' * 100}")
            print(f"[JUEGO] {game_name}")
            print(f"{'=' * 100}")
            print(f"[RUTA] {game_path}")
            print(f"[ESTADO] {mod_status}")
            print(f"[PLATAFORMA] {platform}")
            
            # Verificar archivos core
            optiscaler_dll = Path(game_path) / "OptiScaler.dll"
            optiscaler_ini = Path(game_path) / "OptiScaler.ini"
            
            print(f"\n[ARCHIVOS CORE]")
            print(f"   OptiScaler.dll: {'OK Existe' if optiscaler_dll.exists() else 'NO existe'}")
            print(f"   OptiScaler.ini: {'OK Existe' if optiscaler_ini.exists() else 'NO existe'}")
            
            # Verificar carpeta D3D12_Optiscaler
            d3d12_folder = Path(game_path) / "D3D12_Optiscaler"
            print(f"\n[CARPETAS RUNTIME]")
            print(f"   D3D12_Optiscaler/: {'OK Existe' if d3d12_folder.exists() else '*** NO EXISTE ***'}")
            
            if d3d12_folder.exists():
                try:
                    files = list(d3d12_folder.iterdir())
                    print(f"   Contenido ({len(files)} archivos/carpetas):")
                    for item in sorted(files)[:15]:
                        if item.is_file():
                            size = item.stat().st_size
                            print(f"      [FILE] {item.name} ({size:,} bytes)")
                        else:
                            print(f"      [DIR] {item.name}/")
                    if len(files) > 15:
                        print(f"      ... y {len(files) - 15} elementos mas")
                except Exception as e:
                    print(f"   ! Error al listar: {e}")
            else:
                print(f"   ! LA CARPETA D3D12_Optiscaler NO ESTA PRESENTE")
            
            # Verificar otras carpetas
            nvngx_folder = Path(game_path) / "nvngx_dlss"
            dlss_override = Path(game_path) / "DlssOverrides"
            licenses = Path(game_path) / "Licenses"
            
            if nvngx_folder.exists():
                print(f"   nvngx_dlss/: OK Existe")
            if dlss_override.exists():
                print(f"   DlssOverrides/: OK Existe")
            if licenses.exists():
                print(f"   Licenses/: OK Existe")
            
            # Verificar versión
            try:
                badge_info = get_version_badge_info(game_path, OPTISCALER_DIR)
                print(f"\n[VERSION] {badge_info['text']}")
            except Exception as e:
                print(f"\n! Error al detectar version: {e}")
    
    print("\n" + "=" * 100)
    print(f"RESUMEN: {installed_count} juegos con OptiScaler instalado")
    print("=" * 100)
    
    if installed_count == 0:
        print("\n! No se encontraron juegos con OptiScaler instalado")
        print("   Mostrando primeros 5 juegos detectados para referencia:")
        for i, (game_path, game_name, mod_status, exe_name, platform) in enumerate(games[:5]):
            print(f"\n   {i+1}. {game_name}")
            print(f"      Ruta: {game_path}")
            print(f"      Estado: {mod_status}")

except ImportError as e:
    print(f"Error al importar modulos: {e}")
    print("   Asegurate de ejecutar este script desde la raiz del proyecto")
except Exception as e:
    print(f"Error inesperado: {e}")
    import traceback
    traceback.print_exc()
