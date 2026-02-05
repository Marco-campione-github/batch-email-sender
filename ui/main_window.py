"""Main window coordinator for the Batch Email Sender application."""

from auth import authenticate, is_authenticated
from utils import save_cache, load_cache

from .auth_frame import AuthFrame
from .email_frame import EmailFrame


class BulkMailerUI:
    """Main application window coordinator."""
    
    def __init__(self, root):
        """
        Initialize the main application UI.
        
        Args:
            root: Tkinter root window
        """
        self.root = root
        self.root.title("Bulk Gmail Sender")

        self.service = None
        self.auth_frame_component = None
        self.email_frame_component = None
        
        # Restore window geometry or maximize on first launch
        self._restore_window_geometry()
        
        # Save geometry before closing
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

        # Start with appropriate frame based on authentication state
        if is_authenticated():
            self.service = authenticate()
            self.show_email_frame()
        else:
            self.show_auth_frame()
    
    def show_auth_frame(self):
        """Show the authentication frame."""
        self.auth_frame_component = AuthFrame(
            self.root,
            on_authenticated=self.on_authenticated
        )
    
    def show_email_frame(self):
        """Show the email composition frame."""
        self.email_frame_component = EmailFrame(
            self.root,
            self.service,
            on_logout=self.on_logout
        )
    
    def on_authenticated(self, service):
        """
        Callback when user successfully authenticates.
        
        Args:
            service: Authenticated Gmail service
        """
        self.service = service
        self.show_email_frame()
    
    def on_logout(self):
        """Callback when user logs out."""
        self.service = None
        self.show_auth_frame()
    
    def _restore_window_geometry(self):
        """Restore window size and position from cache, or maximize on first launch."""
        saved_geometry = load_cache("window_geometry", None)
        
        if saved_geometry:
            # Restore saved geometry
            self.root.geometry(saved_geometry)
        else:
            # First launch - maximize window
            self.root.state('zoomed')  # For Windows/Linux
            # Try macOS maximization as fallback
            try:
                self.root.attributes('-zoomed', True)
            except:
                # Fallback to large window if zoomed doesn't work
                self.root.geometry("1200x800")
    
    def _on_closing(self):
        """Save window geometry before closing."""
        # Save current geometry (format: "widthxheight+x+y")
        geometry = self.root.geometry()
        save_cache("window_geometry", geometry)
        
        # Close the window
        self.root.destroy()
