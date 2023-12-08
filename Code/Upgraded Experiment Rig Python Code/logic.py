import tkinter as tk
import time
import random
import numpy as np 

class ExperimentLogic:
    def __init__(self, controller) -> None:
        self.controller = controller 

        self.root = controller.root

        # Initialize these function instance ID variables
        # These hold the values of the function calls when we want to call them repeatedly
        # This is what we call to cancel the function call to avoid errors when closing the program
        self.update_clock_id = None
        self.update_licks_id = None
        self.update_plot_id = None
        
            
            
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
            

    def time_to_contact(self, i, main_gui, arduino_mgr):
        """ defining the TTC state method, argument are self and i. i is passed from TTC to keep track of what stimuli we are on. """
        if self.running:
            self.state = "TTC"
            
            """start reading licks, we pass the same i into this function that we used in the previous function to
            keep track of where we are storing the licks in the data table"""
            self.read_licks(i)
            
            # update state timer header
            main_gui.state_time_label_header.configure(text=(self.state + " Time:"))
            
            # state start time begins 
            self.state_start_time = time.time()
            
            # tell motor arduino to move the door down              
            command = 'DOWN\n'
            arduino_mgr.send_command_to_motor(command.encode('utf-8'))
            
            # Create a list of the stimuli dictionary values, will give list of stimuli. 
            stim_var_list = list(self.stimuli_vars.values())
            
            """ Look in the dataframe in the current trial for the stimulus to give, once found mark the index with corresponding solenoid
            valve number and save into stimulus position variables. """
            for index, string_var in enumerate(stim_var_list):
                if string_var.get() == self.df_stimuli.loc[i,'Stimulus 1']:
                    self.stim1_position = str(index + 1)

                # repeat process for the second stimulus
                elif string_var.get() == self.df_stimuli.loc[i,'Stimulus 2']:
                    self.stim2_position = str(index + 1)

            """concatinate the positions with the commands that are used to tell the arduino which side we are opening the valve for. 
            SIDE_ONE tells the arduino we need to open a valve for side one, it will then read the next line to find which valve to open.
            valves are numbered 1-8 so "SIDE_ONE\n1\n" tells the arduino to open valve one for side one. """
            command = "SIDE_ONE\n" + str(self.stim1_position) + "\nSIDE_TWO\n" + str(self.stim2_position) + "\n"
            
            # send the command
            self.arduinoMotor.write(command.encode('utf-8'))
            
            # write the time to contact to the program information box
            self.append_data("Time to Contact: " + str(self.df_stimuli.loc[i,'TTC'] / 1000) + "s\n")
            
            """main_gui.master.after tells the main tkinter program to wait the amount of time specified for the TTC in the ith row of the table. Save licks is called with previously used 'i' iterator.
            Lambda ensures the function is only called after the wait period and not immediately."""
            self.after_sample_id = main_gui.master.after(int(self.df_stimuli.loc[i, 'TTC']), lambda: self.save_licks(i))

    def sample_time(self, i):
        """ define sample time method, i is again passed to keep track of trial and stimuli """
        if self.running:
            self.state = "Sample"
            
            # change the state time label accordingly                                     
            self.state_time_label_header.configure(text=(self.state + " Time:"))

            # Update the state start time to the current time
            self.state_start_time = time.time()        

            # Appending the sample time interval to the main text box
            self.append_data('Sample Time Interval: ' + str(self.df_stimuli.loc[i,'Sample Time'] / 1000) + "s\n\n\n")  

            # After the sample time specified in the ith row of the 'Sample Time' table, we will jump to the save licks function
            self.master.after(int(self.df_stimuli.loc[i, 'Sample Time']), lambda: self.save_licks(i))                     

    def save_licks(self, i):
        """ define method that saves the licks to the data table and increments our iteration variable. """
        # if we get to this function straight from the TTC function, then we used up the full TTC and set TTC actual for this trial to the predetermined value
        if self.state == 'TTC':
            self.df_stimuli.loc[self.curr_trial_number - 1,'TTC Actual'] = self.df_stimuli.loc[self.curr_trial_number - 1, 'TTC']
            self.command = "SIDE_ONE\n" + str(self.stim1_position) + "\nSIDE_TWO\n" + str(self.stim2_position) + "\n"
            self.arduinoMotor.write(self.command.encode('utf-8'))
        # tell the motor arduino to move the door up
        self.arduinoMotor.write(b'UP\n')   
        # increment the trial number                                     
        self.curr_trial_number += 1        

        # store licks in the ith rows in their respective stimuli column in the data table for the trial                                     
        self.df_stimuli.loc[i, 'Stimulus 1 Licks'] = self.side_one_licks        
        self.df_stimuli.loc[i, 'Stimulus 2 Licks'] = self.side_two_licks

        # this is how processes that are set to execute after a certain amount of time are cancelled. 
        # call the self.master.after_cancel function and pass in the ID that was assigned to the function call
        self.master.after_cancel(self.update_licks_id)

        # try to redraw the program stimuli schdule window to update the information with number of licks, if it is open
        try:
            self.trial_blocks.redraw()
        # if the window is not open, it will throw an error, but we tell the program that its fine just keep going
        except:
            pass
        # Jump to ITI state to begin ITI for next trial by incrementing the i variable
        self.initial_time_interval(i+1)     
        
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
                self.licks_df.loc[self.total_licks, 'Trial Number'] = self.curr_trial_number
                self.licks_df.loc[self.total_licks, 'Port Licked'] = 'Stimulus 1'
                self.licks_df.loc[self.total_licks, 'Time Stamp'] = time.time() - self.start_time
                self.licks_df.loc[self.total_licks, 'State'] = self.state
                # redraw the licks table if it exists, updating the display with the new addition
                if(self.stamped_exists):
                    self.stamped_licks.redraw()

                self.side_one_licks += 1
                self.total_licks += 1

            if "Stimulus Two Lick" in data:
                # if we detect a lick on spout one, then add it to the lick data table
                # and add whether the lick was a TTC lick or a sample lick

                # format for this is self.dataFrame.loc[rowNumber, Column Title] = value
                self.controller.data.licks_dataframe.loc[self.controller.data.total_licks, 'Trial Number'] = self.controller.data.curr_trial_number
                self.controller.data.licks_dataframe.loc[self.controller.data.total_licks, 'Port Licked'] = 'Stimulus 2'
                self.controller.data.licks_dataframe.loc[self.controller.data.total_licks, 'Time Stamp'] = time.time() - self.controller.data.start_time
                self.controller.data.licks_dataframe.loc[self.controller.data.total_licks, 'State'] = self.state


                self.controller.data.side_two_licks += 1
                self.controller.data.total_licks += 1  

        # if we are in the TTC state and detect 3 or more licks from either side, then immediately jump to the sample time 
        # state and continue the trial
        if (self.side_one_licks >= 3 or self.side_two_licks >= 3) and self.state == 'TTC':
            self.controller.data.stimuli_dataframe.loc[self.controller.data.curr_trial_number - 1,'TTC Actual'] = (time.time() - self.state_start_time) * 1000
            self.trial_blocks.update()
            self.root.after_cancel(self.after_sample_id)
            self.side_one_licks = 0
            self.side_two_licks = 0
            self.sample_time(i)

        # Call this method again every 100 ms
        self.update_licks_id = self.root.after(100, lambda: self.read_licks(i))


    def return_trials_remaining(self) -> bool:
        """ Method to return if there are trials remaining """
        return (self.controller.data_mgr.curr_trial_number) \
            <= (self.controller.data_mgr.num_stimuli.get() * self.controller.data_mgr.num_trial_blocks.get())