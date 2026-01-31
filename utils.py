import sys
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
