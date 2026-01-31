import tkinter as tk
from ui import BulkMailerUI

def main():
    root = tk.Tk()
    root.geometry("800x600")
    BulkMailerUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
