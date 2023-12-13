from typing import Optional
from tkinter import ttk
import tkinter as tk


class valveTestWindow:
    def __init__(self, controller):
        self.controller = controller
        self.master = controller.main_gui.root

        self.test_logic = valveTestLogic(controller)

        self.top: Optional[tk.Toplevel] = None

        self.num_valves_to_test = tk.IntVar(value=0)
        self.num_valves_to_test.trace(
            "w", self.create_valve_test_table
        )  # we call create table, whenever the number of valves to test is changed

        self.min_valve = 1
        self.max_valve = 8

        self.table_exists = False

    def create_window(self, master) -> tk.Toplevel:
        # Create a new window for AI solutions
        top = tk.Toplevel(master)
        top.title("Valve Testing")
        top.bind(
            "<Control-w>", lambda e: top.destroy()
        )  # Close the window when the user presses ctl + w
        return top

    def show_window(self) -> None:
        # if the number of simuli is currently set to zero, tell the user that they need to add stmiuli before we can more forward
        if self.controller.data_mgr.num_stimuli.get() > 0:
            if self.top is not None and self.top.winfo_exists():
                self.top.lift()
            else:
                self.top = self.create_window(self.master)
                self.configure_tk_obj_grid(self.top)
                self.top.protocol(
                    "WM_DELETE_WINDOW", self.on_window_close
                )  # Bind the close event

                self.configure_grid()
                self.create_labels()
                self.create_entry_widgets()
                self.create_valve_test_table()
                self.create__start_button()

        self.update_size()

    def configure_grid(self) -> None:
        if self.top is not None:
            for i in range(12):
                self.top.grid_rowconfigure(i, weight=0)
            # The first column is also configured to expand
            # Configure all columns to have equal weight
            for i in range(1):
                self.top.columnconfigure(i, weight=1)

    def create_labels(self) -> None:
        self.number_valves_frame = tk.Frame(self.top)
        self.number_valves_frame.grid(row=0, column=0, pady=10, padx=10, sticky="nsew")

        self.number_valves_label = tk.Label(
            self.number_valves_frame,
            text="Number of Valves to Test",
            bg="light blue",
            font=("Helvetica", 16),
            wraplength=150,
        )
        self.number_valves_label.pack(
            side="left", expand=True, fill="both", anchor="center"
        )

    def create_entry_widgets(self) -> None:
        self.number_valves_entry_frame = tk.Frame(self.top)
        self.number_valves_entry_frame.grid(
            row=1, column=0, pady=10, padx=10, sticky="nsew"
        )

        self.number_valves_entry = tk.Entry(
            self.number_valves_frame,
            textvariable=self.num_valves_to_test,
            font=("Helvetica", 18),
            width=10,
        )
        self.number_valves_entry.pack(
            side="right", expand=True, fill="both", anchor="center", padx=10
        )

    def create_valve_test_table(self, *args) -> None:
        if self.num_valves_to_test.get() in range(self.min_valve, self.max_valve + 1):
            self.valve_table = ttk.Treeview(self.top)

            # Define columns
            self.valve_table["columns"] = ("1", "2")

            # Format our columns
            self.valve_table.column("#0", width=150, minwidth=150, stretch=tk.NO)
            self.valve_table.column("1", width=150, minwidth=150, stretch=tk.NO)
            self.valve_table.column("2", width=150, minwidth=150, stretch=tk.NO)

            # Define headings
            self.valve_table.heading("#0", text="Valve", anchor="center")
            self.valve_table.heading("1", text="Amount Dispensed", anchor="center")
            self.valve_table.heading("2", text="Average Opening time", anchor="center")

            self.insert_rows_into_table()

            self.valve_table.grid(row=2, column=0, pady=10, padx=10, sticky="nsew")

            self.update_size()
            self.table_exists = True
        else:
            if self.table_exists:
                self.controller.main_gui.display_error(
                    "Invalid Number of Valves", "Please enter a number between 1 and 8"
                )

    def insert_rows_into_table(self) -> None:
        for i in range(self.num_valves_to_test.get()):
            self.valve_table.insert(
                "",
                "end",
                text=f"Valve {i+1}",
                values=(
                    f"{self.test_logic.default_measured_volume}ml",
                    f"{self.test_logic.default_valve_opening_time}s",
                ),
            )  # Add items to our treeview

    def create__start_button(self) -> None:
        # Start test button
        self.start_test_frame = tk.Frame(self.top, width=150, height=50)
        self.start_test_frame.grid(row=3, column=0, pady=10, padx=10, sticky="nsew")
        self.startButton = tk.Button(
            self.start_test_frame,
            text="Start testing",
            command=self.test_logic.run_valve_test,
            bg="green",
            font=("Helvetica", 24),
        )
        self.startButton.pack(fill="both", expand=True)

    def on_window_close(self) -> None:
        """Handle the close event when the user clicks the X button on the window."""
        if self.top is not None:
            self.top.destroy()
            self.top = None

    def update_size(self) -> None:
        """update the size of the window to fit the contents"""
        if self.top is not None:
            self.top.update_idletasks()
            width = self.top.winfo_reqwidth()
            height = self.top.winfo_reqheight()
            self.top.geometry("{}x{}".format(width, height))

    def configure_tk_obj_grid(self, obj):
        # setting the tab to expand when we expand the window
        obj.grid_rowconfigure(0, weight=1)
        obj.grid_columnconfigure(0, weight=1)


class valveTestLogic:
    def __init__(self, controller):
        self.controller = controller

        self.default_valve_opening_time = self.calculate_default_valve_opening_time() 
        self.default_measured_volume = 0

    def run_valve_test(self):
        for valve in range(self.controller.data_mgr.num_valves.get()):
            
            self.controller.arduino_mgr.open_valves(valve, valve)
            self.controller.arduino_mgr.close_valves(valve, valve)

    def calculate_default_valve_opening_time(self):
        
        pressure_difference = 0 
        
        pass