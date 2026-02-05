"""
UI module for Batch Email Sender application.

This module has been refactored into smaller, focused components in the ui/ directory:
- auth_frame.py: Authentication UI
- email_frame.py: Main email composition UI
- google_docs_panel.py: Google Docs import functionality
- google_sheets_panel.py: Google Sheets recipients import
- preview_panel.py: HTML preview functionality
- main_window.py: Application coordinator

This file now serves as the backward-compatible entry point.
"""

from ui import BulkMailerUI

# For backward compatibility, export the main class
__all__ = ['BulkMailerUI']
