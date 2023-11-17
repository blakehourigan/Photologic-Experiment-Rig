import tkinter as tk

from logic import ExperimentLogic

class ProgramController:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("Samuelsen Lab Photologic Rig")
        self.current_screen = None
        
        self.logic = ExperimentLogic

    def start_main_gui(self, main_gui_class, controller) -> None:
        self.current_screen = main_gui_class(self.root, controller)
        self.root.mainloop()
