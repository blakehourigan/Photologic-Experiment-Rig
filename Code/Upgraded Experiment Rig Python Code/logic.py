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
        self.controller.state = "ITI"
    
        
        # new trial so reset the lick counters
        self.controller.data_mgr.side_one_licks = 0
        self.controller.data_mgr.side_two_licks = 0

    
        
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
                self.controller.data_mgr.licks_dataframe.loc[self.controller.data_mgr.total_licks, 'State'] = self.controller.state
                
                self.controller.data_mgr.side_one_licks += 1
                self.controller.data_mgr.total_licks += 1

            if "Stimulus Two Lick" in data:
                # if we detect a lick on spout one, then add it to the lick data table
                # and add whether the lick was a TTC lick or a sample lick

                # format for this is self.dataFrame.loc[rowNumber, Column Title] = value
                self.controller.data_mgr.licks_dataframe.loc[self.controller.data_mgr.total_licks, 'Trial Number'] = self.controller.data_mgr.curr_trial_number
                self.controller.data_mgr.licks_dataframe.loc[self.controller.data_mgr.total_licks, 'Port Licked'] = 'Stimulus 2'
                self.controller.data_mgr.licks_dataframe.loc[self.controller.data_mgr.total_licks, 'Time Stamp'] = time.time() - self.controller.data_mgr.start_time
                self.controller.data_mgr.licks_dataframe.loc[self.controller.data_mgr.total_licks, 'State'] = self.controller.state


                self.controller.data_mgr.side_two_licks += 1
                self.controller.data_mgr.total_licks += 1  

        # Call this method again every 100 ms
        self.update_licks_id = self.controller.root.after(100, lambda: self.read_licks(i))
        self.controller.after_ids.append(self.update_licks_id)



    def check_licks(self, iteration):
        """ define method for checking licks during the TTC state """
        # if we are in the TTC state and detect 3 or more licks from either side, then immediately jump to the sample time 
        # state and continue the trial
        if (self.side_one_licks >= 3 or self.side_two_licks >= 3) and self.controller.state == 'TTC':
            self.controller.data_mgr.stimuli_dataframe.loc[self.controller.data_mgr.curr_trial_number - 1,'TTC Actual'] = \
                (time.time() - self.controller.data_mgr.state_start_time) * 1000
                
            self.controller.root.after_cancel(self.controller.after_sample_id)
            self.side_one_licks = 0
            self.side_two_licks = 0
            self.controller.sample_time(iteration)

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