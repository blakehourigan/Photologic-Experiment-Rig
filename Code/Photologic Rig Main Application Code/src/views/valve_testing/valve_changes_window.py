"""
This module defines the ValveChanges class, a Tkinter Toplevel window designed
to act as a confirmation dialog window for auto-generated valve timing adjustments.

It presents the user with a summary of proposed changes to valve open durations
before they are applied to the system configuration.
The user can either confirm the changes, triggering a callback function to `views.valve_testing.valve_testing_window`, or
abort the changes, closing the dialog without further action. It relies on
`system_config` for valve configuration and `views.gui_common.GUIUtils` for
standard widget creation and window management.
"""

import tkinter as tk
import toml
import system_config

###TYPE HINTS###
from typing import Callable
###TYPE HINTS###

from views.gui_common import GUIUtils


rig_config = system_config.get_rig_config()

with open(rig_config, "r") as f:
    VALVE_CONFIG = toml.load(f)["valve_config"]

# pull total valves constant from toml config
TOTAL_VALVES = VALVE_CONFIG["TOTAL_CURRENT_VALVES"]

VALVES_PER_SIDE = TOTAL_VALVES // 2


# lambda: self.confirm_valve_changes(side_one, side_two, side_one_old, side_two_old
class ValveChanges(tk.Toplevel):
    """
    Implements a Tkinter Toplevel window to display and confirm proposed valve duration changes.

    This window acts as a confirmation step, showing the user which valves are
    being changed and their old vs. new duration values (in microseconds).
    It provides "Confirm Changes" and "ABORT CHANGES" buttons. Confirming
    triggers a callback function passed during initialization; aborting simply
    destroys the window. Uses `views.gui_common.GUIUtils` for window centering and icon setting.

    Attributes
    ----------
    - **`valve_changes`** (*List[Tuple[int, Tuple[int, int]]]*): A list where each element is a tuple containing the valve number (int)
        and another tuple with (old_duration, new_duration).
    - **`confirm_callback`** (*Callable*): The function to execute when the "Confirm Changes" button is pressed.
    - **`valve_frame`** (*tk.Frame*): The main container frame holding the side-by-side valve change displays.
    - **`side_one_valves_frame`** (*tk.Frame*): Frame displaying changes for valves on the first side (e.g., 1-8).
    - **`side_two_valves_frame`** (*tk.Frame*): Frame displaying changes for valves on the second side (e.g., 9-16).
    - **`buttons_frame`** (*tk.Frame*): Frame containing the Confirm and Abort buttons.

    Methods
    -------
    - `create_interface`()
        Constructs the main GUI layout, including frames and buttons.
    - `confirmation`()
        Executes the stored callback function and then destroys the window.
    - `create_valve_change_labels`()
        Populates the side frames with labels detailing the old and new duration for each changed valve.
    """

    def __init__(
        self,
        valve_changes: list[tuple[int, tuple[int, int]]],
        confirm_callback: Callable,
    ):
        """
        Initializes the ValveChanges confirmation Toplevel window.

        Parameters
        ----------
        - **valve_changes** (*List[Tuple[int, Tuple[int, int]]]*): A list containing tuples for each valve change.
          Each inner tuple has the format `(valve_number, (old_duration_microseconds, new_duration_microseconds))`.
        - **confirm_callback** (*Callable*): The function that should be called if the user confirms the changes.
          This function takes no arguments.

        Raises
        ------
        - Propagates exceptions from `GUIUtils` methods during icon setting or window centering.
        """
        super().__init__()
        self.title("CONFIRM VALVE DURATION CHANGES")
        self.bind("<Control-w>", lambda event: self.withdraw())

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.grid_rowconfigure(0, weight=1)

        self.resizable(False, False)

        self.valve_changes = valve_changes
        self.confirm_callback = confirm_callback

        self.create_interface()

        self.update_idletasks()
        GUIUtils.center_window(self)

        window_icon_path = GUIUtils.get_window_icon_path()
        GUIUtils.set_program_icon(self, icon_path=window_icon_path)

    def create_interface(self):
        """
        Constructs the main GUI elements within the Toplevel window.

        Creates the frames to hold the valve change information side-by-side,
        populates them using `create_valve_change_labels`, and adds the
        'Confirm' and 'Abort' buttons.
        """

        self.valve_frame = tk.Frame(
            self, highlightbackground="black", highlightthickness=1
        )

        self.valve_frame.grid(row=0, column=0, pady=10, padx=10, sticky="nsew")

        self.valve_frame.grid_columnconfigure(0, weight=1)
        self.valve_frame.grid_columnconfigure(1, weight=1)

        self.valve_frame.grid_rowconfigure(0, weight=1)

        self.side_one_valves_frame = tk.Frame(
            self.valve_frame, highlightbackground="black", highlightthickness=1
        )
        self.side_one_valves_frame.grid(row=0, column=0, pady=10, padx=10, sticky="ew")

        self.side_two_valves_frame = tk.Frame(
            self.valve_frame, highlightbackground="black", highlightthickness=1
        )
        self.side_two_valves_frame.grid(row=0, column=1, pady=10, padx=10, sticky="ew")

        for i in range(2):
            self.side_one_valves_frame.grid_columnconfigure(i, weight=1)
            self.side_two_valves_frame.grid_columnconfigure(i, weight=1)

        for i in range(8):
            self.side_one_valves_frame.grid_rowconfigure(i, weight=1)
            self.side_two_valves_frame.grid_rowconfigure(i, weight=1)

        self.create_valve_change_labels()

        self.buttons_frame = tk.Frame(
            self, highlightbackground="black", highlightthickness=1
        )
        self.buttons_frame.grid(row=1, column=0, pady=10, padx=10, sticky="ew")
        self.buttons_frame.grid_rowconfigure(0, weight=1)
        self.buttons_frame.grid_columnconfigure(0, weight=1)
        self.buttons_frame.grid_columnconfigure(1, weight=1)

        confirm = tk.Button(
            self.buttons_frame,
            text="Confirm Changes",
            command=lambda: self.confirmation(),
            bg="green",
            font=("Helvetica", 20),
            width=20,
        )
        confirm.grid(row=0, column=0, sticky="w", padx=5, ipadx=10, ipady=10)

        abort = tk.Button(
            self.buttons_frame,
            text="ABORT CHANGES",
            command=lambda: self.destroy(),
            bg="tomato",
            font=("Helvetica", 20),
            width=20,
        )
        abort.grid(row=0, column=1, sticky="e", padx=5, ipadx=10, ipady=10)

    def confirmation(self):
        """
        Handles the confirmation action.

        Executes the `confirm_callback` function that was provided during
        class initialization and then closes (destroys) this confirmation window.
        """
        self.confirm_callback()
        self.destroy()

    def create_valve_change_labels(self):
        """
        Generates and places the labels detailing each valve duration change.

        Iterates through the `self.valve_changes` list. For each change, it
        determines which side frame (left or right) the valve belongs to and
        creates two labels: one for the valve number and one showing the
        'From old_duration --> new_duration' information. Labels are placed
        in sequence within the appropriate side frame.
        """

        valve = None
        frame = None
        side_one_row = 0
        side_two_row = 0
        column = 0

        for valve, durations in self.valve_changes:
            valve = valve
            old_duration = durations[0]
            new_duration = durations[1]

            if valve <= VALVES_PER_SIDE:
                frame = self.side_one_valves_frame
                row = side_one_row
                column = 0
            else:
                frame = self.side_two_valves_frame
                row = side_two_row
                column = 1

            label = tk.Label(
                frame,
                text=f"Valve {valve}",
                bg="grey",
                font=("Helvetica", 24),
                highlightthickness=1,
                highlightbackground="dark blue",
                height=3,
                width=26,
            )
            label.grid(row=row, column=column, padx=10, pady=10, sticky="nsew")

            label = tk.Label(
                frame,
                text=f"From {old_duration} --> {new_duration}",
                bg="light blue",
                font=("Helvetica", 24),
                highlightthickness=1,
                highlightbackground="dark blue",
                height=3,
                width=26,
            )
            label.grid(row=row + 1, column=column, padx=10, pady=10, sticky="nsew")

            if valve <= VALVES_PER_SIDE:
                side_one_row += 2
            else:
                side_two_row += 2
