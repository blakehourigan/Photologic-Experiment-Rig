import serial
import time
import tkinter as tk
from tkinter import scrolledtext
import random
import pandas as pd
from pandastable import Table, TableModel
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import itertools
from tkinter import ttk
from serial.serialutil import SerialException
import numpy as np


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
        self.root.iconbitmap('rat.ico')

        # Initialize the interval variables and their corresponding IntVars
        self.interval_vars = {
            'ITI_var': tk.IntVar(value=30000),
            'TTC_var': tk.IntVar(value=15000),
            'sample_time_var': tk.IntVar(value=15000),
            'ITI_random_entry': tk.IntVar(value=5000),
            'TTC_random_entry': tk.IntVar(value=5000),
            'sample_time_entry': tk.IntVar(value=5000),
        }

        self.ITI_intervals_final = []
        self.TTC_intervals_final = []
        self.sample_intervals_final = []

        # Initialize dictionary fill of stimulus variables and fill each entry to hold value equal to the key value
        self.stimuli_vars = {f'stimuli_var_{i+1}': tk.StringVar() for i in range(8)}
        for key in self.stimuli_vars:
            self.stimuli_vars[key].set(key)

        # initialize variable
        self.pairs = []
        self.df_list = []

        self.num_trials = tk.IntVar()
        self.num_trials.set(0)
        self.num_trial_blocks = tk.IntVar()
        self.num_trial_blocks.set(0)
        self.num_stimuli = tk.IntVar()
        self.num_stimuli.set(0)

        # initializing variables for iteration through the trials in the program
        self.curr_trial_number = 1
        self.current_trial_block = 1

        self.ITI_random_intervals = []
        self.TTC_random_intervals = []
        self.sample_random_intervals = []


        # Initialize the running flag to False
        self.running = False

        # Initialize the start time to 0
        self.start_time = 0

        self.side_one_licks = 0
        self.side_two_licks = 0


        self.data_window_open = False
        self.data_window_job = None

        # Initialize these instance variables
        self.update_clock_id = None
        self.read_licks_id = None

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
        self.clearButton = tk.Button(text="Clear", command=self.toggle, bg="grey", font=("Helvetica", 24))
        self.clearButton.grid(row=1, column=2, pady=10, padx=10, sticky='nsew', columnspan=2)

        # button to open the stimuli window
        self.experiment_control_button = tk.Button(text="Experiment Control", command=self.experiment_control, bg="grey", font=("Helvetica", 24))
        self.experiment_control_button.grid(row=10, column=0, pady=10, padx=10, sticky='nsew',columnspan=2)

        # button to open the data window
        self.data_window_button = tk.Button(text="View Data", command=self.data_window, bg="grey", font=("Helvetica", 24))
        self.data_window_button.grid(row=10, column=2, pady=10, padx=10, sticky='nsew')

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
        except SerialException:
            self.serial_exception_instance = tk.Toplevel(self.root)
            self.serial_exception_instance.geometry("800x600")
            self.serial_exception_instance.title("Error")
            self.serial_exception_instance.iconbitmap('rat.ico')

            serial_text_box = tk.Text(self.serial_exception_instance, width=52, height=30)  # Adjust size as needed
            serial_text_box.grid(row=0, column=0)
        # Insert text
            serial_text_box.insert('1.0', "1 or more Arduino boards are not connected, connect arduino boards and relaunch before running program")

        # Wait for the serial connections to settle
        #time.sleep(2)

        # Start the clock 
        self.update_clock()

    # State methods

    def initial_time_interval(self, i):
        if self.running and (self.curr_trial_number) <= (self.num_stimuli.get() * self.num_trial_blocks.get()):

            self.state = "ITI"
            self.side_one_licks = 0
            self.side_two_licks = 0
            self.state_time_label_header.configure(text=(self.state + " Time:"))
            self.state_start_time = time.time()  # Update the state start time
            self.append_data('1:' + self.df_stimuli.loc[i, 'Stimulus 1'] + " vs. 2:" + self.df_stimuli.loc[i, 'Stimulus 2'] + "\n")
            self.append_data('Initial Interval trial #: ' + str(self.curr_trial_number) + ": " + str(self.df_stimuli.loc[i,'ITI'] / 1000) + "s\n")
            # After the 'ITI' time, call time_to_contact
            self.root.after(int(self.df_stimuli.loc[i,'ITI']), lambda: self.time_to_contact(i))
        else: 
            self.state = "OFF"
            self.state_time_label_header.configure(text=(self.state))
            self.running = False
            self.startButton.configure(text="Start", bg="green")



    def time_to_contact(self, i):
        if self.running:
            self.state = "TTC"
            self.read_licks(i)
            self.state_time_label_header.configure(text=(self.state + " Time:"))
            self.state_start_time = 0
            self.state_start_time = time.time()  # Update the state start time
            self.arduinoMotor.write(b'DOWN\n')
            self.append_data("Time to Contact: " + str(self.df_stimuli.loc[i,'TTC'] / 1000) + "s\n")
            self.after_sample_id = self.root.after(int(self.df_stimuli.loc[i, 'TTC']), lambda: self.save_licks(i))

    def sample_time(self, i):
        if self.running:
            self.state = "Sample"                                                   # we are now in the sample time state
            self.state_time_label_header.configure(text=(self.state + " Time:"))    # change the state time label accordingly
            self.state_start_time = 0                                               # state start time starts at 0
            self.state_start_time = time.time()                                     # Update the state start time to reflect the zero we just set
            self.append_data('Sample Time Interval: ' + str(self.df_stimuli.loc[i,'Sample Time'] / 1000) + "s\n\n\n")   # Appending the sample time interval to the main text box
            self.root.after(int(self.df_stimuli.loc[i, 'Sample Time']), lambda: self.save_licks(i))                     # After the sample time as stored in the df_stimuli table, go to the save licks function

            
    def save_licks(self, i):
            self.arduinoMotor.write(b'UP\n')                                        # move the door up
            self.curr_trial_number += 1                                             # increment to the next trial
            self.df_stimuli.loc[i, 'Stimulus 1 Licks'] = self.side_one_licks        # store licks in their respective columns in the data table for the trial
            self.df_stimuli.loc[i, 'Stimulus 2 Licks'] = self.side_two_licks
            self.initial_time_interval(i+1)                                         # begin ITI for next trial



    def experiment_control(self):
        try:
            # Try to lift the window to the top (it will fail if the window is closed)
            self.experiment_control_instance.lift()
        except (AttributeError, tk.TclError):
            self.experiment_control_instance = tk.Toplevel(self.root)
            self.experiment_control_instance.geometry("1600x800")
            self.experiment_control_instance.title("Experiment Control")
            self.experiment_control_instance.iconbitmap('rat.ico')

            # Create the notebook (tab manager)
            notebook = ttk.Notebook(self.experiment_control_instance)
            tab1 = ttk.Frame(notebook)
            notebook.add(tab1, text='Experiment Stimuli')
            notebook.grid(sticky='nsew')                                                # These 3 lines set the contents of the tabs to expand when we expand the window  
            self.experiment_control_instance.grid_rowconfigure(0, weight=1)
            self.experiment_control_instance.grid_columnconfigure(0, weight=1)

            if(self.num_stimuli.get() == 0):
                # Create a text box
                text_box = tk.Text(tab1, width=50, height=30)  # Adjust size as needed
                text_box.grid(row=0, column=0)
                # Insert text
                text_box.insert('1.0', "No stimuli have been added, please close the window, set number of stimuli and try again")
            else: 
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

            # Generate stimuli schedule button 
            self.generate_stimulus = tk.Button(tab1,text="Generate Stimulus", command=lambda: self.create_trial_blocks(tab2, notebook, 0, 0), bg="green", font=("Helvetica", 24))
            self.generate_stimulus.grid(row=8, column=0, pady=10, padx=10, sticky='nsew', columnspan=2)
            self.create_trial_blocks(tab2, notebook, 0, 0)


    def data_window(self):
        try:
            # Try to lift the window to the top (it will fail if the window is closed)
            self.data_window_instance.lift()
        except (AttributeError, tk.TclError):
            # If the window is closed, create a new one
            self.data_window_instance = tk.Toplevel(self.root)
            self.data_window_instance.geometry("800x600")
            self.data_window_instance.title("Data")
            self.data_window_instance.iconbitmap('rat.ico')

            # Override the default close behavior
            self.data_window_instance.protocol("WM_DELETE_WINDOW", self.close_data_window)

            # Create a figure and axes for the plot
            self.fig, self.axes = plt.subplots()
            self.canvas = FigureCanvasTkAgg(self.fig, master=self.data_window_instance)
            self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

            # Create a toolbar for the plot and pack it into the window
            toolbar = NavigationToolbar2Tk(self.canvas, self.data_window_instance)
            toolbar.update()
            self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        
        self.data_window_open = True
        self.update_plot()
        if self.data_window_open:
            self.data_window_job = self.root.after(100, self.data_window)
        else:
            self.data_window_open = False

    # this is the function that will generate the full roster of stimuli for the duration of the program
    def create_trial_blocks(self, tab2, notebook, row_offset, col_offset):

        self.num_trials.set((self.num_stimuli.get() * self.num_trial_blocks.get()))         # the total number of trials equals the number of stimuli times the number of trial blocks that we want

        for entry in range(self.num_trials.get()):
            self.ITI_random_intervals.append(random.randint(-(self.interval_vars['ITI_random_entry'].get()), (self.interval_vars['ITI_random_entry'].get())))
            self.TTC_random_intervals.append(random.randint(-(self.interval_vars['TTC_random_entry'].get()), (self.interval_vars['TTC_random_entry'].get())))
            self.sample_random_intervals.append(random.randint(-(self.interval_vars['sample_time_entry'].get()), (self.interval_vars['sample_time_entry'].get())))

        self.ITI_intervals_final = []
        self.TTC_intervals_final = []
        self.sample_intervals_final = []

        for i in range(self.num_trials.get()):
            self.ITI_intervals_final.append(self.interval_vars['ITI_var'].get() + self.ITI_random_intervals[i])
            self.TTC_intervals_final.append(self.interval_vars['TTC_var'].get() + self.TTC_random_intervals[i])
            self.sample_intervals_final.append(self.interval_vars['sample_time_var'].get() + self.sample_random_intervals[i])


        self.changed_vars = [v for i, (k, v) in enumerate(self.stimuli_vars.items()) if v.get() != f'stimuli_var_{i+1}']
        if len(self.changed_vars) > self.num_stimuli.get():                 # Handling the case that you generate the plan for a large num of stimuli and then chanage to a smaller number
            start_index = self.num_stimuli.get()                            # Start at the number of stimuli you now have
            for index, key in enumerate(self.stimuli_vars):                 # and then set the rest of stimuli past that value back to default to avoid error
                if index >= start_index:
                    self.stimuli_vars[key].set(key)

        self.pairs = [(self.changed_vars[i], self.changed_vars[i+1]) for i in range(0, len(self.changed_vars), 2)]

        # Add reversed pairs
        self.pairs.extend([(pair[1], pair[0]) for pair in self.pairs])


        if hasattr(self, 'stimuli_frame'):                                                         # if the frame is already open then destroy everything in it so we can write over it
            self.trial_blocks.destroy()
            self.stimuli_frame.destroy()
            self.df_list = []

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

            for i in range(len(self.df_stimuli)):
                self.df_stimuli.loc[i, 'ITI'] = self.ITI_intervals_final[i]
                self.df_stimuli.loc[i, 'TTC'] = self.TTC_intervals_final[i]
                self.df_stimuli.loc[i, 'Sample Time'] = self.sample_intervals_final[i]
                self.df_stimuli.loc[i, 'Trial Number'] = int(i + 1) 

            # Now create a new stimuli_frame
            self.stimuli_frame = tk.Frame(tab2)                            # creating the frame that will contain the data table
            self.stimuli_frame.grid(row=0, column=0, sticky='nsew')        # setting the place of the frame

            tab2.grid_rowconfigure(0, weight=1)                            # setting the tab (frame) to expand when we expand the window 
            tab2.grid_columnconfigure(0, weight=1)  

            self.trial_blocks = Table(self.stimuli_frame, dataframe=self.df_stimuli, showtoolbar=True, showstatusbar=True, weight=1)
            self.trial_blocks.autoResizeColumns()
            self.trial_blocks.show()

    def update_plot(self):
        self.axes.clear()  # clear the old plot
        # Assuming that self.side_one_licks and self.side_two_licks are the numbers of licks
        self.axes.bar([self.df_stimuli.loc[self.curr_trial_number-1, 'Stimulus 1'], \
        self.df_stimuli.loc[self.curr_trial_number-1, 'Stimulus 2']], [self.side_one_licks, self.side_two_licks])  # draw the bar plot with correct labels for the current stimuli

        self.canvas.draw()  # update the canvas

    def close_data_window(self):
        self.data_window_open = False
        if self.data_window_job is not None:
            self.root.after_cancel(self.data_window_job)
            self.data_window_job = None
            self.data_window_instance.destroy()
        else:
            self.stimuli_lineup_instance.destroy()

    def on_close(self):
        self.root.after_cancel(self.update_clock_id)
        self.root.after_cancel(self.update_licks_id)
        self.data_window_instance.destroy()

    # Define the method for toggling the program state
    def start_toggle(self):
        # If the program is running, stop it
        if self.running:
            self.state = "OFF"
            self.state_time_label_header.configure(text=(self.state))
            self.running = False
            self.startButton.configure(text="Start", bg="green")
            # Send the reset command to both Arduinos
            try:
                self.arduinoLaser.write(b'reset\n')
                self.arduinoMotor.write(b'reset\n')
                self.curr_trial_number = 1
            except:
                pass

        # If the program is not running, start it
        else:
            # Start the program if it is not already runnning and generate random numbers
            self.running = True
            self.start_time = time.time()
            self.startButton.configure(text="Stop", bg="red")
            self.initial_time_interval(0)

    # Define the method for sending the target position
    def send_target_position(self, target_position):
        # Send the target position to the second Arduino
        self.arduinoMotor.write(target_position.encode())

    def toggle(self):
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
        # If there is data available from the first Arduino, read it
        try:
            if self.arduinoLaser.in_waiting > 0:
                data = self.arduinoLaser.read(self.arduinoLaser.in_waiting).decode('utf-8')
                # Append the data to the scrolled text widget
                if "Left Lick" in data:
                    self.side_one_licks += 1
                if "Right Lick" in data:
                    self.side_two_licks += 1 
            if (self.side_one_licks >= 3 or self.side_two_licks >= 3) and self.state == 'TTC':
                self.root.after_cancel(self.after_sample_id)
                self.side_one_licks = 0
                self.side_two_licks = 0
                self.sample_time(i)
            # Call this method again after 100 ms
            self.update_licks_id = self.root.after(100, lambda: self.read_licks(i))
            
        except AttributeError:
            pass

    # Define the method for appending data to the scrolled text widget
    def append_data(self, data):
        self.data_text.insert(tk.END, data)
        # Scroll the scrolled text widget to the end of the data
        self.data_text.see(tk.END)



# Create an App object
app = App()
# Start the Tkinter event loop
app.root.mainloop()

# Close the serial connections to the Arduinos
app.arduinoLaser.close()
app.arduinoMotor.close()
