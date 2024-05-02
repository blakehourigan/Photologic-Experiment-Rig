import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import re

class ValveTestWindow:
    def __init__(self, controller):
        self.controller = controller
        self.master = controller.main_gui.root
        self.top = None

        self.num_valves_to_test = tk.IntVar(value=8)
        self.desired_volume = tk.DoubleVar(value=5)  # desired volume to dispense in ul

        self.valve_opening_times = []
        self.ul_dispensed = []

        self.setup_trace_variables()

    def input_popup(self, valve, init = False, side = 0) -> float:
        pattern = re.compile(r'\b\d{2}\.\d{2}\b')  # Compile the regex pattern for "d.dd"
        while True:  # Loop until valid input is received
            if init:
                string = "Enter the volume in cm^3 for the starting weight of the beaker for side " + str(side) 
            else: 
                string = "Enter the measured volume cm^3 for valve " + str(valve)
            user_input = simpledialog.askstring("Measured Volume", string, parent=self.top)
            
            if user_input is None:
                response = messagebox.askyesno("Input Cancelled", "No input provided. Would you like to try again?")
                if response:
                    continue  # If the user clicks "Yes", continue to prompt again
                else:
                    return 0.0


            # Check if the input matches the "d.dd" pattern
            if pattern.match(user_input):
                try:
                    return float(user_input)  # Attempt to return the user input as a float
                except ValueError:
                    # This block might not be necessary anymore due to regex check,
                    # but it's kept for safety in case of unexpected input handling.
                    print("Invalid input. Please enter a value in the format d.dd.")
            else:
                print("Invalid input. Please enter a value in the format d.dd.")

    def setup_trace_variables(self):
        self.num_valves_to_test.trace_add("write", self.validate_and_update)
        self.desired_volume.trace_add("write", self.validate_and_update)

    def testing_aborted(self):
        messagebox.showinfo("Testing Aborted", "Testing has been aborted. Run testing again or continue with the experiment.")

        
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
        for i in range(4):
            self.top.grid_rowconfigure(i, weight=1)
        self.top.grid_columnconfigure(0, weight=1)

    def create_widgets(self):
        self.create_label_and_entry("Number of Valves to Test", self.num_valves_to_test, 0)
        self.create_label_and_entry("Desired Volume to Dispense (ul)", self.desired_volume, 1)
        self.create_valve_test_table()
        self.create_buttons()

    def create_label_and_entry(self, label_text, variable, row):
        frame = tk.Frame(self.top, highlightbackground='black', highlightthickness=1)
        frame.grid(row=row, padx=10, pady=5, sticky="ew")
        tk.Label(frame, text=label_text, font=("Helvetica", 16)).pack(side="left")
        tk.Entry(frame, textvariable=variable, font=("Helvetica", 16)).pack(side="right", fill="x", expand=True)
        frame.grid_columnconfigure(1, weight=1)

    def validate_and_update(self, *args):
        try:
            # Attempt to get the value to ensure it's a valid float as expected
            self.num_valves_to_test.get()
            # If successful, call the function to update/create the valve test table
            self.create_valve_test_table()
        except tk.TclError:
            # If it fails to get a valid number (empty string or invalid data), do not update the table
            pass


    def create_valve_test_table(self):
        # this function creates and labels the testing window table that displays the information recieved from the arduino reguarding the results of the tes
        if hasattr(self, 'valve_table'):
            self.valve_table.destroy()
        self.valve_table_frame = tk.Frame(self.top, highlightbackground='black', highlightthickness=1)
        self.valve_table_frame.grid(row=2, column=0, sticky="nsew", pady=10, padx=10)
        self.valve_table = ttk.Treeview(self.valve_table_frame, columns=("Valve","Amount Dispensed", "Valve Opening Times"), show="headings")
        self.valve_table.heading("Valve", text="Valve #")
        self.valve_table.heading("Amount Dispensed", text="Amount Dispensed Per Lick (ul)")
        self.valve_table.heading("Valve Opening Times", text="Valve Opening Time (ms)")
        self.valve_table.pack(expand=True, fill='both')

        # if the tests have been ran and we now have opening times, then update the table to show the opening times and the ul we recieved from the arduinos calculations
        
        if len(self.valve_opening_times) > 0:
            print(self.ul_dispensed)
            for i in range(self.num_valves_to_test.get() // 2 ):
                self.valve_table.insert("", "end", values=(f"{i+1}", f"{self.ul_dispensed[i] * 1000} ul", f"{self.valve_opening_times[i]} ms"))
            for i in range(self.num_valves_to_test.get() // 2 ):   
                self.valve_table.insert("", "end", values=(f"{i+1}", f"{self.ul_dispensed[i+4] * 1000} ul", f"{self.valve_opening_times[i+4]} ms"))
        else:
                
            for i in range(self.num_valves_to_test.get()):
                self.valve_table.insert("", "end", values=(f"{i+1}", f"{self.desired_volume.get()} ul", "0.00 s"))
            

    def create_buttons(self):
        start_test_button_frame = tk.Frame(self.top, highlightbackground='black', highlightthickness=1)
        start_test_button_frame.grid(row=3, column=0, pady=10, padx=10, sticky="ew")
        start_test_button = tk.Button(start_test_button_frame, text="Start Testing", command= lambda: self.controller.run_valve_test(self.num_valves_to_test), bg="green", font=("Helvetica", 16))
        start_test_button.pack(fill='both', expand=True)

    def collect_user_inputs(self):
        user_inputs = []  # Initialize an empty list to store the inputs
        for valve_number in range(1, 9):  # Loop to collect 8 numbers
            user_input = self.input_popup(valve_number)  # Call the existing input_popup method
            if user_input is not None:
                user_inputs.append(user_input)  # Add the valid input to the list
            else:
                messagebox.showwarning("Input Cancelled", "Operation cancelled by user.")
                return  # Exit if the user cancels the input dialog
            
        self.controller.valve_test_logic.update_and_send_opening_times(8, user_inputs[:4], 1)
        self.controller.valve_test_logic.update_and_send_opening_times(8, user_inputs[4:-1], 2)
        print(user_inputs)  # For debugging: Print the collected inputs
        # You can now use the 'user_inputs' list as needed in your application


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

    def set_valve_opening_times(self, new_times):
        self.valve_opening_times = new_times

    def set_ul_dispensed(self, new_volumes):
        self.ul_dispensed = new_volumes
