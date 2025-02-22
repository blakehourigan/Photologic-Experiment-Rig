import tkinter as tk
from tkinter import ttk

from views.gui_common import GUIUtils


class LicksWindow(tk.Toplevel):
    def __init__(self) -> None:
        super().__init__()

        self.title("Licks Data")
        self.bind("<Control-w>", lambda event: self.withdraw())
        # Bind closing the window to self.withdraw()
        self.protocol("WM_DELETE_WINDOW", self.withdraw())

        window_icon_path = GUIUtils.get_window_icon_path()
        GUIUtils.set_program_icon(self, icon_path=window_icon_path)

        self.withdraw()

    def show_table(self) -> None:
        self.licks_frame = tk.Frame(self.top)
        self.licks_frame.grid(row=0, column=0, sticky="nsew")

        # Create a Treeview widget
        self.stamped_licks = ttk.Treeview(
            self.licks_frame, show="headings"
        )  # Set show='headings'
        self.stamped_licks["columns"] = list(
            self.controller.data_mgr.licks_dataframe.columns
        )

        # Configure the columns
        for col in self.stamped_licks["columns"]:
            self.stamped_licks.heading(col, text=col)

        # Insert data from the DataFrame
        for _, row in self.controller.data_mgr.licks_dataframe.iterrows():
            self.stamped_licks.insert("", "end", values=list(row))

        self.stamped_licks.pack(fill="both", expand=True)
