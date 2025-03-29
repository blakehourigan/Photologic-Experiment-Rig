"""
This module defines the ValveTestWindow class, a Tkinter Toplevel window
providing functionality for testing and priming valves. Test and prime procedures are
facilitated via the `controllers.arduino_control.ArduinoManager`.

It allows users to:
- Select individual valves for testing or priming.
- Configure test parameters like desired dispense volume and number of actuations.
- Initiate automated valve tests, calculating new opening durations based on
  user-provided dispensed volumes.
- Initiate valve test/priming sequences.
- Manually override and adjust valve timings via a separate window (`ManualTimeAdjustment`).
- View test results and current valve timings in a table format.
- Confirm or abort automatically calculated timing changes.

This window interacts heavily with the `controllers.arduino_control.ArduinoManager` controller for communication
and the `modesl.arduino_data.ArduinoData` model for storing/retrieving valve duration configurations.

It uses `views.gui_common.GUIUtils` for common UI elements and window management.
"""

import tkinter as tk
from tkinter import N, simpledialog
from tkinter import ttk


import numpy as np

### USED FOR TYPE HINTING ###
import numpy.typing as npt

from enum import Enum
import threading
import logging
import toml

from controllers.arduino_control import ArduinoManager
from models.arduino_data import ArduinoData
from views.gui_common import GUIUtils
from views.valve_testing.manual_time_adjustment_window import ManualTimeAdjustment
from views.valve_testing.valve_changes_window import ValveChanges
import system_config


logger = logging.getLogger()
"""Get the logger in use for the app."""

rig_config = system_config.get_rig_config()

with open(rig_config, "r") as f:
    VALVE_CONFIG = toml.load(f)["valve_config"]

# pull total valves constant from toml config
TOTAL_VALVES = VALVE_CONFIG["TOTAL_CURRENT_VALVES"]

VALVES_PER_SIDE = TOTAL_VALVES // 2


class WindowMode(Enum):
    """
    Represents the two primary operational modes of the ValveTestWindow:
    Testing mode for calibrating valve durations, and Priming mode for
    actuating valves repeatedly without calibration.
    """

    TESTING = "Testing"
    PRIMING = "Priming"


class ValveTestWindow(tk.Toplevel):
    """
    *This is a bit of a god class and should likely be refactored... but for now... it works!*

    Implements the main Tkinter Toplevel window for valve testing and priming operations.

    This window provides an interface to interact with the Arduino
    controller for calibrating valve open times based on dispensed volume or
    for running priming sequences. It features modes for testing and
    priming, manages valve selections, displays test progress and results,
    and handles communication with the Arduino.

    Attributes
    ----------
    - **`arduino_controller`** (*ArduinoManager*): Reference to the main Arduino controller instance, used for sending commands and data.
    - **`arduino_data`** (*ArduinoData*): Reference to the data model holding valve duration configurations.
    - **`window_mode`** (*WindowMode*): Enum indicating the current operational mode (Testing or Priming).
    - **`test_running`** (*bool*): Flag indicating if an automated test sequence is currently active.
    - **`prime_running`** (*bool*): Flag indicating if a priming sequence is currently active.
    - **`desired_volume`** (*tk.DoubleVar*): Tkinter variable storing the target volume (in microliters) per actuation for automatic duration calculation.
    - **`actuations`** (*tk.IntVar*): Tkinter variable storing the number of times each valve should be actuated during a test or prime sequence.
    - **`ml_dispensed`** (*list[tuple[int, float]]*): Stores tuples of (valve_number, dispensed_volume_ml) entered by the user during a test.
    - **`valve_buttons`** (*list[tk.Button | None]*): List holding the Tkinter Button widgets for each valve selection.
    - **`valve_test_button`** (*tk.Button | None*): The main button used to start/abort tests or start/stop priming.
    - **`table_entries`** (*list[str | None]*): List holding the item IDs for each row in the ttk.Treeview table, used for modifying/hiding/showing specific rows.
    - **`valve_selections`** (*npt.NDArray[np.int8]*): Numpy array representing the selection state of each valve (0 if not selected, valve_number if selected).
    - **`side_one_tests`** (*npt.NDArray[np.int8] | None*): Numpy array holding the valve numbers (0-indexed) selected for testing/priming on side one.
    - **`side_two_tests`** (*npt.NDArray[np.int8] | None*): Numpy array holding the valve numbers (0-indexed) selected for testing/priming on side two.
    - **`stop_event`** (*threading.Event*): Event flag used to signal the Arduino listener thread (`run_test`) to stop.
    - **`mode_button`** (*tk.Button*): Button to switch between Testing and Priming modes.
    - **`dispensed_vol_frame`** (*tk.Frame*): Container frame for the desired volume input elements (visible in Testing mode).
    - **`valve_table_frame`** (*tk.Frame*): Container frame for the valve test results table (visible in Testing mode).
    - **`valve_table`** (*ttk.Treeview*): The table widget displaying valve numbers, test status, and timings.
    - **`valve_buttons_frame`** (*tk.Frame*): Main container frame for the side-by-side valve selection buttons.
    - **`side_one_valves_frame`** (*tk.Frame*): Frame holding valve selection buttons for the first side.
    - **`side_two_valves_frame`** (*tk.Frame*): Frame holding valve selection buttons for the second side.
    - **`manual_adjust_window`** (*ManualTimeAdjustment*): Instance of the separate window for manual timing adjustments.

    Methods
    -------
    - `setup_basic_window_attr`()
        Configures basic window properties like title, key bindings, and icon.
    - `show`()
        Makes the window visible (deiconifies).
    - `switch_window_mode`()
        Toggles the window between Testing and Priming modes, adjusting UI elements accordingly.
    - `create_interface`()
        Builds the entire GUI layout, placing widgets and frames.
    - `start_testing_toggle`()
        Handles the press of the main test/prime button in Testing mode (starts or aborts test).
    - `create_buttons`()
        Creates and places the valve selection buttons and the main start/abort button.
    - `create_valve_test_table`()
        Creates the ttk.Treeview table for displaying valve test results and timings.
    - `update_table_entry_test_status`(...)
        Updates the 'Amount Dispensed' column for a specific valve in the table.
    - `update_table_entries`(...)
        Updates the entire valve table, showing/hiding rows based on selections and refreshing currently loaded durations.
    - `toggle_valve_button`(...)
        Handles clicks on valve selection buttons, updating their appearance and the `valve_selections` array.
    - `verify_variables`(...)
        Reads verification data back from Arduino to confirm test parameters were received correctly.
    - `verify_schedule`(...)
        Reads verification data back from Arduino to confirm the valve test/prime schedule was received correctly.
    - `send_schedules`()
        Sends the command, parameters (schedule lengths, actuations), and valve schedule to the Arduino. Handles mode-specific commands and confirmations.
    - `stop_priming`()
        Sends a command to the Arduino to stop an ongoing priming sequence.
    - `take_input`(...)
        Prompts the user (via simpledialog) to enter the dispensed volume for a completed valve test pair. Sends confirmation back to Arduino.
    - `run_test`()
        Runs in a separate thread to listen for messages from the Arduino during a test, triggering events for input prompts or completion.
    - `abort_test`()
        Sends a command to the Arduino to abort the current test and stops the listener thread.
    - `testing_complete`(...)
        Handles the event triggered when the Arduino signals the end of the entire test sequence. Initiates duration updates.
    - `auto_update_durations`()
        Calculates new valve durations based on test results (`ml_dispensed`) and opens the `ValveChanges` confirmation window.
    - `confirm_valve_changes`(...)
        Callback function executed if the user confirms changes in the `ValveChanges` window. Saves new durations and archives old ones via `ArduinoData`.
    """

    def __init__(self, arduino_controller: ArduinoManager) -> None:
        """
        Initializes the ValveTestWindow.

        Parameters
        ----------
        - **arduino_controller** (*ArduinoManager*): The application's instance of the Arduino controller.

        Raises
        ------
        - Propagates exceptions from `GUIUtils` methods during icon setting.
        - Propagates exceptions from `arduino_data.load_durations()`.
        """
        super().__init__()
        self.arduino_controller: ArduinoManager = arduino_controller
        self.arduino_data: ArduinoData = arduino_controller.arduino_data

        self.setup_basic_window_attr()

        self.window_mode: WindowMode = WindowMode.TESTING

        self.test_running: bool = False
        self.prime_running: bool = False

        self.desired_volume: tk.DoubleVar = tk.DoubleVar(value=5)

        self.actuations: tk.IntVar = tk.IntVar(value=1000)

        self.ml_dispensed: list[tuple[int, float]] = []

        self.valve_buttons: list[tk.Button | None] = [None] * TOTAL_VALVES

        self.valve_test_button: tk.Button | None = None

        self.table_entries: list[str | None] = [None] * TOTAL_VALVES

        self.valve_selections: npt.NDArray[np.int8] = np.zeros(
            (TOTAL_VALVES,), dtype=np.int8
        )

        self.side_one_tests: None | npt.NDArray[np.int8] = None
        self.side_two_tests: None | npt.NDArray[np.int8] = None

        self.stop_event: threading.Event = threading.Event()

        self.create_interface()

        # hide main window for now until we deliberately enter this window.
        self.withdraw()

        self.manual_adjust_window = ManualTimeAdjustment(
            self.arduino_controller.arduino_data
        )
        # hide the adjustment window until we need it.
        self.manual_adjust_window.withdraw()

        logging.info("Valve Test Window initialized.")

    def setup_basic_window_attr(self) -> None:
        """
        Sets up fundamental window properties.

        Configures the window title, binds Ctrl+W and the close button ('X')
        to hide the window, sets grid column/row weights for resizing behavior,
        and applies the application icon using `GUIUtils`.
        """

        self.title("Valve Testing")
        self.bind("<Control-w>", lambda event: self.withdraw())
        self.protocol("WM_DELETE_WINDOW", lambda: self.withdraw())

        self.grid_columnconfigure(0, weight=1)

        for i in range(5):
            self.grid_rowconfigure(i, weight=1)
        self.grid_rowconfigure(0, weight=0)

        window_icon_path = GUIUtils.get_window_icon_path()
        GUIUtils.set_program_icon(self, icon_path=window_icon_path)

    def show(self) -> None:
        """
        Makes the ValveTestWindow visible.

        Calls `deiconify()` to show the window if it was previously hidden (withdrawn).
        """
        self.deiconify()

    def switch_window_mode(self) -> None:
        """
        Toggles the window's operational mode between Testing and Priming.

        Updates the window title and mode button text/color. Hides or shows
        mode-specific UI elements (desired volume input, test results table).
        Changes the command associated with the main start/stop button.
        Prevents mode switching if a test or prime sequence is currently running to avoid Arduino
        Communications errors. Resizes and centers the window after GUI changes.
        """

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

            if isinstance(self.valve_test_button, tk.Button):
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

            if isinstance(self.valve_test_button, tk.Button):
                self.valve_test_button.configure(
                    text="Start Testing",
                    bg="green",
                    command=lambda: self.start_testing_toggle(),
                )

        # resize the window to fit current content
        self.update_idletasks()
        GUIUtils.center_window(self)

    def create_interface(self) -> None:
        """
        Constructs and arranges all GUI elements within the window.

        Creates frames for structure, input fields (desired volume, actuations),
        the mode switch button, the valve selection buttons, the test results table,
        and the main start/abort/prime button. Uses `GUIUtils` for
        widget creation where possible. Calls helper methods `create_valve_test_table`
        and `create_buttons`. Centers the window after creation.
        """

        self.mode_button = GUIUtils.create_button(
            self,
            "Switch to Priming Mode",
            command=lambda: self.switch_window_mode(),
            bg="coral",
            row=0,
            column=0,
        )[1]

        # create a new frame to contain the desired dispensed volume label and frame
        self.dispensed_vol_frame = tk.Frame(self)
        self.dispensed_vol_frame.grid(row=1, column=0, padx=5, sticky="nsew")

        self.dispensed_vol_frame.grid_columnconfigure(0, weight=1)
        self.dispensed_vol_frame.grid_rowconfigure(0, weight=1)
        self.dispensed_vol_frame.grid_rowconfigure(1, weight=1)

        label = tk.Label(
            self.dispensed_vol_frame,
            text="Desired Dispensed Volume in Microliters (ul)",
            bg="light blue",
            font=("Helvetica", 20),
            highlightthickness=1,
            highlightbackground="dark blue",
            height=2,
            width=50,
        )
        label.grid(row=0, pady=5)

        entry = tk.Entry(
            self.dispensed_vol_frame,
            textvariable=self.desired_volume,
            font=("Helvetica", 24),
            highlightthickness=1,
            highlightbackground="black",
        )
        entry.grid(row=1, sticky="nsew", pady=5, ipady=14)

        # create another new frame to contain the amount of times each
        # valve should actuate label and frame
        frame = tk.Frame(self)
        frame.grid(row=2, column=0, padx=5, sticky="nsew")

        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=1)

        label = tk.Label(
            frame,
            text="How Many Times Should the Valve Actuate?",
            bg="light blue",
            font=("Helvetica", 20),
            highlightthickness=1,
            highlightbackground="dark blue",
            height=2,
            width=50,
        )
        label.grid(row=0, pady=5)

        entry = tk.Entry(
            frame,
            textvariable=self.actuations,
            font=("Helvetica", 24),
            highlightthickness=1,
            highlightbackground="black",
        )
        entry.grid(row=1, sticky="nsew", pady=5, ipady=12)

        ### ROW 3 ###
        self.create_valve_test_table()

        # setup frames for valve buttons
        self.valve_buttons_frame = tk.Frame(
            self, highlightbackground="black", highlightthickness=1
        )
        ### ROW 4 ###
        self.valve_buttons_frame.grid(row=4, column=0, pady=10, padx=10, sticky="nsew")
        self.valve_buttons_frame.grid_columnconfigure(0, weight=1)
        self.valve_buttons_frame.grid_rowconfigure(0, weight=1)

        self.side_one_valves_frame = tk.Frame(
            self.valve_buttons_frame, highlightbackground="black", highlightthickness=1
        )
        self.side_one_valves_frame.grid(row=0, column=0, pady=10, padx=10, sticky="w")
        self.side_one_valves_frame.grid_columnconfigure(0, weight=1)
        for i in range(4):
            self.side_one_valves_frame.grid_rowconfigure(i, weight=1)

        self.side_two_valves_frame = tk.Frame(
            self.valve_buttons_frame, highlightbackground="black", highlightthickness=1
        )
        self.side_two_valves_frame.grid(row=0, column=1, pady=10, padx=10, sticky="e")
        self.side_two_valves_frame.grid_columnconfigure(0, weight=1)
        for i in range(4):
            self.side_two_valves_frame.grid_rowconfigure(i, weight=1)

        ### ROW 5 ###
        self.create_buttons()

        self.update_idletasks()
        GUIUtils.center_window(self)

    def start_testing_toggle(self) -> None:
        """
        Handles the action of the main button when in Testing mode.

        If a test is running, it calls `abort_test()` and updates the button appearance.
        If no test is running, it calls `send_schedules()` to initiate a new test.
        """

        if self.test_running:
            if isinstance(self.valve_test_button, tk.Button):
                self.valve_test_button.configure(text="Start Testing", bg="green")
            self.abort_test()
        else:
            self.send_schedules()

    def create_buttons(self) -> None:
        """
        Creates and places the individual valve selection buttons and the main action button.

        Generates buttons for each valve (1 to TOTAL_VALVES), arranging them
        into side-one and side-two frames using `GUIUtils.create_button`.
        Assigns the `toggle_valve_button` command to each valve button.

        Creates the main 'Start Testing' / 'Start Priming' / 'Abort' button.
        """
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

    def create_valve_test_table(self) -> None:
        """
        Creates, configures, and populates the initial state of the ttk.Treeview table.

        Sets up the table columns ("Valve", "Amount Dispensed...", "Testing Opening Time...").
        Adds a button above the table to open the `ManualTimeAdjustment` window.

        Loads the currently selected valve durations from `models.arduino_data.ArduinoData`.
        Inserts initial rows for all possible valves, marking them as "Test Not Complete"
        and displaying their current duration. Stores row IDs in `self.table_entries` for later access.
        """

        # this function creates and labels the testing window table that displays the information recieved from the arduino reguarding the results of the tes
        self.valve_table_frame = tk.Frame(
            self, highlightbackground="black", highlightthickness=1
        )
        self.valve_table_frame.grid(row=3, column=0, sticky="nsew", pady=10, padx=10)
        # tell the frame to fill the available width
        self.valve_table_frame.grid_columnconfigure(0, weight=1)

        self.valve_table = ttk.Treeview(
            self.valve_table_frame, show="headings", height=12
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

    def update_table_entry_test_status(self, valve: int, l_per_lick: float) -> None:
        """
        Updates the 'Amount Dispensed Per Lick (ul)' column for a specific valve row.

        Parameters
        ----------
        - **valve** (*int*): The 1-indexed valve number whose row needs updating.
        - **l_per_lick** (*float*): The calculated volume dispensed per lick in milliliters (mL).
        """

        self.valve_table.set(
            self.table_entries[valve - 1], column=1, value=f"{l_per_lick * 1000} uL"
        )

    def update_table_entries(self) -> None:
        """
        Refreshes the entire valve test table based on current selections and durations.

        Hides rows for unselected valves and shows rows for selected valves.
        Reloads the latest durations from `ArduinoData` and updates the
        'Testing Opening Time' column for all visible rows. Resets the
        'Amount Dispensed' column to "Test Not Complete" for visible rows.
        """
        side_one, side_two, _ = self.arduino_data.load_durations()
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

    def toggle_valve_button(self, button: tk.Button, valve_num: int) -> None:
        """
        Handles the click event for a valve selection button.

        Toggles the button's visual state (raised/sunken). Updates the
        corresponding entry in the `self.valve_selections` numpy array (0 for
        deselected, valve_number + 1 for selected). Calls `update_table_entries`
        to refresh the table display. Filling arrays this way allows us to tell
        the arduino exactly which valves should be toggled (1, 4, 7) as long as
        their value in the array is not 0.

        Parameters
        ----------
        - **button** (*tk.Button*): The specific valve button widget that was clicked.
        - **valve_num** (*int*): The 0-indexed number of the valve corresponding to the button.
        """
        # Attempt to get the value to ensure it's a valid float as expected
        # If successful, call the function to update/create the valve test table
        if self.valve_selections[valve_num] == 0:
            button.configure(relief="sunken")
            self.valve_selections[valve_num] = valve_num + 1

        else:
            button.configure(relief="raised")
            self.valve_selections[valve_num] = 0
        self.update_table_entries()

    def verify_variables(self, original_data: bytes) -> bool:
        """
        Verifies that the Arduino correctly received the test/prime parameters.

        Waits for and reads back the schedule lengths and actuation count echoed
        by the Arduino. Compares the received bytes with the originally sent data.

        Parameters
        ----------
        - **original_data** (*bytes*): The byte string containing schedule lengths and actuation count originally sent to the Arduino.

        Returns
        -------
        - *bool*: `True` if the received data matches the original data, `False` otherwise (logs error and shows message box on mismatch).
        """
        # wait until all data is on the wire ready to be read (4 bytes),
        # then read it all in quick succession
        if self.arduino_controller.arduino is None:
            msg = "====INCORRECT SCHEDULE DETECTED, TRY AGAIN===="
            GUIUtils.display_error("TRANSMISSION ERROR", msg)
            logger.error(msg)
            return False

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

    def verify_schedule(
        self, len_sched: int, sent_schedule: npt.NDArray[np.int8]
    ) -> bool:
        """
        Verifies that the Arduino correctly received the valve schedule.

        Waits for and reads back the valve numbers (0-indexed) echoed byte-by-byte
        by the Arduino. Compares the reconstructed numpy array with the schedule
        that was originally sent.

        Parameters
        ----------
        - **len_sched** (*int*): The total number of valves in the schedule being sent.
        - **sent_schedule** (*npt.NDArray[np.int8]*): The numpy array (0-indexed valve numbers) representing the schedule originally sent.

        Returns
        -------
        - *bool*: `True` if the received schedule matches the sent schedule, `False` otherwise (logs error and shows message box on mismatch).
        """
        # np array used for verification later
        received_sched = np.zeros((len_sched,), dtype=np.int8)

        if self.arduino_controller.arduino is None:
            msg = "====INCORRECT SCHEDULE DETECTED, TRY AGAIN===="
            GUIUtils.display_error("TRANSMISSION ERROR", msg)
            logger.error(msg)
            return False

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

    def send_schedules(self) -> None:
        """
        Performs the process of sending test or prime configuration to the Arduino.

        Determines selected valves and schedule lengths for each side. Sends current
        valve durations to Arduino. Then sends the appropriate command ('TEST VOL' or 'PRIME VALVES').

        Sends test parameters (schedule lengths, actuations) and verifies them using `verify_variables`.
        Sends the actual valve schedule (0-indexed) and verifies it using `verify_schedule`.

        User is then prompted to confirm before proceeding.
        If confirmed, initiates the test/prime sequence on the Arduino
        and starts the listener thread (`run_test`) if Testing, or sends start command if Priming.
        Updates button states accordingly.
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

                if isinstance(self.valve_test_button, tk.Button):
                    self.valve_test_button.configure(
                        text="STOP Priming",
                        bg="gold",
                        command=lambda: self.stop_priming(),
                    )

    def stop_priming(self) -> None:
        """
        Sends the stop command to the Arduino during a priming sequence.

        Sets the `prime_running` flag to False. Updates the prime button state.
        Sends a byte representation of 1 (`np.int8(1).tobytes()`) to signal abort to the Arduino.
        """
        self.prime_running = False

        if isinstance(self.valve_test_button, tk.Button):
            self.valve_test_button.configure(
                text="Start Priming",
                bg="coral",
                command=lambda: self.send_schedules(),
            )

        stop = np.int8(1).tobytes()
        self.arduino_controller.send_command(command=stop)

    def take_input(
        self, event: tk.Event | None, pair_num_override: int | None = None
    ) -> None:
        """
        Prompts the user to enter the dispensed volume for a completed test pair.

        Determines which valve(s) were just tested based on the pair number received
        from the Arduino (via the event state or override). Uses `simpledialog.askfloat`
        to get the dispensed volume (in mL) for each valve in the pair. Stores the
        results in `self.ml_dispensed`.

        Sends a byte back to the Arduino to instruct if further pairs will be tested or if this is the final iteration,
        (1 if via event, 0 if via override/final pair).
        Handles potential abort if the user cancels the dialog window.

        Parameters
        ----------
        - **event** (*tk.Event | None*): Uses custom thread-safe event (`<<event1>>`) generated by `run_test`, carrying the pair number in `event.state`
        attribute. This is None if called directly by `testing_complete`, which indicated procedure is now finished.
        - **pair_num_override** (*int | None, optional*): Allows manually specifying the pair number, used when called from `testing_complete` for the
        final pair. Defaults to None.
        """
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

    def run_test(self) -> None:
        """
        Listens for messages from the Arduino during an active test sequence (runs in a background thread).

        Sends the initial 'start test' command byte to the Arduino. Enters a loop
        that continues as long as `self.test_running` is True and `self.stop_event`
        is not set. Checks for incoming data from the Arduino. Reads bytes indicating
        if more tests remain and the number of the just-completed pair. Generates
        custom Tkinter events (`<<event1>>` for input dispensed liquid prompt, `<<event0>>` for test completion)
        to communicate back to the main GUI thread safely. Updates the main button state to 'ABORT TESTING'.
        """
        if self.stop_event.is_set():
            self.stop_event.clear()

        if isinstance(self.valve_test_button, tk.Button):
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

    def abort_test(self) -> None:
        """
        Aborts an ongoing test sequence.

        Sets the `self.stop_event` to signal the `run_test` listener thread to exit.
        Sets `self.test_running` to False. Sends the abort *testing* command byte
        (`np.int8(0).tobytes()`) to the Arduino. Resets the main button state to 'Start Testing'.
        """
        # if test is aborted, stop the test listener thread
        if isinstance(self.valve_test_button, tk.Button):
            self.valve_test_button.configure(text="Start Testing", bg="green")

        self.stop_event.set()
        self.test_running = False
        ###====SENDING ABORT TEST COMMAND====###
        command = np.int8(0).tobytes()
        self.arduino_controller.send_command(command)

    def testing_complete(self, event: tk.Event) -> None:
        """
        Handles the final steps after the Arduino signals test completion.

        Calls `take_input` one last time for the final test pair (using `pair_num_override`).

        Resets the main button state and `self.test_running` flag. Sets the
        `self.stop_event` to ensure the listener thread terminates cleanly.
        Calls `auto_update_durations` to process the collected data and suggest timing changes.

        Parameters
        ----------
        - **event** (*tk.Event*): The custom event (`<<event0>>`) generated by `run_test`, carrying the final pair number in `event.state`.
        """
        # take input from last pair/valve
        self.take_input(event=None, pair_num_override=event.state)
        # reconfigure the testing button and testing state
        if isinstance(self.valve_test_button, tk.Button):
            self.valve_test_button.configure(text="Start Testing", bg="green")

        self.test_running = False
        # stop the arduino testing listener thread
        self.stop_event.set()

        # update valves and such
        self.auto_update_durations()

    def auto_update_durations(self):
        """
        This function is similar to the `views.valve_testing.manual_time_adjustment_window.ManualTimeAdjustment.write_timing_changes` function, it
        calculates new valve durations based on test results and desired volume.

        Loads the current 'selected' durations. Iterates through the collected
        `self.ml_dispensed` data. For each tested valve, it calculates the actual
        volume dispensed per actuation and compares it to the desired volume per actuation.
        It computes a new duration using a ratio (`new_duration = old_duration * (desired_vol / actual_vol)`).

        Updates the corresponding duration in the local copies of the side_one/side_two arrays.
        Updates the table display for the valve using `update_table_entry_test_status`.
        Compiles a list of changes (`changed_durations`) and opens the `ValveChanges`
        confirmation window, passing the changes and the `confirm_valve_changes` callback.
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

    def confirm_valve_changes(
        self,
        side_one: npt.NDArray[np.int32],
        side_two: npt.NDArray[np.int32],
        side_one_old: npt.NDArray[np.int32],
        side_two_old: npt.NDArray[np.int32],
    ):
        """
        Callback function executed when changes are confirmed in the ValveChanges window.

        Instructs `self.arduino_data` to first save the `side_one_old` and `side_two_old`
        arrays to an archive slot, and then save the newly calculated `side_one` and `side_two`
        arrays as the 'selected' durations.

        Parameters
        ----------
        - **side_one** (*npt.NDArray[np.int32]*): The numpy array containing the newly calculated durations for side one valves.
        - **side_two** (*npt.NDArray[np.int32]*): The numpy array containing the newly calculated durations for side two valves.
        - **side_one_old** (*npt.NDArray[np.int32]*): The numpy array containing the durations for side one valves *before* the test.
        - **side_two_old** (*npt.NDArray[np.int32]*): The numpy array containing the durations for side two valves *before* the test.
        """
        self.arduino_data.save_durations(side_one_old, side_two_old, "archive")
        self.arduino_data.save_durations(side_one, side_two, "selected")
