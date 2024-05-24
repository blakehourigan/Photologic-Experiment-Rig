import tkinter as tk
import re
import logging
from tkinter import ttk, messagebox, simpledialog
from typing import TYPE_CHECKING

from gui_utils import GUIUtils

if TYPE_CHECKING:
    from program_control import ProgramController

class ValveTestWindow:
    def __init__(self, controller: 'ProgramController'):
        self.controller = controller
        self.master = controller.main_gui.root
        self.top = None

        self.num_valves_to_test = tk.IntVar(value=8)
        self.desired_volume = tk.DoubleVar(value=5)  # desired volume to dispense in ul

        self.valve_opening_times: list[int] = []
        self.ul_dispensed: list[float] = []

        self.setup_trace_variables()
        logging.debug("ValveTestWindow initialized.")

    def input_popup(self, valve, init=False, side=0) -> float:
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
                    logging.warning("User cancelled input. Returning 0.0.")
                    return 0.0

            # Check if the input matches the "d.dd" pattern
            if pattern.match(user_input):
                try:
                    value = float(user_input)
                    logging.debug(f"Valid input received: {value}")
                    return value  # Attempt to return the user input as a float
                except ValueError:
                    logging.error("ValueError: Invalid input. Please enter a value in the format d.dd.")
            else:
                logging.error("Invalid input. Please enter a value in the format d.dd.")

    def setup_trace_variables(self):
        self.num_valves_to_test.trace_add("write", self.validate_and_update)
        self.desired_volume.trace_add("write", self.validate_and_update)
        logging.debug("Trace variables set up.")

    def testing_aborted(self):
        messagebox.showinfo("Testing Aborted", "Testing has been aborted. Run testing again or continue with the experiment.")
        logging.info("Testing aborted by user.")

    def ask_continue(self):
        response = messagebox.askyesno("Continue", "Are you ready to continue?")
        logging.debug(f"User prompt to continue: {response}")
        return response

    def show_window(self):
        if self.controller.get_num_stimuli() > 0:
            if self.top and self.top.winfo_exists():
                self.top.lift()
            else:
                self.create_window()
                self.configure_window()
                self.create_widgets()
                self.auto_resize_and_center()
                window_icon_path = self.controller.experiment_config.get_window_icon_path()
                GUIUtils.set_program_icon(self.top, icon_path=window_icon_path)
                logging.debug("ValveTestWindow shown.")
        else:
            messagebox.showinfo("Error", "Please add stimuli before proceeding.")
            logging.warning("Attempted to show ValveTestWindow without stimuli.")

    def create_window(self):
        self.top = tk.Toplevel(self.master)
        self.top.title("Valve Testing")
        self.top.bind("<Control-w>", lambda e: self.top.destroy())
        logging.debug("ValveTestWindow created.")

    def configure_window(self):
        for i in range(4):
            self.top.grid_rowconfigure(i, weight=1)
        self.top.grid_columnconfigure(0, weight=1)
        logging.debug("ValveTestWindow configured.")

    def create_widgets(self):
        self.create_label_and_entry("Number of Valves to Test", self.num_valves_to_test, 0)
        self.create_label_and_entry("Desired Volume to Dispense (ul)", self.desired_volume, 1)
        self.create_valve_test_table()
        self.create_buttons()
        logging.debug("Widgets created for ValveTestWindow.")

    def create_label_and_entry(self, label_text, variable, row):
        frame = tk.Frame(self.top, highlightbackground='black', highlightthickness=1)
        frame.grid(row=row, padx=10, pady=5, sticky="ew")
        tk.Label(frame, text=label_text, font=("Helvetica", 16)).pack(side="left")
        tk.Entry(frame, textvariable=variable, font=("Helvetica", 16)).pack(side="right", fill="x", expand=True)
        frame.grid_columnconfigure(1, weight=1)
        logging.debug(f"Label and entry created for {label_text}.")

    def validate_and_update(self, *args):
        try:
            # Attempt to get the value to ensure it's a valid float as expected
            self.num_valves_to_test.get()
            # If successful, call the function to update/create the valve test table
            self.create_valve_test_table()
            logging.debug("Valve test table updated.")
        except tk.TclError:
            # If it fails to get a valid number (empty string or invalid data), do not update the table
            logging.warning("Invalid data for valve test table update.")

    def create_valve_test_table(self, side_one_valve_durations = None, side_two_valve_durations = None, side_one_ul_dispensed = None, side_two_ul_dispensed = None):
        # this function creates and labels the testing window table that displays the information recieved from the arduino reguarding the results of the tes
        if hasattr(self, 'valve_table'):
            self.valve_table.destroy()
        self.valve_table_frame = tk.Frame(self.top, highlightbackground='black', highlightthickness=1)
        self.valve_table_frame.grid(row=2, column=0, sticky="nsew", pady=10, padx=10)
        self.valve_table = ttk.Treeview(self.valve_table_frame, columns=("Valve", "Amount Dispensed", "Valve Opening Times"), show="headings")
        self.valve_table.heading("Valve", text="Valve #")
        self.valve_table.heading("Amount Dispensed", text="Amount Dispensed Per Lick (ul)")
        self.valve_table.heading("Valve Opening Times", text="Valve Opening Time (ms)")
        self.valve_table.pack(expand=True, fill='both')

        # if the tests have been ran and we now have opening times, then update the table to show the opening times and the ul we recieved from the arduinos calculations
        if (side_one_valve_durations is not None)  or (side_two_valve_durations is not None):
            logging.debug("Updating valve test table with opening times and dispensed volumes.")
            for i in range(self.num_valves_to_test.get() // 2):
                self.valve_table.insert("", "end", values=(f"{i + 1}", f"{side_one_ul_dispensed[i] * 1000} ul", f"{side_one_valve_durations[i]} ms"))
            for i in range(self.num_valves_to_test.get() // 2):
                self.valve_table.insert("", "end", values=(f"{i + 1}", f"{side_two_ul_dispensed[i] * 1000} ul", f"{side_two_valve_durations[i]} ms"))
        else:
            for i in range(self.num_valves_to_test.get()):
                self.valve_table.insert("", "end", values=(f"{i + 1}", f"{self.desired_volume.get()} ul", "0.00 s"))
            logging.debug("Initial valve test table created.")

    def create_buttons(self):
        start_test_button_frame = tk.Frame(self.top, highlightbackground='black', highlightthickness=1)
        start_test_button_frame.grid(row=3, column=0, pady=10, padx=10, sticky="ew")
        start_test_button = tk.Button(start_test_button_frame, text="Start Testing", command=lambda: self.controller.run_valve_test(self.num_valves_to_test), bg="green", font=("Helvetica", 16))
        start_test_button.pack(fill='both', expand=True)
        logging.debug("Buttons created for ValveTestWindow.")

    def collect_user_inputs(self):
        user_inputs = []  # Initialize an empty list to store the inputs
        for valve_number in range(1, 9):  # Loop to collect 8 numbers
            user_input = self.input_popup(valve_number)  # Call the existing input_popup method
            if user_input is not None:
                user_inputs.append(user_input)  # Add the valid input to the list
            else:
                messagebox.showwarning("Input Cancelled", "Operation cancelled by user.")
                logging.warning("User input collection cancelled.")
                return  # Exit if the user cancels the input dialog

        self.controller.valve_test_logic.update_and_send_opening_times(8, user_inputs[:4], 1)
        self.controller.valve_test_logic.update_and_send_opening_times(8, user_inputs[4:-1], 2)
        logging.debug(f"Collected user inputs: {user_inputs}")
        print(user_inputs)  # For debugging: Print the collected inputs

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
        logging.debug("Auto-resized and centered ValveTestWindow.")

    def set_valve_opening_times(self, new_times):
        self.valve_opening_times = new_times
        logging.debug(f"Set new valve opening times: {new_times}")

    def set_ul_dispensed(self, new_volumes):
        self.ul_dispensed = new_volumes
        logging.debug(f"Set new dispensed volumes: {new_volumes}")
