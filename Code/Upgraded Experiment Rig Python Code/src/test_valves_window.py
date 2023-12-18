from typing import Optional
from tkinter import ttk
import tkinter as tk
from math import pi


class valveTestWindow:
    def __init__(self, controller):
        self.controller = controller
        self.master = controller.main_gui.root

        self.top: Optional[tk.Toplevel] = None

        self.num_valves_to_test = tk.IntVar(value=0)
        self.num_valves_to_test.trace_add(
            "write", lambda *args: self.create_valve_test_table()
        )  # we call create table, whenever the number of valves to test variable is written to

        self.number_test_runs = tk.IntVar(value=100)

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
                    f"{self.controller.valve_test_logic.desired_volume}ml",
                    f"{round(self.controller.valve_test_logic.opening_time,4)}s",
                ),
            )  # Add items to our treeview

    def create__start_button(self) -> None:
        # Start test button
        self.start_test_frame = tk.Frame(self.top, width=150, height=50)
        self.start_test_frame.grid(row=3, column=0, pady=10, padx=10, sticky="nsew")
        self.startButton = tk.Button(
            self.start_test_frame,
            text="Start testing",
            command=self.controller.valve_test_logic.run_valve_test,
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
    def __init__(self, controller) -> None:
        self.controller = controller

        self.cylinder_radius = 1.25  # radius of the cylinder in cm

        self.height_surface_to_opening = (
            14.0  # height from the opening to the top of the liquid in the cylinder
        )

        self.volume = (
            self.calculate_current_cylinder_Volume()
        )  # volume of the cylinder assuming fill at lip (14cm)

        self.length_teflon_tube = 14.0  # length of the tube in cm
        self.TERFLON_TUBE_RADIUS = .0396875  # radius of the tube in cm
        
        self.desired_volume = 0.05  # desired volume to dispense in ml

        self.opening_time = self.calculate_valve_opening_time()
        
        self.tubes_filled=False

    def run_valve_test(self):
        """_controller function to run the testing sequence on given valves_
        """
        self.fill_tubes()
        self.valve_index = 0
        self.test_run_index = 0
        self.test_valve_sequence()

    def test_valve_sequence(self):
        """_the test sequence that each valve will undergo_
        """
        num_valves = self.controller.valve_testing_window.num_valves_to_test.get()
        num_test_runs = self.controller.valve_testing_window.number_test_runs.get()
        while(True):    
            if self.test_run_index < num_test_runs: # if we have not reached the number of desired test runs, then we will continue to open the current valve
                self.open_valve(self.valve_index + 1)
                self.test_run_index += 1
            elif self.valve_index < num_valves - 1: # else if we have reached the number of desired test runs, but we have not tested all the valves
                self.valve_index += 1               # then we will move on to the next valve and continue the test
                self.test_run_index = 0
            else:
                print("Valve testing completed.")
                break
                
    def fill_tubes(self):
        """_function to fill the tubes with water_
        """
        
        
        self.tubes_filled=True
        self.length_teflon_tube = 14.0
        self.opening_time = self.calculate_valve_opening_time()      
        self.length_teflon_tube = .1 # tube is already filled to the tip, so we use a small value to approximate how long we need to open it only to get a drop          

    def calculate_current_cylinder_Volume(self) -> float:
        """_ calculate cylinder volume based on the current height of the liquid_
        """
        volume = pi * (self.cylinder_radius**2) * self.height_surface_to_opening
        return volume

    def calculate_height_of_liquid(self) -> float:
        """calculate the height of the liquid in the cylinder based on the current volume and the desired volume to dispense
        """
        current_height = self.volume / (pi * self.cylinder_radius**2)
        
        dispensed_height = self.desired_volume / (pi * self.cylinder_radius**2)
        
        remaining_cylinder_height = current_height - dispensed_height
        
        return remaining_cylinder_height

    def calculate_valve_opening_time(self) -> float:
        """ calculate the time that the valve needs to be open based on the desired volume to dispense """
        Q = self.calculate_volumetric_flow_rate()

        time_to_open = self.desired_volume / Q  # time to open the valve in seconds

        return time_to_open

    def calculate_volumetric_flow_rate(self) -> float:
        GRAVITY = 980.665  # gravity in centimeters per second squared

        Q = (
            pi
            * 1 # g / cm^3 density of water
            * GRAVITY
            * self.height_surface_to_opening # height from the opening to the top of the liquid in the cylinder
            * self.TERFLON_TUBE_RADIUS**4          # radius of the cylinder in cm ^ 4
        ) / (8 * 1 * self.length_teflon_tube)  # 8 * (viscosity of water g / cm * s)* length of tube in cm

        return Q  # volumetric flow rate in cm^3/s

    def open_valve(self, valve) -> None:
        self.controller.arduino_mgr.open_valve(valve)

        self.controller.valve_testing_window.top.after(
            int(self.opening_time * 1000), lambda: self.close_valve(valve)
        )

    def close_valve(self, valve):
        self.controller.arduino_mgr.close_valve(valve)

        self.volume = self.calculate_current_cylinder_Volume()
        self.height = self.calculate_height_of_liquid()
        self.opening_time = self.calculate_valve_opening_time()

        self.controller.valve_testing_window.top.after(
            500,  # Give some time before starting the next test run
            self.test_valve_sequence,
        )
