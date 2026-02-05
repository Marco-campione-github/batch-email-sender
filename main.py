import tkinter as tk
from ui import BulkMailerUI

def main():
    root = tk.Tk()
    root.geometry("800x600")
    
    # Apply Sun Valley theme matching system theme (lazy load)
    try:
        import sv_ttk
        import darkdetect
        theme = darkdetect.theme()
        if theme:
            sv_ttk.set_theme(theme)
    except ImportError:
        pass  # Continue without theme if not available
    
    BulkMailerUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
