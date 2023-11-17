import tkinter as tk

from logic import ExperimentLogic
from arduino_control import AduinoManager
from experiment_config import Config

from data_management import DataManager

# GUI classses
from main_gui import MainGUI
from data_window import DataWindow
from experiment_control_window import ExperimentCtlWindow

class ProgramController:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("Samuelsen Lab Photologic Rig")
        self.current_screen = None
        
        self.main_gui = None
        self.config = Config()
        self.logic = ExperimentLogic(self)
        self.arduino_mgr = AduinoManager(self)
        self.data_mgr = DataManager(self)
        self.experiment_ctl_wind = ExperimentCtlWindow(self, self.logic, self.config)

    def start_main_gui(self) -> None:
        self.main_gui = MainGUI(self.root, self, self.config, self.logic)
        self.arduino_mgr.connect_to_arduino()
        self.root.mainloop()
    
    def start_button_handler(self) -> None:
        self.logic.start_button_logic(self.main_gui, self.arduino_mgr)
        
    def clear_button_handler(self) -> None:
        self.logic.clear_button_logic(self.main_gui)
        
    def display_error(self, label, error) -> None:
        self.main_gui.display_error(label, error)
        
    def show_experiment_ctl_window(self, master):
        self.experiment_ctl_wind.show_window(master)
