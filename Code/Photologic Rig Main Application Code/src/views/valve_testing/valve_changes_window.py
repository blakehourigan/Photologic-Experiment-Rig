import tkinter as tk
import toml
import system_config

from views.gui_common import GUIUtils


rig_config = system_config.get_rig_config()

with open(rig_config, "r") as f:
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
