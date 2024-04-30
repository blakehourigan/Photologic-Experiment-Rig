import tkinter as tk

class PrimeValves:
    def __init__(self, controller):
        self.controller = controller
        self.top = tk.Toplevel(self.controller.main_gui.root)  # Use main GUI's root for Toplevel
        self.top.title("Prime Valves")
        self.top.protocol("WM_DELETE_WINDOW", self.close_window)  # Proper close handling

        self.valve_states = []

        self.maximum_num_valves = 8
        self.set_initial_valve_states()
        self.setup_ui()
        
    def set_initial_valve_states(self):
        self.valve_states = ['1'] * self.maximum_num_valves  # Initialize all valves as closed initially


    def setup_ui(self):
        # Label and entry for number of valves
        label = tk.Label(self.top, text="Enter number of valves to prime:")
        label.pack(pady=10)

        # Frame to hold valve buttons
        self.valves_frame = tk.Frame(self.top)
        self.valves_frame.pack(pady=10)
        self.create_valve_buttons()


    def create_valve_buttons(self):
        self.buttons = []

        print("Initial valve states:", self.valve_states)
        # First half (1-4)
        for i in range(self.maximum_num_valves // 2):  # This runs 0, 1, 2, 3
            btn_text = f"Valve {i + 1}: Open"
            btn = tk.Button(self.valves_frame, text=btn_text, bg='green', 
                            command=lambda b=i: self.toggle_button(b))
            btn.pack(pady=2, padx=2, fill=tk.X)
            self.buttons.append(btn)

        # Second half (5-8)
        for i in range(self.maximum_num_valves // 2, self.maximum_num_valves):  # This runs 4, 5, 6, 7
            btn_text = f"Valve {i + 1}: Open"
            btn = tk.Button(self.valves_frame, text=btn_text, bg='green', 
                            command=lambda b=i: self.toggle_button(b))
            btn.pack(pady=2, padx=2, fill=tk.X)
            self.buttons.append(btn)
        self.update_valve_states()



    def toggle_button(self, index):
        btn = self.buttons[index]
        if btn['text'].endswith("Open"):
            btn.configure(text=f"Valve {index+1}: Closed", bg='red')
            self.valve_states[index] = '0'
        else:
            btn.configure(text=f"Valve {index+1}: Open", bg='green')
            self.valve_states[index] = '1'
        self.update_valve_states()
        
    def update_valve_states(self):
        # Take the first 4 elements
        first_four = self.valve_states[:4]
        first_four.reverse()  # Reverses in place
        first_four = "".join(first_four)  # Convert each item to string and join

        
        # Take the last 4 elements
        last_four = self.valve_states[-4:]
        last_four.reverse()
        last_four = "".join(last_four)
        last_four += "0000"
        
        print(first_four, last_four)
        
        first_four = self.binary_to_decimal(first_four)
        last_four = self.binary_to_decimal(last_four)
        
        print(first_four, last_four)
        
        # Send the command to open the valves with the current selection from the buttons in the GUI
        command = "<O," + f"{first_four}," + f"{last_four}"+ ">"
        
        print(command)
        
        self.controller.send_command_to_motor(command)

    def binary_to_decimal(self, binary_number):
        # Convert the binary string to decimal
        decimal_number = int(str(binary_number), 2)
        return decimal_number
        

    def close_window(self):
        self.top.destroy()