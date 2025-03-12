import tkinter as tk
import re
import logging
from tkinter import ttk, messagebox, simpledialog

from valve_testing_logic import valveTestLogic
from views.gui_common import GUIUtils


class ValveTestWindow(tk.Toplevel):
    def __init__(self):
        super().__init__()
        self.title("Valve Testing")
        self.bind("<Control-w>", lambda event: self.withdraw())

        window_icon_path = GUIUtils.get_window_icon_path()
        GUIUtils.set_program_icon(self, icon_path=window_icon_path)

        for i in range(4):
            self.grid_rowconfigure(i, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.num_valves_to_test = tk.IntVar(value=8)
        self.desired_volume = tk.DoubleVar(value=5)  # desired volume to dispense in ul

        self.valve_opening_times: list[int] = []
        self.ul_dispensed: list[float] = []

        self.create_widgets()
        GUIUtils.center_window(self)
        logging.info("ValveTestWindow shown.")
        self.setup_trace_variables()

        # we don't want to show this window until the user decides to click the corresponding button,
        # withdraw (hide) it for now
        self.withdraw()

        # create and hide manual timing adjustment window
        self.manual_adjust_window = ManualTimeAdjustment(
            self.arduino_controller.arduino_data, self.valve_selections
        )
        self.manual_adjust_window.withdraw()
        logging.info("Valve Test Window initialized.")

    def show(self):
        self.deiconify()

    def input_popup(self, valve, init=False, side=0) -> float:
        pattern = re.compile(
            r"\b\d{2}\.\d{2}\b"
        )  # Compile the regex pattern for "d.dd"
        while True:  # Loop until valid input is received
            if init:
                string = (
                    "Enter the volume in cm^3 for the starting weight of the beaker for side "
                    + str(side)
                )
            else:
                string = "Enter the measured volume cm^3 for valve " + str(valve)
            user_input = simpledialog.askstring("Measured Volume", string, parent=self)

            if user_input is None:
                response = messagebox.askyesno(
                    "Input Cancelled", "No input provided. Would you like to try again?"
                )
                if response:
                    continue  # If the user clicks "Yes", continue to prompt again
                else:
                    logging.warning("User cancelled input. Returning 0.0.")
                    return 0.0

            # Check if the input matches the "d.dd" pattern
            if pattern.match(user_input):
                try:
                    value = float(user_input)
                    logging.info(f"Valid input received: {value}")
                    return value  # Attempt to return the user input as a float
                except ValueError:
                    logging.error(
                        "ValueError: Invalid input. Please enter a value in the format d.dd."
                    )
            else:
                logging.error("Invalid input. Please enter a value in the format d.dd.")

    def setup_trace_variables(self):
        self.num_valves_to_test.trace_add("write", self.validate_and_update)
        self.desired_volume.trace_add("write", self.validate_and_update)
        logging.info("Trace variables set up.")

    def testing_aborted(self):
        messagebox.showinfo(
            "Testing Aborted",
            "Testing has been aborted. Run testing again or continue with the experiment.",
        )
        logging.info("Testing aborted by user.")

    def ask_continue(self):
        response = messagebox.askyesno("Continue", "Are you ready to continue?")
        logging.info(f"User prompt to continue: {response}")
        return response

    def create_widgets(self):
        self.create_label_and_entry(
            "Number of Valves to Test", self.num_valves_to_test, 0
        )
        self.create_label_and_entry(
            "Desired Volume to Dispense (ul)", self.desired_volume, 1
        )
        self.create_valve_test_table()
        self.create_buttons()
        logging.info("Widgets created for ValveTestWindow.")

    def create_label_and_entry(self, label_text, variable, row):
        frame = tk.Frame(self, highlightbackground="black", highlightthickness=1)
        frame.grid(row=row, padx=10, pady=5, sticky="ew")
        tk.Label(frame, text=label_text, font=("Helvetica", 16)).pack(side="left")
        tk.Entry(frame, textvariable=variable, font=("Helvetica", 16)).pack(
            side="right", fill="x", expand=True
        )
        frame.grid_columnconfigure(1, weight=1)
        logging.info(f"Label and entry created for {label_text}.")

    def validate_and_update(self, *args):
        try:
            # Attempt to get the value to ensure it's a valid float as expected
            self.num_valves_to_test.get()
            # If successful, call the function to update/create the valve test table
            self.create_valve_test_table()
            logging.info("Valve test table updated.")
        except tk.TclError:
            # If it fails to get a valid number (empty string or invalid data), do not update the table
            logging.warning("Invalid data for valve test table update.")

    def create_valve_test_table(
        self,
        side_one_valve_durations=None,
        side_two_valve_durations=None,
        side_one_ul_dispensed=None,
        side_two_ul_dispensed=None,
    ):
        # this function creates and labels the testing window table that displays the information recieved from the arduino reguarding the results of the tes
        if hasattr(self, "valve_table"):
            self.valve_table.destroy()
        self.valve_table_frame = tk.Frame(
            self, highlightbackground="black", highlightthickness=1
        )
        self.valve_table_frame.grid(row=2, column=0, sticky="nsew", pady=10, padx=10)
        self.valve_table = ttk.Treeview(
            self.valve_table_frame,
            columns=("Valve", "Amount Dispensed", "Valve Opening Times"),
            show="headings",
        )
<<<<<<< Updated upstream
        self.valve_table.heading("Valve", text="Valve #")
        self.valve_table.heading(
            "Amount Dispensed", text="Amount Dispensed Per Lick (ul)"
=======
        self.valve_table.grid(row=1, sticky="ew")

        button = tk.Button(
            self.valve_table_frame,
            text="Manual Valve Duration Override",
            command=lambda: self.manual_adjust_window.deiconify(),
            bg="light blue",
            highlightbackground="black",
            highlightthickness=1,
>>>>>>> Stashed changes
        )
        self.valve_table.heading("Valve Opening Times", text="Valve Opening Time (ms)")
        self.valve_table.pack(expand=True, fill="both")

<<<<<<< Updated upstream
        # if the tests have been ran and we now have opening times, then update the table to show the opening times and the ul we recieved from the arduinos calculations
        if (side_one_valve_durations is not None) or (
            side_two_valve_durations is not None
        ):
            logging.info(
                "Updating valve test table with opening times and dispensed volumes."
=======
        headings = [
            "Valve",
            "Amount Dispensed Per Lick (ul)",
            "Testing Opening Time of (ms)",
        ]

        self.valve_table["columns"] = headings

        # Configure the columns
        for col in self.valve_table["columns"]:
            self.valve_table.heading(col, text=col)

        arduino_data = self.arduino_controller.arduino_data
        side_one_durations, side_two_durations, date_used = (
            arduino_data.load_durations()
        )

        # insert default entries for each total valve until user selects how many
        # they want to test
        for i in range(TOTAL_VALVES // 2):
            self.table_entries[i] = self.valve_table.insert(
                "",
                "end",
                values=(
                    f"{i + 1}",
                    "Test Not Complete",
                    f"{side_one_durations[i]} ms",
                ),
            )
            self.table_entries[i + 4] = self.valve_table.insert(
                "",
                "end",
                values=(
                    f"{i + TOTAL_VALVES // 2 + 1}",
                    "Test Not Complete",
                    f"{side_one_durations[i + TOTAL_VALVES // 2]} ms",
                ),
>>>>>>> Stashed changes
            )
            for i in range(self.num_valves_to_test.get() // 2):
                self.valve_table.insert(
                    "",
                    "end",
                    values=(
                        f"{i + 1}",
                        f"{side_one_ul_dispensed[i] * 1000} ul",
                        f"{side_one_valve_durations[i]} ms",
                    ),
                )
            for i in range(self.num_valves_to_test.get() // 2):
                self.valve_table.insert(
                    "",
                    "end",
                    values=(
                        f"{i + 1}",
                        f"{side_two_ul_dispensed[i] * 1000} ul",
                        f"{side_two_valve_durations[i]} ms",
                    ),
                )
        else:
            for i in range(self.num_valves_to_test.get()):
                self.valve_table.insert(
                    "",
                    "end",
                    values=(f"{i + 1}", f"{self.desired_volume.get()} ul", "0.00 s"),
                )
            logging.info("Initial valve test table created.")

    def create_buttons(self):
        start_test_button_frame = tk.Frame(
            self, highlightbackground="black", highlightthickness=1
        )
        start_test_button_frame.grid(row=3, column=0, pady=10, padx=10, sticky="ew")
        start_test_button = tk.Button(
            start_test_button_frame,
            text="Start Testing",
            command=lambda: self.controller.run_valve_test(self.num_valves_to_test),
            bg="green",
            font=("Helvetica", 16),
        )
        start_test_button.pack(fill="both", expand=True)
        logging.info("Buttons created for ValveTestWindow.")

    def collect_user_inputs(self):
        user_inputs = []  # Initialize an empty list to store the inputs
        for valve_number in range(1, 9):  # Loop to collect 8 numbers
            user_input = self.input_popup(
                valve_number
            )  # Call the existing input_popup method
            if user_input is not None:
                user_inputs.append(user_input)  # Add the valid input to the list
            else:
                messagebox.showwarning(
                    "Input Cancelled", "Operation cancelled by user."
                )
                logging.warning("User input collection cancelled.")
                return  # Exit if the user cancels the input dialog

        self.controller.valve_test_logic.update_and_send_opening_times(
            8, user_inputs[:4], 1
        )
        self.controller.valve_test_logic.update_and_send_opening_times(
            8, user_inputs[4:-1], 2
        )
        logging.info(f"Collected user inputs: {user_inputs}")
        # For debugging: Print the collected inputs
        print(user_inputs)

    def set_valve_opening_times(self, new_times):
        self.valve_opening_times = new_times
        logging.info(f"Set new valve opening times: {new_times}")

    def set_ul_dispensed(self, new_volumes):
        self.ul_dispensed = new_volumes
        logging.info(f"Set new dispensed volumes: {new_volumes}")

    def update_valve_test_table(
        self,
        side_one_durations=None,
        side_two_durations=None,
        side_one_ul=None,
        Side_two_ul=None,
    ) -> None:
        self.valve_testing_window.create_valve_test_table(
            side_one_valve_durations=side_one_durations,
            side_two_valve_durations=side_two_durations,
            side_one_ul_dispensed=side_one_ul,
            side_two_ul_dispensed=Side_two_ul,
        )
<<<<<<< Updated upstream
=======

        ### include section to manually modify timings
        if test_confirmed:
            self.run_test()
        else:
            self.abort_test()

    def run_test(self):
        """
        we send raw bytes here as apposed to using strings, encoding them,
        and readStringUntil on the arduino becuase this was causing memory
        corruption issues with side ones schedules and durations vectors.
        Same goes for abort.
        """
        self.valve_test_button.configure(text="ABORT TESTING", bg="red")

        self.test_running = True
        ###====SENDING BEGIN TEST COMMAND====###
        command = np.int8(1).tobytes()
        self.arduino_controller.send_command(command)

    def abort_test(self):
        ###====SENDING BEGIN TEST COMMAND====###
        self.test_running = False
        command = np.int8(0).tobytes()
        self.arduino_controller.send_command(command)


class ManualTimeAdjustment(tk.Toplevel):
    def __init__(self, arduino_data, valve_selections):
        super().__init__()

        self.arduino_data = arduino_data

        self.title("Manual Valve Timing Adjustment")
        self.bind("<Control-w>", lambda event: self.withdraw())

        self.resizable(False, False)

        self.tk_vars = {}
        self.labelled_entries = [None] * 8

        self.fill_tk_vars()
        self.create_interface(valve_selections)

        window_icon_path = GUIUtils.get_window_icon_path()
        GUIUtils.set_program_icon(self, icon_path=window_icon_path)

    def show(self):
        self.update_interface()

    def update_interface(self, event):
        # event is the selection event of the self.combobox. using .get gets the self.duration_type dict key
        load_durations_key = self.duration_types[f"{event.widget.get()}"]
        side_one, side_two, date_used = self.arduino_data.load_durations(
            load_durations_key
        )
        print(side_one)
        print(side_two)
        print(date_used)
        pass

    def create_dropdown(self):
        self.duration_types = {
            "Default": "default_durations",
            "Last Used": "selected_durations",
            "Archive 1": "archive_1",
            "Archive 2": "archive_2",
            "Archive 3": "archive_3",
        }
        self.dropdown = ttk.Combobox(self, values=list(self.duration_types.keys()))
        self.dropdown.current(1)
        self.dropdown.grid(row=1, column=0)
        self.dropdown.bind("<<ComboboxSelected>>", lambda e: self.update_interface(e))

    def create_interface(self, valve_selections):
        warning = tk.Label(
            self,
            text="ALL TIMINGS IN MICROSECONDS (e.g 24125 equivalent to 24.125 ms)",
            bg="white",
            fg="black",
            font=("Helvetica", 15),
            highlightthickness=1,
            highlightbackground="black",
        )

        warning.grid(row=0, column=0, sticky="nsew", pady=10)

        self.create_dropdown()

        self.timing_frame = tk.Frame(
            self, highlightbackground="black", highlightthickness=1
        )

        self.timing_frame.grid(row=2, column=0, pady=10, padx=10, sticky="nsew")
        self.timing_frame.grid_columnconfigure(0, weight=1)

        for i in range(TOTAL_VALVES // 2):
            # GUIUtils.create_button returns both the buttons frame and button object in a tuple. using [1] on the
            # return item yields the button object.

            self.labelled_entries[i] = GUIUtils.create_labeled_entry(
                self.timing_frame,
                f"Valve {i + 1} Open Time",
                self.tk_vars[f"Valve {i + 1}"],
                i,
                0,
            )

            self.labelled_entries[i] = GUIUtils.create_labeled_entry(
                self.timing_frame,
                f"Valve {i + (TOTAL_VALVES // 2) + 1} Open Time",
                self.tk_vars[f"Valve {i + (TOTAL_VALVES) + 1}"],
                i,
                1,
            )

        warning = tk.Label(
            self,
            text="This will archive current configuration in assets/valve_durations.toml and set \nthis config to selected timings",
            bg="white",
            fg="black",
            font=("Helvetica", 15),
            highlightthickness=1,
            highlightbackground="black",
        )

        warning.grid(row=3, column=0)
        self.save_changes_bttn = GUIUtils.create_button(
            self,
            "Write Timing Changes",
            lambda: self.write_timing_changes(),
            bg="green",
            row=4,
            column=0,
        )[1]

    def fill_tk_vars(self):
        """
        in this function we fill self.tk_vars dictionary with tk.IntVar objects usable in tkinter entry objects. we fill these
        variables by default with the selected durations saved in the toml configuration file for the arduino timings.
        """
        side_one, side_two, date_used = self.arduino_data.load_durations()

        for i, duration in enumerate(side_one):
            self.tk_vars[f"Valve {i + 1}"] = tk.IntVar(value=duration)
        for i, duration in enumerate(side_two):
            self.tk_vars[f"Valve {i + 9}"] = tk.IntVar(value=duration)

    def write_timing_changes(self):
        """
        Load in the old config, save it under whichever archive slot is available or notify of overwrite.
        save new config under selected configuration.
        """
        side_one, side_two, date_used = self.arduino_data.load_durations()

        ## save durations in the oldest valve duration archival location
        self.arduino_data.save_durations(side_one, side_two, "archive")

        timings = [GUIUtils.safe_tkinter_get(value) for value in self.tk_vars.values()]
        print(timings)

        # check if one of the fields are empty
        if None in timings:
            msg = "ONE OR MORE FIELDS ARE EMPTY, FILL BEFORE TRYING ANOTHER ADJUSTMENT"
            logger.error(msg)
            GUIUtils.display_error("FIELD ERROR", msg)
            return

        side_one_new = np.full(8, np.int32(0))
        side_two_new = np.full(8, np.int32(0))

        for i in range(len(timings) // 2):
            side_one_new[i] = timings[i]
            side_two_new[i] = timings[i + 8]
        print(side_one_new)
        print(side_two_new)

        # save new durations in the selected slot of the configuration file
        self.arduino_data.save_durations(side_one_new, side_two_new, "selected")
>>>>>>> Stashed changes
