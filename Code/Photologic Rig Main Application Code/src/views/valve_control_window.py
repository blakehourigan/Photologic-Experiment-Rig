import tkinter as tk
import toml
import numpy as np
import system_config

from views.gui_common import GUIUtils

rig_config = system_config.get_rig_config()

with open(rig_config, "r") as f:
    VALVE_CONFIG = toml.load(f)["valve_config"]

# pull total valves constant from toml config
TOTAL_CURRENT_VALVES = VALVE_CONFIG["TOTAL_CURRENT_VALVES"]
VALVES_PER_SIDE = TOTAL_CURRENT_VALVES // 2


class ValveControlWindow(tk.Toplevel):
    def __init__(self, arduino_controller) -> None:
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
        self.deiconify()

    def create_interface(self):
        self.valves_frame = tk.Frame(self)

        self.valves_frame.grid(row=0, column=0, pady=10, sticky="nsew")
        self.valves_frame.grid_columnconfigure(0, weight=1)
        self.valves_frame.grid_rowconfigure(0, weight=1)

        self.create_buttons()

    def toggle_motor(self):
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

    def toggle_valve_button(self, valve_num):
        """
        Every time that a valve button is toggled, we will send a np array TOTAL_CURRENT_VALVES bits wide
        to the arduino. a 1 represents a on valve, while 0 means off. arduino will iterate through half of this
        array for side one valves, and hald for side two.
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
