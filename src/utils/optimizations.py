"""Optimizaciones para el sistema dual-mod.

Basado en los resultados de testing, estas optimizaciones mejoran:
1. Rendimiento de detección de mods
2. Eficiencia de instalación
3. Manejo de errores robusto
"""

import os
from functools import lru_cache
from typing import Tuple, Optional

# ============================================================================
# OPTIMIZACIÓN 1: Cache de detección de archivos de mods
# ============================================================================

@lru_cache(maxsize=128)
def cached_file_exists(filepath: str) -> bool:
    """Cache de os.path.exists para archivos que no cambian frecuentemente.
    
    Args:
        filepath: Ruta absoluta del archivo
        
    Returns:
        bool: True si el archivo existe
    """
    return os.path.exists(filepath)


def invalidate_file_cache():
    """Invalida el cache de existencia de archivos.
    
    Llamar después de instalar/desinstalar mods.
    """
    cached_file_exists.cache_clear()


# ============================================================================
# OPTIMIZACIÓN 2: Detección rápida de estructura de carpetas
# ============================================================================

def find_mod_files_fast(root_dir: str, required_files: list, max_depth: int = 3) -> Optional[str]:
    """Búsqueda optimizada de archivos de mod con límite de profundidad.
    
    Args:
        root_dir: Directorio raíz donde buscar
        required_files: Lista de archivos requeridos
        max_depth: Profundidad máxima de búsqueda
        
    Returns:
        str | None: Ruta del directorio que contiene los archivos, o None
    """
    def walk_limited(directory: str, depth: int = 0):
        """Walk con límite de profundidad."""
        if depth > max_depth:
            return
            
        try:
            for entry in os.scandir(directory):
                if entry.is_dir(follow_symlinks=False):
                    # Verificar en este nivel
                    files_in_dir = {f.name for f in os.scandir(entry.path) if f.is_file()}
                    if all(f in files_in_dir for f in required_files):
                        yield entry.path
                    
                    # Recursión limitada
                    yield from walk_limited(entry.path, depth + 1)
        except (PermissionError, OSError):
            # Ignorar directorios inaccesibles
            pass
    
    # Primero verificar el directorio raíz
    try:
        files_in_root = {f.name for f in os.scandir(root_dir) if f.is_file()}
        if all(f in files_in_root for f in required_files):
            return root_dir
    except (PermissionError, OSError):
        return None
    
    # Buscar en subdirectorios
    for found_dir in walk_limited(root_dir):
        return found_dir  # Retornar el primero encontrado
    
    return None


# ============================================================================
# OPTIMIZACIÓN 3: Instalación batch de archivos
# ============================================================================

def batch_copy_files(file_list: list, source_dir: str, target_dir: str) -> Tuple[int, list]:
    """Copia múltiples archivos en lote con manejo de errores.
    
    Args:
        file_list: Lista de nombres de archivos
        source_dir: Directorio origen
        target_dir: Directorio destino
        
    Returns:
        Tuple[int, list]: (archivos_copiados, errores)
    """
    import shutil
    
    copied = 0
    errors = []
    
    for filename in file_list:
        source_path = os.path.join(source_dir, filename)
        target_path = os.path.join(target_dir, filename)
        
        if not os.path.exists(source_path):
            continue
            
        try:
            shutil.copy2(source_path, target_path)
            copied += 1
        except Exception as e:
            errors.append((filename, str(e)))
    
    return copied, errors


# ============================================================================
# OPTIMIZACIÓN 4: Verificación paralela de múltiples juegos
# ============================================================================

def check_multiple_mods_parallel(game_paths: list) -> dict:
    """Verifica estado de mods en múltiples juegos en paralelo.
    
    Args:
        game_paths: Lista de rutas de juegos
        
    Returns:
        dict: {game_path: status}
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed
    from src.core.scanner import check_mod_status
    
    results = {}
    
    with ThreadPoolExecutor(max_workers=4) as executor:
        future_to_path = {
            executor.submit(check_mod_status, path): path 
            for path in game_paths
        }
        
        for future in as_completed(future_to_path):
            path = future_to_path[future]
            try:
                results[path] = future.result()
            except Exception as e:
                results[path] = f"ERROR: {e}"
    
    return results


# ============================================================================
# OPTIMIZACIÓN 5: Pre-validación de instalación
# ============================================================================

def pre_validate_installation(
    optiscaler_dir: Optional[str],
    nukem_dir: Optional[str],
    target_dir: str,
    install_nukem: bool
) -> Tuple[bool, list]:
    """Pre-valida que la instalación puede proceder sin errores.
    
    Args:
        optiscaler_dir: Directorio de OptiScaler
        nukem_dir: Directorio de dlssg-to-fsr3
        target_dir: Directorio de destino
        install_nukem: Si se instalará dlssg-to-fsr3
        
    Returns:
        Tuple[bool, list]: (puede_proceder, lista_de_errores)
    """
    from src.config.constants import (
        MOD_CHECK_FILES_OPTISCALER,
        NUKEM_REQUIRED_FILES
    )
    
    errors = []
    
    # Verificar OptiScaler
    if not optiscaler_dir or not os.path.isdir(optiscaler_dir):
        errors.append("Directorio de OptiScaler no válido")
    else:
        optiscaler_dll = os.path.join(optiscaler_dir, 'OptiScaler.dll')
        if not os.path.exists(optiscaler_dll):
            errors.append("OptiScaler.dll no encontrado")
    
    # Verificar dlssg-to-fsr3 si se solicita
    if install_nukem:
        if not nukem_dir or not os.path.isdir(nukem_dir):
            errors.append("Directorio de dlssg-to-fsr3 no válido")
        else:
            for req_file in NUKEM_REQUIRED_FILES:
                file_path = os.path.join(nukem_dir, req_file)
                if not os.path.exists(file_path):
                    errors.append(f"Archivo requerido no encontrado: {req_file}")
    
    # Verificar target accesible y escribible
    if not os.path.isdir(target_dir):
        errors.append(f"Directorio de destino no válido: {target_dir}")
    else:
        # Test de escritura
        test_file = os.path.join(target_dir, '.write_test_temp')
        try:
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
        except (PermissionError, OSError) as e:
            errors.append(f"No se puede escribir en destino: {e}")
    
    return len(errors) == 0, errors


# ============================================================================
# OPTIMIZACIÓN 6: Rollback automático en caso de fallo
# ============================================================================

class InstallationTransaction:
    """Gestor de transacciones para instalación con rollback automático."""
    
    def __init__(self, target_dir: str):
        self.target_dir = target_dir
        self.backups = []
        self.created_files = []
        self.success = False
        
    def backup_file(self, filename: str):
        """Crea backup de un archivo existente."""
        source = os.path.join(self.target_dir, filename)
        if os.path.exists(source):
            backup = source + '.transaction_bak'
            import shutil
            shutil.copy2(source, backup)
            self.backups.append((source, backup))
    
    def track_created_file(self, filename: str):
        """Registra archivo creado durante instalación."""
        filepath = os.path.join(self.target_dir, filename)
        self.created_files.append(filepath)
    
    def commit(self):
        """Marca transacción como exitosa."""
        self.success = True
        # Limpiar backups temporales
        for _, backup in self.backups:
            try:
                os.remove(backup)
            except Exception:
                pass
    
    def rollback(self):
        """Revierte todos los cambios."""
        if self.success:
            return
        
        # Eliminar archivos creados
        for filepath in self.created_files:
            try:
                if os.path.exists(filepath):
                    os.remove(filepath)
            except Exception:
                pass
        
        # Restaurar backups
        for original, backup in self.backups:
            try:
                if os.path.exists(backup):
                    import shutil
                    shutil.move(backup, original)
            except Exception:
                pass
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.rollback()
        return False


# ============================================================================
# OPTIMIZACIÓN 7: Logging estructurado para mejor debugging
# ============================================================================

class StructuredLogger:
    """Logger estructurado con niveles y timestamps."""
    
    def __init__(self, log_func):
        self.log_func = log_func
        self.context = {}
    
    def set_context(self, **kwargs):
        """Establece contexto para logs siguientes."""
        self.context.update(kwargs)
    
    def clear_context(self):
        """Limpia contexto."""
        self.context.clear()
    
    def log(self, level: str, message: str, **extra):
        """Log con contexto estructurado."""
        ctx_str = ""
        if self.context or extra:
            all_ctx = {**self.context, **extra}
            ctx_str = f" [{', '.join(f'{k}={v}' for k, v in all_ctx.items())}]"
        
        self.log_func(level, f"{message}{ctx_str}")
    
    def info(self, msg, **extra):
        self.log('INFO', msg, **extra)
    
    def warn(self, msg, **extra):
        self.log('WARN', msg, **extra)
    
    def error(self, msg, **extra):
        self.log('ERROR', msg, **extra)
    
    def ok(self, msg, **extra):
        self.log('OK', msg, **extra)


# ============================================================================
# EJEMPLO DE USO
# ============================================================================

if __name__ == "__main__":
    print("Módulo de optimizaciones cargado")
    print("\nOptimizaciones disponibles:")
    print("  1. cached_file_exists() - Cache de existencia de archivos")
    print("  2. find_mod_files_fast() - Búsqueda rápida con límite de profundidad")
    print("  3. batch_copy_files() - Copia en lote con manejo de errores")
    print("  4. check_multiple_mods_parallel() - Verificación paralela")
    print("  5. pre_validate_installation() - Pre-validación antes de instalar")
    print("  6. InstallationTransaction - Rollback automático")
    print("  7. StructuredLogger - Logging mejorado")
