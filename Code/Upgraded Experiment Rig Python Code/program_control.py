import tkinter as tk
import time
import numpy as np

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
        self.state = "OFF"
        
        self.after_ids = []

    def start_main_gui(self) -> None:
        """start the main GUI and connect to the arduino
        """
        self.main_gui.setup_gui()
        self.arduino_mgr.connect_to_arduino()
        self.root.mainloop()
    
    def initial_time_interval(self, iteration) -> None:
        """defining the ITI state method, arguments given are self which says that the function should be called on the instance of the class, which is our app 
        the second argument is i, which is the iteration variable that we use to keep track of what trial we are on. 
        i is defined on line 650 where we first call the function."""

        # if we have pressed start, and the current trial number is less than the number of trials determined by number of stim * number of trial blocks, then continue running through more trials
        if self.running and self.logic.return_trials_remaining() and self.data_mgr.blocks_generated == True:
            
            self.state = "ITI"
            
            self.logic.new_ITI_reset()
            
            # configure the state time label in the top right of the main window to hold the value of the new state
            self.main_gui.state_time_label_header.configure(text=(self.state + " Time:"))
            
            # update the state start time to now, so that it starts at 0
            self.data_mgr.state_start_time = time.time()  
            
            # Get trial number and stimuli in the trial and add them to the main information screen
            # self.df_stimuli.loc is what we use to get values that are held in the main data table. Accessed using .loc[row_num, 'Column Name']
            string = f'\nTRIAL # ({self.data_mgr.curr_trial_number}) Stimulus 1)  {self.data_mgr.stimuli_dataframe.loc[iteration, "Stimulus 1"]} vs. Stimulus 2)  {self.data_mgr.stimuli_dataframe.loc[iteration, "Stimulus 2"]}\n'
                
            # this command is what adds things to the main information screen
            self.main_gui.append_data(string)
            
            # for every letter in the string we just created, create a dash to separate the title of the trial from the contents
            for letter in range(len(string)):
                self.main_gui.append_data("-")
            
            # add the initial interval to the program information box
            ITI_Value = self.logic.check_dataframe_entry_isfloat(iteration, 'ITI')
            
            self.main_gui.append_data('\nInitial Interval Time: ' +  str(ITI_Value/ 1000.0) + "s\n")
            
            """main_gui.master.after tells the main tkinter program to wait the amount of time specified for the TTC in the ith row of the table. Save licks is called with previously used 'i' iterator.
            Lambda ensures the function is only called after the wait period and not immediately."""
            self.main_gui.master.after(int(ITI_Value), lambda: self.time_to_contact(iteration))
        else: 
            # if we have gone through every trial then end the program.
            self.stop_program()

    def time_to_contact(self, iteration):
        """ defining the TTC state method, argument are self and i. i is passed from TTC to keep track of what stimuli we are on. """
        if self.running:
            self.state = "TTC"
            
            """start reading licks, we pass the same i into this function that we used in the previous function to
            keep track of where we are storing the licks in the data table"""
            self.logic.read_licks(iteration)
            
            # update state timer header
            self.main_gui.state_time_label_header.configure(text=(self.state + " Time:"))
            
            # state start time begins 
            self.data_mgr.state_start_time = time.time()
            
            # tell motor arduino to move the door down              
            command = 'DOWN\n'
            self.arduino_mgr.send_command_to_motor(command)
        
            """ Look in the dataframe in the current trial for the stimulus to give, once found mark the index with corresponding solenoid
            valve number and save into stimulus position variables. """
            
            stimulus_1_position, stimulus_2_position = self.data_mgr.find_stimuli_positions(iteration)

            """concatinate the positions with the commands that are used to tell the arduino which side we are opening the valve for. 
            SIDE_ONE tells the arduino we need to open a valve for side one, it will then read the next line to find which valve to open.
            valves are numbered 1-8 so "SIDE_ONE\n1\n" tells the arduino to open valve one for side one. """
            command = "SIDE_ONE\n" + str(stimulus_1_position) + "\nSIDE_TWO\n" + str(stimulus_2_position) + "\n"
            
            # send the command
            self.arduino_mgr.send_command_to_motor(command)
            
            TTC_Value = self.logic.check_dataframe_entry_isfloat(iteration, 'TTC')
            
            # write the time to contact to the program information box
            self.main_gui.append_data("Time to Contact: " + str(TTC_Value/ 1000.0) + "s\n")
            
            """main_gui.master.after tells the main tkinter program to wait the amount of time specified for the TTC in the ith row of the table. Save licks is called with previously used 'i' iterator.
            Lambda ensures the function is only called after the wait period and not immediately."""
            self.after_sample_id = self.root.after(int(TTC_Value), lambda: self.logic.save_licks(iteration))
            self.after_ids.append(self.after_sample_id)

    def sample_time(self, iteration):
        """ define sample time method, i is again passed to keep track of trial and stimuli """
        if self.running:
            self.state = "Sample"
            
            # change the state time label accordingly                                     
            self.main_gui.state_time_label_header.configure(text=(self.state + " Time:"))

            # Update the state start time to the current time
            self.state_start_time = time.time()        

            sample_interval_value = self.logic.check_dataframe_entry_isfloat(iteration, 'Sample Time')

            # Appending the sample time interval to the main text box
            self.main_gui.append_data('Sample Time Interval: ' + str(sample_interval_value/ 1000.0) + "s\n\n\n")  

            # After the sample time specified in the ith row of the 'Sample Time' table, we will jump to the save licks function
            self.root.after(int(sample_interval_value), lambda: self.logic.save_licks(iteration))   

    def check_licks(self, iteration):
        """ define method for checking licks during the TTC state """
        # if we are in the TTC state and detect 3 or more licks from either side, then immediately jump to the sample time 
        # state and continue the trial
        if (self.side_one_licks >= 3 or self.side_two_licks >= 3) and self.state == 'TTC':
            self.data_mgr.stimuli_dataframe.loc[self.data_mgr.curr_trial_number - 1,'TTC Actual'] = \
                (time.time() - self.data_mgr.state_start_time) * 1000
                
            self.root.after_cancel(self.after_sample_id)
            self.side_one_licks = 0
            self.side_two_licks = 0
            self.sample_time(iteration)

    def start_button_handler(self) -> None:
        """ Define the method for toggling the program state via the start/stop button """
        # If the program is running, stop it
        if self.running:
            self.stop_program()

        # If the program is not running, start it
        else:
            self.start_program()
        
    def clear_button_handler(self) -> None:
        elapsed_time, state_elapsed_time = self.logic.reset_clock()
        self.main_gui.data_text.delete('1.0', tk.END)
        self.main_gui.time_label.configure(text="{:.3f}s".format(elapsed_time))
        self.main_gui.state_time_label.configure(text="{:.3f}s".format(state_elapsed_time))
        
    def show_experiment_ctl_window(self, master) -> None:
        self.experiment_ctl_wind.show_window(master)
        
    def generate_trial_blocks_data_mgr(self):
        return self.data_mgr.initialize_stimuli_dataframe()
    
    def stop_program(self) -> None:
        """ Method to halt the program and set it to the off state, changing the button back to start. """
        self.state = "OFF"
        
        # set the state timer label
        self.main_gui.state_time_label_header.configure(text=(self.state))
        
        # set the running variable to false to halt execution in the state functions
        self.running = False
        
        # Turn the program execution button back to the green start button
        self.main_gui.startButton.configure(text="Start", bg="green")
        
        for after_id in self.after_ids:         # cancel all after calls which cancels every recursive function call
            self.root.after_cancel(after_id)
        
        self.after_ids.clear()

        # send the reset command to reboot both Arduino boards 

        self.arduino_mgr.reset_arduinos()
        self.curr_trial_number = 1
        
    def start_program(self) -> None:
        # Start the program if it is not already runnning and generate random numbers
        self.running = True
        
        # program main start time begins now
        self.data_mgr.start_time = time.time()
        self.data_mgr.state_start_time = time.time()
        
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