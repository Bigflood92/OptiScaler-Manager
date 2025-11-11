"""Script de testing comprehensivo para dual-mod support.

Pruebas:
1. Imports y dependencias
2. Detección de archivos de mods
3. Detección de estado de mods
4. Funciones de instalación (dry-run)
5. GitHubClient dual-repositorio
"""

import sys
import os
import tempfile
import shutil
from pathlib import Path

# Agregar src al path
sys.path.insert(0, os.path.dirname(__file__))

def simple_log(level, msg):
    """Logger simple para pruebas."""
    print(f"[{level:5s}] {msg}")


class TestRunner:
    """Ejecutor de tests para dual-mod."""
    
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.tests = []
        
    def test(self, name, func):
        """Ejecuta un test y registra resultado."""
        print(f"\n{'='*70}")
        print(f"TEST: {name}")
        print(f"{'='*70}")
        try:
            func()
            print(f"✅ PASS: {name}")
            self.passed += 1
            self.tests.append((name, True, None))
        except Exception as e:
            print(f"❌ FAIL: {name}")
            print(f"   Error: {e}")
            import traceback
            traceback.print_exc()
            self.failed += 1
            self.tests.append((name, False, str(e)))
            
    def summary(self):
        """Muestra resumen de tests."""
        print(f"\n{'='*70}")
        print("RESUMEN DE TESTS")
        print(f"{'='*70}")
        print(f"Total:   {self.passed + self.failed}")
        print(f"Pasados: {self.passed}")
        print(f"Fallados: {self.failed}")
        print(f"Ratio:   {self.passed}/{self.passed + self.failed}")
        
        if self.failed > 0:
            print(f"\n{'='*70}")
            print("TESTS FALLADOS:")
            for name, passed, error in self.tests:
                if not passed:
                    print(f"  ❌ {name}")
                    print(f"     {error}")
                    
        return self.failed == 0


# ============================================================================
# TESTS DE IMPORTS
# ============================================================================

def test_imports():
    """Verifica que todos los módulos se importan correctamente."""
    from src.core.installer import (
        check_nukem_mod_files,
        install_nukem_mod,
        install_combined_mods,
        check_mod_source_files,
        inject_fsr_mod
    )
    
    from src.core.scanner import check_mod_status
    
    from src.core.github import GitHubClient
    
    from src.gui.legacy_adapter import (
        install_combined_mods as legacy_install_combined,
        check_nukem_mod_files as legacy_check_nukem,
        install_nukem_mod as legacy_install_nukem
    )
    
    from src.config.constants import (
        NUKEM_REPO_OWNER,
        NUKEM_REPO_NAME,
        NUKEM_REQUIRED_FILES,
        NUKEM_OPTIONAL_FILES,
        MOD_CHECK_FILES_OPTISCALER,
        MOD_CHECK_FILES_NUKEM
    )
    
    assert NUKEM_REPO_OWNER == "Nukem9"
    assert NUKEM_REPO_NAME == "dlssg-to-fsr3"
    assert len(NUKEM_REQUIRED_FILES) == 2
    assert len(MOD_CHECK_FILES_OPTISCALER) == 2
    assert len(MOD_CHECK_FILES_NUKEM) == 2
    
    print("  ✓ Todos los imports correctos")
    print(f"  ✓ Constantes Nukem configuradas: {NUKEM_REPO_OWNER}/{NUKEM_REPO_NAME}")
    print(f"  ✓ Archivos requeridos: {NUKEM_REQUIRED_FILES}")


# ============================================================================
# TESTS DE DETECCIÓN DE ARCHIVOS
# ============================================================================

def test_check_nukem_files():
    """Verifica detección de archivos de dlssg-to-fsr3."""
    from src.core.installer import check_nukem_mod_files
    from src.config.constants import NUKEM_REQUIRED_FILES
    
    # Crear directorio temporal con archivos simulados
    with tempfile.TemporaryDirectory() as tmpdir:
        # Test 1: Directorio vacío
        source_dir, found = check_nukem_mod_files(tmpdir, simple_log)
        assert not found, "Directorio vacío debería retornar False"
        print("  ✓ Detección correcta de directorio vacío")
        
        # Test 2: Crear archivos requeridos
        for filename in NUKEM_REQUIRED_FILES:
            filepath = os.path.join(tmpdir, filename)
            Path(filepath).touch()
        
        source_dir, found = check_nukem_mod_files(tmpdir, simple_log)
        assert found, "Directorio con archivos requeridos debería retornar True"
        assert source_dir == tmpdir
        print("  ✓ Detección correcta de archivos requeridos")
        
        # Test 3: Estructura anidada
        nested_dir = os.path.join(tmpdir, "release", "dlssg-to-fsr3")
        os.makedirs(nested_dir, exist_ok=True)
        
        for filename in NUKEM_REQUIRED_FILES:
            filepath = os.path.join(nested_dir, filename)
            Path(filepath).touch()
            
        source_dir, found = check_nukem_mod_files(tmpdir, simple_log)
        assert found
        assert source_dir == nested_dir
        print("  ✓ Detección correcta en estructura anidada")


def test_mod_status_detection():
    """Verifica detección de estado de mods instalados."""
    from src.core.scanner import check_mod_status
    from src.config.constants import (
        MOD_CHECK_FILES_OPTISCALER,
        MOD_CHECK_FILES_NUKEM
    )
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Test 1: Sin mods
        status = check_mod_status(tmpdir)
        assert "AUSENTE" in status
        print(f"  ✓ Directorio vacío: {status}")
        
        # Test 2: Solo OptiScaler
        for filename in MOD_CHECK_FILES_OPTISCALER:
            Path(os.path.join(tmpdir, filename)).touch()
        
        status = check_mod_status(tmpdir)
        assert "OptiScaler" in status
        print(f"  ✓ Solo OptiScaler: {status}")
        
        # Test 3: OptiScaler + dlssg-to-fsr3
        for filename in MOD_CHECK_FILES_NUKEM:
            Path(os.path.join(tmpdir, filename)).touch()
        
        status = check_mod_status(tmpdir)
        assert "COMPLETO" in status or ("Upscaling" in status and "FG" in status)
        print(f"  ✓ Dual-mod completo: {status}")
        
        # Test 4: Solo dlssg-to-fsr3 (caso raro)
        for filename in MOD_CHECK_FILES_OPTISCALER:
            os.remove(os.path.join(tmpdir, filename))
        
        status = check_mod_status(tmpdir)
        assert "Frame Generation" in status or "FG" in status
        print(f"  ✓ Solo Frame Generation: {status}")


# ============================================================================
# TESTS DE GITHUB CLIENT
# ============================================================================

def test_github_client_dual_repo():
    """Verifica que GitHubClient funciona con ambos repositorios."""
    from src.core.github import GitHubClient
    
    # Test 1: Cliente OptiScaler (default)
    client_optiscaler = GitHubClient(simple_log, repo_type='optiscaler')
    assert client_optiscaler.repo_type == 'optiscaler'
    assert client_optiscaler.owner == 'cdozdil'
    assert client_optiscaler.repo == 'OptiScaler'
    assert 'optiscaler' in client_optiscaler.cache_dir.lower()
    print("  ✓ Cliente OptiScaler configurado correctamente")
    
    # Test 2: Cliente Nukem
    client_nukem = GitHubClient(simple_log, repo_type='nukem')
    assert client_nukem.repo_type == 'nukem'
    assert client_nukem.owner == 'Nukem9'
    assert client_nukem.repo == 'dlssg-to-fsr3'
    assert 'nukem' in client_nukem.cache_dir.lower()
    print("  ✓ Cliente Nukem configurado correctamente")
    
    # Test 3: Verificar cache separado
    assert client_optiscaler.cache_dir != client_nukem.cache_dir
    print("  ✓ Directorios de cache separados")
    print(f"    OptiScaler: {client_optiscaler.cache_dir}")
    print(f"    Nukem:      {client_nukem.cache_dir}")


# ============================================================================
# TESTS DE INSTALACIÓN (DRY-RUN)
# ============================================================================

def test_install_nukem_mod_dryrun():
    """Verifica instalación de dlssg-to-fsr3 sin modificar sistema."""
    from src.core.installer import install_nukem_mod
    from src.config.constants import NUKEM_REQUIRED_FILES
    
    with tempfile.TemporaryDirectory() as source_dir:
        with tempfile.TemporaryDirectory() as target_dir:
            # Crear archivos fuente simulados
            for filename in NUKEM_REQUIRED_FILES:
                filepath = os.path.join(source_dir, filename)
                with open(filepath, 'w') as f:
                    f.write(f"// Mock {filename}\n")
            
            # Intentar instalación
            result = install_nukem_mod(source_dir, target_dir, simple_log)
            
            assert result, "Instalación debería ser exitosa"
            
            # Verificar archivos copiados
            for filename in NUKEM_REQUIRED_FILES:
                target_file = os.path.join(target_dir, filename)
                assert os.path.exists(target_file), f"Falta archivo: {filename}"
            
            print("  ✓ Instalación simulada exitosa")
            print(f"  ✓ Archivos copiados: {len(NUKEM_REQUIRED_FILES)}")


def test_install_combined_mods_dryrun():
    """Verifica instalación combinada sin modificar sistema."""
    from src.core.installer import install_combined_mods
    from src.config.constants import (
        NUKEM_REQUIRED_FILES,
        MOD_CHECK_FILES_OPTISCALER
    )
    
    with tempfile.TemporaryDirectory() as optiscaler_dir:
        with tempfile.TemporaryDirectory() as nukem_dir:
            with tempfile.TemporaryDirectory() as target_dir:
                # Crear archivos OptiScaler simulados
                for filename in ['OptiScaler.dll', 'OptiScaler.ini']:
                    filepath = os.path.join(optiscaler_dir, filename)
                    with open(filepath, 'w') as f:
                        f.write(f"// Mock {filename}\n")
                
                # Crear archivos Nukem simulados
                for filename in NUKEM_REQUIRED_FILES:
                    filepath = os.path.join(nukem_dir, filename)
                    with open(filepath, 'w') as f:
                        f.write(f"// Mock {filename}\n")
                
                # Instalación combinada
                result = install_combined_mods(
                    optiscaler_dir,
                    nukem_dir,
                    target_dir,
                    simple_log,
                    install_nukem=True
                )
                
                assert result, "Instalación combinada debería ser exitosa"
                
                # Verificar ambos mods instalados
                optiscaler_dll = os.path.join(target_dir, 'dxgi.dll')  # Renombrado
                nukem_dll = os.path.join(target_dir, NUKEM_REQUIRED_FILES[0])
                
                assert os.path.exists(optiscaler_dll), "Falta OptiScaler renombrado"
                assert os.path.exists(nukem_dll), "Falta dlssg-to-fsr3"
                
                print("  ✓ Instalación combinada exitosa")
                print(f"  ✓ OptiScaler: dxgi.dll presente")
                print(f"  ✓ dlssg-to-fsr3: archivos presentes")


# ============================================================================
# TESTS DE RENDIMIENTO Y OPTIMIZACIÓN
# ============================================================================

def test_performance_imports():
    """Mide tiempo de importación de módulos críticos."""
    import time
    
    start = time.perf_counter()
    from src.core import installer, scanner, github
    from src.gui import legacy_adapter
    end = time.perf_counter()
    
    elapsed_ms = (end - start) * 1000
    
    print(f"  ✓ Tiempo de importación: {elapsed_ms:.2f}ms")
    
    if elapsed_ms > 500:
        print(f"  ⚠️ ADVERTENCIA: Importación lenta (>{500}ms)")
    else:
        print(f"  ✓ Rendimiento de importación aceptable")
    
    return elapsed_ms


def test_cache_functionality():
    """Verifica que el sistema de cache funciona."""
    from src.core.github import GitHubClient
    import time
    
    client = GitHubClient(simple_log, repo_type='optiscaler')
    
    # Simular datos de cache
    cache_data = {
        "test": "data",
        "version": "1.0"
    }
    
    # Guardar en cache
    client._cache_response("test_key", cache_data)
    print("  ✓ Datos guardados en cache")
    
    # Leer de cache (sin límite de tiempo)
    cached = client._get_cached_response("test_key", max_age=None)
    assert cached is not None
    assert cached["test"] == "data"
    print("  ✓ Datos recuperados de cache correctamente")
    
    # Limpiar cache
    client.clear_cache()
    cached_after_clear = client._get_cached_response("test_key", max_age=None)
    assert cached_after_clear is None
    print("  ✓ Cache limpiado correctamente")


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Ejecuta todos los tests."""
    print("="*70)
    print("SUITE DE TESTS: Dual-Mod Support")
    print("OptiScaler + dlssg-to-fsr3")
    print("="*70)
    
    runner = TestRunner()
    
    # Tests de imports
    runner.test("Imports y dependencias", test_imports)
    
    # Tests de detección
    runner.test("Detección de archivos Nukem", test_check_nukem_files)
    runner.test("Detección de estado de mods", test_mod_status_detection)
    
    # Tests de GitHub
    runner.test("GitHubClient dual-repositorio", test_github_client_dual_repo)
    runner.test("Sistema de cache", test_cache_functionality)
    
    # Tests de instalación
    runner.test("Instalación dlssg-to-fsr3 (dry-run)", test_install_nukem_mod_dryrun)
    runner.test("Instalación combinada (dry-run)", test_install_combined_mods_dryrun)
    
    # Tests de rendimiento
    runner.test("Rendimiento de importación", test_performance_imports)
    
    # Resumen
    success = runner.summary()
    
    print("\n" + "="*70)
    if success:
        print("✅ TODOS LOS TESTS PASARON")
        print("La implementación dual-mod está lista para producción")
    else:
        print("❌ ALGUNOS TESTS FALLARON")
        print("Revisa los errores arriba antes de continuar")
    print("="*70)
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
