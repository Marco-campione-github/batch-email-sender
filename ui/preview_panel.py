"""Preview panel component for email HTML preview."""

import tkinter as tk
from tkinter import scrolledtext, ttk
import re
from html import unescape

from html_converter import markdown_to_html


class PreviewPanel:
    """Handles the HTML preview functionality for email body."""
    
    def __init__(self, parent_frame, root, body_paned, body_text):
        """
        Initialize the preview panel.
        
        Args:
            parent_frame: Parent frame (body_paned will be added here)
            root: Root window for focus management
            body_paned: PanedWindow widget to add/remove preview
            body_text: Body text widget to get content from
        """
        self.parent_frame = parent_frame
        self.root = root
        self.body_paned = body_paned
        self.body_text = body_text
        
        self.right_frame = None
        self.preview_text = None
        self.preview_button = None
        self.preview_visible = False
        
        self.create_preview_widgets()
    
    def create_preview_widgets(self):
        """Create the preview widgets (but don't show them yet)."""
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
    
    def set_preview_button(self, button):
        """Set the reference to the preview toggle button."""
        self.preview_button = button
    
    def toggle_preview(self):
        """Toggle the HTML preview pane visibility."""
        if self.preview_visible:
            # Hide preview
            self.body_paned.remove(self.right_frame)
            if self.preview_button:
                self.preview_button.config(text="Show Preview")
            self.preview_visible = False
        else:
            # Show preview
            self.body_paned.add(self.right_frame)
            if self.preview_button:
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
        except Exception:
            # Silently handle preview errors
            pass
    
    @staticmethod
    def render_html_for_preview(html):
        """Convert HTML to a readable preview format (simplified rendering)."""
        if not html:
            return ""
        
        # This is a simplified text-based preview
        # Remove HTML tags but show structure
        preview = html
        
        # Show headings with emphasis
        for i in range(1, 7):
            preview = re.sub(
                f'<h{i}[^>]*>(.*?)</h{i}>',
                lambda m: f"\n{'=' * (7-i)} {m.group(1).upper()} {'=' * (7-i)}\n",
                preview,
                flags=re.IGNORECASE | re.DOTALL
            )
        
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
        preview = re.sub(
            r'<a[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>',
            r'\2 (→ \1)',
            preview,
            flags=re.IGNORECASE | re.DOTALL
        )
        
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
        preview = unescape(preview)
        
        # Clean up excessive whitespace
        preview = re.sub(r'\n{3,}', '\n\n', preview)
        
        return preview.strip()
