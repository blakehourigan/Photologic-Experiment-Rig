# Importing libraries that are used for this program
import sys
import serial                           
import time
import random
import itertools
import numpy as np
import tkinter as tk
from tkinter import ttk
from tkinter import scrolledtext
from tkinter import filedialog
from tkinter import messagebox
import pandas as pd
from pandastable import Table, TableModel
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from serial.serialutil import SerialException

# defining the baud rate for communication with the arduinos

BAUD_RATE = 9600          

class App:
    # Initialize the App object
    def __init__(self):
        # Create a Tkinter window
        self.root = tk.Tk()
        # Set the initial size of the window
        self.root.geometry("1400x800")
        # Set the title of the window
        self.root.title("Upgraded Experiment Rig")
        self.root.iconbitmap('C:\\Users\\Samuelsen Data 4\\Documents\\Upgraded Experiment Rig\\Code\\Upgraded Experiment Rig Python Code\\rat.ico')
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # Initialize the interval variables and their corresponding IntVars types in a dictionary

        self.interval_vars = {
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

        # Initialize dictionary full of stimulus variables and fill each entry to hold default value equal to the key value

        self.stimuli_vars = {f'stimuli_var_{i+1}': tk.StringVar() for i in range(8)}
        for key in self.stimuli_vars:
            self.stimuli_vars[key].set(key)

        # initialize lists to hold original pairs and the list that will hold our dataframes.

        self.pairs = []
        self.df_list = []

        # Initialize variables that will keep track of the total number of trials we will have, the total number of trial blocks that the user wants to run
        # and the total number of stimuli. These are of type IntVar because they are used in the GUI. 

        self.num_trials = tk.IntVar()
        self.num_trials.set(0)
        self.num_trial_blocks = tk.IntVar()
        self.num_trial_blocks.set(0)
        self.num_stimuli = tk.IntVar()
        self.num_stimuli.set(0)

        # initializing variable for iteration through the trials in the program

        self.curr_trial_number = 1

        # Initialize the running flag to False
        self.running = False

        self.blocks_generated = False

        self.lick_table_created = False

        # Initialize the start time to 0
        self.start_time = 0

        self.side_one_licks = 0
        self.side_two_licks = 0
        self.total_licks = 0


        self.data_window_open = False
        
        # Initialize these function instance ID variables
        self.update_clock_id = None
        self.update_licks_id = None
        self.update_plot_id = None

        # Program defaults to the off state
        self.state = "OFF"

        # Configure the GUI grid layout
        for i in range(8):
            self.root.grid_rowconfigure(i, weight=1 if i == 3 else 0)
        # The column is also configured to expand
        self.root.grid_columnconfigure(0, weight=1)

        # Label headers
        self.time_label_header = tk.Label(text="Elapsed Time:", bg="light blue", font=("Helvetica", 24))
        self.time_label_header.grid(row=0, column=0, pady=10, padx=10, sticky='e')

        self.state_time_label_header = tk.Label(text=(self.state), bg="light blue", font=("Helvetica", 24))
        self.state_time_label_header.grid(row=0, column=2, pady=10, padx=10, sticky='e')

        # Timer labels
        self.time_label = tk.Label(text="", bg="light blue", font=("Helvetica", 24))
        self.time_label.grid(row=0, column=1, pady=10, padx=10, sticky='w')

        self.state_time_label = tk.Label(text="", bg="light blue", font=("Helvetica", 24))
        self.state_time_label.grid(row=0, column=3, pady=10, padx=10, sticky='w')

        # Labels for Interval Entry widgets
        self.interval1_label = tk.Label(self.root, text="Initial Interval:", bg="light blue", font=("Helvetica", 24))
        self.interval1_label.grid(row=5, column=0, pady=10, padx=10, sticky='nsew')

        self.interval2_label = tk.Label(self.root, text="Time to Contact:", bg="light blue", font=("Helvetica", 24))
        self.interval2_label.grid(row=5, column=1, pady=10, padx=10, sticky='nsew')

        self.interval3_label = tk.Label(self.root, text="Time to Sample:", bg="light blue", font=("Helvetica", 24))
        self.interval3_label.grid(row=5, column=2, pady=10, padx=10, sticky='nsew')

        # Add Data Entry widgets for intervals
        self.interval1_entry = tk.Entry(self.root, textvariable=self.interval_vars['ITI_var'], font=("Helvetica", 24))
        self.interval1_entry.grid(row=6, column=0, pady=10, padx=10, sticky='nsew')

        self.interval2_entry = tk.Entry(self.root, textvariable=self.interval_vars['TTC_var'], font=("Helvetica", 24))
        self.interval2_entry.grid(row=6, column=1, pady=10, padx=10, sticky='nsew')

        self.interval3_entry = tk.Entry(self.root, textvariable=self.interval_vars['sample_time_var'], font=("Helvetica", 24))
        self.interval3_entry.grid(row=6, column=2, pady=10, padx=10, sticky='nsew')

        # Labels for Interval Entry widgets
        self.interval1_label = tk.Label(self.root, text="+/- (All times in ms)", bg="light blue", font=("Helvetica", 24))
        self.interval1_label.grid(row=7, column=0, pady=10, padx=10, sticky='nsew', columnspan=3)

        # Label for # of trials
        self.num_trials_label = tk.Label(self.root, text="Trial Blocks", bg="light blue", font=("Helvetica", 24))
        self.num_trials_label.grid(row=5, column=3, pady=10, padx=10, sticky='nsew')

        # Entry for # of trials
        self.num_trial_blocks_entry = tk.Entry(self.root, textvariable=self.num_trial_blocks, font=("Helvetica", 24))
        self.num_trial_blocks_entry.grid(row=6, column=3, pady=10, padx=10, sticky='nsew')

        # Label for # stimuli
        self.num_stimuli_label = tk.Label(self.root, text="# of Stimuli", bg="light blue", font=("Helvetica", 24))
        self.num_stimuli_label.grid(row=7, column=3, pady=10, padx=10, sticky='nsew')

        # Entry for # of trials
        self.num_stimuli_entry = tk.Entry(self.root, textvariable=self.num_stimuli, font=("Helvetica", 24))
        self.num_stimuli_entry.grid(row=8, column=3, pady=10, padx=10, sticky='nsew')

        # Add Data Entry widgets for random plus/minus intervals
        self.interval1Rand_entry = tk.Entry(self.root, textvariable=self.interval_vars['ITI_random_entry'], font=("Helvetica", 24))
        self.interval1Rand_entry.grid(row=8, column=0, pady=10, padx=10, sticky='nsew')

        self.interval2Rand_entry = tk.Entry(self.root, textvariable=self.interval_vars['TTC_random_entry'], font=("Helvetica", 24))
        self.interval2Rand_entry.grid(row=8, column=1, pady=10, padx=10, sticky='nsew')

        self.interval3Rand_entry = tk.Entry(self.root, textvariable=self.interval_vars['sample_time_entry'], font=("Helvetica", 24))
        self.interval3Rand_entry.grid(row=8, column=2, pady=10, padx=10, sticky='nsew')

        # Program information label
        self.program_label = tk.Label(text="Program Information", bg="light blue", font=("Helvetica", 24))
        self.program_label.grid(row=2, column=0, pady=10, padx=10, sticky='nsew', columnspan=4)

        # Start/stop button
        self.startButton = tk.Button(text="Start", command=self.start_toggle, bg="green", font=("Helvetica", 24))
        self.startButton.grid(row=1, column=0, pady=10, padx=10, sticky='nsew', columnspan=2)

        # Clear screen button
        self.clear_button = tk.Button(text="Clear", command=self.clear_toggle, bg="grey", font=("Helvetica", 24))
        self.clear_button.grid(row=1, column=2, pady=10, padx=10, sticky='nsew', columnspan=2)

        # button to open the stimuli window
        self.experiment_control_button = tk.Button(text="Experiment CTL", command=self.experiment_control, bg="grey", font=("Helvetica", 24))
        self.experiment_control_button.grid(row=10, column=0, pady=10, padx=10, sticky='nsew',columnspan=1)

        self.lick_window_button = tk.Button(text="Lick Data", command=self.lick_window, bg="grey", font=("Helvetica", 24))
        self.lick_window_button.grid(row=10, column=1, pady=10, padx=10, sticky='nsew',columnspan=1)

        # button to open the data window
        self.data_window_button = tk.Button(text="View Data", command=self.data_window, bg="grey", font=("Helvetica", 24))
        self.data_window_button.grid(row=10, column=2, pady=10, padx=10, sticky='nsew')

        # button to save expirement data to excel sheets
        self.data_window_button = tk.Button(text="Save Data Externally", command=self.save_data, bg="grey", font=("Helvetica", 24))
        self.data_window_button.grid(row=10, column=3, pady=10, padx=10, sticky='nsew')

        # Create a frame to contain the scrolled text widget and place it in the grid
        self.frame = tk.Frame(self.root)
        self.frame.grid(row=3, column=0, pady=10, padx=10, sticky='nsew', columnspan=4)

        # Configure the frame's column and row to expand as the window resizes
        self.frame.grid_columnconfigure(0, weight=1)
        self.frame.grid_rowconfigure(0, weight=1)

        # Create a scrolled text widget for displaying data, place it in the frame, and set it to expand with the frame
        self.data_text = scrolledtext.ScrolledText(self.frame, font=("Helvetica", 24), height=10, width=30)
        self.data_text.grid(row=0, column=0, sticky='nsew')

        try:
            # Open a serial connection to the first Arduino
            self.arduinoLaser = serial.Serial('COM3', BAUD_RATE)
            # Open a serial connection to the second Arduino
            self.arduinoMotor = serial.Serial('COM4', BAUD_RATE)
            # if one or more of the arduinos are not connected then we need to let the user know 
        except SerialException:
                messagebox.showinfo("Serial Error", "1 or more Arduino boards are not connected, connect arduino boards and relaunch before running program")
        # Start the program clock function 
        self.update_clock()

    # Program state methods

    def initial_time_interval(self, i):
        # if we have pressed start, and the current trial number is less than the number of trials determined by number of stim * number of trial blocks, then continue running through more trials
        if self.running and (self.curr_trial_number) <= (self.num_stimuli.get() * self.num_trial_blocks.get()) and self.blocks_generated == True:
            # Set the program state to initial time interval
            self.state = "ITI"
            # new trial so reset the lick counters
            self.side_one_licks = 0
            self.side_two_licks = 0
            # configure the state time label in the top right of the main window to hold the value of the new state
            self.state_time_label_header.configure(text=(self.state + " Time:"))
            # update the state start time to now, so that it starts at 0
            self.state_start_time = time.time()  
            # 
            string = 'TRIAL # (' + str(self.curr_trial_number) + ') Stimulus 1:' + self.df_stimuli.loc[i, 'Stimulus 1'] + " vs. Stimulus 2:" + self.df_stimuli.loc[i, 'Stimulus 2'] + "\n"
            self.append_data(string)
            for letter in range(len(string)):
                self.append_data("-")

            self.append_data('\nInitial Interval Time: ' +  str(self.df_stimuli.loc[i,'ITI'] / 1000) + "s\n")
            # After the 'ITI' time, call time_to_contact
            self.root.after(int(self.df_stimuli.loc[i,'ITI']), lambda: self.time_to_contact(i))
        else: 
            self.stop_program()

    def time_to_contact(self, i):
        if self.running:
            # Change program state to TTC
            self.state = "TTC"
            # start reading licks, we pass the same i into this function that we used in the previous function to
            # continue iterating
            self.read_licks(i)
            # update state timer header
            self.state_time_label_header.configure(text=(self.state + " Time:"))
            # Update the state start time to current time
            self.state_start_time = time.time()
            # move the door down  
            self.arduinoMotor.write(b'DOWN\n')
            stim_var_list = list(self.stimuli_vars.values())
            for index, string_var in enumerate(stim_var_list):
                if string_var.get() == self.df_stimuli.loc[i,'Stimulus 1']:
                    stim1_position = str(index + 1)
            for index, string_var in enumerate(stim_var_list):
                if string_var.get() == self.df_stimuli.loc[i,'Stimulus 2']:
                    stim2_position = str(index + 1)
            stim1_position = b'Stimulus 1 Position: ' + stim1_position.encode('utf-8') + b'\n'  
            stim2_position = b'Stimulus 2 Position: ' + stim2_position.encode('utf-8') + b'\n'  
            print(str(stim1_position) + "        " + str(stim2_position))
            self.arduinoMotor.write(stim1_position)
            self.arduinoMotor.write(stim2_position)
            self.append_data("Time to Contact: " + str(self.df_stimuli.loc[i,'TTC'] / 1000) + "s\n")
            self.after_sample_id = self.root.after(int(self.df_stimuli.loc[i, 'TTC']), lambda: self.save_licks(i))

    def sample_time(self, i):
        if self.running:
            # we are now in the sample time state
            self.state = "Sample"
            # change the state time label accordingly                                     
            self.state_time_label_header.configure(text=(self.state + " Time:"))

            # Update the state start time to the current time
            self.state_start_time = time.time()        

            # Appending the sample time interval to the main text box
            self.append_data('Sample Time Interval: ' + str(self.df_stimuli.loc[i,'Sample Time'] / 1000) + "s\n\n\n")  

            # After the sample time as stored in the df_stimuli table, go to the save licks function
            self.root.after(int(self.df_stimuli.loc[i, 'Sample Time']), lambda: self.save_licks(i))                     

            
    def save_licks(self, i):
            # if we get to this function straight from the TTC function, then we used up the full TTC and set TTC actual for this trial to the predetermined value
            if self.state == 'TTC':
                self.df_stimuli.loc[self.curr_trial_number - 1,'TTC Actual'] = self.df_stimuli.loc[self.curr_trial_number - 1, 'TTC']

            # tell the motor arduino to move the door up
            self.arduinoMotor.write(b'UP\n')   
            # increment the trial number                                     
            self.curr_trial_number += 1        

            # store licks in their respective columns in the data table for the trial                                     
            self.df_stimuli.loc[i, 'Stimulus 1 Licks'] = self.side_one_licks        
            self.df_stimuli.loc[i, 'Stimulus 2 Licks'] = self.side_two_licks

            # stop calling the lick function so we don't register any licks while we're in the ITI
            self.root.after_cancel(self.update_licks_id)

            # try to redraw the program stimuli schdule window to update the information with number of licks, if it is open
            try:
                self.trial_blocks.redraw()
            # if the window is not open, it will throw an error, but we tell the program that its fine just keep going
            except:
                pass
            # Jump to ITI state to begin ITI for next trial
            self.initial_time_interval(i+1)                                        

    def experiment_control(self):
        try:
            # Try to lift the window to the top (it will fail if the window is closed)
            self.experiment_control_instance.lift()
        except (AttributeError, tk.TclError):
            if(self.num_stimuli.get() == 0):
               messagebox.showinfo("Stimuli Not changed from 0", "No stimuli have been added, please close the window, set number of stimuli and try again")
            else: 
                self.experiment_control_instance = self.window_instance_generator("Experiment Control","1000x800")
                # Create the notebook (tab manager)

                notebook = ttk.Notebook(self.experiment_control_instance)
                tab1 = ttk.Frame(notebook)
                notebook.add(tab1, text='Experiment Stimuli')

                # These 3 lines set the contents of the tabs to expand when we expand the window  
                notebook.grid(sticky='nsew')                                                
                self.experiment_control_instance.grid_rowconfigure(0, weight=1)
                self.experiment_control_instance.grid_columnconfigure(0, weight=1)


                for i in range(self.num_stimuli.get()):

                    # Decide column based on iteration number
                    column = 0 if i < 4 else 1
                    # Adjust row for the second column
                    row = 2 * (i % 4)

                    # Labels/Entry boxes for Stimuli
                    label = tk.Label(tab1, text=f"Stimulus {i+1}", bg="light blue", font=("Helvetica", 24))
                    label.grid(row=row, column=column, pady=10, padx=10, sticky='nsew')

                    entry = tk.Entry(tab1, textvariable=self.stimuli_vars[f'stimuli_var_{i+1}'], font=("Helvetica", 24))
                    entry.grid(row=row+1, column=column, pady=10, padx=10, sticky='nsew')

                tab2 = ttk.Frame(notebook)
                notebook.add(tab2, text='Program Stimuli Schedule')

                self.lick_window_button = tk.Button(tab2, text="Lick Data", command=self.lick_window, bg="grey", font=("Helvetica", 24))
                self.lick_window_button.grid(row=1, column=0, pady=10, padx=10, sticky='nsew')

                # Generate stimuli schedule button 
                self.generate_stimulus = tk.Button(tab1,text="Generate Stimulus", command=lambda: self.create_trial_blocks(tab2, notebook, 0, 0), bg="green", font=("Helvetica", 24))
                self.generate_stimulus.grid(row=8, column=0, pady=10, padx=10, sticky='nsew', columnspan=2)
                self.create_trial_blocks(tab2, notebook, 0, 0)


    def lick_window(self):
        try:
            # Try to lift the window to the top (it will fail if the window is closed)
            self.lick_window_instance.lift()
        except (AttributeError, tk.TclError):
            # if blocks have been generated, then generate the blank lick table
            if self.blocks_generated:
                if not self.lick_table_created:
                    # Set column names for the table
                    self.licks_df = pd.DataFrame(columns=['Trial Number', 'Stimulus Licked', 'Time Stamp'])
                    # sets the row specified at .loc[len(self.licks_df)] which is zero at this time
                    # so the zeroth row is set to np.nan
                    self.licks_df.loc[len(self.licks_df)] = np.nan

                    # creating the frame that will contain the lick data table

                self.lick_table_created = True
                self.lick_window_instance = self.window_instance_generator("Licks Data Table", "300x00")
                self.licks_frame = tk.Frame(self.lick_window_instance)
                self.licks_frame.grid(row=0, column=0, sticky='nsew')  
                self.stamped_licks = Table(self.licks_frame, dataframe=self.licks_df, showtoolbar=False, showstatusbar=False, weight=1)
                self.stamped_licks.autoResizeColumns()
                self.stamped_licks.show()

            else:
                messagebox.showinfo("Blocks Not Generated","Experiment blocks haven't been generated yet, please generate trial blocks and try again")

    def window_instance_generator(self, name, size):

        self.window_instance = tk.Toplevel(self.root)
        self.window_instance.geometry(size)
        self.window_instance.title(name)
        self.window_instance.iconbitmap('C:\\Users\\Samuelsen Data 4\\Documents\\Upgraded Experiment Rig\\Code\\Upgraded Experiment Rig Python Code\\rat.ico')
        self.window_instance.grid_rowconfigure(0, weight=1)
        self.window_instance.grid_columnconfigure(0, weight=1)
        

        return self.window_instance

    def stop_program(self):
        self.state = "OFF"
        self.state_time_label_header.configure(text=(self.state))
        self.running = False
        self.startButton.configure(text="Start", bg="green")


    def data_window(self):
        try:
            # Try to lift the window to the top (it will fail if the window is closed)
            self.data_window_instance.lift()
        except (AttributeError, tk.TclError):
            if self.update_plot_id is not None:
                self.root.after_cancel(self.update_plot_id)
            if self.blocks_generated:
                self.data_window_instance = self.window_instance_generator("Data", "800x600")

                # Create a figure and axes for the plot
                self.fig, self.axes = plt.subplots()
                self.canvas = FigureCanvasTkAgg(self.fig, master=self.data_window_instance)
                self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

                # Create a toolbar for the plot and pack it into the window
                toolbar = NavigationToolbar2Tk(self.canvas, self.data_window_instance)
                toolbar.update()
                self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
                self.update_plot()
            else:
                messagebox.showinfo("Blocks Not Generated","Experiment blocks haven't been generated yet, please generate trial blocks and try again")

        

    # this is the function that will generate the full roster of stimuli for the duration of the program
    def create_trial_blocks(self, tab2, notebook, row_offset, col_offset):

        # the total number of trials equals the number of stimuli times the number of trial blocks that we want
        self.num_trials.set((self.num_stimuli.get() * self.num_trial_blocks.get()))         

        for entry in range(self.num_trials.get()):

            # Generating random intervals from +/- user entry
            self.ITI_random_intervals.append(random.randint(-(self.interval_vars['ITI_random_entry'].get()), (self.interval_vars['ITI_random_entry'].get())))
            self.TTC_random_intervals.append(random.randint(-(self.interval_vars['TTC_random_entry'].get()), (self.interval_vars['TTC_random_entry'].get())))
            self.sample_random_intervals.append(random.randint(-(self.interval_vars['sample_time_entry'].get()), (self.interval_vars['sample_time_entry'].get())))

            # Calculating final total intervals, adding random number to state constant
            self.ITI_intervals_final.append(self.interval_vars['ITI_var'].get() + self.ITI_random_intervals[entry])
            self.TTC_intervals_final.append(self.interval_vars['TTC_var'].get() + self.TTC_random_intervals[entry])
            self.sample_intervals_final.append(self.interval_vars['sample_time_var'].get() + self.sample_random_intervals[entry])

        self.changed_vars = [v for i, (k, v) in enumerate(self.stimuli_vars.items()) if v.get() != f'stimuli_var_{i+1}']
        # Handling the case that you generate the plan for a large num of stimuli and then change to a smaller number
        
        if len(self.changed_vars) > self.num_stimuli.get():

        # Start at the number of stimuli you now have               
            start_index = self.num_stimuli.get()  
            # and then set the rest of stimuli past that value back to default to avoid error                          
            for index, key in enumerate(self.stimuli_vars):
                if index >= start_index:
                    self.stimuli_vars[key].set(key)

        # from our list of variables that were changed from their default values, pair them together.
        # 1 is paired with 2. 3 with 4, etc
        try:
            self.pairs = [(self.changed_vars[i], self.changed_vars[i+1]) for i in range(0, len(self.changed_vars), 2)]
        except:
            messagebox.showinfo("Stimulus Not Changed","One or more of the default stimuli have not been changed, please change the default value and try again")
        # for each pair in pairs list, include each pair flipped
        self.pairs.extend([(pair[1], pair[0]) for pair in self.pairs])

        # if the frame is already open then destroy everything in it so we can write over it with a new one
        if hasattr(self, 'stimuli_frame'):                                                        
            self.trial_blocks.destroy()
            self.stimuli_frame.destroy()
            self.df_list = []

        # if the user has changed the defualt values of num_blocks and changed variables, then generate the 
        # expirament schedule

        if self.num_trial_blocks.get() != 0 and len(self.changed_vars) > 0:                                             # if the number of trial blocks is greater than 0 and we have changed more than one default stimulus,
            for i in range(self.num_trial_blocks.get()):                                                                # filling pair information in the tables with trial numbers and random interval times
                pairs_copy = [(var1.get(), var2.get()) for var1, var2 in self.pairs]                                    # copy the list of pairs from pairs 
                random.shuffle(pairs_copy)                                                                              # then shuffle the pairs so we get pseudo random generation 
                pairs_copy = [(str(i+1) if k % len(pairs_copy) == 0 else '', np.nan) + pair for k, pair in enumerate(pairs_copy)]
                # Create a DataFrame and add it to the list
                df = pd.DataFrame(pairs_copy, columns=['Trial Block', 'Trial Number', 'Stimulus 1', 'Stimulus 2'])      # create the dataframe skeleton, include listed headings 
                df['Stimulus 1 Licks'] = np.nan                                                                         # we don't have any licks yet so, fill with blank or 'nan' values
                df['Stimulus 2 Licks'] = np.nan

                self.df_list.append(df)                                                                                 # add df to the list of data frames
            self.df_stimuli = pd.concat(self.df_list, ignore_index=True)                                                # add the df list to the pandas df_stimuli table

            # fill the tables with the values of all random intervals that were previously generated
            # from their respective lists 

            for i in range(len(self.df_stimuli)):
                self.df_stimuli.loc[i, 'ITI'] = self.ITI_intervals_final[i]
                self.df_stimuli.loc[i, 'TTC'] = self.TTC_intervals_final[i]
                self.df_stimuli.loc[i, 'Sample Time'] = self.sample_intervals_final[i]
                self.df_stimuli.loc[i, 'Trial Number'] = int(i + 1) 

            # Create new column for the actual time elapsed in Time to contact state to be filled during program execution
            self.df_stimuli['TTC Actual'] = np.nan

            # creating the frame that will contain the data table
            self.stimuli_frame = tk.Frame(tab2)     
            # setting the place of the frame                       
            self.stimuli_frame.grid(row=0, column=0, sticky='nsew') 

            # setting the tab to expand when we expand the window 
            tab2.grid_rowconfigure(0, weight=1)                            
            tab2.grid_columnconfigure(0, weight=1)  

            # Creating the main data table and adding the dataframe that we just created

            self.trial_blocks = Table(self.stimuli_frame, dataframe=self.df_stimuli, showtoolbar=True, showstatusbar=True, weight=1)
            self.trial_blocks.autoResizeColumns()
            self.trial_blocks.show()

            # blocks have been generated
            self.blocks_generated = True          

    def update_plot(self):

        # clear the old plot
        self.axes.clear()  

        # this line is continued on the next line
        self.axes.bar([self.df_stimuli.loc[self.curr_trial_number-1, 'Stimulus 1'], \
        self.df_stimuli.loc[self.curr_trial_number - 1, 'Stimulus 2']], [self.side_one_licks, self.side_two_licks])  # draw the bar plot with correct labels for the current stimuli

        # update the plot

        self.canvas.draw()  

        # set the update plot funtion to call itself again, and set the id to the scheduling identifier so 
        # that we can cancel it later when we want to stop calling the function

        self.update_plot_id = self.root.after(50, self.update_plot)


        # this function is called when the main app window is closed, this is set on line 35
    def on_close(self):
        # stop calling the clock update function, we're done with it 

        self.root.after_cancel(self.update_clock_id)

        # if we have called the update licks function at all, 
        #then stop it from being called now.

        if self.update_licks_id is not None:  
            self.root.after_cancel(self.update_licks_id)

        # if we have a data window open, then close it

        if self.update_plot_id is not None:
            self.root.after_cancel(self.update_plot_id)
            self.data_window_instance.destroy()
        try:
            self.arduinoLaser.close()
            self.arduinoMotor.close()
        except: 
            pass
        self.root.destroy();
        self.root.quit()

    # Define the method for toggling the program state
    def start_toggle(self):
        # If the program is running, stop it
        if self.running:
            # state of the program is OFF
            self.state = "OFF"
            # set the state timer label
            self.state_time_label_header.configure(text=(self.state))
            # set the running variable to false to halt execution in the state functions
            self.running = False
            # Turn the program execution button back to the green start button
            self.startButton.configure(text="Start", bg="green")
            self.root.after_cancel(self.update_clock_id)
            # if we have called the update licks function at all, then stop it from being called now, we're done with it 
            if self.update_licks_id is not None:  
                self.root.after_cancel(self.update_licks_id)

            # if we have a data window open, then close it
            if self.update_plot_id is not None:
                self.root.after_cancel(self.update_plot_id)
                self.data_window_instance.destroy()
            # try to send the reset command to both Arduinos
            try:
                self.arduinoLaser.write(b'reset\n')
                self.arduinoMotor.write(b'reset\n')
                self.curr_trial_number = 1
            # if it fails, then the arduinos are not connected
            except:
                pass

        # If the program is not running, start it
        else:
            # Start the program if it is not already runnning and generate random numbers
            self.running = True
            # program main start time begins now
            self.start_time = time.time()
            # turn the main button to the red stop button
            self.startButton.configure(text="Stop", bg="red")
            # call the first ITI state with an iteration variable (i acts as a 
            # variable to iterate throgh the program schedule data table) starting at 0
            self.initial_time_interval(0)

    def clear_toggle(self):
        # Clear the scrolled text widget
        self.data_text.delete('1.0', tk.END)
        elapsed_time = 0 
        self.time_label.configure(text="{:.3f}s".format(elapsed_time))
        state_elapsed_time = 0
        self.state_time_label.configure(text="{:.3f}s".format(state_elapsed_time))

    # Define the method for updating the clock
    def update_clock(self):
        # If the program is running, update the elapsed time
        if self.running:
            elapsed_time = time.time() - self.start_time
            self.time_label.configure(text="{:.3f}s".format(elapsed_time))
            state_elapsed_time = time.time() - self.state_start_time
            self.state_time_label.configure(text="{:.3f}s".format(state_elapsed_time))
            self.update_clock_id = True
        # Call this method again after 100 ms
        self.update_clock_id = self.root.after(50, self.update_clock)
        

    # Define the method for reading data from the first Arduino
    def read_licks(self, i):
        # try to read licks if there is a arduino connected
        try:
            if(self.arduinoLaser.in_waiting > 0):
                data = self.arduinoLaser.read(self.arduinoLaser.in_waiting).decode('utf-8')
                # Append the data to the scrolled text widget
                if "Stimulus One Lick" in data:
                    # if we detect a lick on spout one, then add it to the lick data table
                    # and add whether the lick was a TTC lick or a sample lick

                    # format for this is self.dataFrame.loc[rowNumber, Column Title] = value
                    self.licks_df.loc[self.total_licks, 'Trial Number'] = self.curr_trial_number
                    self.licks_df.loc[self.total_licks, 'Stimulus Licked'] = 'Stimulus 1'
                    self.licks_df.loc[self.total_licks, 'Time Stamp'] = time.time() - self.start_time
                    self.licks_df.loc[self.total_licks, 'State'] = self.state
                    self.stamped_licks.redraw()

                    self.side_one_licks += 1
                    self.total_licks += 1


                if "Stimulus Two Lick" in data:
                    # if we detect a lick on spout one, then add it to the lick data table
                    # and add whether the lick was a TTC lick or a sample lick

                    # format for this is self.dataFrame.loc[rowNumber, Column Title] = value
                    self.licks_df.loc[self.total_licks, 'Trial Number'] = self.curr_trial_number
                    self.licks_df.loc[self.total_licks, 'Stimulus Licked'] = 'Stimulus 2'
                    self.licks_df.loc[self.total_licks, 'Time Stamp'] = time.time() - self.start_time
                    self.licks_df.loc[self.total_licks, 'State'] = self.state
                    self.stamped_licks.redraw()

                    self.side_two_licks += 1
                    self.total_licks += 1  



            if (self.side_one_licks >= 3 or self.side_two_licks >= 3) and self.state == 'TTC':
                self.df_stimuli.loc[self.curr_trial_number - 1,'TTC Actual'] = time.time() - self.state_start_time
                self.trial_blocks.update()
                self.root.after_cancel(self.after_sample_id)
                self.side_one_licks = 0
                self.side_two_licks = 0
                self.sample_time(i)

            # Call this method again after 100 ms
            self.update_licks_id = self.root.after(100, lambda: self.read_licks(i))
        # if the arduino is not connected, tell the user to connect one
        except AttributeError:
            messagebox.showinfo("Arduino Not Connected","One or more Arduino boards are not connected, please ensure both arduinos are connected and try again")

    # Define the method for appending data to the scrolled text widget
    def append_data(self, data):
        self.data_text.insert(tk.END, data)
        # Scroll the scrolled text widget to the end of the data
        self.data_text.see(tk.END)

    def save_data(self):
        try:
            file_name = filedialog.asksaveasfilename(defaultextension='.xlsx',
                                                 filetypes=[('Excel Files', '*.xlsx')],
                                                 initialfile='lineup',
                                                 title='Save Excel file')

            self.df_stimuli.to_excel(file_name, index=False)

            licks_file_name = filedialog.asksaveasfilename(defaultextension='.xlsx',
                                                 filetypes=[('Excel Files', '*.xlsx')],
                                                 initialfile='lineup',
                                                 title='Save Excel file')

            self.licks_df.to_excel(licks_file_name, index=False)
        except:
            messagebox.showinfo("Blocks Not Generated","Experiment blocks haven't been generated yet, please generate trial blocks and try again")

# Create an App object
app = App()
# Start the Tkinter event loop
app.root.mainloop()

# Close the serial connections to the Arduinos
app.arduinoLaser.close()
app.arduinoMotor.close()
