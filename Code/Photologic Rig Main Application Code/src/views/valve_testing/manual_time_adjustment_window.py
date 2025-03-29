"""
This module defines the ManualTimeAdjustment class, a Tkinter Toplevel window
responsible for allowing users to view, modify, and save valve open duration
timings used by the Arduino controller.

It provides an interface to load different timing profiles (default, last used,
archived), edit individual valve timings (in microseconds), and save the
updated configuration, which also involves archiving the previously active
timings. It relies on configuration loaded via `system_config` and interacts
with an `models.arduino_data` object so that the Arduino can 'remember' durations
over many experiments.
"""

import tkinter as tk
from tkinter import ttk
import numpy as np
import toml
from models.arduino_data import ArduinoData
import system_config
import logging

from views.gui_common import GUIUtils

###TYPE HINTS###
import numpy.typing as npt
import datetime
###TYPE HINTS###

logger = logging.getLogger()

rig_config = system_config.get_rig_config()

with open(rig_config, "r") as f:
    VALVE_CONFIG = toml.load(f)["valve_config"]

# pull total valves constant from toml config
TOTAL_VALVES = VALVE_CONFIG["TOTAL_CURRENT_VALVES"]

VALVES_PER_SIDE = TOTAL_VALVES // 2


class ManualTimeAdjustment(tk.Toplevel):
    """
    Implements a Tkinter Toplevel window for manually adjusting valve open durations.

    This window allows users to:
    - Select and load different valve timing profiles (Default, Last Used, Archives).
    - View and edit the open duration (in microseconds) for each valve.
    - Save the modified timings, which automatically archives the previously
      'selected' timings and sets the new ones as 'selected'.

    It interacts with `models.arduino_data` object (passed during initialization)
    to load and persist timing configurations. Uses `views.gui_common.GUIUtils` for standard
    widget creation and layout.

    Attributes
    ----------
    - **arduino_data** (*ArduinoData*): This is a reference to the program instance of `models.arduino_data` ArduinoData. It allows access to this
    class and its methods which allows for the loading of data stored there such as valve duration times and schedule indicies.
    - **`tk_vars`** (*dict[str, tk.IntVar]*): Dictionary mapping valve names (e.g., "Valve 1") to Tkinter IntVars holding their durations.
    - **`labelled_entries`** (*list[tuple OR None]*): List storing tuples of (Frame, Label, Entry) widgets for each valve timing input. Stored to make possible later
    modification of the widgets.
    - **`dropdown`** (*ttk.Combobox*): Widget for selecting the duration profile to load/view.
    - **`date_used_label`** (*tk.Label*): Label displaying the timestamp of the currently loaded profile.
    - **`timing_frame`** (*tk.Frame*): Frame containing the grid of labeled entries for valve timings.
    - **`save_changes_bttn`** (*tk.Button*): Button to trigger the save operation.
    - **`duration_types`** (*dict[str, str]*): Maps user friendly display names in the dropdown to internal keys used for loading profiles.

    Methods
    -------
    - `show`()
        Updates the interface with the latest data and makes the window visible.
    - `update_interface`(...)
        Callback for dropdown selection; loads and displays the chosen timing profile.
    - `create_dropdown`()
        Creates and configures the Combobox for selecting duration profiles.
    - `create_interface`(...)
        Constructs the main GUI layout, including labels, dropdown, entry fields, and buttons.
    - `fill_tk_vars`(...)
        Populates `self.tk_vars` with Tkinter variables based on loaded duration arrays.
    - `write_timing_changes`()
        Handles archiving old timings, validating user input, and saving new timings in 'selected' profile.
    """

    def __init__(self, arduino_data: ArduinoData):
        """
        Initializes the ManualTimeAdjustment Toplevel window.

        Parameters
        ----------
        - **arduino_data** (*ArduinoData*): Reference to program instance of `models.arduino_data.ArduinoData`, used for loading and saving valve durations.

        Raises
        ------
        - Propagates exceptions from `GUIUtils` methods during icon setting.
        - Propagates exceptions from `arduino_data.load_durations()`.
        """
        super().__init__()

        self.arduino_data = arduino_data

        self.title("Manual Valve Timing Adjustment")
        self.bind("<Control-w>", lambda event: self.withdraw())

        self.resizable(False, False)

        self.tk_vars: dict[str, tk.IntVar] = {}
        self.labelled_entries: list[tuple | None] = [None] * TOTAL_VALVES

        # load default 'selected' dur profile
        side_one, side_two, date_used = self.arduino_data.load_durations()

        self.fill_tk_vars(side_one, side_two)
        self.create_interface(date_used)

        window_icon_path = GUIUtils.get_window_icon_path()
        GUIUtils.set_program_icon(self, icon_path=window_icon_path)

    def show(self):
        """
        Updates the interface with either default 'Last Used' profile data or selected profile from dropdown and makes the window visible.
        """
        self.update_interface(event=None)
        self.deiconify()

    def update_interface(self, event: tk.Event | None):
        """
        Loads and displays the valve timings based on the selected profile from the dropdown.

        If `event` is None (e.g., called from `show`), it loads the 'Last Used'
        profile. Otherwise, it uses the profile selected in the dropdown. Updates
        the *tk.IntVar* variables, which refreshes the Entry widgets, and updates
        the 'date last used' label.

        Parameters
        ----------
        - **event** (*tk.Event | None*): The Combobox selection event, or None to default
          to loading the 'Last Used' profile.

        Raises
        ------
        - Propagates exceptions from `arduino_data.load_durations()`.
        """

        # event is the selection event of the self.combobox. using .get gets the self.duration_type dict key
        load_durations_key = None
        if event is None:
            load_durations_key = self.duration_types["Last Used"]
        else:
            load_durations_key = self.duration_types[f"{event.widget.get()}"]

        side_one, side_two, _ = self.arduino_data.load_durations(load_durations_key)

        # set default durations for side one
        for i, duration in enumerate(side_one):
            self.tk_vars[f"Valve {i + 1}"].set(duration)
        # set default durations for side two
        for i, duration in enumerate(side_two):
            self.tk_vars[f"Valve {i + 8 + 1}"].set(duration)

    def create_dropdown(self):
        """
        Creates the `ttk.Combobox` widget for selecting duration profiles.

        Populates the dropdown with user-friendly names for duration profiles and maps them to keys in
        `self.duration_types` dict, sets the default selection to 'Last Used',
        and binds the selection event to `self.update_interface`.
        """
        self.duration_types = {
            "Default": "default_durations",
            "Last Used": "selected_durations",
            "(most recent) Archive 1": "archive_1",
            "Archive 2": "archive_2",
            "(oldest) Archive 3": "archive_3",
        }
        self.dropdown = ttk.Combobox(self, values=list(self.duration_types.keys()))
        self.dropdown.current(1)
        self.dropdown.grid(row=1, column=0, sticky="e", padx=10)
        self.dropdown.bind("<<ComboboxSelected>>", lambda e: self.update_interface(e))

    def create_interface(self, date_used: datetime.datetime):
        """
        Constructs the main GUI elements within the Toplevel window.

        Creates labels, the duration profile dropdown, the grid of labeled
        entries for valve timings, and the save button. Uses `views.gui_common.GUIUtils` for
        widget creation.

        Parameters
        ----------
        - **date_used** (*datetime.datetime*): The timestamp for date selected profile was created,
          used to populate the date label.

        Raises
        ------
        - Propagates exceptions from `GUIUtils` methods during widget creation.
        """
        warning = tk.Label(
            self,
            text="ALL TIMINGS IN MICROSECONDS (e.g 24125 equivalent to 24.125 ms)",
            bg="white",
            fg="black",
            font=("Helvetica", 15),
            highlightthickness=1,
            highlightbackground="black",
        )

        warning.grid(row=0, column=0, sticky="nsew", pady=10, padx=10)

        self.create_dropdown()

        formatted_date = date_used.strftime("%B/%d/%Y")
        formatted_time = date_used.strftime("%I:%M %p")
        self.date_used_label = tk.Label(
            self,
            text=f"Timing profile created on: {formatted_date} at {formatted_time}",
            bg="white",
            fg="black",
            font=("Helvetica", 15),
            highlightthickness=1,
            highlightbackground="black",
        )
        self.date_used_label.grid(row=1, column=0, sticky="w", padx=10)

        self.timing_frame = tk.Frame(
            self, highlightbackground="black", highlightthickness=1
        )

        self.timing_frame.grid(row=2, column=0, pady=10, padx=10, sticky="nsew")
        self.timing_frame.grid_columnconfigure(0, weight=1)

        for i in range(VALVES_PER_SIDE):
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
                f"Valve {i + (VALVES_PER_SIDE) + 1} Open Time",
                self.tk_vars[f"Valve {i + (TOTAL_VALVES) + 1}"],
                i,
                1,
            )

        warning = tk.Label(
            self,
            text="This action will archive the current timing configuration into assets/valve_durations.toml\n and set these new timings to selected timings",
            bg="white",
            fg="black",
            font=("Helvetica", 15),
            highlightthickness=1,
            highlightbackground="black",
        )

        warning.grid(row=3, column=0, padx=10)
        self.save_changes_bttn = GUIUtils.create_button(
            self,
            "Write Timing Changes",
            lambda: self.write_timing_changes(),
            bg="green",
            row=4,
            column=0,
        )[1]

    def fill_tk_vars(
        self, side_one: npt.NDArray[np.int32], side_two: npt.NDArray[np.int32]
    ):
        """
        Populates the `self.tk_vars` dictionary with *tk.IntVar* objects.

        Initializes each *tk.IntVar* with the corresponding duration value
        loaded from the provided numpy arrays (`side_one`, `side_two`). These
        variables are then linked to the Entry widgets in the UI.

        Parameters
        ----------
        - **side_one** (*np.ndarray*): Numpy array of np.int32 durations for the first side of valves.
        - **side_two** (*np.ndarray*): Numpy array of np.int32 durations for the second side of valves.
        """

        for i, duration in enumerate(side_one):
            self.tk_vars[f"Valve {i + 1}"] = tk.IntVar(value=duration)
        for i, duration in enumerate(side_two):
            self.tk_vars[f"Valve {i + 9}"] = tk.IntVar(value=duration)

    def write_timing_changes(self):
        """
        Archives the current 'selected' timings, validates the user-entered
        timings, and saves the new timings as the 'selected' profile.

        Retrieves values from the Entry widgets via their linked *tk.IntVar*s.
        Performs basic validation (checks for empty fields). If valid, it
        instructs `models.arduino_data` to archive the old 'selected' profile and
        save the new profile as 'selected'. Displays error messages on failure.

        Raises
        ------
        - Propagates exceptions from `arduino_data.load_durations()` or
          `arduino_data.save_durations()`.
        """
        side_one, side_two, _ = self.arduino_data.load_durations()

        ## save durations in the oldest valve duration archival location
        self.arduino_data.save_durations(side_one, side_two, "archive")

        timings = [GUIUtils.safe_tkinter_get(value) for value in self.tk_vars.values()]

        # check if one of the fields are empty
        if None in timings:
            msg = "ONE OR MORE FIELDS ARE EMPTY, FILL BEFORE TRYING ANOTHER ADJUSTMENT"
            logger.error(msg)
            GUIUtils.display_error("FIELD ERROR", msg)
            return

        # using total possible valves per side here (maximum of 16 valves) for future proofing
        side_one_new = np.full(8, np.int32(0))
        side_two_new = np.full(8, np.int32(0))

        for i in range(len(timings) // 2):
            side_one_new[i] = timings[i]
            side_two_new[i] = timings[i + 8]

        # save new durations in the selected slot of the configuration file
        self.arduino_data.save_durations(side_one_new, side_two_new, "selected")
