"""Actualización REAL del auto-updater con confirmación interactiva.

ADVERTENCIA: Este script descarga y actualiza OptiScaler.
Se recomienda hacer backup manual antes de ejecutar.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.core.updater import OptiScalerUpdater
from src.config.paths import OPTISCALER_DIR


def log_colored(level, msg):
    """Logger con colores."""
    colors = {
        'INFO': '\033[94m',
        'OK': '\033[92m',
        'WARN': '\033[93m',
        'ERROR': '\033[91m',
        'TITLE': '\033[95m'
    }
    reset = '\033[0m'
    color = colors.get(level, '')
    print(f"{color}[{level}] {msg}{reset}")


def progress_callback(stage: str, percent: float):
    """Callback para mostrar progreso."""
    bar_len = 40
    filled = int(bar_len * percent)
    bar = '█' * filled + '░' * (bar_len - filled)
    pct_text = int(percent * 100)
    print(f"\r{stage}: [{bar}] {pct_text}%", end='', flush=True)
    if percent >= 1.0:
        print()  # Nueva línea al completar


def main():
    """Ejecuta actualización REAL con confirmaciones."""
    print("\n" + "🚀 " + "="*58)
    print("🚀  AUTO-UPDATER REAL - OptiScaler Manager")
    print("🚀 " + "="*58 + "\n")
    
    updater = OptiScalerUpdater(OPTISCALER_DIR, log_func=log_colored)
    
    # Paso 1: Verificar versión actual
    log_colored('INFO', "Detectando versión instalada...")
    current = updater.get_current_version()
    log_colored('OK', f"Versión actual: {current or 'No detectada'}\n")
    
    # Paso 2: Consultar GitHub
    log_colored('INFO', "Consultando GitHub Releases API...")
    release = updater.fetch_latest_release()
    
    if not release:
        log_colored('ERROR', "❌ No se pudo obtener información de releases")
        return
    
    log_colored('OK', f"✅ Última versión disponible: {release.version}")
    log_colored('INFO', f"Publicada: {release.published_at}")
    log_colored('INFO', f"Changelog: {release.html_url}\n")
    
    # Paso 3: Comparar versiones
    if not updater.is_newer(release.version, current):
        log_colored('INFO', f"ℹ️ Ya tienes la última versión ({current})")
        log_colored('INFO', "No hay nada que actualizar.\n")
        return
    
    # Paso 4: Confirmar actualización
    log_colored('WARN', "⚠️ ADVERTENCIA: Esto descargará y actualizará OptiScaler")
    log_colored('WARN', f"⚠️ De {current or '?'} → {release.version}")
    log_colored('WARN', "⚠️ Los archivos antiguos se preservarán en carpetas separadas\n")
    
    respuesta = input("¿Deseas continuar con la actualización? (si/no): ").strip().lower()
    
    if respuesta not in ['si', 's', 'sí', 'yes', 'y']:
        log_colored('INFO', "❌ Actualización cancelada por el usuario\n")
        return
    
    # Paso 5: Descargar y actualizar
    print()
    log_colored('TITLE', "🔄 Iniciando actualización...")
    
    try:
        success = updater.install_release(release, progress=progress_callback)
        
        if success:
            log_colored('OK', "\n✅ ¡Actualización completada con éxito!")
            log_colored('INFO', f"OptiScaler {release.version} está listo para usar")
            log_colored('INFO', f"Ubicación: {OPTISCALER_DIR / f'OptiScaler_{release.version}'}")
            
            # Opción para actualizar juegos instalados
            print()
            respuesta_games = input("¿Actualizar juegos ya instalados? (si/no): ").strip().lower()
            
            if respuesta_games in ['si', 's', 'sí', 'yes', 'y']:
                log_colored('WARN', "⚠️ Esta función requiere ejecutar desde la app principal")
                log_colored('INFO', "Usa: python -m src.main → Ajustes → Buscar actualización")
            else:
                log_colored('INFO', "Puedes actualizar juegos manualmente desde la app")
        else:
            log_colored('ERROR', "❌ Falló la actualización (ver logs arriba)")
            
    except KeyboardInterrupt:
        log_colored('WARN', "\n⚠️ Actualización interrumpida por el usuario")
    except Exception as e:
        log_colored('ERROR', f"\n❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
    
    print()


if __name__ == "__main__":
    main()
