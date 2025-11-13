"""Script de prueba para el auto-updater de OptiScaler.

Simula diferentes escenarios sin modificar instalación real.
"""

import sys
from pathlib import Path

# Añadir src al path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.updater import OptiScalerUpdater
from src.config.paths import OPTISCALER_DIR


def log_test(level, msg):
    """Logger simple para testing."""
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


def test_fetch_latest():
    """Test 1: Verificar que se puede obtener la última release."""
    print("\n" + "="*60)
    print("TEST 1: Fetch Latest Release")
    print("="*60)
    
    updater = OptiScalerUpdater(OPTISCALER_DIR, log_func=log_test)
    release = updater.fetch_latest_release()
    
    if release:
        log_test('OK', f"✅ Release encontrada: {release.version}")
        log_test('INFO', f"  Tag: {release.tag_name}")
        log_test('INFO', f"  Publicada: {release.published_at}")
        log_test('INFO', f"  URL: {release.html_url}")
        log_test('INFO', f"  Download: {release.download_url[:80]}...")
        return release
    else:
        log_test('ERROR', "❌ No se pudo obtener release")
        return None


def test_version_comparison():
    """Test 2: Verificar lógica de comparación de versiones."""
    print("\n" + "="*60)
    print("TEST 2: Version Comparison")
    print("="*60)
    
    updater = OptiScalerUpdater(OPTISCALER_DIR, log_func=log_test)
    
    test_cases = [
        ("0.8.0", "0.7.9", True),   # Newer
        ("0.7.9", "0.7.9", False),  # Same
        ("0.7.9", "0.8.0", False),  # Older
        ("1.0.0", "0.9.9", True),   # Major bump
        ("0.8.1", None, True),      # No current version
    ]
    
    for remote, current, expected in test_cases:
        result = updater.is_newer(remote, current)
        status = "✅" if result == expected else "❌"
        log_test('INFO', f"{status} is_newer('{remote}', '{current}') = {result} (expected {expected})")


def test_current_version():
    """Test 3: Detectar versión actualmente instalada."""
    print("\n" + "="*60)
    print("TEST 3: Current Version Detection")
    print("="*60)
    
    updater = OptiScalerUpdater(OPTISCALER_DIR, log_func=log_test)
    current = updater.get_current_version()
    
    if current:
        log_test('OK', f"✅ Versión instalada detectada: {current}")
    else:
        log_test('WARN', "⚠️ No se detectó versión instalada")
    
    return current


def test_update_check():
    """Test 4: Verificar si hay actualización disponible."""
    print("\n" + "="*60)
    print("TEST 4: Update Check")
    print("="*60)
    
    updater = OptiScalerUpdater(OPTISCALER_DIR, log_func=log_test)
    
    current = updater.get_current_version()
    release = updater.fetch_latest_release()
    
    if not release:
        log_test('ERROR', "❌ No se pudo obtener release remota")
        return
    
    log_test('INFO', f"Versión actual: {current or 'No detectada'}")
    log_test('INFO', f"Versión remota: {release.version}")
    
    needs_update = updater.is_newer(release.version, current)
    
    if needs_update:
        log_test('OK', f"✅ ACTUALIZACIÓN DISPONIBLE: {current or '?'} → {release.version}")
    else:
        log_test('INFO', f"ℹ️ Ya tienes la última versión ({current})")


def test_dry_run_download():
    """Test 5: Simulación de descarga (sin ejecutar)."""
    print("\n" + "="*60)
    print("TEST 5: Dry-Run Download Simulation")
    print("="*60)
    
    updater = OptiScalerUpdater(OPTISCALER_DIR, log_func=log_test)
    release = updater.fetch_latest_release()
    
    if not release or not release.download_url:
        log_test('ERROR', "❌ No hay URL de descarga")
        return
    
    log_test('INFO', f"Se descargaría desde: {release.download_url}")
    log_test('INFO', f"Destino: {OPTISCALER_DIR / f'_download_{release.version}.zip'}")
    log_test('INFO', f"Carpeta final: {OPTISCALER_DIR / f'OptiScaler_{release.version}'}")
    log_test('WARN', "⚠️ Este es un dry-run, no se descargó nada")


def main():
    """Ejecuta todos los tests."""
    print("\n" + "🔧 " + "="*58)
    print("🔧  TESTING AUTO-UPDATER - OptiScaler Manager v2.3.0")
    print("🔧 " + "="*58)
    
    try:
        # Test 1: Fetch release
        release = test_fetch_latest()
        if not release:
            log_test('ERROR', "Abortando: No se pudo obtener release de GitHub")
            return
        
        # Test 2: Version comparison
        test_version_comparison()
        
        # Test 3: Current version
        current = test_current_version()
        
        # Test 4: Update check
        test_update_check()
        
        # Test 5: Dry run
        test_dry_run_download()
        
        # Resumen final
        print("\n" + "="*60)
        print("📊 RESUMEN")
        print("="*60)
        log_test('OK', "✅ Todos los tests básicos completados")
        log_test('INFO', "")
        log_test('INFO', "🚀 Para probar actualización REAL:")
        log_test('INFO', "   1. Ejecuta la app: python -m src.main")
        log_test('INFO', "   2. Ve a Ajustes → Gestión de Mods")
        log_test('INFO', "   3. Click 'Buscar actualización'")
        log_test('INFO', "")
        log_test('WARN', "⚠️ IMPORTANTE: Haz backup antes de actualizar!")
        
    except KeyboardInterrupt:
        log_test('WARN', "\n⚠️ Tests interrumpidos por el usuario")
    except Exception as e:
        log_test('ERROR', f"❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
