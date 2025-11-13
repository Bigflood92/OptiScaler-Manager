"""
Script para verificar la existencia de la carpeta D3D12_Optiscaler en las rutas de los juegos
"""
import os
from pathlib import Path

# Rutas de ejemplo de juegos donde probablemente instalaste el mod
# Basado en el log, voy a verificar algunas rutas comunes

game_paths = [
    r"C:\Program Files (x86)\Steam\steamapps\common\BlackMythWukong\Engine\Binaries\Win64",
    r"C:\Program Files (x86)\Steam\steamapps\common\Days Gone\BendGame\Binaries\Win64",
    r"C:\Program Files (x86)\Steam\steamapps\common\Lies of P\LiesofP\Binaries\Win64",
    r"C:\XboxGames\Call of Duty\Content",
    r"C:\XboxGames\DOOM- The Dark Ages\Content",
    r"C:\XboxGames\Forza Horizon 5\Content",
    r"C:\XboxGames\Ghostwire- Tokyo\Content\Snowfall\Binaries\WinGDK",
]

print("=" * 80)
print("VERIFICACIÓN DE CARPETAS D3D12_Optiscaler")
print("=" * 80)

for game_path in game_paths:
    game_name = Path(game_path).parts[-3] if len(Path(game_path).parts) >= 3 else Path(game_path).parts[-1]
    
    print(f"\n📂 {game_name}")
    print(f"   Ruta: {game_path}")
    
    if not os.path.exists(game_path):
        print(f"   ⚠️  La ruta del juego NO existe")
        continue
    
    # Verificar archivos core de OptiScaler
    optiscaler_dll = os.path.join(game_path, "OptiScaler.dll")
    optiscaler_ini = os.path.join(game_path, "OptiScaler.ini")
    
    # Verificar carpeta D3D12_Optiscaler
    d3d12_folder = os.path.join(game_path, "D3D12_Optiscaler")
    
    print(f"   OptiScaler.dll: {'✅ Existe' if os.path.exists(optiscaler_dll) else '❌ No existe'}")
    print(f"   OptiScaler.ini: {'✅ Existe' if os.path.exists(optiscaler_ini) else '❌ No existe'}")
    print(f"   D3D12_Optiscaler/: {'✅ Existe' if os.path.exists(d3d12_folder) else '❌ No existe'}")
    
    # Si la carpeta existe, mostrar su contenido
    if os.path.exists(d3d12_folder):
        try:
            files = os.listdir(d3d12_folder)
            print(f"   Archivos en D3D12_Optiscaler ({len(files)}):")
            for f in sorted(files)[:10]:  # Mostrar max 10 archivos
                file_path = os.path.join(d3d12_folder, f)
                size = os.path.getsize(file_path) if os.path.isfile(file_path) else 0
                print(f"      - {f} ({size} bytes)")
            if len(files) > 10:
                print(f"      ... y {len(files) - 10} archivos más")
        except Exception as e:
            print(f"   ⚠️  Error al listar contenido: {e}")
    
    # Verificar otras carpetas relacionadas
    nvngx_folder = os.path.join(game_path, "nvngx_dlss")
    dlss_override_folder = os.path.join(game_path, "DlssOverrides")
    
    if os.path.exists(nvngx_folder):
        print(f"   nvngx_dlss/: ✅ Existe")
    if os.path.exists(dlss_override_folder):
        print(f"   DlssOverrides/: ✅ Existe")

print("\n" + "=" * 80)
print("FIN DE LA VERIFICACIÓN")
print("=" * 80)
