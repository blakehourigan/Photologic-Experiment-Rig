import tkinter as tk
import time

class ExperimentLogic:
    def __init__(self, controller) -> None:
        self.controller = controller 
            
    def clear_button_logic(self, main_gui):
        # Clear the scrolled text widget
        main_gui.data_text.delete('1.0', tk.END)
        # reset timers to hold 0  
        elapsed_time = 0 
        main_gui.time_label.configure(text="{:.3f}s".format(elapsed_time))
        state_elapsed_time = 0
        main_gui.state_time_label.configure(text="{:.3f}s".format(state_elapsed_time))
        
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
            
            command = "SIDE_ONE\n" + str(self.stim1_position) + "\nSIDE_TWO\n" + str(self.stim2_position) + "\n"
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

        # try to redraw the program stimuli schdule window to update the information with number of licks, if it is open
        try:
            self.trial_blocks.redraw()
        # if the window is not open, it will throw an error, but we tell the program that its fine just keep going
        except:
            pass
        # Jump to ITI state to begin ITI for next trial by incrementing the i variable
        self.controller.initial_time_interval(i+1)     
        
    def read_licks(self, i):
        """ Define the method for reading data from the optical fiber Arduino """
        # try to read licks if there is a arduino connected
        if(self.arduinoLaser.in_waiting > 0):
            data = self.arduinoLaser.read(self.arduinoLaser.in_waiting).decode('utf-8')
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

        # if we are in the TTC state and detect 3 or more licks from either side, then immediately jump to the sample time 
        # state and continue the trial
        if (self.side_one_licks >= 3 or self.side_two_licks >= 3) and self.state == 'TTC':
            self.controller.data_mgr.stimuli_dataframe.loc[self.controller.data_mgr.curr_trial_number - 1,'TTC Actual'] = \
                (time.time() - self.controller.data_mgr.state_start_time) * 1000
                
            self.trial_blocks.update()
            self.controller.root.after_cancel(self.after_sample_id)
            self.side_one_licks = 0
            self.side_two_licks = 0
            self.controller.sample_time(i)

        # Call this method again every 100 ms
        self.update_licks_id = self.controller.root.after(100, lambda: self.read_licks(i))


    def return_trials_remaining(self) -> bool:
        """ Method to return if there are trials remaining """
        return (self.controller.data_mgr.curr_trial_number) \
            <= (self.controller.data_mgr.num_stimuli.get() * self.controller.data_mgr.num_trial_blocks.get())