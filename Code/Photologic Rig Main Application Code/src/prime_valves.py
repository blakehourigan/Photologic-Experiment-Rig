import tkinter as tk
from tkinter import PhotoImage
import platform

class PrimeValves:
    def __init__(self, controller) -> None:
        self.controller = controller
        self.top = tk.Toplevel(self.controller.main_gui.root)
        self.top.title("Prime Valves")
        self.top.protocol("WM_DELETE_WINDOW", self.close_window)
        self.top.resizable(False, False)
        icon_path = self.controller.get_window_icon_path()
        self.set_program_icon(icon_path)
        self.priming_active = False  # Track priming state

        self.setup_ui()
        self.center_window(300, 150)  # Smaller window for just a label and button

    def set_program_icon(self, icon_path) -> None:
        os_name = platform.system()

        if os_name == "Windows":
            self.top.iconbitmap(icon_path)
        else:
            # Use .png or .gif file directly
            photo = PhotoImage(file=icon_path)
            self.root.tk.call("wm", "iconphoto", self.root._w, photo)  # type: ignore

    def setup_ui(self):
        # Label for priming instruction
        label = tk.Label(self.top, text="Prime Valves", font=("Helvetica", 14), pady=20)
        label.pack()

        # Button to start/stop priming
        self.priming_button = tk.Button(self.top, text="Start Priming", command=self.toggle_priming, bg='green', width=15)
        self.priming_button.pack(pady=10)

    def center_window(self, width, height):
        screen_width = self.top.winfo_screenwidth()
        screen_height = self.top.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.top.geometry(f'{width}x{height}+{x}+{y}')

    def toggle_priming(self):
        self.priming_active = not self.priming_active
        if self.priming_active:
            self.priming_button.configure(text="Stop Priming", bg='red')
            self.controller.send_command_to_arduino('motor', '<F>')
        else:
            self.priming_button.configure(text="Start Priming", bg='green')
            self.controller.send_command_to_arduino('motor', 'E')

    def close_window(self):
        self.priming_active = False  # Ensure priming is marked as stopped
        self.top.destroy()

