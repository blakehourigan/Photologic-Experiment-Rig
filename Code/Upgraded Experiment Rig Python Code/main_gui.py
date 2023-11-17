import platform
from tkinter import Tk, PhotoImage

from experiment_config import Config

class MainGUI():
    def __init__(self, master, controller) -> None:
        self.master = master
        self.controller = controller
        self.config = Config()
        
        self.setup_window()

    def setup_window(self) -> None:
        # Set the initial size of the window
        self.master.geometry(self.config.main_gui_window_size)

        self.master.title("Upgraded Experiment Rig")
        icon_path = self.config.get_window_icon_path() 
        self.set_program_icon(icon_path)

    def set_program_icon(self, icon_path) -> None:
        os_name = platform.system()

        if os_name == 'Windows':
            self.master.iconbitmap(icon_path)
        else:
            # Use .png or .gif file directly
            photo = PhotoImage(file=icon_path)
            self.master.tk.call('wm', 'iconphoto', self.master._w, photo)
            
            
    def start_program(self):
        self.controller.start_logic()