"""Google Sheets import panel component."""

import tkinter as tk
from tkinter import messagebox, ttk

from utils import save_cache, load_cache


class GoogleSheetsPanel:
    """Handles Google Sheets recipients import functionality."""
    
    def __init__(self, parent_frame, root, recipients_text):
        """
        Initialize the Google Sheets panel.
        
        Args:
            parent_frame: Parent tkinter frame to add this panel to
            root: Root window for update_idletasks and after_idle
            recipients_text: Recipients text widget to populate
        """
        self.parent_frame = parent_frame
        self.root = root
        self.recipients_text = recipients_text
        
        self.sheet_entry = None
        self.column_var = None
        self.column_combo = None
        self.load_columns_btn = None
        self.sheets_status_label = None
        
        self.create_ui()
    
    def create_ui(self):
        """Create the Google Sheets import UI."""
        sheets_frame = ttk.LabelFrame(
            self.parent_frame,
            text="📊 Load from Google Sheets",
            padding=(15, 10)
        )
        sheets_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Label(
            sheets_frame,
            text="Enter Spreadsheet ID or URL",
            font=("Helvetica", 9)
        ).pack(anchor="w", pady=(0, 8))
        
        sheets_input_frame = ttk.Frame(sheets_frame)
        sheets_input_frame.pack(fill="x", pady=(0, 8))
        
        self.sheet_entry = ttk.Entry(
            sheets_input_frame,
            font=("Helvetica", 11)
        )
        self.sheet_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        # Load cached sheet URL if available
        cached_sheet_url = load_cache("last_sheet_url", "")
        if cached_sheet_url:
            self.sheet_entry.insert(0, cached_sheet_url)
        
        # Column selection frame
        column_select_frame = ttk.Frame(sheets_frame)
        column_select_frame.pack(fill="x", pady=(0, 8))
        
        ttk.Label(
            column_select_frame,
            text="Column:",
            font=("Helvetica", 10)
        ).pack(side="left", padx=(0, 5))
        
        self.column_var = tk.StringVar()
        self.column_combo = ttk.Combobox(
            column_select_frame,
            textvariable=self.column_var,
            state="readonly",
            width=15
        )
        self.column_combo.pack(side="left", padx=(0, 10))
        
        # Load cached column if available
        cached_column = load_cache("last_sheet_column", "")
        if cached_column:
            self.column_var.set(cached_column)
        
        # Bind column selection to save to cache
        self.column_combo.bind("<<ComboboxSelected>>", self.on_column_selected)
        
        # Load columns button (store reference for dynamic text)
        self.load_columns_btn = ttk.Button(
            column_select_frame,
            text="🔄 Reload Columns" if cached_column else "🔄 Load Columns",
            command=self.load_sheet_columns
        )
        self.load_columns_btn.pack(side="left", padx=(0, 10))
        
        # Import button
        import_recipients_btn = ttk.Button(
            column_select_frame,
            text="📥 Import Recipients",
            command=self.load_recipients_from_sheet
        )
        import_recipients_btn.pack(side="left")
        
        # Status labels for Sheets
        sheets_status_frame = ttk.Frame(sheets_frame)
        sheets_status_frame.pack(fill="x", pady=(5, 0))
        
        self.sheets_status_label = ttk.Label(
            sheets_status_frame,
            text="",
            font=("Helvetica", 9),
            foreground="green"
        )
        self.sheets_status_label.pack(anchor="w")
        
        # Auto-load columns if sheet URL is cached (run after UI is ready)
        if cached_sheet_url:
            self.root.after_idle(lambda: self.load_sheet_columns(silent=True))
    
    def load_sheet_columns(self, silent=False):
        """
        Load column headers from the Google Sheet.
        
        Args:
            silent: If True, don't show success status message (for auto-load on startup)
        """
        sheet_input = self.sheet_entry.get().strip()
        
        if not sheet_input:
            if not silent:
                messagebox.showwarning("Missing Input", "Please enter a Google Sheets URL or Spreadsheet ID.")
            return
        
        try:
            # Disable entry during loading
            self.sheet_entry.config(state="disabled")
            self.root.update_idletasks()
            
            # Fetch column headers
            from sheets_service import get_sheet_columns, column_number_to_letter
            headers = get_sheet_columns(sheet_input)
            
            if not headers:
                messagebox.showwarning("No Headers", "No column headers found in the sheet.")
                return
            
            # Create column options with letter and header name
            column_options = []
            for i, header in enumerate(headers):
                col_letter = column_number_to_letter(i)
                column_options.append(f"{col_letter}: {header}")
            
            # Update combobox
            self.column_combo['values'] = column_options
            
            # Cache the successfully loaded sheet URL
            save_cache("last_sheet_url", sheet_input)
            
            # Select first column by default if none cached
            if column_options and not self.column_var.get():
                self.column_combo.current(0)
                self.column_var.set(column_options[0])
            
            # Update button text to Reload
            self.load_columns_btn.config(text="🔄 Reload Columns")
            
            # Show success status (unless silent auto-load)
            if not silent:
                self.sheets_status_label.config(
                    text=f"✓ Found {len(headers)} column{'s' if len(headers) != 1 else ''}!",
                    foreground="green"
                )
            
        except Exception as e:
            self.sheets_status_label.config(text="", foreground="green")  # Clear status
            # Skip error dialogs during silent auto-load
            if not silent:
                error_msg = str(e)
                # Provide friendly error message for 404
                if "404" in error_msg and "not found" in error_msg.lower():
                    messagebox.showerror(
                        "Spreadsheet Not Found",
                        "The spreadsheet could not be found. Please check that:\n\n"
                        "• The spreadsheet ID or URL is correct\n"
                        "• The spreadsheet exists and hasn't been deleted\n"
                        "• You have permission to access this spreadsheet\n\n"
                        "Tip: Make sure the spreadsheet is shared with your Google account."
                    )
                elif "403" in error_msg and "insufficient" in error_msg.lower():
                    messagebox.showerror(
                        "Permission Required",
                        "You need to grant permission to access Google Sheets.\n\n"
                        "The app will now close. Please restart and sign in again to grant the required permissions."
                    )
                else:
                    messagebox.showerror("Load Error", f"Failed to load columns:\n{error_msg}")
        finally:
            # Restore input field
            self.sheet_entry.config(state="normal")
    
    def load_recipients_from_sheet(self):
        """Load recipients from the selected column in the Google Sheet."""
        sheet_input = self.sheet_entry.get().strip()
        selected_column = self.column_var.get()
        
        if not sheet_input:
            messagebox.showwarning("Missing Input", "Please enter a Google Sheets URL or Spreadsheet ID.")
            return
        
        if not selected_column:
            messagebox.showwarning("Missing Selection", "Please select a column first. Click 'Load Columns' to see available columns.")
            return
        
        try:
            # Extract column letter from selection (format is "A: Header Name")
            col_letter = selected_column.split(':')[0].strip()
            
            # Disable UI during loading
            self.sheet_entry.config(state="disabled")
            self.column_combo.config(state="disabled")
            self.root.update_idletasks()
            
            # Fetch recipients from column
            from sheets_service import read_column_from_sheet
            recipients = read_column_from_sheet(sheet_input, col_letter)
            
            if not recipients:
                messagebox.showwarning("No Data", "No email addresses found in the selected column.")
                return
            
            # Clear existing recipients
            self.recipients_text.delete("1.0", tk.END)
            
            # Insert recipients (one per line)
            self.recipients_text.insert("1.0", "\n".join(recipients))
            
            # Show success status
            self.sheets_status_label.config(
                text=f"✓ Imported {len(recipients)} email address{'es' if len(recipients) != 1 else ''}!",
                foreground="green"
            )
            
        except Exception as e:
            self.sheets_status_label.config(text="", foreground="green")  # Clear status
            error_msg = str(e)
            # Provide friendly error message for 404
            if "404" in error_msg and "not found" in error_msg.lower():
                messagebox.showerror(
                    "Spreadsheet Not Found",
                    "The spreadsheet could not be found. Please check that:\n\n"
                    "• The spreadsheet ID or URL is correct\n"
                    "• The spreadsheet exists and hasn't been deleted\n"
                    "• You have permission to access this spreadsheet\n\n"
                    "Tip: Make sure the spreadsheet is shared with your Google account."
                )
            else:
                messagebox.showerror("Import Error", f"Failed to import recipients:\n{error_msg}")
        finally:
            # Restore UI
            self.sheet_entry.config(state="normal")
            self.column_combo.config(state="readonly")
    
    def on_column_selected(self, event=None):
        """Cache the selected column when user makes a selection."""
        selected = self.column_var.get()
        if selected:
            save_cache("last_sheet_column", selected)
            # Update button text to Reload since we now have a selection
            self.load_columns_btn.config(text="🔄 Reload Columns")
