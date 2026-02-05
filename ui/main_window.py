"""Main window coordinator for the Batch Email Sender application."""

from auth import authenticate, is_authenticated

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
        self.root.geometry("800x600")

        self.service = None
        self.auth_frame_component = None
        self.email_frame_component = None

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
