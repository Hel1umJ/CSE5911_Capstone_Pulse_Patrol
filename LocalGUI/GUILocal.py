import tkinter as tk
from tkinter import ttk
import tkinter.messagebox as mb

class MedicalDeviceGUI:
    def __init__(self, master):
        self.master = master
        master.title("Medical Device GUI")

        # Create and place widgets
        self.label = tk.Label(master, text="Patient Data")
        self.label.grid(row=0, column=0, columnspan=2)

        self.name_label = tk.Label(master, text="Name:")
        self.name_label.grid(row=1, column=0)
        self.name_entry = tk.Entry(master)
        self.name_entry.grid(row=1, column=1)

        self.id_label = tk.Label(master, text="Patient ID:")
        self.id_label.grid(row=2, column=0)
        self.id_entry = tk.Entry(master)
        self.id_entry.grid(row=2, column=1)

        self.submit_button = tk.Button(master, text="Submit", command=self.submit_data)
        self.submit_button.grid(row=3, column=0, columnspan=2)

    def submit_data(self):
        name = self.name_entry.get()
        patient_id = self.id_entry.get()

        # Perform data validation and processing here
        if not name or not patient_id:
            mb.showerror("Error", "Please enter all fields")
            return

        # Simulate data processing
        mb.showinfo("Success", f"Data submitted for {name} (ID: {patient_id})")

root = tk.Tk()
app = MedicalDeviceGUI(root)


if(__name__ == "__main__"):
    root.mainloop()
