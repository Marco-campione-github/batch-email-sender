"""Google Docs import panel component."""

import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk

from docs_service import read_google_doc
from utils import save_cache, load_cache
from html_converter import html_to_markdown


class GoogleDocsPanel:
    """Handles Google Docs document import functionality."""
    
    def __init__(self, parent_frame, root, subject_entry, body_text, update_preview_callback):
        """
        Initialize the Google Docs panel.
        
        Args:
            parent_frame: Parent tkinter frame to add this panel to
            root: Root window for update_idletasks
            subject_entry: Subject entry widget to populate
            body_text: Body text widget to populate
            update_preview_callback: Callback to update preview after loading
        """
        self.parent_frame = parent_frame
        self.root = root
        self.subject_entry = subject_entry
        self.body_text = body_text
        self.update_preview_callback = update_preview_callback
        
        self.doc_entry = None
        self.docs_status_label = None
        self.loaded_body_html = None
        self.loaded_body_text = None
        
        self.create_ui()
    
    def create_ui(self):
        """Create the Google Docs import UI."""
        docs_frame = ttk.LabelFrame(
            self.parent_frame,
            text="📄 Load from Google Docs",
            padding=(15, 10)
        )
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
        
        # Status label for Google Docs
        self.docs_status_label = ttk.Label(
            docs_frame,
            text="",
            font=("Helvetica", 9),
            foreground="green"
        )
        self.docs_status_label.pack(anchor="w", pady=(5, 0))
    
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
            if self.update_preview_callback:
                self.update_preview_callback()
            
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
                self.docs_status_label.config(text="✓ Document loaded (with warnings)", foreground="orange")
            else:
                self.docs_status_label.config(text="✓ Document loaded successfully!", foreground="green")
            
        except Exception as e:
            self.docs_status_label.config(text="", foreground="green")  # Clear status
            error_msg = str(e)
            # Provide friendly error message for 404
            if "404" in error_msg and "not found" in error_msg.lower():
                messagebox.showerror(
                    "Document Not Found",
                    "The document could not be found. Please check that:\n\n"
                    "• The document ID or URL is correct\n"
                    "• The document exists and hasn't been deleted\n"
                    "• You have permission to access this document\n\n"
                    "Tip: Make sure the document is shared with your Google account."
                )
            else:
                messagebox.showerror("Load Error", f"Failed to load document:\n{error_msg}")
        finally:
            # Restore input field
            self.doc_entry.config(state="normal")
    
    @staticmethod
    def show_formatting_help(root):
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
        dialog = tk.Toplevel(root)
        dialog.title("Markdown Formatting Help")
        dialog.geometry("500x600")
        
        # Make dialog modal
        dialog.transient(root)
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
