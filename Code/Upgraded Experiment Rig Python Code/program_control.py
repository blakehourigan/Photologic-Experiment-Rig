import tkinter as tk
import time

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
        self.data_mgr = DataManager(self,self.logic)
        self.experiment_ctl_wind = ExperimentCtlWindow(self, self.logic, self.config)

    def start_main_gui(self) -> None:
        self.main_gui = MainGUI(self.root, self, self.config, self.logic)
        self.arduino_mgr.connect_to_arduino()
        self.root.mainloop()
    
    def start_button_handler(self) -> None:
        """ Define the method for toggling the program state via the start/stop button """
        # If the program is running, stop it
        if self.logic.running:
            self.stop_program()
            #self.master.after_cancel(self.update_clock_id)
            # if we have called the update licks function at all, then stop it from being called now, we're done with it 
            if self.update_licks_id is not None:  
                self.master.after_cancel(self.update_licks_id)

            # if we have opened a data window and have a update for the plot scheduled, then cancel it and close the window
            if self.update_plot_id is not None:
                self.main_gui.master.after_cancel(self.update_plot_id)
                #self.data_window_instance.destroy()
            # try to send the reset command to reboot both Arduino boards 

            self.arduino_mgr.reset_arduinos()
            self.curr_trial_number = 1
        # If the program is not running, start it
        else:
            # Start the program if it is not already runnning and generate random numbers
            self.running = True
            # program main start time begins now
            self.start_time = time.time()
            
            self.update_clock()
            # turn the main button to the red stop button
            self.main_gui.startButton.configure(text="Stop", bg="red")
            # call the first ITI state with an iteration variable (i acts as a 
            # variable to iterate throgh the program schedule data table) starting at 0
            self.initial_time_interval(0)
        
    def clear_button_handler(self) -> None:
        self.logic.clear_button_logic(self.main_gui)
        
    def display_error(self, label, error) -> None:
        self.main_gui.display_error(label, error)
        
    def show_experiment_ctl_window(self, master):
        self.experiment_ctl_wind.show_window(master)
        
    def generate_trial_blocks_data_mgr(self):
        return self.data_mgr.generate_trial_blocks()
    
    def stop_program(self):
        """ Method to halt the program and set it to the off state, changing the button back to start. """
        self.state = "OFF"
        # set the state timer label
        self.main_gui.state_time_label_header.configure(text=(self.state))
        # set the running variable to false to halt execution in the state functions
        self.running = False
        # Turn the program execution button back to the green start button
        self.main_gui.startButton.configure(text="Start", bg="green")
        
    # Define the method for updating the clock
    def update_clock(self):
        # If the program is running, update the elapsed time
        if self.running:
            # total elapsed time is current minus program start time
            elapsed_time = time.time() - self.logic.start_time
            # update the main screen label and set the number of decimal points to 3 
            self.main_gui.time_label.configure(text="{:.3f}s".format(elapsed_time))
            # state elapsed time is current time minus the time we entered the state 
            state_elapsed_time = time.time() - self.state_start_time
            # update the main screen label and set the number of decimal points to 3
            self.main_gui.state_time_label.configure(text="{:.3f}s".format(state_elapsed_time))
            # Call this method again after 100 ms
            self.main_gui.master.after(50, lambda: self.update_clock())