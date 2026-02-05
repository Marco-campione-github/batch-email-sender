import tkinter as tk
import sv_ttk
import darkdetect
from ui import BulkMailerUI

def main():
    root = tk.Tk()
    root.geometry("800x600")
    
    # Apply Sun Valley theme matching system theme
    sv_ttk.set_theme(darkdetect.theme())
    
    BulkMailerUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
