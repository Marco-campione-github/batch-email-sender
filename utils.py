import sys
import json
from pathlib import Path


def get_app_data_dir():
    """
    Get the application's data directory for storing user files.
    This is separate from the source code directory and always writable.
    """
    if getattr(sys, 'frozen', False):
        # Running as PyInstaller bundle
        # Use platform-specific user data directory
        if sys.platform == 'darwin':  # macOS
            # Use ~/Library/Application Support/batch-email-sender
            app_dir = Path.home() / "Library" / "Application Support" / "batch-email-sender"
        elif sys.platform == 'win32':  # Windows
            # Use %APPDATA%/batch-email-sender or next to executable
            appdata = Path.home() / "AppData" / "Roaming" / "batch-email-sender"
            app_dir = appdata if appdata.parent.exists() else Path(sys.executable).parent
        else:  # Linux and others
            app_dir = Path.home() / ".batch-email-sender"
        
        app_dir.mkdir(parents=True, exist_ok=True)
        return app_dir
    else:
        # Running in development - use a hidden folder in user's home directory
        app_dir = Path.home() / ".batch-email-sender"
        app_dir.mkdir(exist_ok=True)
        return app_dir


def get_resource_path(relative_path):
    """
    Get absolute path to resource, works for dev and for PyInstaller bundled apps.
    
    When running as a PyInstaller bundle, files are extracted to a temp folder.
    sys._MEIPASS contains the path to that temp folder.
    
    For user-writable files (like token.pickle), we use the app's directory or
    the user's home directory.
    """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = Path(sys._MEIPASS)
    except AttributeError:
        # Running in normal Python environment
        base_path = Path(__file__).parent
    
    return base_path / relative_path


def get_data_path(relative_path):
    """
    Get path for user-writable data files (like tokens and credentials).
    
    These files need to persist between app runs and should be stored
    in a dedicated app data directory.
    """
    return get_app_data_dir() / relative_path


def save_cache(key, value):
    """
    Save a key-value pair to the app's cache file.
    
    Args:
        key: The cache key (string)
        value: The value to cache (must be JSON-serializable)
    """
    cache_file = get_data_path("app_cache.json")
    
    # Load existing cache
    cache = {}
    if cache_file.exists():
        try:
            with open(cache_file, 'r') as f:
                cache = json.load(f)
        except (json.JSONDecodeError, IOError):
            cache = {}
    
    # Update cache
    cache[key] = value
    
    # Save cache
    try:
        with open(cache_file, 'w') as f:
            json.dump(cache, f, indent=2)
    except IOError as e:
        print(f"Failed to save cache: {e}")


def load_cache(key, default=None):
    """
    Load a value from the app's cache file.
    
    Args:
        key: The cache key (string)
        default: Default value if key doesn't exist
        
    Returns:
        The cached value or default if not found
    """
    cache_file = get_data_path("app_cache.json")
    
    if not cache_file.exists():
        return default
    
    try:
        with open(cache_file, 'r') as f:
            cache = json.load(f)
            return cache.get(key, default)
    except (json.JSONDecodeError, IOError):
        return default
