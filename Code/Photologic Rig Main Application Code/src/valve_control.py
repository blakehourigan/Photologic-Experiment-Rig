import tkinter as tk

class ValveControl:
    def __init__(self, controller) -> None:
        self.setup_gui()
        self.controller = controller

    def setup_gui(self) -> None:
        self.root = tk.Tk()
        self.root.title("Valve Control")
        self.root.geometry("300x200")  # Window size

        self.create_buttons()

    def create_buttons(self) -> None:
        frame = tk.Frame(self.root)
        frame.pack(pady=20)

        # Prime Valves Button
        prime_valves_btn = tk.Button(
            frame, text="Prime Valves", command=self.prime_valves, width=20
        )
        prime_valves_btn.pack(pady=5)

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

    def prime_valves(self) -> None:
        for i in range(1000):
            print(i)
            command = "<F>"
            self.controller.arduino_mgr.send_command_to_motor(command)
            
            

    def open_all_valves(self) -> None:
        print("Opening all valves...")

    def close_all_valves(self) -> None:
        print("Closing all valves...")


