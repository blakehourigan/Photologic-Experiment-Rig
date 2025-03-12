import tkinter as tk
import numpy as np
import logging
from tkinter import ttk
import toml
from pathlib import Path

from views.gui_common import GUIUtils

# Get the logger in use for the app
logger = logging.getLogger()

toml_config_dir = Path(__file__).parent.parent.resolve()
toml_config_path = toml_config_dir / "rig_config.toml"
with open(toml_config_path, "r") as f:
    VALVE_CONFIG = toml.load(f)["valve_config"]

# pull total valves constant from toml config
TOTAL_VALVES = VALVE_CONFIG["TOTAL_CURRENT_VALVES"]


class ValveTestWindow(tk.Toplevel):
    def __init__(self, arduino_controller):
        super().__init__()
        self.title("Valve Testing / Valve Priming")
        self.bind("<Control-w>", lambda event: self.withdraw())

        self.resizable(False, False)

        window_icon_path = GUIUtils.get_window_icon_path()
        GUIUtils.set_program_icon(self, icon_path=window_icon_path)

        self.arduino_controller = arduino_controller

        self.test_running = False

        # desired volume to dispense in ul
        self.desired_volume = tk.DoubleVar(value=5)
        # how many times the valves should actuate per test
        self.actuations = tk.IntVar(value=1000)

        self.ul_dispensed: list[float] = []

        # list holding 8 None values
        self.valve_buttons = [None] * 8
        self.valve_test_button = None
        # holds valve detail entries, so they can be 'removed' but still
        # available to place back
        self.table_entries = [None] * 8

        self.valve_selections = np.zeros((TOTAL_VALVES,), dtype=np.int8)

        self.create_widgets()

        GUIUtils.center_window(self)

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
        GUIUtils.center_window(self)
        self.deiconify()

    def create_widgets(self):
        """
        Create and place the various buttons/entry boxes/table into the window
        """
        GUIUtils.create_labeled_entry(
            self,
            "Desired Dispensed Volume in Microliters (ul)",
            self.desired_volume,
            0,
            0,
        )

        GUIUtils.create_labeled_entry(
            self,
            "How Many Times Should the Valve Actuate?",
            self.actuations,
            1,
            0,
        )

        # setup frames for valve buttons
        self.valve_buttons_frame = tk.Frame(
            self, highlightbackground="black", highlightthickness=1
        )

        self.valve_buttons_frame.grid(row=3, column=0, pady=10, padx=10, sticky="nsew")
        self.valve_buttons_frame.grid_columnconfigure(0, weight=1)

        self.side_one_valves_frame = tk.Frame(
            self.valve_buttons_frame, highlightbackground="black", highlightthickness=1
        )
        self.side_one_valves_frame.grid(row=0, column=0, pady=10, padx=10, sticky="w")

        self.side_two_valves_frame = tk.Frame(
            self.valve_buttons_frame, highlightbackground="black", highlightthickness=1
        )
        self.side_two_valves_frame.grid(row=0, column=1, pady=10, padx=10, sticky="e")

        self.create_buttons()

        self.create_valve_test_table()

    def start_toggle_handler(self):
        if self.test_running:
            self.valve_test_button.configure(text="Start Testing", bg="green")
            self.abort_test()
        else:
            self.send_schedules()

    def create_buttons(self):
        for i in range(TOTAL_VALVES // 2):
            # GUIUtils.create_button returns both the buttons frame and button object in a tuple. using [1] on the
            # return item yields the button object.

            # return the side one button and put it on the side one 'side'
            # of the list (0-4)
            self.valve_buttons[i] = GUIUtils.create_button(
                self.side_one_valves_frame,
                f"Valve {i + 1}",
                lambda i=i: self.toggle_valve_button(self.valve_buttons[i], i),
                "light blue",
                i,
                0,
            )[1]

            # return the side two button and put it on the side two 'side'
            # of the list (5-8)
            self.valve_buttons[i + (TOTAL_VALVES // 2)] = GUIUtils.create_button(
                self.side_two_valves_frame,
                f"Valve {i + (TOTAL_VALVES // 2) + 1}",
                lambda i=i: self.toggle_valve_button(
                    self.valve_buttons[i + (TOTAL_VALVES // 2)], i + (TOTAL_VALVES // 2)
                ),
                "light blue",
                i,
                0,
            )[1]

        self.valve_test_button = GUIUtils.create_button(
            self, "Start Testing", lambda: self.start_toggle_handler(), "green", 4, 0
        )[1]

    def create_valve_test_table(self):
        # this function creates and labels the testing window table that displays the information recieved from the arduino reguarding the results of the tes
        self.valve_table_frame = tk.Frame(
            self, highlightbackground="black", highlightthickness=1
        )
        self.valve_table_frame.grid(row=2, column=0, sticky="nsew", pady=10, padx=10)
        # tell the frame to fill the available width
        self.valve_table_frame.grid_columnconfigure(0, weight=1)

        self.valve_table = ttk.Treeview(
            self.valve_table_frame,
            show="headings",
        )
<<<<<<< HEAD
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
=======
        self.valve_table.grid(row=1, sticky="ew")

        button = tk.Button(
            self.valve_table_frame,
            text="Manual Valve Duration Override",
            command=lambda: ManualTimeAdjustment(self.arduino_controller.arduino_data),
            bg="light blue",
            highlightbackground="black",
            highlightthickness=1,
        )
        button.grid(row=0, sticky="e")

>>>>>>> 0e668c65127430a018b69e97e10add84bc948422
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
<<<<<<< HEAD
        side_one_durations, side_two_durations, date_used = (
            arduino_data.load_durations()
        )
=======
        side_one_durations, side_two_durations = arduino_data.load_durations()
>>>>>>> 0e668c65127430a018b69e97e10add84bc948422

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
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
>>>>>>> 0e668c65127430a018b69e97e10add84bc948422
            )

    def update_table_entries(self, test_completed=False) -> None:
        """
        all that this funtion does is show or hide valve information based on which valves are
        selected and de-selected. dispensed liquid during a test will be calculated later.
        """

        selected_valves = self.valve_selections[self.valve_selections != 0]

        for i in range(TOTAL_VALVES):
            if i in (selected_valves - 1):
                self.valve_table.reattach(self.table_entries[i], "", i)
            else:
                self.valve_table.detach(self.table_entries[i])

        logging.info("Valve test table updated.")

    def toggle_valve_button(self, button, valve_num):
        # Attempt to get the value to ensure it's a valid float as expected
        # If successful, call the function to update/create the valve test table
        if self.valve_selections[valve_num] == 0:
            button.configure(relief="sunken")
            self.valve_selections[valve_num] = valve_num + 1

        else:
            button.configure(relief="raised")
            self.valve_selections[valve_num] = 0
        self.update_table_entries()

    def verify_variables(self, original_data) -> bool:
        while self.arduino_controller.arduino.in_waiting < 4:
            pass

        ver_len_sched_sd_one = self.arduino_controller.arduino.read()
        ver_len_sched_sd_two = self.arduino_controller.arduino.read()

        ver_valve_act_time = self.arduino_controller.arduino.read(2)

        verification_data = (
            ver_len_sched_sd_one + ver_len_sched_sd_two + ver_valve_act_time
        )

        if verification_data == original_data:
            logger.info("====VERIFIED TEST VARIABLES====")
            return True
        else:
            msg = "====INCORRECT VARIABLES DETECTED, TRY AGAIN===="
            GUIUtils.display_error("TRANSMISSION ERROR", msg)
            logger.error(msg)
            return False

    def verify_schedule(self, len_sched, sent_schedule) -> bool:
        # np array used for verification later
        received_sched = np.zeros((len_sched,), dtype=np.int8)

        while self.arduino_controller.arduino.in_waiting < len_sched:
            pass

        for i in range(len_sched):
            received_sched[i] = int.from_bytes(
                self.arduino_controller.arduino.read(), byteorder="little", signed=False
            )

        if np.array_equal(received_sched, sent_schedule):
            logger.info(f"===TESTING SCHEDULE VERIFIED as ==> {received_sched}===")
            logger.info("====================BEGIN TESTING NOW====================")
            return True
        else:
            msg = "====INCORRECT SCHEDULE DETECTED, TRY AGAIN===="
            GUIUtils.display_error("TRANSMISSION ERROR", msg)
            logger.error(msg)
            return False

    def send_schedules(self):
        """
        Calculate schedule lengths so arduino knows how many entried to look for on each schedule
        receive operation. valve_selections is a np_array equivalent to the full test schedule
        lineup. valves in schedule for side on come first, then side two.
        """
        len_sched_one = np.count_nonzero(self.valve_selections[0:4])
        len_sched_two = np.count_nonzero(self.valve_selections[4:])

        len_sched_one = np.int8(len_sched_one)
        len_sched_two = np.int8(len_sched_two)
        len_sched = len_sched_one + len_sched_two

        # because self.actuations is a IntVar, we use .get() method to get its value
        valve_acuations = np.int16(self.actuations.get())

        # schedule is TOTAL_VALVES long to accomodate testing of up to all valves at one time.
        # if we are not testing them all, filter out the zero entries (valves we are not testing)
        schedule = self.valve_selections[self.valve_selections != 0]
        # decrement each element in the array by one to move to zero-indexing. We moved to 1
        # indexing becuase using zero indexing does not work with the method of toggling valves
        # defined above
        schedule -= 1

        len_sched_one = len_sched_one
        len_sched_two = len_sched_two
        valve_acuations = valve_acuations

        self.arduino_controller.send_valve_durations()

        ###====SENDING TEST COMMAND====###
        command = "TEST VOL\n".encode("utf-8")
        self.arduino_controller.send_command(command)

        ###====SENDING TEST VARIABLES (len side one, two, num_actuations per test)====###
        data_bytes = (
            len_sched_one.tobytes()
            + len_sched_two.tobytes()
            + valve_acuations.tobytes()
        )
        self.arduino_controller.send_command(data_bytes)

        # verify the data
        if not self.verify_variables(data_bytes):
            return

        ###====SENDING TEST SCHEDULE====###
        sched_data_bytes = schedule.tobytes()
        self.arduino_controller.send_command(sched_data_bytes)

        if not self.verify_schedule(len_sched, schedule):
            return

        ####### ARDUINO SHOULD HALT HERE UNTIL THE GO-AHEAD IS GIVEN HERE
        # inc each sched element by one so that it is 1-indexes and matches the valve labels
        schedule += 1

        valves = ",".join(str(valve) for valve in schedule)

        test_confirmed = GUIUtils.askyesno(
            "CONFIRM THE TEST SCHEDULE",
            f"Valves {valves}, will be tested. Review the test table to confirm schedule and timings. Each valve will be actuated {valve_acuations} times. Ok to begin?",
        )
<<<<<<< HEAD
<<<<<<< Updated upstream
=======
=======
>>>>>>> 0e668c65127430a018b69e97e10add84bc948422

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
<<<<<<< HEAD
    def __init__(self, arduino_data, valve_selections):
=======
    def __init__(self, arduino_data):
>>>>>>> 0e668c65127430a018b69e97e10add84bc948422
        super().__init__()

        self.arduino_data = arduino_data

        self.title("Manual Valve Timing Adjustment")
        self.bind("<Control-w>", lambda event: self.withdraw())

        self.resizable(False, False)

<<<<<<< HEAD
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
=======
        window_icon_path = GUIUtils.get_window_icon_path()
        GUIUtils.set_program_icon(self, icon_path=window_icon_path)

    def create_interface(self):
        pass
>>>>>>> 0e668c65127430a018b69e97e10add84bc948422
