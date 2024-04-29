import tkinter as tk
from tkinter import messagebox

class PrimeValves:
    def __init__(self, controller):
        self.controller = controller
        self.top = tk.Toplevel(self.controller.main_gui.root)  # Use main GUI's root for Toplevel
        self.top.title("Prime Valves")
        self.top.protocol("WM_DELETE_WINDOW", self.close_window)  # Proper close handling

        self.num_valves = tk.IntVar(value=8)  # Default number of valves
        self.setup_ui()

    def setup_ui(self):
        # Label and entry for number of valves
        label = tk.Label(self.top, text="Enter number of valves to prime:")
        label.pack(pady=10)

        entry = tk.Entry(self.top, textvariable=self.num_valves)
        entry.pack()

        submit_button = tk.Button(self.top, text="Set Valves", command=self.create_valve_buttons)
        submit_button.pack(pady=10)

        # Frame to hold valve buttons
        self.valves_frame = tk.Frame(self.top)
        self.valves_frame.pack(pady=10)

    def create_valve_buttons(self):
        num_valves = self.num_valves.get()
        if num_valves < 1:
            messagebox.showerror("Error", "Please enter a valid number of valves.")
            return

        # Clear existing buttons if any
        for widget in self.valves_frame.winfo_children():
            widget.destroy()

        self.buttons = []

        # First half (1-4)
        for i in range(num_valves // 2):  # This runs 0, 1, 2, 3
            btn_text = f"Valve {i + 1}: Running"
            btn = tk.Button(self.valves_frame, text=btn_text, bg='green', 
                            command=lambda b=i: self.toggle_button(b))
            btn.pack(pady=2, padx=2, fill=tk.X)
            self.buttons.append(btn)

        # Second half (5-8)
        for i in range(num_valves // 2, num_valves):  # This runs 4, 5, 6, 7
            btn_text = f"Valve {i + 1}: Running"
            btn = tk.Button(self.valves_frame, text=btn_text, bg='green', 
                            command=lambda b=i: self.toggle_button(b))
            btn.pack(pady=2, padx=2, fill=tk.X)
            self.buttons.append(btn)


    def toggle_button(self, index):
        btn = self.buttons[index]
        if btn['text'].endswith("Running"):
            btn.configure(text=f"Valve {index+1}: Off", bg='red')
        else:
            btn.configure(text=f"Valve {index+1}: Running", bg='green')

    def close_window(self):
        self.top.destroy()