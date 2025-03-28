"""
This module defines the ValveControlWindow class, a Toplevel window in the GUI
designed for direct manual control of individual valves and the door motor
on the experimental rig.

It reads valve configuration (number of valves) from a TOML file, creates buttons for each valve,
allows toggling their state (Open/Closed), and provides a button to move the motor
(Up/Down). Valve state changes and motor commands are sent to Arduino via `controllers.arduino_control.ArduinoManager`.
"""

import tkinter as tk
import toml
import numpy as np
from controllers.arduino_control import ArduinoManager
import system_config

from views.gui_common import GUIUtils

rig_config = system_config.get_rig_config()

with open(rig_config, "r") as f:
    VALVE_CONFIG = toml.load(f)["valve_config"]

# pull total valves constant from toml config
TOTAL_CURRENT_VALVES = VALVE_CONFIG["TOTAL_CURRENT_VALVES"]
VALVES_PER_SIDE = TOTAL_CURRENT_VALVES // 2


class ValveControlWindow(tk.Toplevel):
    """
    A Toplevel window providing manual control over individual valves and the main motor.

    This window displays buttons for each configured valve, allowing users to toggle them
    between 'Open' and 'Closed' states. It also includes a button to command the
    main motor to move 'Up' or 'Down'. State changes and commands are sent to the
    connected Arduino controller.

    Attributes
    ----------
    - **arduino_controller** (*ArduinoManager*): An instance of the controller class
      responsible for communicating with the Arduino board.
    - **valve_selections** (*np.ndarray*): A NumPy array storing the current state (0 for Closed, 1 for Open)
      of each valve. The index corresponds to the valve number (0-indexed).
    - **buttons** (*List[tk.Button OR None]*): A list holding references to the `tk.Button` widgets
      for each valve, allowing individual access for state updates.
    - **motor_button** (*tk.Button*): The `tk.Button` widget used to control the motor's position.
    - **motor_down** (*bool*): A flag indicating the current assumed state of the motor
      (True if commanded Down, False if commanded Up).
    - **valves_frame** (*tk.Frame*): The main container frame within the Toplevel window holding the control buttons.

    Methods
    -------
    - `show()`
        Makes the Valve Control window visible (`deiconify`).
    - `create_interface()`
        Sets up the main frame (`valves_frame`) and calls `create_buttons` to populate it.
    - `toggle_motor()`
        Callback for the motor control button. Toggles the `motor_down` state, updates the button
        text/color, and sends the corresponding "UP" or "DOWN" command to the Arduino.
    - `create_buttons()`
        Creates and arranges the `tk.Button` widgets for each valve based on
        `TOTAL_CURRENT_VALVES` and `VALVES_PER_SIDE`. Creates the motor control button.
    - `toggle_valve_button(valve_num)`
        Callback for individual valve buttons. Toggles the state of the specified valve
        in `valve_selections`, updates the button's text/color, and sends the "OPEN SPECIFIC"
        command followed by the current state of all valves (`valve_selections`) to the Arduino.
    """

    def __init__(self, arduino_controller: ArduinoManager) -> None:
        super().__init__()
        self.title("Valve Control")
        self.protocol("WM_DELETE_WINDOW", lambda: self.withdraw())
        self.bind("<Control-w>", lambda event: self.withdraw())

        for i in range(3):
            self.grid_columnconfigure(i, weight=1)
        for i in range(2):
            self.grid_rowconfigure(i, weight=1)

        self.resizable(False, False)

        self.arduino_controller = arduino_controller

        window_icon_path = GUIUtils.get_window_icon_path()
        GUIUtils.set_program_icon(self, window_icon_path)

        self.valve_selections = np.zeros((TOTAL_CURRENT_VALVES,), dtype=np.int8)

        self.create_interface()
        self.motor_down = False

        # we don't want to show this window until the user decides to click the corresponding button,
        # withdraw (hide) it for now
        self.withdraw()

    def show(self):
        """Makes the window visible by calling `deiconify`."""
        self.deiconify()

    def create_interface(self):
        """Creates the main frame for holding the valve and motor buttons."""
        self.valves_frame = tk.Frame(self)

        self.valves_frame.grid(row=0, column=0, pady=10, sticky="nsew")
        self.valves_frame.grid_columnconfigure(0, weight=1)
        self.valves_frame.grid_rowconfigure(0, weight=1)

        self.create_buttons()

    def toggle_motor(self):
        """
        Toggles the motor's position between 'Up' and 'Down'.

        Updates the motor control button's appearance (text and color) to reflect the
        new target state and sends the appropriate command ("UP\n" or "DOWN\n")
        to the Arduino controller. Also updates the internal `motor_down` flag.
        """
        # if motor is not down, command it down
        if self.motor_down is False:
            self.motor_button.configure(text="Move Motor Up", bg="blue", fg="white")

            motor_command = "DOWN\n".encode("utf-8")
            self.motor_down = True
        else:
            self.motor_button.configure(text="Move motor down", bg="green", fg="black")

            motor_command = "UP\n".encode("utf-8")
            self.motor_down = False

        self.arduino_controller.send_command(command=motor_command)

    def create_buttons(self):
        """
        Creates and arranges the buttons for valve and motor control.

        Populates the `self.buttons` list with `tk.Button` widgets for each valve,
        placing them in two columns ("Side One" and "Side Two"). Creates the
        motor control button and places it in the center column.
        """
        # Create list of buttons to be able to access each one easily later
        self.buttons = [None] * TOTAL_CURRENT_VALVES

        # Side one valves (1-4)
        for i in range(VALVES_PER_SIDE):  # This runs 0, 1, 2, 3
            btn_text = f"Valve {i + 1}: Closed"
            button = GUIUtils.create_button(
                self.valves_frame,
                btn_text,
                lambda i=i: self.toggle_valve_button(i),
                "firebrick1",
                row=i,
                column=0,
            )[1]
            self.buttons[i] = button

            # This runs 4, 5, 6, 7
            btn_text = f"Valve {i + VALVES_PER_SIDE + 1}: Closed"
            button = GUIUtils.create_button(
                self.valves_frame,
                btn_text,
                lambda i=i + VALVES_PER_SIDE: self.toggle_valve_button(i),
                "firebrick1",
                row=i,
                column=2,
            )[1]
            self.buttons[i + VALVES_PER_SIDE] = button

        self.motor_button = GUIUtils.create_button(
            self.valves_frame,
            "Move Motor Down",
            command=lambda: self.toggle_motor(),
            bg="green",
            row=TOTAL_CURRENT_VALVES,
            column=1,
        )[1]

    def toggle_valve_button(self, valve_num: int):
        """
        Updates the state of the clicked valve (`valve_num`) in the `valve_selections` array.
        Changes the button's text and background color to reflect the new state (Open/Green or Closed/Red).
        Sends an "OPEN SPECIFIC" command to the Arduino, followed by the byte representation
        of the entire `valve_selections` array, instructing the Arduino which valves should be open or closed.

        Parameters
        ----------
        - **valve_num** (*int*): The 0-based index of the valve whose button was clicked.
        """
        # if a valve is currently a zero (off), make it a 1, and turn the button green
        if self.valve_selections[valve_num] == 0:
            self.buttons[valve_num].configure(
                text=f"Valve {valve_num + 1}: Open", bg="green"
            )
            self.valve_selections[valve_num] = 1

        # if a valve is currently a one (on), make it a zero (off), and turn the button red
        else:
            self.buttons[valve_num].configure(
                text=f"Valve {valve_num + 1}: Closed", bg="firebrick1"
            )
            self.valve_selections[valve_num] = 0

        open_command = "OPEN SPECIFIC\n".encode("utf-8")
        self.arduino_controller.send_command(command=open_command)

        # send desired valve states to the arduino
        selections = self.valve_selections.tobytes()
        self.arduino_controller.send_command(command=selections)
