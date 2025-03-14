import tkinter as tk
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


class ValveChanges(tk.Toplevel):
    def __init__(self, valve_changes, confirm_callback):
        super().__init__()
        self.title("CONFIRM VALVE DURATION CHANGES")
        self.bind("<Control-w>", lambda event: self.withdraw())
        self.grid_columnconfigure(0, weight=1)
        self.resizable(False, False)

        self.valve_changes = valve_changes
        self.confirm_callback = confirm_callback

        self.create_interface()
        self.update_idletasks()
        GUIUtils.center_window(self)

        window_icon_path = GUIUtils.get_window_icon_path()
        GUIUtils.set_program_icon(self, icon_path=window_icon_path)

    def create_interface(self):
        self.valve_frame = tk.Frame(
            self, highlightbackground="black", highlightthickness=1
        )

        self.valve_frame.grid(row=0, column=0, pady=10, padx=10, sticky="nsew")
        self.valve_frame.grid_columnconfigure(0, weight=1)
        self.valve_frame.grid_rowconfigure(1, weight=1)

        self.side_one_valves_frame = tk.Frame(
            self.valve_frame, highlightbackground="black", highlightthickness=1
        )
        self.side_one_valves_frame.grid(row=0, column=0, pady=10, padx=10, sticky="w")
        self.valve_frame.grid_columnconfigure(0, weight=1)
        self.valve_frame.grid_rowconfigure(1, weight=1)

        self.side_two_valves_frame = tk.Frame(
            self.valve_frame, highlightbackground="black", highlightthickness=1
        )
        self.side_two_valves_frame.grid(row=0, column=1, pady=10, padx=10, sticky="e")
        self.valve_frame.grid_columnconfigure(0, weight=1)
        self.valve_frame.grid_rowconfigure(1, weight=1)

        self.create_valve_change_labels()

        confirm = tk.Button(
            self,
            text="Confirm Changes",
            command=lambda: self.confirmation(),
            bg="green",
            font=("Helvetica", 24),
        )
        confirm.grid(row=1, column=0, sticky="w", ipadx=10, ipady=10)

        abort = tk.Button(
            self,
            text="ABORT CHANGES",
            command=lambda: self.destroy(),
            bg="tomato",
            font=("Helvetica", 24),
        )
        abort.grid(row=1, column=0, sticky="e", ipadx=10, ipady=10)

    def confirmation(self):
        self.confirm_callback()
        self.destroy()

    def create_valve_change_labels(self):
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
            )
            label.grid(row=row, column=column, padx=10, pady=10, sticky="nsew")

            label = tk.Label(
                frame,
                text=f"From {old_duration} --> {new_duration}",
                bg="light blue",
                font=("Helvetica", 24),
                highlightthickness=1,
                highlightbackground="dark blue",
            )
            label.grid(row=row + 1, column=column, padx=10, pady=10, sticky="nsew")

            if valve <= VALVES_PER_SIDE:
                side_one_row += 2
            else:
                side_two_row += 2
