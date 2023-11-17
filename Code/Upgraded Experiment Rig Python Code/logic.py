import tkinter as tk
import time

class ExperimentLogic:
    def __init__(self, controller) -> None:
        
        self.interval_vars = \
        {
            'ITI_var': tk.IntVar(value=30000),
            'TTC_var': tk.IntVar(value=15000),
            'sample_time_var': tk.IntVar(value=15000),
            'ITI_random_entry': tk.IntVar(value=5000),
            'TTC_random_entry': tk.IntVar(value=5000),
            'sample_time_entry': tk.IntVar(value=5000),
        }
        
        # initializing the lists that will hold the final calculated random interval values 

        self.ITI_intervals_final = []
        self.TTC_intervals_final = []
        self.sample_intervals_final = []

        # These will be used to store the random +/- values to be added to the constant values

        self.ITI_random_intervals = []
        self.TTC_random_intervals = []
        self.sample_random_intervals = []
    
        self.stimuli_vars = {f'stimuli_var_{i+1}': tk.StringVar() for i in range(8)}
        for key in self.stimuli_vars:
            self.stimuli_vars[key].set(key)
            
            
        # initialize lists to hold original pairs and the list that will hold our dataframes.

        self.pairs = []
        self.df_list = []

        # Initialize variables that will keep track of the total number of trials we will have, the total number of trial blocks that the user wants to run
        # and the total number of stimuli. These are of type IntVar because they are used in the GUI. 

        self.num_trials = tk.IntVar(value=0)
        self.num_trial_blocks = tk.IntVar(value=0)
        self.num_stimuli = tk.IntVar(value=0)
        
        # initializing variable for iteration through the trials in the program

        self.curr_trial_number = 1

        # Initialize boolean flags to false
        self.running = False

        self.blocks_generated = False

        self.stamped_exists = False

        self.data_window_open = False
        
        # Initialize the time, licks to 0
        
        self.start_time = 0
        self.state_start_time = 0
        self.side_one_licks = 0
        self.side_two_licks = 0
        self.total_licks = 0

        # Initialize these function instance ID variables
        # These hold the values of the function calls when we want to call them repeatedly
        # This is what we call to cancel the function call to avoid errors when closing the program
        self.update_clock_id = None
        self.update_licks_id = None
        self.update_plot_id = None
        
        self.state = "OFF"
            
    def start_button_logic(self, main_gui, arduino_mgr):
        """ Define the method for toggling the program state via the start/stop button """
        # If the program is running, stop it
        if self.running:
            self.stop_program(main_gui)
            #self.master.after_cancel(self.update_clock_id)
            # if we have called the update licks function at all, then stop it from being called now, we're done with it 
            if self.update_licks_id is not None:  
                self.master.after_cancel(self.update_licks_id)

            # if we have opened a data window and have a update for the plot scheduled, then cancel it and close the window
            if self.update_plot_id is not None:
                self.main_gui.master.after_cancel(self.update_plot_id)
                #self.data_window_instance.destroy()
            # try to send the reset command to reboot both Arduino boards 

            arduino_mgr.reset_arduinos()
            self.curr_trial_number = 1
        # If the program is not running, start it
        else:
            # Start the program if it is not already runnning and generate random numbers
            self.running = True
            # program main start time begins now
            self.start_time = time.time()
            
            self.update_clock(main_gui)
            # turn the main button to the red stop button
            main_gui.startButton.configure(text="Stop", bg="red")
            # call the first ITI state with an iteration variable (i acts as a 
            # variable to iterate throgh the program schedule data table) starting at 0
            self.initial_time_interval(0, main_gui, arduino_mgr)
            
    def stop_program(self, main_gui):
        """ Method to halt the program and set it to the off state, changing the button back to start. """
        self.state = "OFF"
        # set the state timer label
        main_gui.state_time_label_header.configure(text=(self.state))
        # set the running variable to false to halt execution in the state functions
        self.running = False
        # Turn the program execution button back to the green start button
        main_gui.startButton.configure(text="Start", bg="green")
            
    def clear_button_logic(self, main_gui):
        # Clear the scrolled text widget
        main_gui.data_text.delete('1.0', tk.END)
        # reset timers to hold 0  
        elapsed_time = 0 
        main_gui.time_label.configure(text="{:.3f}s".format(elapsed_time))
        state_elapsed_time = 0
        main_gui.state_time_label.configure(text="{:.3f}s".format(state_elapsed_time))
        
    # Define the method for updating the clock
    def update_clock(self, main_gui):
        # If the program is running, update the elapsed time
        if self.running:
            # total elapsed time is current minus program start time
            elapsed_time = time.time() - self.start_time
            # update the main screen label and set the number of decimal points to 3 
            main_gui.time_label.configure(text="{:.3f}s".format(elapsed_time))
            # state elapsed time is current time minus the time we entered the state 
            state_elapsed_time = time.time() - self.state_start_time
            # update the main screen label and set the number of decimal points to 3
            main_gui.state_time_label.configure(text="{:.3f}s".format(state_elapsed_time))
            # Call this method again after 100 ms
            main_gui.master.after(50, lambda: self.update_clock(main_gui))
            
    def initial_time_interval(self, i, main_gui, arduino_mgr):
        """defining the ITI state method, arguments given are self which says that the function should be called on the instance of the class, which is our app 
        the second argument is i, which is the iteration variable that we use to keep track of what trial we are on. 
        i is defined on line 650 where we first call the function."""
        
        # if we have pressed start, and the current trial number is less than the number of trials determined by number of stim * number of trial blocks, then continue running through more trials
        if self.running and (self.curr_trial_number) <= (self.num_stimuli.get() * self.num_trial_blocks.get()) and self.blocks_generated == True:
            # Set the program state to initial time interval
            self.state = "ITI"
            
            # new trial so reset the lick counters
            self.side_one_licks = 0
            self.side_two_licks = 0
            
            # configure the state time label in the top right of the main window to hold the value of the new state
            main_gui.state_time_label_header.configure(text=(self.state + " Time:"))
            
            # update the state start time to now, so that it starts at 0
            self.state_start_time = time.time()  
            
            # Get trial number and stimuli in the trial and add them to the main information screen
            # self.df_stimuli.loc is what we use to get values that are held in the main data table. Accessed using .loc[row_num, 'Column Name']
            string = '\nTRIAL # (' + str(self.curr_trial_number) + ') Stimulus 1:' + self.df_stimuli.loc[i, 'Stimulus 1'] + " vs. Stimulus 2:" + self.df_stimuli.loc[i, 'Stimulus 2'] + "\n"
            
            # this command is what adds things to the main information screen
            main_gui.append_data(string)
            
            # for every letter in the string we just created, create a dash to separate the title of the trial from the contents
            for letter in range(len(string)):
                self.append_data("-")
            
            # add the initial interval to the program information box
            main_gui.append_data('\nInitial Interval Time: ' +  str(self.df_stimuli.loc[i,'ITI'] / 1000) + "s\n")
            
            """main_gui.master.after tells the main tkinter program to wait the amount of time specified for the TTC in the ith row of the table. Save licks is called with previously used 'i' iterator.
            Lambda ensures the function is only called after the wait period and not immediately."""
            main_gui.master.after(int(self.df_stimuli.loc[i,'ITI']), lambda: self.time_to_contact(i, main_gui, arduino_mgr))
        else: 
            # if we have gone through every trial then end the program.
            self.stop_program()

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
                self.licks_df.loc[self.total_licks, 'Trial Number'] = self.curr_trial_number
                self.licks_df.loc[self.total_licks, 'Port Licked'] = 'Stimulus 2'
                self.licks_df.loc[self.total_licks, 'Time Stamp'] = time.time() - self.start_time
                self.licks_df.loc[self.total_licks, 'State'] = self.state
                # redraw the licks table if it exists, updating the display with the new addition
                if(self.stamped_exists):
                    self.stamped_licks.redraw()

                self.side_two_licks += 1
                self.total_licks += 1  

        # if we are in the TTC state and detect 3 or more licks from either side, then immediately jump to the sample time 
        # state and continue the trial
        if (self.side_one_licks >= 3 or self.side_two_licks >= 3) and self.state == 'TTC':
            self.df_stimuli.loc[self.curr_trial_number - 1,'TTC Actual'] = (time.time() - self.state_start_time) * 1000
            self.trial_blocks.update()
            self.root.after_cancel(self.after_sample_id)
            self.side_one_licks = 0
            self.side_two_licks = 0
            self.sample_time(i)

        # Call this method again every 100 ms
        self.update_licks_id = self.root.after(100, lambda: self.read_licks(i))

            