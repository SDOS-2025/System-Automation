#!/usr/bin/env python
"""Utility for gathering and caching system information."""

import platform
import json
import os
import glob
from pathlib import Path
from datetime import datetime, timedelta
import configparser
from typing import Optional

from .logging_setup import get_logger

logger = get_logger(__name__)

# Define cache location relative to workspace root
# Assumes this script is run from a context where workspace root is accessible
# (e.g., via PROJECT_ROOT.parent in assistant.py)
DEFAULT_CACHE_DIR = Path("cache")
DEFAULT_CACHE_FILE = DEFAULT_CACHE_DIR / "system_info.json"

def get_os_info() -> dict:
    """Gathers basic OS information."""
    return {
        "system": platform.system(),  # E.g., 'Linux', 'Windows', 'Darwin'
        "release": platform.release(),
        "version": platform.version(),
        "architecture": platform.machine(),
    }

def guess_super_key() -> dict:
    """Makes an educated guess about the Super/Win key based on OS."""
    system = platform.system()
    key_name = "Unknown"
    if system == "Linux":
        # Often Super_L on Linux desktops
        key_name = "Super_L"
    elif system == "Windows":
        key_name = "Win" # Typically the Windows key
    elif system == "Darwin":
        key_name = "Meta_L" # Command key often acts like Super
    
    # Testing if it *works* automatically is unreliable. Assume true for now.
    return {
        "key_name": key_name,
        "works": True
    }

def _parse_desktop_file(filepath: Path) -> Optional[str]:
    """Parses a .desktop file to extract the application name."""
    try:
        config = configparser.ConfigParser(interpolation=None)
        # Read file with UTF-8 encoding, handle potential errors
        with filepath.open('r', encoding='utf-8') as f:
            config.read_file(f)
        
        if 'Desktop Entry' in config:
            entry = config['Desktop Entry']
            # Check common flags to filter out non-app entries
            if entry.getboolean('NoDisplay', False) or entry.get('Type', 'Application') != 'Application':
                return None
            # Prefer Name[locale], fallback to Name
            # TODO: Add locale handling if needed
            return entry.get('Name')
    except configparser.Error as e:
        logger.debug(f"Error parsing desktop file {filepath}: {e}")
    except Exception as e:
        logger.debug(f"Error reading or processing file {filepath}: {e}")
    return None

def get_installed_apps() -> list[str]:
    """Gathers a list of installed GUI applications (Linux focused)."""
    apps = set()
    system = platform.system()

    if system == "Linux":
        logger.info("Scanning for Linux applications (.desktop files)...")
        desktop_paths = [
            Path("/usr/share/applications"),
            Path(os.path.expanduser("~/.local/share/applications"))
        ]
        for dir_path in desktop_paths:
            if dir_path.is_dir():
                for filepath in dir_path.glob("*.desktop"):
                    app_name = _parse_desktop_file(filepath)
                    if app_name:
                        apps.add(app_name.strip())
        logger.info(f"Found {len(apps)} potential applications.")

    elif system == "Windows":
        logger.warning("Application discovery for Windows is not implemented yet.")
        # TODO: Implement Windows app discovery (e.g., PowerShell, registry)
        pass
    elif system == "Darwin":
        logger.warning("Application discovery for macOS is not implemented yet.")
        # TODO: Implement macOS app discovery (e.g., /Applications, Spotlight)
        pass
    else:
        logger.warning(f"Application discovery not supported for OS: {system}")

    return sorted(list(apps))

def load_system_info_cache(cache_path: Path = DEFAULT_CACHE_FILE) -> Optional[dict]:
    """Loads system info from the cache file."""
    if cache_path.exists():
        try:
            with cache_path.open('r', encoding='utf-8') as f:
                data = json.load(f)
            logger.info(f"Loaded system info from cache: {cache_path}")
            return data
        except (json.JSONDecodeError, OSError) as e:
            logger.error(f"Failed to load or parse cache file {cache_path}: {e}")
            return None
    else:
        logger.info(f"System info cache file not found: {cache_path}")
        return None

def save_system_info_cache(data: dict, cache_path: Path = DEFAULT_CACHE_FILE):
    """Saves system info to the cache file."""
    try:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        with cache_path.open('w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        logger.info(f"Saved system info to cache: {cache_path}")
    except OSError as e:
        logger.error(f"Failed to save cache file {cache_path}: {e}")

def get_system_info(cache_path: Path = DEFAULT_CACHE_FILE, refresh_apps_if_older_days: int = 1) -> dict:
    """Gets system info, using cache if available and not too old."""
    cached_data = load_system_info_cache(cache_path)
    
    system_info = {}
    refresh_apps = True
    
    if cached_data:
        system_info = cached_data
        # Check if app list needs refreshing based on timestamp
        app_info = cached_data.get("installed_apps", {})
        last_updated_str = app_info.get("last_updated")
        if last_updated_str:
            try:
                last_updated_dt = datetime.fromisoformat(last_updated_str)
                if datetime.now() - last_updated_dt < timedelta(days=refresh_apps_if_older_days):
                    refresh_apps = False
                    logger.info(f"Installed app list cache is recent (< {refresh_apps_if_older_days} days). Using cached list.")
                else:
                    logger.info("Installed app list cache is older than threshold. Refreshing.")
            except ValueError:
                logger.warning("Could not parse last_updated timestamp from cache. Refreshing app list.")
        else:
             logger.info("No last_updated timestamp found for apps in cache. Refreshing app list.")
            
        # Ensure basic OS info and super key are present if cache exists
        if "os_info" not in system_info:
            system_info["os_info"] = get_os_info()
            save_system_info_cache(system_info, cache_path) # Save updated cache
        if "super_key" not in system_info:
            system_info["super_key"] = guess_super_key()
            save_system_info_cache(system_info, cache_path)

    else:
        # Cache doesn't exist or failed to load, gather everything
        logger.info("Gathering fresh system information...")
        system_info["os_info"] = get_os_info()
        system_info["super_key"] = guess_super_key()
        # refresh_apps is already True

    # Gather/refresh app list if needed
    if refresh_apps:
        logger.info("Refreshing installed application list...")
        apps = get_installed_apps()
        system_info["installed_apps"] = {
            "last_updated": datetime.now().isoformat(),
            "apps": apps
        }
        save_system_info_cache(system_info, cache_path) # Save updated cache

    return system_info

# Example Usage (can be run directly for testing)
if __name__ == '__main__':
    # Assuming script is run from project root or similar
    # Set cache path relative to the script location or a known base
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent # Adjust if needed
    cache_dir = project_root / DEFAULT_CACHE_DIR 
    cache_file = cache_dir / DEFAULT_CACHE_FILE.name
    
    print(f"Using cache file: {cache_file}")
    info = get_system_info(cache_path=cache_file, refresh_apps_if_older_days=1)
    print("--- System Information ---")
    print(json.dumps(info, indent=2))
    print("--------------------------")
    # Demonstrate cache usage on second run
    print("Running again to test cache...")
    info_cached = get_system_info(cache_path=cache_file, refresh_apps_if_older_days=1)
    assert info_cached == info # Should be same unless refresh triggered
    print("Second run loaded from cache (or refreshed if needed).")
    print(f"App count: {len(info_cached.get('installed_apps', {}).get('apps', []))}") 