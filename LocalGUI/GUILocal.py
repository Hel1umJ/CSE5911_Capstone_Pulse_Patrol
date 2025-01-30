import tkinter as tk
from tkinter import ttk

COLORS = {
    "fg": "black",
    "red": "red",
    "highlight": "lightgray",
    "gray": "gray"
}

FONTS = {
    "title": ("Arial", 14, "bold"),
    "subtitle": ("Arial", 12, "bold"),
    "label": ("Arial", 10),
    "bold_label": ("Arial", 10, "bold"),
    "footer": ("Arial", 10, "italic")
}

def create_gui():
    root = tk.Tk()
    root.title("NORA")
    root.geometry("800x600")
    root.configure(bg="white")
    root.minsize(600, 425)

    #red border frame
    borderFrame = tk.Frame(root, bg="red", bd=2)
    borderFrame.pack(expand=True, fill=tk.BOTH, padx=5, pady=5)

    #main tkinter frame that all widgets will be added to
    contentFrame = tk.Frame(borderFrame, bg="white")
    contentFrame.pack(expand=True, fill=tk.BOTH, padx=4, pady=4)

    #set contentFrame to have 5 rows (0–4), 2 columns (0–1); Weight: 0 (dont expand to fill), 1 (expand to fill space)
    contentFrame.rowconfigure(0, weight=1)
    contentFrame.rowconfigure(1, weight=1)
    contentFrame.rowconfigure(2, weight=1)
    contentFrame.rowconfigure(3, weight=1)
    contentFrame.rowconfigure(4, weight=1)

    contentFrame.columnconfigure(0, weight=1)  # Vitals (left column)
    contentFrame.columnconfigure(1, weight=1)  # Patient Info & Flow (right column)


    return root

if __name__ == "__main__":
    app = create_gui()
    app.mainloop()
