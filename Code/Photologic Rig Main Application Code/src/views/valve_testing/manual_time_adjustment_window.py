import tkinter as tk
from tkinter import ttk
import numpy as np
import toml
from pathlib import Path

from views.gui_common import GUIUtils

toml_config_dir = Path(__file__).parent.parent.parent.resolve()
toml_config_path = toml_config_dir / "rig_config.toml"
with open(toml_config_path, "r") as f:
    VALVE_CONFIG = toml.load(f)["valve_config"]

# pull total valves constant from toml config
TOTAL_VALVES = VALVE_CONFIG["TOTAL_CURRENT_VALVES"]

VALVES_PER_SIDE = TOTAL_VALVES // 2


class ManualTimeAdjustment(tk.Toplevel):
    def __init__(self, arduino_data, valve_selections):
        super().__init__()

        self.arduino_data = arduino_data

        self.title("Manual Valve Timing Adjustment")
        self.bind("<Control-w>", lambda event: self.withdraw())

        self.resizable(False, False)

        self.tk_vars = {}
        self.labelled_entries = [None] * 8

        # load default 'selected' dur profile
        side_one, side_two, date_used = self.arduino_data.load_durations()

        self.fill_tk_vars(side_one, side_two)
        self.create_interface(valve_selections, date_used)

        window_icon_path = GUIUtils.get_window_icon_path()
        GUIUtils.set_program_icon(self, icon_path=window_icon_path)

    def show(self):
        self.deiconify()

    def update_interface(self, event):
        # event is the selection event of the self.combobox. using .get gets the self.duration_type dict key
        load_durations_key = self.duration_types[f"{event.widget.get()}"]

        side_one, side_two, date_used = self.arduino_data.load_durations(
            load_durations_key
        )

        for i, duration in enumerate(side_one):
            self.tk_vars[f"Valve {i + 1}"].set(duration)
        for i, duration in enumerate(side_two):
            self.tk_vars[f"Valve {i + 9}"].set(duration)

    def create_dropdown(self):
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

    def create_interface(self, valve_selections, date_used):
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

    def fill_tk_vars(self, side_one, side_two):
        """
        in this function we fill self.tk_vars dictionary with tk.IntVar objects usable in tkinter entry objects. we fill these
        variables by default with the selected durations saved in the toml configuration file for the arduino timings.
        """

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
