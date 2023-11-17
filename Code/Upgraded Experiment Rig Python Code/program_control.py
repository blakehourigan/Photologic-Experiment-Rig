import tkinter as tk

class ProgramController:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Samuelsen Lab Photologic Rig")
        self.current_screen = None

    def start_main_gui(self, main_gui_class):
        self.current_screen = main_gui_class(self.root)
        self.root.mainloop()
