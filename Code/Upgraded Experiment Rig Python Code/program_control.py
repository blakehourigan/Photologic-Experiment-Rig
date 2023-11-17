import tkinter as tk

from logic import ExperimentLogic
from arduino_control import AduinoManager
from experiment_config import Config
from main_gui import MainGUI

class ProgramController:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("Samuelsen Lab Photologic Rig")
        self.current_screen = None
        
        self.main_gui = None
        self.config = Config()
        self.logic = ExperimentLogic(self)
        self.arduino_mgr = AduinoManager(self)


    def start_main_gui(self) -> None:
        self.main_gui = MainGUI(self.root, self, self.config, self.logic)
        self.arduino_mgr.connect_to_arduino()
        self.root.mainloop()
    
    def start_button_handler(self):
        self.logic.start_button_logic(self.main_gui, self.arduino_mgr)
        
    def clear_button_handler(self):
        self.logic.clear_button_logic(self.main_gui)
        
    def display_error(self, label, error):
        self.main_gui.display_error(label, error)
    
