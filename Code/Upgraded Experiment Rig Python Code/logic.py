import time
import numpy as np
from typing import Tuple

class ExperimentLogic:
    def __init__(self, controller) -> None:
        self.controller = controller 
            
    def reset_clock(self) -> Tuple[int, int]:
        # reset timers to hold 0  
        elapsed_time = 0 
        state_elapsed_time = 0
        
        return elapsed_time, state_elapsed_time
        
    def new_ITI_reset(self):
        # Set the program state to initial time interval
        self.state = "ITI"
        
        # new trial so reset the lick counters
        self.side_one_licks = 0
        self.side_two_licks = 0

    def save_licks(self, i):
        """ define method that saves the licks to the data table and increments our iteration variable. """
        # if we get to this function straight from the TTC function, then we used up the full TTC and set TTC actual for this trial to the predetermined value
        if self.state == 'TTC':
            self.controller.data_mgr.stimuli_dataframe.loc[self.controller.data_mgr.curr_trial_number - 1,'TTC Actual'] = \
                self.controller.data_mgr.stimuli_dataframe.loc[self.controller.data_mgr.curr_trial_number - 1, 'TTC']
            
            command = "SIDE_ONE\n" + str(self.controller.data_mgr.stim1_position) + "\nSIDE_TWO\n" + str(self.controller.data_mgr.stim2_position) + "\n"
            self.controller.arduino_mgr.arduinoMotor.write(command)
            
        command = b'UP\n'
        # tell the motor arduino to move the door up
        self.controller.arduino_mgr.arduinoMotor.write(command)
           
        # increment the trial number                                     
        self.controller.data_mgr.curr_trial_number += 1        

        # store licks in the ith rows in their respective stimuli column in the data table for the trial                                     
        self.controller.data_mgr.stimuli_dataframe.loc[i, 'Stimulus 1 Licks'] = self.side_one_licks        
        self.controller.data_mgr.stimuli_dataframe.loc[i, 'Stimulus 2 Licks'] = self.side_two_licks

        # this is how processes that are set to execute after a certain amount of time are cancelled. 
        # call the self.master.after_cancel function and pass in the ID that was assigned to the function call
        self.controller.root.after_cancel(self.update_licks_id)

        # Jump to ITI state to begin ITI for next trial by incrementing the i variable
        self.controller.initial_time_interval(i+1)     
        
    def read_licks(self, i):
        """ Define the method for reading data from the optical fiber Arduino """
        # try to read licks if there is a arduino connected
        available_data, data = self.controller.arduino_mgr.read_from_laser()
        if(available_data):
            # Append the data to the scrolled text widget
            if "Stimulus One Lick" in data:
                # if we detect a lick on spout one, then add it to the lick data table
                # and add whether the lick was a TTC lick or a sample lick


                # format for this is self.dataFrame.loc[rowNumber, Column Title] = value
                self.controller.data_mgr.licks_dataframe.loc[self.controller.data_mgr.total_licks, 'Trial Number'] = self.controller.data_mgr.curr_trial_number
                self.controller.data_mgr.licks_dataframe.loc[self.controller.data_mgr.total_licks, 'Port Licked'] = 'Stimulus 1'
                self.controller.data_mgr.licks_dataframe.loc[self.controller.data_mgr.total_licks, 'Time Stamp'] = time.time() - self.controller.data_mgr.start_time
                self.controller.data_mgr.licks_dataframe.loc[self.controller.data_mgr.total_licks, 'State'] = self.state
                
                self.controller.data_mgr.side_one_licks += 1
                self.controller.data_mgr.total_licks += 1

            if "Stimulus Two Lick" in data:
                # if we detect a lick on spout one, then add it to the lick data table
                # and add whether the lick was a TTC lick or a sample lick

                # format for this is self.dataFrame.loc[rowNumber, Column Title] = value
                self.controller.data_mgr.licks_dataframe.loc[self.controller.data_mgr.total_licks, 'Trial Number'] = self.controller.data_mgr.curr_trial_number
                self.controller.data_mgr.licks_dataframe.loc[self.controller.data_mgr.total_licks, 'Port Licked'] = 'Stimulus 2'
                self.controller.data_mgr.licks_dataframe.loc[self.controller.data_mgr.total_licks, 'Time Stamp'] = time.time() - self.controller.data_mgr.start_time
                self.controller.data_mgr.licks_dataframe.loc[self.controller.data_mgr.total_licks, 'State'] = self.state


                self.controller.data_mgr.side_two_licks += 1
                self.controller.data_mgr.total_licks += 1  

        # Call this method again every 100 ms
        self.update_licks_id = self.controller.root.after(100, lambda: self.read_licks(i))
        self.controller.after_ids.append(self.update_licks_id)


    def return_trials_remaining(self) -> bool:
        """ Method to return if there are trials remaining """
        return (self.controller.data_mgr.curr_trial_number) \
            <= (self.controller.data_mgr.num_stimuli.get() * self.controller.data_mgr.num_trial_blocks.get())
            
    def check_dataframe_entry_isfloat(self, iteration, state):
        """ Method to check if the value in the dataframe is a numpy float. If it is, then we return the value. If not, we return -1. """
        if isinstance(self.controller.data_mgr.stimuli_dataframe.loc[iteration, state], (int, np.integer, float)):
           interval_value = self.controller.data_mgr.stimuli_dataframe.loc[iteration, state]
        else:
            interval_value = -1
        return interval_value