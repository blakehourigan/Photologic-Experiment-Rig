import tkinter as tk

class ValveControl:
    def __init__(self, controller) -> None:
        self.controller = controller
        self.setup_gui()

    def setup_gui(self) -> None:
        self.root = tk.Tk()
        self.root.title("Valve Control")
        self.root.geometry("300x200")  # Window size

        self.create_buttons()

    def create_buttons(self) -> None:
        frame = tk.Frame(self.root)
        frame.pack(pady=20)
        
        # Open All Valves Button
        open_all_valves_btn = tk.Button(
            frame, text="Open All Valves", command=self.open_all_valves, width=20
        )
        open_all_valves_btn.pack(pady=5)

        # Close All Valves Button
        close_all_valves_btn = tk.Button(
            frame, text="Close All Valves", command=self.close_all_valves, width=20
        )
        close_all_valves_btn.pack(pady=5)
        
        # Button to begin the draining procedure
        drain_valves_btn = tk.Button(
            frame, text="Drain Valves", command=self.controller.open_drain_valves_window, width=20
        )
        drain_valves_btn.pack(pady=5)

    def prime_valves(self) -> None:
        command = "<F>"
        self.controller.arduino_mgr.send_command_to_motor(command)
            
    def open_all_valves(self) -> None:
        command = '<O>'
        self.controller.arduino_mgr.send_command_to_motor(command)


    def close_all_valves(self) -> None:
        command = '<C>'
        self.controller.arduino_mgr.send_command_to_motor(command)


