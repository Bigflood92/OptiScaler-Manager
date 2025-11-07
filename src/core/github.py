"""GitHub API client for FSR Injector."""

import os
import json
import sys
import urllib.request
import subprocess
from typing import List, Dict, Optional, Callable, Tuple
from datetime import datetime, timedelta
from urllib.parse import urljoin
import requests
from ..config.constants import (
    GITHUB_API_URL,
    MOD_SOURCE_DIR,
    SEVEN_ZIP_EXE_NAME,
    GITHUB_REPO_OWNER,
    GITHUB_REPO_NAME,
    CACHE_DIR
)
from ..utils.error_handling import error_handler, FSRException
from ..utils.paths import normalize_path, create_directory

class GitHubClient:
    """Client for interacting with GitHub API."""
    
    def __init__(self, logger: Optional[Callable] = None):
        """Initialize the GitHub client.
        
        Args:
            logger: Optional logging function to use
        """
        self.logger = logger or print
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'FSR-Injector'
        })
        self.api_base = GITHUB_API_URL
        self.owner = GITHUB_REPO_OWNER
        self.repo = GITHUB_REPO_NAME
        self.cache_dir = os.path.join(CACHE_DIR, "github")
        create_directory(self.cache_dir)
        
    def _get_api_url(self, endpoint: str) -> str:
        """Get full API URL for endpoint.
        
        Args:
            endpoint: API endpoint path
            
        Returns:
            Full API URL
        """
        # La API base ya tiene la ruta completa
        if endpoint == "releases":
            return self.api_base
        elif endpoint == "releases/latest":
            return self.api_base.rstrip('/') + "/latest"
        else:
            return f"{self.api_base.rstrip('/')}/{endpoint}"

    def _get_cached_response(self, cache_key: str, max_age: Optional[timedelta] = None) -> Optional[Dict]:
        """Get cached API response.
        
        Args:
            cache_key: Cache file key
            max_age: Maximum age of cache data
            
        Returns:
            Cached response data or None
        """
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
        try:
            if os.path.exists(cache_file):
                # Check cache age if max_age specified
                if max_age:
                    mtime = datetime.fromtimestamp(os.path.getmtime(cache_file))
                    if datetime.now() - mtime > max_age:
                        return None
                
                with open(cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            self.logger('WARN', f"Failed to read cache: {e}")
        return None

    def _cache_response(self, cache_key: str, data: Dict) -> None:
        """Cache API response data.
        
        Args:
            cache_key: Cache file key
            data: Response data to cache
        """
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f)
        except Exception as e:
            self.logger('WARN', f"Failed to write cache: {e}")
        
    @error_handler()
    def get_releases(self, use_cache: bool = True) -> List[Dict]:
        """Get list of releases from GitHub.
        
        Args:
            use_cache: Whether to use cached data
            
        Returns:
            List of release dictionaries
        """
        if use_cache:
            cached = self._get_cached_response("releases", timedelta(hours=1))
            if cached:
                return cached
                
        try:
            response = self.session.get(self._get_api_url("releases"))
            response.raise_for_status()
            releases = response.json()
            
            # Sort releases by date
            for release in releases:
                # Parse date string to datetime for sorting
                release['published_at_dt'] = datetime.strptime(
                    release['published_at'],
                    '%Y-%m-%dT%H:%M:%SZ'
                )
            releases.sort(key=lambda x: x['published_at_dt'], reverse=True)
            
            # Cache the response
            if use_cache:
                self._cache_response("releases", releases)
            
            return releases
            
        except requests.exceptions.RequestException as e:
            self.logger('ERROR', f"Failed to fetch releases: {e}")
            return []
            
    @error_handler()
    def get_latest_release(self, use_cache: bool = True) -> Dict:
        """Get latest release info.
        
        Args:
            use_cache: Whether to use cached data
            
        Returns:
            Release info dict
            
        Raises:
            FSRException: If request fails
        """
        if use_cache:
            cached = self._get_cached_response("latest_release", timedelta(hours=1))
            if cached:
                return cached
                
        url = self._get_api_url("releases/latest")
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if use_cache:
                self._cache_response("latest_release", data)
                
            return data
            
        except requests.RequestException as e:
            error_msg = f"Failed to get latest release: {str(e)}"
            self.logger('ERROR', error_msg)
            raise FSRException(error_msg)
            
    def get_release_download_url(
            self, 
            release_data: Dict, 
            asset_name: str
    ) -> Optional[str]:
        """Get download URL for release asset.
        
        Args:
            release_data: Release info dict
            asset_name: Name of asset to find
            
        Returns:
            Download URL or None if not found
        """
        try:
            for asset in release_data.get("assets", []):
                if asset["name"] == asset_name:
                    return asset["browser_download_url"]
        except (KeyError, TypeError) as e:
            self.logger('ERROR', f"Failed to get download URL: {e}")
        return None
            
    def check_for_updates(self, current_version: str) -> Tuple[bool, Optional[str]]:
        """Check if updates are available.
        
        Args:
            current_version: Current version string
            
        Returns:
            Tuple of (update_available, latest_version)
            
        Raises:
            FSRException: If version check fails
        """
        try:
            release = self.get_latest_release()
            latest_version = release["tag_name"].lstrip('v')
            
            if latest_version != current_version:
                return True, latest_version
                
            return False, None
            
        except Exception as e:
            error_msg = f"Failed to check for updates: {str(e)}"
            self.logger('ERROR', error_msg)
            raise FSRException(error_msg)
            
    def get_release_notes(self, version: str = "latest") -> str:
        """Get release notes.
        
        Args:
            version: Version to get notes for ("latest" or version string)
            
        Returns:
            Release notes markdown text
            
        Raises:
            FSRException: If notes retrieval fails
        """
        try:
            if version == "latest":
                release = self.get_latest_release()
            else:
                # Get specific release by tag
                url = self._get_api_url(f"releases/tags/v{version}")
                response = self.session.get(url, timeout=10)
                response.raise_for_status()
                release = response.json()
                
            return release.get("body", "No release notes available.")
            
        except Exception as e:
            error_msg = f"Failed to get release notes: {str(e)}"
            self.logger('ERROR', error_msg)
            raise FSRException(error_msg)
            
    @error_handler()
    def download_release(self, release_info: Dict, progress_callback: Optional[Callable] = None) -> bool:
        """Download a specific release.
        
        Args:
            release_info: Release information dictionary
            progress_callback: Optional callback for download progress
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create mod_source directory if needed
            os.makedirs(MOD_SOURCE_DIR, exist_ok=True)
            
            # Get download URL and expected file size
            assets = release_info.get('assets', [])
            if not assets:
                error_msg = "No assets found in release"
                self.logger('ERROR', error_msg)
                raise FSRException(error_msg)
                
            # Find .7z asset
            asset = None
            for a in assets:
                if a['name'].endswith('.7z'):
                    asset = a
                    break
                    
            if not asset:
                error_msg = "No .7z asset found in release"
                self.logger('ERROR', error_msg)
                raise FSRException(error_msg)
                
            download_url = asset['browser_download_url']
            expected_size = asset['size']
            
            # Download file with progress reporting
            local_file = os.path.join(MOD_SOURCE_DIR, asset['name'])
            
            response = self.session.get(download_url, stream=True)
            response.raise_for_status()
            
            with open(local_file, 'wb') as f:
                downloaded = 0
                chunk_size = 8192
                
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if progress_callback:
                            progress = min(downloaded / expected_size, 1.0)
                            progress_callback(downloaded, expected_size, False,
                                           f"Downloading release... {progress:.1%}")
                                           
            # Extract the archive
            self._extract_release(local_file, progress_callback)
            
            # Clean up downloaded archive
            try:
                os.remove(local_file)
            except Exception as e:
                self.logger('WARN', f"Failed to clean up downloaded file: {e}")
                
            if progress_callback:
                progress_callback(1, 1, True, "Download and extraction complete!")
                
            return True
            
        except requests.RequestException as e:
            error_msg = f"Failed to download release: {e}"
            self.logger('ERROR', error_msg)
            if progress_callback:
                progress_callback(0, 1, True, f"Download failed: {e}")
            raise FSRException(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error during release download: {e}"
            self.logger('ERROR', error_msg)
            if progress_callback:
                progress_callback(0, 1, True, f"Download failed: {e}")
            raise FSRException(error_msg)
            
    def _extract_release(self, archive_path: str, progress_callback: Optional[Callable] = None) -> bool:
        """Extract downloaded release archive.
        
        Args:
            archive_path: Path to downloaded archive
            progress_callback: Optional callback for extraction progress
            
        Returns:
            bool: True if successful, False otherwise
            
        Raises:
            FSRException: If extraction fails
        """
        try:
            # Get possible 7z.exe paths
            base_path = self._get_script_base_path()
            search_paths = [
                os.path.join(base_path, SEVEN_ZIP_EXE_NAME),
                os.path.join(base_path, "tools", SEVEN_ZIP_EXE_NAME),
                os.path.join(os.environ.get("ProgramFiles", ""), "7-Zip", "7z.exe"),
                os.path.join(os.environ.get("ProgramFiles(x86)", ""), "7-Zip", "7z.exe")
            ]
            
            seven_zip_exe = None
            for path in search_paths:
                if os.path.exists(path):
                    seven_zip_exe = path
                    break
                    
            if not seven_zip_exe:
                error_msg = "7-Zip executable not found. Please make sure 7-Zip is installed."
                self.logger('ERROR', f"{error_msg}\nSearched paths:\n" + "\n".join(f"- {p}" for p in search_paths))
                raise FSRException(error_msg)
                
            # Prepare extraction directory name from archive name
            extract_dir = os.path.splitext(os.path.basename(archive_path))[0]
            extract_path = os.path.join(MOD_SOURCE_DIR, extract_dir)
            
            # Create extraction directory
            os.makedirs(extract_path, exist_ok=True)
            
            if progress_callback:
                progress_callback(0, 1, False, "Extracting files...")
                
            # Run 7z.exe command
            command = [
                seven_zip_exe,
                'x',       # Extract with full paths
                '-y',      # Yes to all prompts
                f'-o{extract_path}',  # Output directory
                archive_path  # Input archive
            ]
            
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,  # Use text mode for better output handling
                encoding='utf-8',
                errors='replace'  # Handle encoding errors gracefully
            )
            
            # Monitor extraction and check progress
            while True:
                line = process.stdout.readline()
                if not line and process.poll() is not None:
                    break
                    
                # Try to parse progress from 7-Zip output
                if line.startswith(" "):
                    try:
                        percent = int(line.strip().rstrip("%"))
                        if progress_callback:
                            progress_callback(percent, 100, False, f"Extracting files... {percent}%")
                    except (ValueError, IndexError):
                        pass
            
            returncode = process.wait()
            stderr = process.stderr.read()
            
            if returncode != 0:
                error_msg = f"7-Zip extraction failed:\nErrors: {stderr}"
                self.logger('ERROR', error_msg)
                raise FSRException(error_msg)
                
            if progress_callback:
                progress_callback(100, 100, True, "Extraction complete!")
                
            return True
            
        except FSRException:
            raise
        except Exception as e:
            error_msg = f"Failed to extract release: {str(e)}"
            self.logger('ERROR', error_msg)
            if progress_callback:
                progress_callback(0, 100, True, f"Extraction failed: {str(e)}")
            raise FSRException(error_msg)
            
    def clear_cache(self) -> None:
        """Clear cached API responses."""
        try:
            for file in os.listdir(self.cache_dir):
                try:
                    os.remove(os.path.join(self.cache_dir, file))
                except Exception as e:
                    self.logger('WARN', f"Failed to delete cache file {file}: {e}")
        except Exception as e:
            self.logger('WARN', f"Failed to clear cache: {e}")
            
    def __enter__(self):
        """Context manager entry.
        
        Returns:
            self
        """
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit.
        
        Args:
            exc_type: Exception type if error occurred
            exc_val: Exception value if error occurred  
            exc_tb: Exception traceback if error occurred
        """
        self.session.close()
            
    def _get_script_base_path(self) -> str:
        """Get base path for the application.
        
        Returns:
            str: Base path
        """
        try:
            if getattr(sys, 'frozen', False):
                # Running as compiled executable
                return os.path.dirname(sys.executable)
            else:
                # Running as script
                return os.path.dirname(os.path.dirname(__file__))
        except Exception:
            return os.path.abspath(".")