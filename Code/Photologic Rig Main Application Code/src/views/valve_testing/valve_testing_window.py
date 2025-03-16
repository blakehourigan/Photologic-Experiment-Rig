import tkinter as tk
from tkinter import simpledialog
import numpy as np
import logging
import threading
from tkinter import ttk
import toml
from enum import Enum
import system_config

from views.gui_common import GUIUtils
from views.valve_testing.manual_time_adjustment_window import ManualTimeAdjustment
from views.valve_testing.valve_changes_window import ValveChanges


# Get the logger in use for the app
logger = logging.getLogger()

rig_config = system_config.get_rig_config()

with open(rig_config, "r") as f:
    VALVE_CONFIG = toml.load(f)["valve_config"]

# pull total valves constant from toml config
TOTAL_VALVES = VALVE_CONFIG["TOTAL_CURRENT_VALVES"]

VALVES_PER_SIDE = TOTAL_VALVES // 2


class WindowMode(Enum):
    TESTING = "Testing"
    PRIMING = "Priming"


class ValveTestWindow(tk.Toplevel):
    def __init__(self, arduino_controller):
        super().__init__()
        self.title("Valve Testing")
        self.bind("<Control-w>", lambda event: self.withdraw())
        self.protocol("WM_DELETE_WINDOW", lambda: self.withdraw())

        self.resizable(False, False)

        window_icon_path = GUIUtils.get_window_icon_path()
        GUIUtils.set_program_icon(self, icon_path=window_icon_path)

        self.arduino_controller = arduino_controller
        self.arduino_data = arduino_controller.arduino_data

        self.window_mode = WindowMode.TESTING

        self.test_running = False
        self.prime_running = False

        # desired volume to dispense in ul
        self.desired_volume = tk.DoubleVar(value=5)
        # how many times the valves should actuate per test
        self.actuations = tk.IntVar(value=1000)

        # will hold ml dispensed during each test
        self.ml_dispensed = None

        # list holding 8 None values
        self.valve_buttons = [None] * TOTAL_VALVES
        self.valve_test_button = None
        # holds valve detail entries, so they can be 'removed' but still
        # available to place back
        self.table_entries = [None] * TOTAL_VALVES

        self.valve_selections = np.zeros((TOTAL_VALVES,), dtype=np.int8)
        # the following are used to track side-specific tests
        # side one holds side one valves to be tested and vice versa for side two
        self.side_one_tests = None
        self.side_two_tests = None

        # will be used to halt valve test arduino listener thread if test is
        # aborted
        self.stop_event = threading.Event()

        self.create_interface()

        self.update_idletasks()
        GUIUtils.center_window(self)

        # we don't want to show this window until the user decides to click the corresponding button,
        # withdraw (hide) it for now
        self.withdraw()

        # create and hide manual timing adjustment window
        # so that we don't have to generate it later
        self.manual_adjust_window = ManualTimeAdjustment(
            self.arduino_controller.arduino_data, self.valve_selections
        )
        self.manual_adjust_window.withdraw()

        logging.info("Valve Test Window initialized.")

    def show(self):
        self.deiconify()

    def switch_window_mode(self):
        if self.window_mode == WindowMode.TESTING:
            if self.test_running:
                # if the test is currently running we do not want to switch modes. Stop testing to switch modes
                GUIUtils.display_error(
                    "ACTION PROHIBITED",
                    "You cannot switch modes while a test is running. If you'd like to switch modes, please abort the test and try again.",
                )
                return
            self.title("Valve Priming")

            self.window_mode = WindowMode.PRIMING

            self.mode_button.configure(text="Switch to Testing Mode", bg="DeepSkyBlue3")

            # orig. row 1
            self.dispensed_vol_frame.grid_forget()
            # orig. row 3
            self.valve_table_frame.grid_forget()

            # start testing button -> start priming button / command
            self.valve_test_button.configure(
                text="Start Priming",
                bg="coral",
                command=lambda: self.send_schedules(),
            )

        else:
            if self.prime_running:
                # if the test is currently running we do not want to switch modes. Stop testing to switch modes
                GUIUtils.display_error(
                    "ACTION PROHIBITED",
                    "You cannot switch modes while a valve prime operation is running. If you'd like to switch modes, please abort the prime and try again.",
                )
                return

            self.title("Valve Testing")

            self.window_mode = WindowMode.TESTING

            self.mode_button.configure(text="Switch to Priming Mode", bg="coral")

            self.valve_table_frame.grid(
                row=3, column=0, sticky="nsew", pady=10, padx=10
            )
            self.dispensed_vol_frame.grid(row=1, column=0, padx=5, sticky="nsew")

            self.valve_test_button.configure(
                text="Start Testing",
                bg="green",
                command=lambda: self.start_testing_toggle(),
            )

        # resize the window to fit current content
        self.update_idletasks()
        GUIUtils.center_window(self)

    def create_interface(self):
        """
        Create and place the various buttons/entry boxes/table into the window
        """

        self.mode_button = GUIUtils.create_button(
            self,
            "Switch to Priming Mode",
            command=lambda: self.switch_window_mode(),
            bg="coral",
            row=0,
            column=0,
        )[1]

        # return the frame so we can remove the element on mode switch
        self.dispensed_vol_frame = GUIUtils.create_labeled_entry(
            self,
            "Desired Dispensed Volume in Microliters (ul)",
            self.desired_volume,
            1,
            0,
        )[0]

        GUIUtils.create_labeled_entry(
            self,
            "How Many Times Should the Valve Actuate?",
            self.actuations,
            2,
            0,
        )

        ### ROW 3 ###
        self.create_valve_test_table()

        # setup frames for valve buttons
        self.valve_buttons_frame = tk.Frame(
            self, highlightbackground="black", highlightthickness=1
        )

        ### ROW 4 ###
        self.valve_buttons_frame.grid(row=4, column=0, pady=10, padx=10, sticky="nsew")
        self.valve_buttons_frame.grid_columnconfigure(0, weight=1)

        self.side_one_valves_frame = tk.Frame(
            self.valve_buttons_frame, highlightbackground="black", highlightthickness=1
        )
        self.side_one_valves_frame.grid(row=0, column=0, pady=10, padx=10, sticky="w")

        self.side_two_valves_frame = tk.Frame(
            self.valve_buttons_frame, highlightbackground="black", highlightthickness=1
        )
        self.side_two_valves_frame.grid(row=0, column=1, pady=10, padx=10, sticky="e")

        ### ROW 5 ###
        self.create_buttons()

    def start_testing_toggle(self):
        if self.test_running:
            self.valve_test_button.configure(text="Start Testing", bg="green")
            self.abort_test()
        else:
            self.send_schedules()

    def create_buttons(self):
        for i in range(VALVES_PER_SIDE):
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
            self.valve_buttons[i + (VALVES_PER_SIDE)] = GUIUtils.create_button(
                self.side_two_valves_frame,
                f"Valve {i + (VALVES_PER_SIDE) + 1}",
                lambda i=i: self.toggle_valve_button(
                    self.valve_buttons[i + (VALVES_PER_SIDE)], i + (VALVES_PER_SIDE)
                ),
                "light blue",
                i,
                0,
            )[1]

        self.valve_test_button = GUIUtils.create_button(
            self, "Start Testing", lambda: self.start_testing_toggle(), "green", 5, 0
        )[1]

    def create_valve_test_table(self):
        # this function creates and labels the testing window table that displays the information recieved from the arduino reguarding the results of the tes
        self.valve_table_frame = tk.Frame(
            self, highlightbackground="black", highlightthickness=1
        )
        self.valve_table_frame.grid(row=3, column=0, sticky="nsew", pady=10, padx=10)
        # tell the frame to fill the available width
        self.valve_table_frame.grid_columnconfigure(0, weight=1)

        self.valve_table = ttk.Treeview(
            self.valve_table_frame,
            show="headings",
        )

        headings = [
            "Valve",
            "Amount Dispensed Per Lick (ul)",
            "Testing Opening Time of (ms)",
        ]

        self.valve_table["columns"] = headings

        self.valve_table.grid(row=1, sticky="ew")

        button = tk.Button(
            self.valve_table_frame,
            text="Manual Valve Duration Override",
            command=lambda: self.manual_adjust_window.show(),
            bg="light blue",
            highlightbackground="black",
            highlightthickness=1,
        )

        button.grid(row=0, sticky="e")

        # Configure the columns
        for col in self.valve_table["columns"]:
            self.valve_table.heading(col, text=col)

        arduino_data = self.arduino_controller.arduino_data

        side_one_durations, side_two_durations, date_used = (
            arduino_data.load_durations()
        )

        # insert default entries for each total valve until user selects how many
        # they want to test
        for i in range(VALVES_PER_SIDE):
            self.table_entries[i] = self.valve_table.insert(
                "",
                i,
                values=(
                    f"{i + 1}",
                    "Test Not Complete",
                    f"{side_one_durations[i]} ms",
                ),
            )
            self.table_entries[i + 4] = self.valve_table.insert(
                "",
                i + VALVES_PER_SIDE,
                values=(
                    f"{i + VALVES_PER_SIDE + 1}",
                    "Test Not Complete",
                    f"{side_two_durations[i]} ms",
                ),
            )

    def update_table_entry_test_status(self, valve, l_per_lick):
        self.valve_table.set(
            self.table_entries[valve - 1], column=1, value=f"{l_per_lick * 1000} uL"
        )

    def update_table_entries(self, test_completed=False) -> None:
        """
        all that this funtion does is show or hide valve information based on which valves are
        selected and de-selected. dispensed liquid during a test will be calculated later.
        """
        side_one, side_two, date_used = self.arduino_data.load_durations()
        # np array where the entry is not zero but the valve number itself
        selected_valves = self.valve_selections[self.valve_selections != 0]

        # for all valve numbers, if that number is in selected_valves -1 (the entire array
        # decremented by one) place it in the table and ensure its duration is up-to-date
        for i in range(TOTAL_VALVES):
            # if the iter number is also contained in the selected valves arr
            if i in (selected_valves - 1):
                # check if it's side two or side one
                if i >= VALVES_PER_SIDE:
                    duration = side_two[i - VALVES_PER_SIDE]
                else:
                    duration = side_one[i]
                self.valve_table.item(
                    self.table_entries[i],
                    values=(
                        f"{i + 1}",
                        "Test Not Complete",
                        f"{duration} ms",
                    ),
                )
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
        # wait until all data is on the wire ready to be read (4 bytes),
        # then read it all in quick succession
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
        len_sched_one = np.count_nonzero(self.valve_selections[:VALVES_PER_SIDE])
        len_sched_two = np.count_nonzero(self.valve_selections[VALVES_PER_SIDE:])

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

        self.side_one_tests = schedule[:len_sched_one]
        self.side_two_tests = schedule[len_sched_one:]

        len_sched_one = len_sched_one
        len_sched_two = len_sched_two
        valve_acuations = valve_acuations

        self.arduino_controller.send_valve_durations()
        if self.window_mode == WindowMode.TESTING:
            ###====SENDING TEST COMMAND====###
            command = "TEST VOL\n".encode("utf-8")
            self.arduino_controller.send_command(command)

        elif self.window_mode == WindowMode.PRIMING:
            self.prime_running = True

            command = "PRIME VALVES\n".encode("utf-8")
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

        ###====SENDING SCHEDULE====###
        sched_data_bytes = schedule.tobytes()
        self.arduino_controller.send_command(sched_data_bytes)

        if not self.verify_schedule(len_sched, schedule):
            return

        schedule += 1

        valves = ",".join(str(valve) for valve in schedule)
        if self.window_mode == WindowMode.TESTING:
            ####### ARDUINO HALTS HERE UNTIL THE GO-AHEAD IS GIVEN #######
            # inc each sched element by one so that it is 1-indexes and matches the valve labels
            test_confirmed = GUIUtils.askyesno(
                "CONFIRM THE TEST SCHEDULE",
                f"Valves {valves}, will be tested. Review the test table to confirm schedule and timings. Each valve will be actuated {valve_acuations} times. Ok to begin?",
            )

            self.ml_dispensed = []
            ### include section to manually modify timings
            if test_confirmed:
                self.bind("<<event0>>", self.testing_complete)
                self.bind("<<event1>>", self.take_input)
                threading.Thread(target=self.run_test).start()
            else:
                self.abort_test()
        elif self.window_mode == WindowMode.PRIMING:
            priming_confirmed = GUIUtils.askyesno(
                "CONFIRM THE ACTION",
                f"Valves {valves}, will be primed (opened and closed) {valve_acuations} times. Ok to begin?",
            )
            if priming_confirmed:
                # in case of prime, we send 0 to mean continue or start
                # and we send a 1 at any point to abort or cancel the prime
                start = np.int8(0).tobytes()
                self.arduino_controller.send_command(command=start)

                self.valve_test_button.configure(
                    text="STOP Priming",
                    bg="gold",
                    command=lambda: self.stop_priming(),
                )

    def stop_priming(self):
        self.prime_running = False

        self.valve_test_button.configure(
            text="Start Priming",
            bg="coral",
            command=lambda: self.send_schedules(),
        )

        stop = np.int8(1).tobytes()
        self.arduino_controller.send_command(command=stop)

    def take_input(self, event, pair_num_override=None):
        if event is not None:
            pair_number = event.state
        else:
            pair_number = pair_num_override

        # decide how many valves were tested last. if 0 we will not arrive
        # here so we need not test for this.
        if pair_number < len(self.side_one_tests) and pair_number < len(
            self.side_two_tests
        ):
            valves_tested = [
                self.side_one_tests[pair_number],
                self.side_two_tests[pair_number],
            ]
        elif pair_number < len(self.side_one_tests):
            valves_tested = [
                self.side_one_tests[pair_number],
            ]
        else:
            valves_tested = [
                self.side_two_tests[pair_number],
            ]

        # for each test that we ran store the amount dispensed or abort
        for valve in valves_tested:
            response = simpledialog.askfloat(
                "INPUT AMOUNT DISPENSED",
                f"Please input the amount of liquid dispensed for the test of valve {valve}",
            )
            if response is None:
                self.abort_test()
            else:
                self.ml_dispensed.append((valve, response))
        if pair_num_override is not None:
            self.arduino_controller.send_command(np.int8(0).tobytes())
        else:
            self.arduino_controller.send_command(np.int8(1).tobytes())

    def run_test(self):
        """
        we send raw bytes here as apposed to using strings, encoding them,
        and readStringUntil on the arduino becuase this was causing memory
        corruption issues with side ones schedules and durations vectors.
        Same goes for abort.
        """
        if self.stop_event.is_set():
            self.stop_event.clear()

        self.valve_test_button.configure(text="ABORT TESTING", bg="red")

        self.test_running = True
        ###====SENDING BEGIN TEST COMMAND====###
        command = np.int8(1).tobytes()
        self.arduino_controller.send_command(command)

        while self.test_running:
            # if stop event, shut down the thread
            if self.stop_event.is_set():
                break
            if self.arduino_controller.arduino.in_waiting > 0:
                remaining_tests = self.arduino_controller.arduino.read()
                pair_number = int.from_bytes(
                    self.arduino_controller.arduino.read(),
                    byteorder="little",
                    signed=False,
                )

                if remaining_tests == np.int8(1).tobytes():
                    self.event_generate("<<event1>>", when="tail", state=pair_number)
                if remaining_tests == np.int8(0).tobytes():
                    self.event_generate("<<event0>>", when="tail", state=pair_number)

    def abort_test(self):
        # if test is aborted, stop the test listener thread
        self.valve_test_button.configure(text="Start Testing", bg="green")
        self.stop_event.set()
        self.test_running = False
        ###====SENDING ABORT TEST COMMAND====###
        command = np.int8(0).tobytes()
        self.arduino_controller.send_command(command)

    def testing_complete(self, event):
        # take input from last pair/valve
        self.take_input(event=None, pair_num_override=event.state)
        # reconfigure the testing button and testing state
        self.valve_test_button.configure(text="Start Testing", bg="green")
        self.test_running = False
        # stop the arduino testing listener thread
        self.stop_event.set()

        # update valves and such
        self.auto_update_durations()

    def auto_update_durations(self):
        """
        This function is similar to the ManualTimeAdjustment 'write_timing_changes' function, with the
        exception of the calculations involving volume dispensed per opening and which valve to assign
        a duration to ' function, with the
        exception of the calculations involving volume dispensed per opening and which valve to assign
        a duration to.
        """
        # list of tuples of tuples ==> [(valve, (old_dur, new_dur))] sent to ChangesWindow instance, so that
        # user can confirm duration changes
        changed_durations = []

        ## save current durations in the oldest valve duration archival location
        side_one, side_two, date_used = self.arduino_data.load_durations()

        side_one_old = side_one.copy()
        side_two_old = side_two.copy()

        for valve, dispensed_amt in self.ml_dispensed:
            logical_valve = None
            tested_duration = None
            side_durations = None

            if valve > VALVES_PER_SIDE:
                logical_valve = (valve - 1) - VALVES_PER_SIDE

                tested_duration = side_two[logical_valve]
                side_durations = side_two
            else:
                logical_valve = valve - 1

                tested_duration = side_one[logical_valve]
                side_durations = side_one

            # divide by 1000 to get to mL from ul
            desired_per_open_vol = self.desired_volume.get() / 1000

            # divide by 1000 to get amount per opening, NOT changing units
            actual_per_open_vol = dispensed_amt / self.actuations.get()

            self.update_table_entry_test_status(valve, actual_per_open_vol)

            new_duration = round(
                tested_duration * (desired_per_open_vol / actual_per_open_vol)
            )

            side_durations[logical_valve] = new_duration

            changed_durations.append((valve, (tested_duration, new_duration)))

        ValveChanges(
            changed_durations,
            lambda: self.confirm_valve_changes(
                side_one, side_two, side_one_old, side_two_old
            ),
        )

    def confirm_valve_changes(self, side_one, side_two, side_one_old, side_two_old):
        self.arduino_data.save_durations(side_one_old, side_two_old, "archive")
        self.arduino_data.save_durations(side_one, side_two, "selected")
