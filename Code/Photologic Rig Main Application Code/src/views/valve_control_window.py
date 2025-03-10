import tkinter as tk

from views.gui_common import GUIUtils


class ValveControlWindow(tk.Toplevel):
    def __init__(self) -> None:
        super().__init__()
        self.title("Valve Control")
        self.protocol("WM_DELETE_WINDOW", lambda: self.withdraw())
        self.bind("<Control-w>", lambda event: self.withdraw())

        window_icon_path = GUIUtils.get_window_icon_path()
        GUIUtils().set_program_icon(self, window_icon_path)

        self.maximum_num_valves = 8
        self.valve_states = ["0"] * self.maximum_num_valves

        self.valves_frame = tk.Frame(self)
        self.valves_frame.pack(pady=10)
        self.create_valve_buttons()
        # self.create_motor_control_button()

        self.motor_button_text = tk.StringVar()
        self.motor_button_text.set("")
        # self.setup_ui()
        GUIUtils.center_window(self)

        # we don't want to show this window until the user decides to click the corresponding button,
        # withdraw (hide) it for now
        self.withdraw()

    def show(self):
        self.deiconify()

    def toggle_motor(self):
        if self.motor_button_text.get() == "Move motor down":
            self.motor_button_text.set("Move motor up")
            self.motor_button.configure(bg="blue")
            motor_command = "DOWN\n".encode("utf-8")
        else:
            self.motor_button_text.set("Move motor down")
            self.motor_button.configure(bg="green")
            motor_command = "UP\n".encode("utf-8")
        self.controller.send_command_to_arduino(arduino="motor", command=motor_command)

    def create_motor_control_button(self):
        self.motor_button = tk.Button(
            self.valves_frame,
            textvariable=self.motor_button_text,
            bg="green",
            command=self.toggle_motor,
        )
        self.motor_button.pack(pady=2)

    def create_valve_buttons(self):
        # Create list of buttons to be able to access each one easily later
        self.buttons = []

        # Side one valves (1-4)
        for i in range(self.maximum_num_valves // 2):  # This runs 0, 1, 2, 3
            btn_text = f"Valve {i + 1}: Closed"
            btn = tk.Button(
                self.valves_frame,
                text=btn_text,
                bg="red",
                command=lambda b=i: self.toggle_button(b),
            )
            btn.pack(pady=2, padx=2, fill=tk.X)
            self.buttons.append(btn)

        # Side two valves (5-8)
        for i in range(
            self.maximum_num_valves // 2, self.maximum_num_valves
        ):  # This runs 4, 5, 6, 7
            btn_text = f"Valve {i + 1}: Closed"
            btn = tk.Button(
                self.valves_frame,
                text=btn_text,
                bg="red",
                command=lambda b=i: self.toggle_button(b),
            )
            btn.pack(pady=2, padx=2, fill=tk.X)
            self.buttons.append(btn)

        # self.update_valve_states()

    def toggle_button(self, index):
        btn = self.buttons[index]
        if btn["text"].endswith("Open"):
            btn.configure(text=f"Valve {index + 1}: Closed", bg="red")
            self.valve_states[index] = "0"
        else:
            btn.configure(text=f"Valve {index + 1}: Open", bg="green")
            self.valve_states[index] = "1"
        self.update_valve_states()

    def update_valve_states(self):
        """This method looks at the current states of self.valve_states, splits the valves into their respective sides, and sends a command to the motor Arduino to open and
        close valves as the user selects via the buttons in the GUI."""

        # Determine how many valves are on each side based on the value stored in self.maximum_num_valves
        valves_per_side = self.maximum_num_valves // 2
        # Select side ones states from valve_states
        side_one_valves = self.valve_states[:valves_per_side]
        """While the states are stored in self.valves_states incrementally, e.g state 1 stored at pos 0 starting from the left, then state 2 at pos 1, etc.
        Arduino's PORTC which controls the side one valves begins with its least significant value on the rightmost bit moving left, where valve one is 
        associated with the rightmost bit. for this reason we must reverse the list to line up the bits to match. """
        side_one_valves.reverse()  # Reverses in place
        side_one_valves = "".join(
            side_one_valves
        )  # This collapses the list into one value stored in a string variable

        """Repeat the steps for side one here, except there is no need to reverse the list, because here the lowest numbered valve is associated with PORTA's most 
        significant bit PA7"""
        side_two_valves = self.valve_states[-valves_per_side:]
        side_two_valves.reverse()  # Reverses in place
        side_two_valves = "".join(side_two_valves)
        # side_two_valves += "0000"
        """Adding these extra bits is necessary because valves 5-8 are tied to the most significant bits in the PORTC register. 
        so simply using four bits in the case of maximum 8 valves would result in the computer sending signals to the pins meant to control valves 12-16 which are yet to be added."""

        # Convert the binary values we have constructed to decimal values to be sent to the motor Arduino
        side_one_valves = self.binary_to_decimal(side_one_valves)
        side_two_valves = self.binary_to_decimal(side_two_valves)

        # Send the command to open the valves with the current selection from the buttons in the GUI
        self.controller.send_command_to_arduino(
            arduino="motor",
            command="<O," + f"{side_one_valves}," + f"{side_two_valves}" + ">",
        )

    def binary_to_decimal(self, binary_number):
        # Convert the binary string to decimal
        decimal_number = int(str(binary_number), 2)
        return decimal_number
