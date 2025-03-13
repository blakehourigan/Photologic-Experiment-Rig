import tkinter as tk

from views.gui_common import GUIUtils


class ValveChanges(tk.Toplevel):
    def __init__(self, valve_changes, confirm_callback):
        super().__init__()
        self.title("CONFIRM VALVE DURATION CHANGES")
        self.bind("<Control-w>", lambda event: self.withdraw())

        self.valve_changes = valve_changes
        self.confirm_callback = confirm_callback

        self.create_interface()

        window_icon_path = GUIUtils.get_window_icon_path()
        GUIUtils.set_program_icon(self, icon_path=window_icon_path)

    def create_interface(self):
        self.valve_frame = tk.Frame(
            self, highlightbackground="black", highlightthickness=1
        )

        self.valve_frame.grid(row=3, column=0, pady=10, padx=10, sticky="nsew")
        self.valve_frame.grid_columnconfigure(0, weight=1)

        self.side_one_valves_frame = tk.Frame(
            self.valve_frame, highlightbackground="black", highlightthickness=1
        )
        self.side_one_valves_frame.grid(row=0, column=0, pady=10, padx=10, sticky="w")
        self.side_one_valves_frame.grid_columnconfigure(0, weight=1)

        self.side_two_valves_frame = tk.Frame(
            self.valve_frame, highlightbackground="black", highlightthickness=1
        )
        self.side_two_valves_frame.grid(row=0, column=1, pady=10, padx=10, sticky="e")
        self.side_two_valves_frame.grid_columnconfigure(0, weight=1)

        valve = None
        frame = None
        side_one_row = 0
        side_two_row = 0
        column = 0

        for valve, durations in self.valve_changes:
            valve = valve
            old_duration = durations[0]
            new_duration = durations[1]
            print(valve, old_duration, new_duration)

            if valve <= 4:
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
                bg="light blue",
                font=("Helvetica", 24),
                highlightthickness=1,
                highlightbackground="dark blue",
            )
            label.grid(row=row, column=column, pady=10)
            label = tk.Label(
                frame,
                text=f"From {old_duration} --> {new_duration}",
                bg="light blue",
                font=("Helvetica", 24),
                highlightthickness=1,
                highlightbackground="dark blue",
            )
            label.grid(row=row + 1, column=column, pady=10)

            if valve <= 4:
                side_one_row += 2
            else:
                side_two_row += 2

            GUIUtils.center_window(self)
