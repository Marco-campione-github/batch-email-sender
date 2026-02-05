"""Authentication frame UI component."""

import tkinter as tk
from tkinter import messagebox, ttk, filedialog
import shutil

from auth import authenticate, credentials_file_exists, CREDENTIALS_FILE


class AuthFrame:
    """Handles the authentication UI when user is not logged in."""
    
    def __init__(self, root, on_authenticated):
        """
        Initialize the authentication frame.
        
        Args:
            root: Parent tkinter widget
            on_authenticated: Callback function to call when authentication succeeds
        """
        self.root = root
        self.on_authenticated = on_authenticated
        self.auth_frame = None
        self.credentials_status = None
        self.auth_button = None
        
        self.create_ui()
    
    def create_ui(self):
        """Create the authentication UI."""
        self.auth_frame = ttk.Frame(self.root)
        self.auth_frame.pack(expand=True, fill="both")

        # Center container
        center_frame = ttk.Frame(self.auth_frame)
        center_frame.place(relx=0.5, rely=0.5, anchor="center")

        ttk.Label(
            center_frame,
            text="🚀 Bulk Gmail Sender",
            font=("Helvetica", 24, "bold")
        ).pack(pady=(0, 10))

        ttk.Label(
            center_frame,
            text="Login with Google",
            font=("Helvetica", 16)
        ).pack(pady=(0, 30))

        # Check if credentials file already exists
        if credentials_file_exists():
            status_text = "✓ Credentials file loaded"
        else:
            status_text = "⚠ No credentials file found"
        
        self.credentials_status = ttk.Label(
            center_frame,
            text=status_text,
            font=("Helvetica", 11)
        )
        self.credentials_status.pack(pady=(0, 20))

        # Upload credentials button
        upload_btn = ttk.Button(
            center_frame,
            text="📁 Upload Credentials File",
            command=self.upload_credentials
        )
        upload_btn.pack(pady=10, fill="x")

        # Authenticate button
        self.auth_button = ttk.Button(
            center_frame,
            text="🔐 Authenticate with Google",
            command=self.handle_auth,
            state="normal" if credentials_file_exists() else "disabled"
        )
        self.auth_button.pack(pady=10, fill="x")

        # Instructions
        ttk.Label(
            center_frame,
            text="First, upload your google-oauth-credentials.json file,\nthen click 'Authenticate with Google' to continue.",
            font=("Helvetica", 10),
            justify="center"
        ).pack(pady=(20, 0))
    
    def upload_credentials(self):
        """Allow user to select and upload their credentials file."""
        file_path = filedialog.askopenfilename(
            title="Select Google OAuth Credentials File",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialfile="google-oauth-credentials.json"
        )
        
        if not file_path:
            return  # User cancelled
        
        try:
            # Ensure the directory exists
            CREDENTIALS_FILE.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy the selected file to the app's data directory
            shutil.copy2(file_path, CREDENTIALS_FILE)
            
            # Update UI
            self.credentials_status.config(
                text="✓ Credentials file loaded"
            )
            self.auth_button.config(state="normal")
            
            messagebox.showinfo(
                "Success",
                "Credentials file uploaded successfully!\nYou can now authenticate with Google."
            )
        except Exception as e:
            messagebox.showerror(
                "Upload Error",
                f"Failed to upload credentials file:\n{str(e)}"
            )
    
    def handle_auth(self):
        """Handle authentication button click."""
        # Check if credentials file exists (should always be true if button is enabled)
        if not credentials_file_exists():
            messagebox.showerror(
                "Missing Credentials File",
                "Please upload your google-oauth-credentials.json file first."
            )
            return
        
        try:
            service = authenticate()
            messagebox.showinfo("Success", "Authenticated successfully!")
            self.destroy()
            self.on_authenticated(service)
        except Exception as e:
            messagebox.showerror("Authentication Error", str(e))
    
    def destroy(self):
        """Destroy the authentication frame."""
        if self.auth_frame:
            self.auth_frame.destroy()
