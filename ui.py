import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk, filedialog
import threading
import shutil
import re
import sv_ttk
import darkdetect

from auth import authenticate, is_authenticated, get_authenticated_user_email, TOKEN_FILE, credentials_file_exists, CREDENTIALS_FILE
from email_service import send_email
from docs_service import read_google_doc
from utils import save_cache, load_cache
from html_converter import html_to_markdown, markdown_to_html


class BulkMailerUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Bulk Gmail Sender")
        self.root.geometry("800x600")

        self.service = None
        self.loaded_body_html = None  # Store HTML version from Google Docs
        self.loaded_body_text = None  # Store original plain text from Google Docs

        self.auth_frame = None
        self.email_frame = None
        self.send_button = None
        self.account_label = None

        if is_authenticated():
            self.init_email_frame(auto_auth=True)
        else:
            self.init_auth_frame()

    # ---------- AUTH FRAME ----------
    def init_auth_frame(self):
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
        # Check if credentials file exists (should always be true if button is enabled)
        if not credentials_file_exists():
            messagebox.showerror(
                "Missing Credentials File",
                "Please upload your google-oauth-credentials.json file first."
            )
            return
        
        try:
            self.service = authenticate()
            messagebox.showinfo("Success", "Authenticated successfully!")
            self.auth_frame.destroy()
            self.init_email_frame()
        except Exception as e:
            messagebox.showerror("Authentication Error", str(e))

    # ---------- EMAIL FRAME ----------
    def init_email_frame(self, auto_auth=False):
        if auto_auth:
            self.service = authenticate()

        self.email_frame = ttk.Frame(self.root)
        self.email_frame.pack(fill="both", expand=True)

        # Header with account info and logout
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

        # Create scrollable canvas
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
        
        # Enable mousewheel scrolling
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        canvas.bind_all("<MouseWheel>", on_mousewheel)

        # Google Docs section
        docs_frame = ttk.LabelFrame(content_frame, text="📄 Load from Google Docs", padding=(15, 10))
        docs_frame.pack(fill="x", pady=(0, 15))
        
        ttk.Label(
            docs_frame,
            text="Enter Document ID or URL",
            font=("Helvetica", 9)
        ).pack(anchor="w", pady=(0, 8))
        
        input_frame = ttk.Frame(docs_frame)
        input_frame.pack(fill="x", pady=(0, 0))
        
        self.doc_entry = ttk.Entry(
            input_frame,
            font=("Helvetica", 11)
        )
        self.doc_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        # Load cached doc URL if available
        cached_doc_url = load_cache("last_doc_url", "")
        if cached_doc_url:
            self.doc_entry.insert(0, cached_doc_url)
        
        import_btn = ttk.Button(
            input_frame,
            text="📥 Import",
            command=self.load_from_google_docs
        )
        import_btn.pack(side="right")

        # Subject
        ttk.Label(
            content_frame,
            text="Subject",
            font=("Helvetica", 12, "bold")
        ).pack(anchor="w", pady=(10, 5))
        
        self.subject_entry = ttk.Entry(
            content_frame,
            font=("Helvetica", 11)
        )
        self.subject_entry.pack(fill="x")

        # Body - Side by Side View with Toggle
        body_header = ttk.Frame(content_frame)
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
        help_label.bind("<Button-1>", lambda e: self.show_formatting_help())
        
        self.preview_button = ttk.Button(
            body_header,
            text="Show Preview",
            command=self.toggle_preview
        )
        self.preview_button.pack(side="right", padx=(10, 0))
        
        # Create a PanedWindow for resizable panes
        self.body_paned = ttk.PanedWindow(
            content_frame,
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
        
        # Bind text change event to detect edits and update preview
        self.body_text.bind("<<Modified>>", self.on_body_text_modified)
        self.body_text.bind("<KeyRelease>", self.update_preview)
        
        # Add left frame to paned window
        self.body_paned.add(left_frame)
        
        # Right side: HTML Preview (initially hidden)
        self.right_frame = ttk.Frame(self.body_paned)
        
        right_header = ttk.Frame(self.right_frame)
        right_header.pack(fill="x")
        ttk.Label(
            right_header,
            text="👁️ Preview (HTML)",
            font=("Helvetica", 10, "bold"),
            padding=(10, 8)
        ).pack(anchor="w")
        
        self.preview_text = scrolledtext.ScrolledText(
            self.right_frame, 
            wrap="word",
            state="disabled",
            font=("Helvetica", 11),
            background="#f0f0f0"
        )
        self.preview_text.pack(fill="both", expand=True)
        
        # Track preview visibility
        self.preview_visible = False

        # Recipients
        ttk.Label(
            content_frame,
            text="Recipients",
            font=("Helvetica", 12, "bold")
        ).pack(anchor="w", pady=(15, 5))
        
        ttk.Label(
            content_frame,
            text="Enter one email address per line",
            font=("Helvetica", 9)
        ).pack(anchor="w", pady=(0, 5))
        
        recipients_frame = ttk.Frame(content_frame)
        recipients_frame.pack(fill="x", pady=(0, 15))
        
        self.recipients_text = scrolledtext.ScrolledText(
            recipients_frame,
            height=8,
            font=("Helvetica", 11),
            background="#f0f0f0"
        )
        self.recipients_text.pack(fill="both", expand=True)

        # Send button and progress
        send_frame = ttk.Frame(content_frame)
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

    # ---------- THEME SWITCHING ----------
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

    # ---------- LOGOUT ----------
    def handle_logout(self):
        confirm = messagebox.askyesno("Logout", "Are you sure you want to logout?")
        if confirm:
            # Delete token
            if TOKEN_FILE.exists():
                TOKEN_FILE.unlink()
            self.service = None
            self.email_frame.destroy()
            self.init_auth_frame()
            messagebox.showinfo("Logged out", "You have been logged out successfully.")

    # ---------- SEND LOGIC ----------
    def confirm_send(self):
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
                    # Call the email_service function
                    from email_service import send_email
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
        raw = self.recipients_text.get("1.0", tk.END)
        return [line.strip() for line in raw.splitlines() if line.strip()]

    def on_body_text_modified(self, event=None):
        """Called when body text is modified."""
        if self.body_text.edit_modified():
            # Reset the modified flag for next change detection
            self.body_text.edit_modified(False)
    
    def toggle_preview(self):
        """Toggle the HTML preview pane visibility."""
        if self.preview_visible:
            # Hide preview
            self.body_paned.remove(self.right_frame)
            self.preview_button.config(text="Show Preview")
            self.preview_visible = False
        else:
            # Show preview
            self.body_paned.add(self.right_frame)
            self.preview_button.config(text="Hide Preview")
            self.preview_visible = True
            # Set sash position to middle after adding the pane
            self.root.update_idletasks()  # Ensure widget is rendered
            paned_width = self.body_paned.winfo_width()
            if paned_width > 1:  # Only set if width is valid
                self.body_paned.sashpos(0, paned_width // 2)
            # Update preview when showing
            self.update_preview()
        
        # Remove focus from button to avoid white border
        self.root.focus_set()
    
    def update_preview(self, event=None):
        """Update the HTML preview in real-time as user types."""
        try:
            # Get current Markdown text
            markdown_text = self.body_text.get("1.0", tk.END).strip()
            
            # Convert to HTML
            html = markdown_to_html(markdown_text)
            
            # Render a simplified version in the preview
            preview_text = self.render_html_for_preview(html)
            
            # Update preview widget
            self.preview_text.config(state="normal")
            self.preview_text.delete("1.0", tk.END)
            self.preview_text.insert("1.0", preview_text)
            self.preview_text.config(state="disabled")
        except Exception as e:
            # Silently handle preview errors
            pass
    
    def render_html_for_preview(self, html):
        """Convert HTML to a readable preview format (simplified rendering)."""
        if not html:
            return ""
        
        # This is a simplified text-based preview
        # Remove HTML tags but show structure
        preview = html
        
        # Show headings with emphasis
        for i in range(1, 7):
            preview = re.sub(f'<h{i}[^>]*>(.*?)</h{i}>', lambda m: f"\n{'=' * (7-i)} {m.group(1).upper()} {'=' * (7-i)}\n", preview, flags=re.IGNORECASE | re.DOTALL)
        
        # Show bold with indicators
        preview = re.sub(r'<strong[^>]*>(.*?)</strong>', r'**\1**', preview, flags=re.IGNORECASE | re.DOTALL)
        preview = re.sub(r'<b[^>]*>(.*?)</b>', r'**\1**', preview, flags=re.IGNORECASE | re.DOTALL)
        
        # Show italic with indicators
        preview = re.sub(r'<em[^>]*>(.*?)</em>', r'*\1*', preview, flags=re.IGNORECASE | re.DOTALL)
        preview = re.sub(r'<i[^>]*>(.*?)</i>', r'*\1*', preview, flags=re.IGNORECASE | re.DOTALL)
        
        # Show underline
        preview = re.sub(r'<u[^>]*>(.*?)</u>', r'_\1_', preview, flags=re.IGNORECASE | re.DOTALL)
        
        # Show strikethrough
        preview = re.sub(r'<s[^>]*>(.*?)</s>', r'~~\1~~', preview, flags=re.IGNORECASE | re.DOTALL)
        
        # Show links
        preview = re.sub(r'<a[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', r'\2 (→ \1)', preview, flags=re.IGNORECASE | re.DOTALL)
        
        # Handle lists
        preview = re.sub(r'<li[^>]*>(.*?)</li>', r'  • \1\n', preview, flags=re.IGNORECASE | re.DOTALL)
        preview = re.sub(r'</?ul[^>]*>', '', preview, flags=re.IGNORECASE)
        preview = re.sub(r'</?ol[^>]*>', '', preview, flags=re.IGNORECASE)
        
        # Handle paragraphs and breaks
        preview = re.sub(r'<p[^>]*>(.*?)</p>', r'\1\n\n', preview, flags=re.IGNORECASE | re.DOTALL)
        preview = re.sub(r'<br\s*/?>', '\n', preview, flags=re.IGNORECASE)
        
        # Remove any remaining HTML tags
        preview = re.sub(r'<[^>]+>', '', preview)
        
        # Decode HTML entities
        from html import unescape
        preview = unescape(preview)
        
        # Clean up excessive whitespace
        preview = re.sub(r'\n{3,}', '\n\n', preview)
        
        return preview.strip()

    # ---------- GOOGLE DOCS LOADER ----------
    def load_from_google_docs(self):
        """Load subject and body from a Google Doc."""
        doc_input = self.doc_entry.get().strip()
        
        if not doc_input:
            messagebox.showwarning("Missing Input", "Please enter a Google Docs URL or Document ID.")
            return
        
        try:
            # Disable entry during loading (but keep the text visible)
            self.doc_entry.config(state="disabled")
            self.root.update_idletasks()
            
            # Fetch document content
            result = read_google_doc(doc_input)
            
            # Store the HTML version for reference
            self.loaded_body_html = result.get('body_html', '')
            
            # Convert HTML to Markdown for easy editing
            body_markdown = html_to_markdown(self.loaded_body_html) if self.loaded_body_html else result['body']
            self.loaded_body_text = body_markdown
            
            # Check for missing Subject or Body and show warnings
            warnings = []
            if not result['subject']:
                warnings.append("Subject is empty")
            if not body_markdown:
                warnings.append("Body is empty")
            
            # Populate fields with Markdown (editable)
            self.subject_entry.delete(0, tk.END)
            self.subject_entry.insert(0, result['subject'])
            
            self.body_text.delete("1.0", tk.END)
            self.body_text.insert("1.0", body_markdown)
            
            # Update preview
            self.update_preview()
            
            # Reset the modified flag after insertion
            self.body_text.edit_modified(False)
            
            # Cache the successfully loaded doc URL
            save_cache("last_doc_url", doc_input)
            
            # Show success or warning message
            if warnings:
                messagebox.showwarning(
                    "Partial Load",
                    f"Document loaded, but the following fields are missing:\n" + "\n".join([f"• {w}" for w in warnings]) +
                    "\n\nPlease verify your document format."
                )
            else:
                messagebox.showinfo("Success", "Document loaded successfully!")
            
        except Exception as e:
            messagebox.showerror("Load Error", f"Failed to load document:\n{str(e)}")
        finally:
            # Restore input field
            self.doc_entry.config(state="normal")

    def show_formatting_help(self):
        """Show a dialog with markdown formatting help."""
        help_text = """Markdown Formatting Guide

• Bold Text
  **your text** or __your text__
  Example: **Hello World**

• Italic Text
  *your text*
  Example: *Hello World*

• Bold + Italic
  ***your text***
  Example: ***Hello World***

• Underline
  __your text__
  Example: __Hello World__

• Strikethrough
  ~~your text~~
  Example: ~~Hello World~~

• Links
  [link text](https://url.com)
  Example: [Google](https://google.com)

• Headings
  # Heading 1
  ## Heading 2
  ### Heading 3

• Bullet Lists
  • Item 1
  • Item 2
  or
  * Item 1
  * Item 2

• Paragraphs
  Separate with blank lines
  
  New paragraph starts here
"""
        
        # Create a custom dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Markdown Formatting Help")
        dialog.geometry("500x600")
        
        # Make dialog modal
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Main frame
        main_frame = ttk.Frame(dialog)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        ttk.Label(
            main_frame,
            text="📝 Markdown Formatting Guide",
            font=("Helvetica", 16, "bold")
        ).pack(pady=(0, 10))
        
        # Scrolled text with help content
        text_frame = ttk.Frame(main_frame)
        text_frame.pack(fill="both", expand=True, pady=(0, 20))
        
        help_display = scrolledtext.ScrolledText(
            text_frame,
            font=("Helvetica", 11),
            wrap="word"
        )
        help_display.pack(fill="both", expand=True)
        help_display.insert("1.0", help_text)
        help_display.config(state="disabled")
        
        # Close button
        ttk.Button(
            main_frame,
            text="Got it!",
            command=dialog.destroy
        ).pack(pady=(0, 0))

    # ---------- HELPER ----------
    def get_logged_in_email(self):
        """Return the Gmail account currently authenticated."""
        return get_authenticated_user_email(self.service)