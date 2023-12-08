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
        
        self.config = Config()
        self.logic = ExperimentLogic(self)
        self.data_mgr = DataManager(self)
        self.arduino_mgr = AduinoManager(self)
        self.experiment_ctl_wind = ExperimentCtlWindow(self, self.logic, self.config)
        self.main_gui = MainGUI(self.root, self, self.config, self.logic)
        
        # Initialize running flag to false
        self.running = False

    def start_main_gui(self) -> None:
        """start the main GUI and connect to the arduino
        """
        self.main_gui.setup_gui()
        self.arduino_mgr.connect_to_arduino()
        self.root.mainloop()
    
    def initial_time_interval(self, i):
        """defining the ITI state method, arguments given are self which says that the function should be called on the instance of the class, which is our app 
        the second argument is i, which is the iteration variable that we use to keep track of what trial we are on. 
        i is defined on line 650 where we first call the function."""
        
        # if we have pressed start, and the current trial number is less than the number of trials determined by number of stim * number of trial blocks, then continue running through more trials
        if self.running and self.logic.return_trials_remaining() and self.data_mgr.blocks_generated == True:
            
            self.logic.new_ITI_reset()
            
            # configure the state time label in the top right of the main window to hold the value of the new state
            self.main_gui.state_time_label_header.configure(text=(self.state + " Time:"))
            
            # update the state start time to now, so that it starts at 0
            self.logic.state_start_time = time.time()  
            
            # Get trial number and stimuli in the trial and add them to the main information screen
            # self.df_stimuli.loc is what we use to get values that are held in the main data table. Accessed using .loc[row_num, 'Column Name']
            string = f'\nTRIAL # ({self.curr_trial_number}) Stimulus 1:{self.data_mgr.stimuli_dataframe.loc[i, "Stimulus 1"]} vs. \
                Stimulus 2:{self.data_mgr.stimuli_dataframe.loc[i, "Stimulus 2"]}\n'
                
            # this command is what adds things to the main information screen
            self.main_gui.append_data(string)
            
            # for every letter in the string we just created, create a dash to separate the title of the trial from the contents
            for letter in range(len(string)):
                self.main_gui.append_data("-")
            
            # add the initial interval to the program information box

            self.main_gui.append_data('\nInitial Interval Time: ' +  str(self.data_mgr.stimuli_dataframe.loc[i,'ITI']/ 1000.0) + "s\n")
            
            """main_gui.master.after tells the main tkinter program to wait the amount of time specified for the TTC in the ith row of the table. Save licks is called with previously used 'i' iterator.
            Lambda ensures the function is only called after the wait period and not immediately."""
            #self.main_gui.master.after(int(self.df_stimuli.loc[i,'ITI']), lambda: self.time_to_contact(i))
        else: 
            # if we have gone through every trial then end the program.
            self.stop_program()

    def start_button_handler(self) -> None:
        """ Define the method for toggling the program state via the start/stop button """
        # If the program is running, stop it
        if self.running:
            self.stop_program()

        # If the program is not running, start it
        else:
            self.start_program()
        
    def clear_button_handler(self) -> None:
        self.logic.clear_button_logic(self.main_gui)
        
    def display_error(self, label, error) -> None:
        self.main_gui.display_error(label, error)
        
    def show_experiment_ctl_window(self, master) -> None:
        self.experiment_ctl_wind.show_window(master)
        
    def generate_trial_blocks_data_mgr(self):
        return self.data_mgr.generate_trial_blocks()
    
    def stop_program(self) -> None:
        """ Method to halt the program and set it to the off state, changing the button back to start. """
        self.state = "OFF"
        # set the state timer label
        self.main_gui.state_time_label_header.configure(text=(self.state))
        # set the running variable to false to halt execution in the state functions
        self.running = False
        # Turn the program execution button back to the green start button
        self.main_gui.startButton.configure(text="Start", bg="green")
        
        #self.master.after_cancel(self.update_clock_id)
        # if we have called the update licks function at all, then stop it from being called now, we're done with it 
        if self.logic.update_licks_id is not None:  
            self.root.after_cancel(self.logic.update_licks_id)

        # if we have opened a data window and have a update for the plot scheduled, then cancel it and close the window
        if self.logic.update_plot_id is not None:
            self.main_gui.master.after_cancel(self.logic.update_plot_id)
            #self.data_window_instance.destroy()
        # try to send the reset command to reboot both Arduino boards 

        self.arduino_mgr.reset_arduinos()
        self.curr_trial_number = 1
        
    def start_program(self) -> None:
        # Start the program if it is not already runnning and generate random numbers
        self.running = True
        # program main start time begins now
        self.start_time = time.time()
        
        self.update_clock_label()
        # turn the main button to the red stop button
        self.main_gui.startButton.configure(text="Stop", bg="red")
        # call the first ITI state with an iteration variable (i acts as a 
        # variable to iterate throgh the program schedule data table) starting at 0
        self.initial_time_interval(0)
        
    def update_clock_label(self) -> None:
        # if the program is running, update the clock label
        if self.running:
            self.main_gui.update_clock_label()