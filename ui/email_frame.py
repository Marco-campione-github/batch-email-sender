"""Email composition frame component."""

import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk
import threading
import sv_ttk
import darkdetect

from auth import get_authenticated_user_email, TOKEN_FILE
from email_service import send_email
from utils import save_cache, load_cache
from html_converter import markdown_to_html

from .google_docs_panel import GoogleDocsPanel
from .google_sheets_panel import GoogleSheetsPanel
from .preview_panel import PreviewPanel


class EmailFrame:
    """Handles the main email composition UI."""
    
    def __init__(self, root, service, on_logout):
        """
        Initialize the email composition frame.
        
        Args:
            root: Root window
            service: Authenticated Gmail service
            on_logout: Callback function to call when user logs out
        """
        self.root = root
        self.service = service
        self.on_logout = on_logout
        
        self.email_frame = None
        self.account_label = None
        self.theme_var = None
        self.theme_combo = None
        self.subject_entry = None
        self.body_text = None
        self.body_paned = None
        self.recipients_text = None
        self.send_button = None
        self.progress_label = None
        self.progress_bar = None
        self.preview_button = None
        
        # Component references
        self.docs_panel = None
        self.sheets_panel = None
        self.preview_panel = None
        
        self.create_ui()
    
    def create_ui(self):
        """Create the email composition UI."""
        self.email_frame = ttk.Frame(self.root)
        self.email_frame.pack(fill="both", expand=True)

        # Header with account info and logout
        self._create_header()
        
        # Create scrollable canvas for main content
        canvas, content_frame = self._create_scrollable_canvas()
        
        # Google Docs section
        self.docs_panel = GoogleDocsPanel(
            content_frame,
            self.root,
            None,  # Will be set after subject_entry is created
            None,  # Will be set after body_text is created
            None   # Will be set after preview_panel is created
        )
        
        # Subject
        self._create_subject_section(content_frame)
        
        # Body with preview
        self._create_body_section(content_frame)
        
        # Recipients
        self._create_recipients_section(content_frame)
        
        # Send button and progress
        self._create_send_section(content_frame)
        
        # Update docs panel references
        self.docs_panel.subject_entry = self.subject_entry
        self.docs_panel.body_text = self.body_text
        self.docs_panel.update_preview_callback = self.preview_panel.update_preview
        
        # Enable mousewheel scrolling
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        canvas.bind_all("<MouseWheel>", on_mousewheel)
    
    def _create_header(self):
        """Create the header with account info, theme selector, and logout button."""
        header_frame = ttk.Frame(self.email_frame)
        header_frame.pack(fill="x", side="top", pady=(0, 10))

        # Account email display
        account_email = get_authenticated_user_email(self.service)
        self.account_label = ttk.Label(
            header_frame,
            text=f"👤 {account_email}",
            font=("Helvetica", 11)
        )
        self.account_label.pack(side="left", padx=20, pady=15)

        # Theme selector
        theme_frame = ttk.Frame(header_frame)
        theme_frame.pack(side="right", padx=(0, 10), pady=15)
        
        ttk.Label(
            theme_frame,
            text="🌗 Theme:",
            font=("Helvetica", 10)
        ).pack(side="left", padx=(0, 5))
        
        self.theme_var = tk.StringVar()
        self.theme_combo = ttk.Combobox(
            theme_frame,
            textvariable=self.theme_var,
            values=["System", "Light", "Dark"],
            state="readonly",
            width=10
        )
        self.theme_combo.pack(side="left")
        
        # Load saved theme preference or default to "System"
        saved_theme = load_cache("theme_preference", "System")
        self.theme_var.set(saved_theme)
        
        # Bind theme change event
        self.theme_combo.bind("<<ComboboxSelected>>", self.on_theme_change)

        # Logout button
        logout_btn = ttk.Button(
            header_frame,
            text="Logout",
            command=self.handle_logout
        )
        logout_btn.pack(side="right", padx=20, pady=15)
    
    def _create_scrollable_canvas(self):
        """Create and return the scrollable canvas and content frame."""
        canvas_frame = ttk.Frame(self.email_frame)
        canvas_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        canvas = tk.Canvas(canvas_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
        
        # Main content frame inside canvas
        content_frame = ttk.Frame(canvas)
        
        # Configure canvas
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        
        # Create window in canvas
        canvas_window = canvas.create_window((0, 0), window=content_frame, anchor="nw")
        
        # Update scroll region when content changes
        def on_frame_configure(event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))
            # Also update window width to match canvas
            canvas.itemconfig(canvas_window, width=canvas.winfo_width())
        
        content_frame.bind("<Configure>", on_frame_configure)
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(canvas_window, width=e.width))
        
        return canvas, content_frame
    
    def _create_subject_section(self, parent):
        """Create the subject input section."""
        ttk.Label(
            parent,
            text="Subject",
            font=("Helvetica", 12, "bold")
        ).pack(anchor="w", pady=(10, 5))
        
        self.subject_entry = ttk.Entry(
            parent,
            font=("Helvetica", 11)
        )
        self.subject_entry.pack(fill="x")
    
    def _create_body_section(self, parent):
        """Create the body text section with preview toggle."""
        # Body header
        body_header = ttk.Frame(parent)
        body_header.pack(fill="x", pady=(15, 5))
        
        body_title_frame = ttk.Frame(body_header)
        body_title_frame.pack(side="left", anchor="w")
        
        ttk.Label(
            body_title_frame,
            text="Email Body",
            font=("Helvetica", 12, "bold")
        ).pack(anchor="w")
        
        # Clickable formatting help label
        help_label = ttk.Label(
            body_title_frame,
            text="Formatting help",
            font=("Helvetica", 9, "underline"),
            cursor="hand2"
        )
        help_label.pack(anchor="w")
        help_label.bind("<Button-1>", lambda e: GoogleDocsPanel.show_formatting_help(self.root))
        
        self.preview_button = ttk.Button(
            body_header,
            text="Show Preview",
            command=None  # Will be set after preview_panel is created
        )
        self.preview_button.pack(side="right", padx=(10, 0))
        
        # Create a PanedWindow for resizable panes
        self.body_paned = ttk.PanedWindow(
            parent,
            orient=tk.HORIZONTAL
        )
        self.body_paned.pack(fill="both", expand=False, pady=(5, 15))
        # Set height via configure
        self.body_paned.configure(height=300)
        
        # Left side: Editable text (Markdown)
        left_frame = ttk.Frame(self.body_paned)
        
        left_header = ttk.Frame(left_frame)
        left_header.pack(fill="x")
        ttk.Label(
            left_header,
            text="✏️ Edit (Markdown)",
            font=("Helvetica", 10, "bold"),
            padding=(10, 8)
        ).pack(anchor="w")
        
        self.body_text = scrolledtext.ScrolledText(
            left_frame,
            wrap="word",
            font=("Helvetica", 11),
            background="#f0f0f0"
        )
        self.body_text.pack(fill="both", expand=True)
        
        # Bind text change event to detect edits
        self.body_text.bind("<<Modified>>", self.on_body_text_modified)
        
        # Add left frame to paned window
        self.body_paned.add(left_frame)
        
        # Create preview panel
        self.preview_panel = PreviewPanel(
            parent,
            self.root,
            self.body_paned,
            self.body_text
        )
        
        # Set preview button command and preview panel reference
        self.preview_button.config(command=self.preview_panel.toggle_preview)
        self.preview_panel.set_preview_button(self.preview_button)
        
        # Bind text change to update preview
        self.body_text.bind("<KeyRelease>", self.preview_panel.update_preview)
    
    def _create_recipients_section(self, parent):
        """Create the recipients input section with Google Sheets integration."""
        ttk.Label(
            parent,
            text="Recipients",
            font=("Helvetica", 12, "bold")
        ).pack(anchor="w", pady=(15, 5))
        
        # Google Sheets import section
        self.sheets_panel = GoogleSheetsPanel(
            parent,
            self.root,
            None  # Will be set after recipients_text is created
        )
        
        ttk.Label(
            parent,
            text="Or enter one email address per line manually",
            font=("Helvetica", 9)
        ).pack(anchor="w", pady=(0, 5))
        
        recipients_frame = ttk.Frame(parent)
        recipients_frame.pack(fill="x", pady=(0, 15))
        
        self.recipients_text = scrolledtext.ScrolledText(
            recipients_frame,
            height=8,
            font=("Helvetica", 11),
            background="#f0f0f0"
        )
        self.recipients_text.pack(fill="both", expand=True)
        
        # Update sheets panel reference
        self.sheets_panel.recipients_text = self.recipients_text
    
    def _create_send_section(self, parent):
        """Create the send button and progress indicators."""
        send_frame = ttk.Frame(parent)
        send_frame.pack(fill="x", pady=(10, 20))
        
        self.send_button = ttk.Button(
            send_frame,
            text="🚀 Send Emails",
            command=self.confirm_send
        )
        self.send_button.pack(fill="x", padx=20, pady=10)

        # Progress label
        self.progress_label = ttk.Label(
            send_frame,
            text="",
            font=("Helvetica", 10)
        )
        self.progress_label.pack(pady=(10, 0))

        # Progress bar
        self.progress_bar = ttk.Progressbar(
            send_frame,
            length=400,
            mode="determinate"
        )
        self.progress_bar.pack(pady=(0, 20))
    
    def on_theme_change(self, event=None):
        """Handle theme selection change."""
        selected_theme = self.theme_var.get()
        
        # Save preference
        save_cache("theme_preference", selected_theme)
        
        # Apply theme
        if selected_theme == "System":
            theme = darkdetect.theme()  # Returns "dark" or "light"
            if theme:
                sv_ttk.set_theme(theme)
        else:
            sv_ttk.set_theme(selected_theme.lower())
        
        # Remove focus and clear selection from combobox
        self.theme_combo.selection_clear()
        self.root.focus_set()
    
    def handle_logout(self):
        """Handle logout button click."""
        confirm = messagebox.askyesno("Logout", "Are you sure you want to logout?")
        if confirm:
            # Delete token
            if TOKEN_FILE.exists():
                TOKEN_FILE.unlink()
            self.service = None
            self.destroy()
            messagebox.showinfo("Logged out", "You have been logged out successfully.")
            self.on_logout()
    
    def confirm_send(self):
        """Confirm before sending emails."""
        subject = self.subject_entry.get().strip()
        body = self.body_text.get("1.0", tk.END).strip()
        recipients = self.get_recipients()

        if not subject or not body or not recipients:
            messagebox.showwarning("Missing data", "Subject, body, and recipients are required.")
            return

        confirm = messagebox.askyesno(
            "Confirm Send",
            f"Send email to {len(recipients)} recipients?"
        )

        if confirm:
            self.send_emails(subject, body, recipients)
    
    def send_emails(self, subject, body, recipients):
        """Send emails to all recipients."""
        def task():
            total = len(recipients)
            sent = 0

            # Reset progress bar
            self.progress_bar["maximum"] = total
            self.progress_bar["value"] = 0
            self.progress_label.config(text="")
            self.send_button.config(state="disabled")
            self.root.update_idletasks()
            
            # Convert current Markdown text to HTML for sending
            body_to_send = markdown_to_html(body)

            for i, email in enumerate(recipients, start=1):
                try:
                    send_email(self.service, email, subject, body_to_send)
                    sent += 1
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to send to {email}\n{e}")
                finally:
                    # Update progress
                    self.progress_bar["value"] = i
                    self.progress_label.config(text=f"Sending email {i} / {total}")
                    self.root.update_idletasks()

            self.send_button.config(state="normal")
            self.progress_label.config(text=f"Done! Sent {sent}/{total} emails.")

        threading.Thread(target=task).start()
    
    def get_recipients(self):
        """Get list of recipients from text field."""
        raw = self.recipients_text.get("1.0", tk.END)
        return [line.strip() for line in raw.splitlines() if line.strip()]
    
    def on_body_text_modified(self, event=None):
        """Called when body text is modified."""
        if self.body_text.edit_modified():
            # Reset the modified flag for next change detection
            self.body_text.edit_modified(False)
    
    def destroy(self):
        """Destroy the email frame."""
        if self.email_frame:
            self.email_frame.destroy()
