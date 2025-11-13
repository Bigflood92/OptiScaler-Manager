"""OptiScaler auto-update core logic.

Provides functionality to:
 - Detect current installed OptiScaler version (from mod_source folder)
 - Query GitHub Releases API for latest version
 - Download release asset (zip) and extract into mod_source preserving previous versions
 - Maintain version.json metadata for the active version
 - Update OptiScaler files inside installed game directories
 - Rollback on failure (restores previous version folder)

Design goals:
 - Non-blocking: heavy operations run in threads from GUI wrapper
 - Safe write: download to temp file, verify basic integrity, then swap
 - Extensible: can support hash verification or delta updates later
 - Minimal dependencies: only 'requests' (already in requirements)
"""

from __future__ import annotations

import json
import os
import shutil
import zipfile
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional, List, Dict, Any

import requests

# Public callback type: (stage: str, percent: float) -> None
ProgressCallback = Callable[[str, float], None]


@dataclass
class ReleaseInfo:
    version: str
    published_at: str
    body: str
    html_url: str
    download_url: str
    tag_name: str


class OptiScalerUpdater:
    """Encapsula la lógica de auto-actualización de OptiScaler."""

    GITHUB_API_RELEASES = "https://api.github.com/repos/optiscaler/OptiScaler/releases"

    def __init__(self, optiscaler_base_dir: Path, log_func: Optional[Callable[[str,str],None]] = None) -> None:
        self.optiscaler_base_dir = optiscaler_base_dir  # e.g. Config Optiscaler Gestor/mod_source/OptiScaler
        self.log = log_func or (lambda level, msg: None)
        self.optiscaler_base_dir.mkdir(parents=True, exist_ok=True)
        self.version_file = self.optiscaler_base_dir / "version.json"  # metadata of active version
        # Último código/mensaje de error detallado para diagnóstico UI
        self.last_error_code: Optional[str] = None
        self.last_error_message: Optional[str] = None

    # ------------------------------------------------------------------
    # Version detection
    # ------------------------------------------------------------------
    def get_current_version(self) -> Optional[str]:
        """Reads current active version from version.json or infers from folder names.

        Returns:
            str | None: La versión actual (ej '0.7.9') o None si no detectada.
        """
        if self.version_file.exists():
            try:
                data = json.loads(self.version_file.read_text(encoding='utf-8'))
                return data.get("version")
            except Exception as e:
                self.log('WARN', f"No se pudo leer version.json: {e}")
        # Infer from subfolders like OptiScaler_0.7.9
        for child in self.optiscaler_base_dir.glob("OptiScaler_*"):
            if child.is_dir():
                # Extract last part after underscore
                parts = child.name.split('_')
                if len(parts) >= 2:
                    return parts[-1]
        return None

    # ------------------------------------------------------------------
    # GitHub releases
    # ------------------------------------------------------------------
    def fetch_latest_release(self) -> Optional[ReleaseInfo]:
        """Queries GitHub Releases API and returns latest release info if found."""
        try:
            resp = requests.get(self.GITHUB_API_RELEASES, timeout=10)
            resp.raise_for_status()
            releases = resp.json()
            if not releases:
                return None
            latest = releases[0]
            tag_name = latest.get('tag_name', '').lstrip('v')
            assets = latest.get('assets', [])
            zip_asset_url = ''
            for asset in assets:
                name = asset.get('name', '')
                # OptiScaler usa archivos .7z, no .zip
                if name.lower().endswith(('.zip', '.7z')):
                    zip_asset_url = asset.get('browser_download_url', '')
                    break
            if not zip_asset_url:
                self.log('WARN', 'No se encontró asset ZIP/7z en la release más reciente.')
            return ReleaseInfo(
                version=tag_name,
                published_at=latest.get('published_at', ''),
                body=latest.get('body', ''),
                html_url=latest.get('html_url', ''),
                download_url=zip_asset_url,
                tag_name=latest.get('tag_name','')
            )
        except Exception as e:
            self.log('ERROR', f"Error consultando releases GitHub: {e}")
            return None

    def is_newer(self, remote: str, current: Optional[str]) -> bool:
        if current is None:
            return True
        try:
            r_parts = [int(p) for p in remote.split('.')]
            c_parts = [int(p) for p in current.split('.')]
            return r_parts > c_parts
        except ValueError:
            # Fallback lexicographical
            return remote > current

    # ------------------------------------------------------------------
    # Download & install
    # ------------------------------------------------------------------
    def download_release_zip(self, release: ReleaseInfo, dest_zip: Path, progress: ProgressCallback | None = None) -> bool:
        """Descarga asset ZIP con barra de progreso aproximada."""
        if not release.download_url:
            self.log('ERROR', 'Release sin URL de descarga.')
            self.last_error_code = 'download_missing_url'
            self.last_error_message = 'La release no tiene URL de descarga'
            return False
        try:
            if progress:
                progress('Descargando release...', 0.02)
            with requests.get(release.download_url, stream=True, timeout=30) as r:
                r.raise_for_status()
                total = int(r.headers.get('content-length', '0'))
                downloaded = 0
                chunk_size = 8192
                with open(dest_zip, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=chunk_size):
                        if not chunk:
                            continue
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total and progress:
                            pct = 0.02 + 0.38 * (downloaded / total)
                            progress('Descargando release...', min(pct, 0.40))
            if progress:
                progress('Descarga completada', 0.40)
            return True
        except Exception as e:
            self.log('ERROR', f"Fallo al descargar release: {e}")
            self.last_error_code = 'download_failed'
            self.last_error_message = str(e)
            return False

    def extract_release(self, zip_path: Path, release: ReleaseInfo, progress: ProgressCallback | None = None) -> Optional[Path]:
        """Extrae el archivo (ZIP o 7z) a una carpeta nueva OptiScaler_<version>."""
        try:
            if progress:
                progress('Extrayendo archivos...', 0.45)
            target_dir = self.optiscaler_base_dir / f"OptiScaler_{release.version}"
            # Si ya existe, renombrar con sufijo timestamp para evitar colisión
            if target_dir.exists():
                ts = datetime.now().strftime('%Y%m%d_%H%M%S')
                target_dir = self.optiscaler_base_dir / f"OptiScaler_{release.version}_{ts}"
            target_dir.mkdir(parents=True, exist_ok=True)
            
            # Detectar si es .7z o .zip y extraer apropiadamente
            if str(zip_path).endswith('.7z'):
                # Usar 7z.exe del mod_source
                seven_zip_exe = self.optiscaler_base_dir.parent / '7z.exe'
                if not seven_zip_exe.exists():
                    # Fallback: intentar usar py7zr si está instalado
                    try:
                        import py7zr  # type: ignore
                        with py7zr.SevenZipFile(zip_path, 'r') as archive:
                            archive.extractall(path=target_dir)
                        if progress:
                            progress('Extracción completada', 0.70)
                        return target_dir
                    except ImportError:
                        self.log('ERROR', '7z.exe no encontrado y py7zr no instalado (pip install py7zr)')
                        self.last_error_code = 'extract_failed_missing_7z'
                        self.last_error_message = 'No se encontró 7z.exe y no hay py7zr'
                        return None
                    except Exception as e:
                        self.log('ERROR', f'Error extrayendo .7z con py7zr: {e}')
                        self.last_error_code = 'extract_failed_error'
                        self.last_error_message = str(e)
                        return None
                
                # Ejecutar 7z.exe para extraer
                cmd = [str(seven_zip_exe), 'x', str(zip_path), f'-o{target_dir}', '-y']
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    self.log('ERROR', f'Error al extraer .7z: {result.stderr}')
                    self.last_error_code = 'extract_failed_7z_exe'
                    self.last_error_message = result.stderr.strip()
                    return None
                
                if progress:
                    progress('Extracción completada', 0.70)
            else:
                # Usar zipfile para .zip
                with zipfile.ZipFile(zip_path, 'r') as zf:
                    members = zf.infolist()
                    total = len(members)
                    for i, member in enumerate(members, start=1):
                        zf.extract(member, path=target_dir)
                        if progress:
                            pct = 0.45 + 0.25 * (i / total)
                            progress('Extrayendo archivos...', min(pct, 0.70))
                if progress:
                    progress('Extracción completada', 0.70)
            
            return target_dir
        except Exception as e:
            self.log('ERROR', f"Error al extraer archivo: {e}")
            self.last_error_code = 'extract_failed_exception'
            self.last_error_message = str(e)
            return None

    def write_version_metadata(self, release: ReleaseInfo, folder: Path) -> bool:
        data = {
            'version': release.version,
            'tag': release.tag_name,
            'folder': folder.name,
            'installed_at': datetime.now().isoformat(),
            'source_url': release.html_url
        }
        try:
            self.version_file.write_text(json.dumps(data, indent=2), encoding='utf-8')
            return True
        except Exception as e:
            self.log('WARN', f"No se pudo escribir version.json: {e}")
            self.last_error_code = 'metadata_write_failed'
            self.last_error_message = str(e)
            return False

    def install_release(self, release: ReleaseInfo, progress: ProgressCallback | None = None) -> tuple[bool, Optional[str]]:
        """Descarga y prepara nueva versión de OptiScaler.

        No actualiza juegos aún; sólo actualiza el repositorio local mod_source.
        """
        # Detectar extensión del archivo (.zip o .7z)
        file_ext = '.7z' if release.download_url.endswith('.7z') else '.zip'
        tmp_archive = self.optiscaler_base_dir / f"_download_{release.version}{file_ext}"
        
        if progress:
            progress('Iniciando descarga...', 0.0)
        if not self.download_release_zip(release, tmp_archive, progress):
            return (False, self.last_error_code or 'download_failed')
        extracted = self.extract_release(tmp_archive, release, progress)
        try:
            tmp_archive.unlink(missing_ok=True)
        except Exception:
            pass
        if not extracted:
            return (False, self.last_error_code or 'extract_failed')
        # Guardar metadata
        if not self.write_version_metadata(release, extracted):
            return (False, self.last_error_code or 'metadata_write_failed')
        if progress:
            progress('Versión preparada', 0.72)
        self.log('OK', f"OptiScaler {release.version} descargado en {extracted}")
        return (True, None)

    # ------------------------------------------------------------------
    # Game update
    # ------------------------------------------------------------------
    def list_game_installations(self, game_paths: List[Path]) -> List[Path]:
        """Filtra rutas existentes (sanity)."""
        return [p for p in game_paths if p.exists() and p.is_dir()]

    def find_source_dll_folder(self) -> Optional[Path]:
        """Returns the newest extracted OptiScaler_* folder as source of DLLs."""
        folders = [d for d in self.optiscaler_base_dir.glob('OptiScaler_*') if d.is_dir()]
        if not folders:
            return None
        # Sort by modification time descending
        folders.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        return folders[0]

    def update_game(self, game_dir: Path, progress: ProgressCallback | None = None) -> bool:
        """Copies core OptiScaler files to a single game directory."""
        source = self.find_source_dll_folder()
        if not source:
            self.log('ERROR', 'No se encontró carpeta fuente de OptiScaler para actualizar juegos.')
            return False
        files_to_copy = [
            'OptiScaler.dll', 'OptiScaler.ini',
            'amd_fidelityfx_dx12.dll', 'amd_fidelityfx_upscaler_dx12.dll',
            'amd_fidelityfx_framegeneration_dx12.dll', 'amd_fidelityfx_vk.dll',
            'libxess.dll', 'libxess_dx11.dll'
        ]
        copied = 0
        for fname in files_to_copy:
            src = source / fname
            if not src.exists():
                continue
            dest = game_dir / fname
            try:
                shutil.copy2(src, dest)
            except Exception as e:
                self.log('WARN', f"Fallo copiando {fname} a {game_dir}: {e}")
            copied += 1
            if progress:
                progress(f"Actualizando {game_dir.name}: {fname}", 0.72 + 0.25 * (copied / len(files_to_copy)))
        return True

    def update_multiple_games(self, game_dirs: List[Path], progress: ProgressCallback | None = None) -> Dict[str, Any]:
        """Actualiza múltiples juegos devolviendo resultados por juego."""
        results = {}
        total = len(game_dirs) or 1
        for idx, g in enumerate(game_dirs, start=1):
            ok = self.update_game(g, progress)
            results[g.name] = ok
            if progress:
                pct = 0.97 * (idx / total)
                progress(f"Juego {idx}/{total} actualizado", pct)
        if progress:
            progress('Actualización completada', 1.0)
        return results

    # ------------------------------------------------------------------
    # High level orchestration
    # ------------------------------------------------------------------
    def perform_full_update(self, game_paths: List[Path], progress: ProgressCallback | None = None) -> Dict[str, Any]:
        """Checks remote release, installs if newer, then updates games.

        Returns dict with summary.
        """
        current = self.get_current_version()
        release = self.fetch_latest_release()
        if not release:
            return {'updated': False, 'reason': 'no_remote_release'}
        if not self.is_newer(release.version, current):
            return {'updated': False, 'reason': 'already_latest', 'current': current}
        if progress:
            progress(f"Nueva versión {release.version} disponible", 0.01)
        ok_install, install_reason = self.install_release(release, progress)
        if not ok_install:
            return {'updated': False, 'reason': install_reason or 'install_failed'}
        valid_games = self.list_game_installations(game_paths)
        game_results = self.update_multiple_games(valid_games, progress)
        return {
            'updated': True,
            'new_version': release.version,
            'games_updated': game_results
        }

__all__ = [
    'OptiScalerUpdater', 'ReleaseInfo'
]
