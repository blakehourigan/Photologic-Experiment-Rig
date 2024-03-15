import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

class ValveTestWindow:
    def __init__(self, controller):
        self.controller = controller
        self.master = controller.main_gui.root
        self.top = None

        self.num_valves_to_test = tk.IntVar(value=4)
        self.desired_volume = tk.DoubleVar(value=0.05)  # desired volume to dispense in ml
        self.number_test_runs = tk.IntVar(value=10)

        self.setup_trace_variables()

        self.min_valve = 1
        self.max_valve = 8

    def input_popup(self, valve ) -> float:
        while True:  # Loop until valid input is received
            user_input = simpledialog.askstring("Measured Volume", "Enter the measured volume for valve: " + str(valve))
            
            if user_input is None:
                print("Input canceled, please enter a value.")
                continue  # If the user cancels, prompt again
            
            try:
                return float(user_input)  # Attempt to return the user input as a float
            except ValueError:
                print("Invalid input. Please enter a valid number.")
                # The loop will continue, prompting the user again

    def setup_trace_variables(self):
        self.num_valves_to_test.trace_add("write", self.validate_and_update)
        self.desired_volume.trace_add("write", self.validate_and_update)

    def tesing_aborted(self):
        messagebox("Testing Aborted", "Testing has been aborted, run testing again or continue with experiement.")

    def ask_continue(self):
        return messagebox.askyesno("Continue", "Are you ready to continue?")

    def show_window(self):
        if self.controller.data_mgr.num_stimuli.get() > 0:
            if self.top and self.top.winfo_exists():
                self.top.lift()
            else:
                self.create_window()
                self.configure_window()
                self.create_widgets()
                self.auto_resize_and_center()
        else:
            messagebox.showinfo("Error", "Please add stimuli before proceeding.")

    def create_window(self):
        self.top = tk.Toplevel(self.master)
        self.top.title("Valve Testing")
        self.top.bind("<Control-w>", lambda e: self.top.destroy())

    def configure_window(self):
        for i in range(12):
            self.top.grid_rowconfigure(i, weight=1)
        self.top.grid_columnconfigure(0, weight=1)

    def create_widgets(self):
        self.create_label_and_entry("Number of Valves to Test", self.num_valves_to_test, 0)
        self.create_label_and_entry("Desired Volume to Dispense (ml)", self.desired_volume, 1)
        self.create_valve_test_table()
        self.create_buttons()

    def create_label_and_entry(self, label_text, variable, row):
        frame = tk.Frame(self.top, highlightbackground='black', highlightthickness=1)
        frame.grid(row=row, padx=10, pady=5, sticky="ew")
        tk.Label(frame, text=label_text, font=("Helvetica", 16)).pack(side="left")
        tk.Entry(frame, textvariable=variable, font=("Helvetica", 16)).pack(side="right", fill="x", expand=True)
        frame.grid_columnconfigure(1, weight=1)

    def validate_and_update(self, *args):
        self.create_valve_test_table()

    def create_valve_test_table(self):
        if hasattr(self, 'valve_table'):
            self.valve_table.destroy()
        self.valve_table_frame = tk.Frame(self.top, highlightbackground='black', highlightthickness=1)
        self.valve_table_frame.grid(row=2, column=0, sticky="nsew", pady=10, padx=10)
        self.valve_table = ttk.Treeview(self.valve_table_frame, columns=("Amount Dispensed", "Average Opening Time"), show="headings")
        self.valve_table.heading("Amount Dispensed", text="Amount Dispensed (ml)")
        self.valve_table.heading("Average Opening Time", text="Average Opening Time (s)")
        self.valve_table.pack(expand=True, fill='both')

        for i in range(self.num_valves_to_test.get()):
            self.valve_table.insert("", "end", values=(f"{self.desired_volume.get()} ml", "0.00 s"))

    def create_buttons(self):
        start_test_button_frame = tk.Frame(self.top, highlightbackground='black', highlightthickness=1)
        start_test_button_frame.grid(row=3, column=0, pady=10, padx=10, sticky="ew")
        start_test_button = tk.Button(start_test_button_frame, text="Start Testing", command=self.controller.valve_test_logic.run_valve_test(self.num_valves_to_test), bg="green", font=("Helvetica", 16))
        start_test_button.pack(fill='both', expand=True)


    def auto_resize_and_center(self):
        self.top.update_idletasks()  
        # get required width and height required to neatly fit all frames and widgets 
        width = self.top.winfo_reqwidth()
        height = self.top.winfo_reqheight()
        screen_width = self.top.winfo_screenwidth()
        screen_height = self.top.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.top.geometry("{}x{}+{}+{}".format(width, height, x, y))

    def run_valve_test(self):
        # Placeholder for the method to start valve testing logic
        pass

