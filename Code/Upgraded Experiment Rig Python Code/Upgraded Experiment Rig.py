# Importing libraries that are used for this program
import sys, serial, serial.tools.list_ports, time, random, itertools, platform, numpy as np, tkinter as tk, pandas as pd, matplotlib.pyplot as plt
from tkinter import ttk, scrolledtext, filedialog, messagebox
from pandastable import Table, TableModel
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from serial.serialutil import SerialException

# defining the baud rate for communication with the arduinos

       

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
        # value = x sets the defalt value that shows when you first boot the program

            
        """        
            self.interval_vars = {
            'ITI_var': tk.IntVar(value=30000),
            'TTC_var': tk.IntVar(value=15000),
            'sample_time_var': tk.IntVar(value=15000),
            'ITI_random_entry': tk.IntVar(value=5000),
            'TTC_random_entry': tk.IntVar(value=5000),
            'sample_time_entry': tk.IntVar(value=5000),
        }"""

        """        
        # initializing the lists that will hold the final calculated random interval values 

        self.ITI_intervals_final = []
        self.TTC_intervals_final = []
        self.sample_intervals_final = []

        # These will be used to store the random +/- values to be added to the constant values

        self.ITI_random_intervals = []
        self.TTC_random_intervals = []
        self.sample_random_intervals = []"""

        # Initialize dictionary full of stimulus variables and fill each entry to hold default value equal to the key value

        """        
        self.stimuli_vars = {f'stimuli_var_{i+1}': tk.StringVar() for i in range(8)}
        for key in self.stimuli_vars:
            self.stimuli_vars[key].set(key)"""

        """        
        # initialize lists to hold original pairs and the list that will hold our dataframes.

        self.pairs = []
        self.df_list = []

        # Initialize variables that will keep track of the total number of trials we will have, the total number of trial blocks that the user wants to run
        # and the total number of stimuli. These are of type IntVar because they are used in the GUI. 

        self.num_trials = tk.IntVar(value=0)
        self.num_trial_blocks = tk.IntVar(value=0)
        self.num_stimuli = tk.IntVar(value=0)"""

        """        
        # initializing variable for iteration through the trials in the program

        self.curr_trial_number = 1

        # Initialize boolean flags to false
        self.running = False

        self.blocks_generated = False

        self.stamped_exists = False

        self.data_window_open = False"""

        # BAUD_RATE = 9600  
         
        """
        # Initialize the time, licks to 0
        
        self.start_time = 0
        self.side_one_licks = 0
        self.side_two_licks = 0
        self.total_licks = 0

        # Initialize these function instance ID variables
        # These hold the values of the function calls when we want to call them repeatedly
        # This is what we call to cancel the function call to avoid errors when closing the program
        self.update_clock_id = None
        self.update_licks_id = None
        self.update_plot_id = None"""

        # Set program default to the off state
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

        # Open a serial connection to the first Arduino
        self.arduinoLaser, self.arduinoMotor = self.connect_to_arduino(BAUD_RATE)

        self.arduinoLaser.flush() 
        self.arduinoMotor.flush()  

        # Start the program clock function 
        self.update_clock()

    # this function is defined to find which arduino contains the code for which function automatically 
    def identify_arduino(self, port, BAUD_RATE):
        try:
            # connect to arduino on specified port
            arduino = serial.Serial(port, BAUD_RATE, timeout=1)
            # Wait for Arduino to initialize
            time.sleep(2)  
            # ask nicely who the arduino is and wait for response, store it in identifier 
            arduino.write(b'WHO_ARE_YOU\n')
            identifier = arduino.readline().decode('utf-8').strip()
            arduino.close()
            #return identifier back to connect function 
            return identifier
        
        except Exception:
            print(f"An error occurred: {Exception}")
            return None
        
    # function that establishes the connection to the arduinos 
    def connect_to_arduino(self, BAUD_RATE):
        # define a list of all ports on the device 
        ports = [port.device for port in serial.tools.list_ports.comports()]

        arduinoLaser = None
        arduinoMotor = None

        # for each port on the device, check if it has an Arduino attached to it and identify that arduino if it does
        for port in ports:
            identifier = self.identify_arduino(port, BAUD_RATE)
            if identifier == "LASER":
                arduinoLaser = serial.Serial(port, BAUD_RATE)
            elif identifier == "MOTOR":
                arduinoMotor = serial.Serial(port, BAUD_RATE)
        # if we didn't find either arduino then display the error message to the user
        if arduinoLaser is None or arduinoMotor is None:
            messagebox.showinfo("Serial Error", "1 or more Arduino boards are not connected, connect arduino boards and relaunch before running program")
            if arduinoLaser is not None:
                arduinoLaser.close()
            if arduinoMotor is not None: 
                arduinoMotor.close()
            return arduinoLaser, arduinoMotor
            



    # Program state methods
    # defining the ITI state method, arguments given are self which says that the function should be called on the instance of the class, which is our app 
    # the second argument is i, which is the iteration variable that we use to keep track of what trial we are on. 
    # i is defined on line 650 where we first call the function.
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
            # Get trial number and stimuli in the trial and add them to the main information screen
            # self.df_stimuli.loc is what we use to get values that are held in the main data table. Accessed using .loc[row_num, 'Column Name']
            string = '\nTRIAL # (' + str(self.curr_trial_number) + ') Stimulus 1:' + self.df_stimuli.loc[i, 'Stimulus 1'] + " vs. Stimulus 2:" + self.df_stimuli.loc[i, 'Stimulus 2'] + "\n"
            # this command is what adds things to the main information screen
            self.append_data(string)
            # for every letter in the string we just created, create a dash to separate the title of the trial from the contents
            for letter in range(len(string)):
                self.append_data("-")
            # add the initial interval to the program information box
            self.append_data('\nInitial Interval Time: ' +  str(self.df_stimuli.loc[i,'ITI'] / 1000) + "s\n")
            # self.root.after tells the program to wait a certain amount of time, and then after that time to do the function that follows it. 
            # So here, we wait the amount of time specified for the ITI in the ith row of the table. Then we call save_licks with the i that we've been using.
            # using lambda takes a snapshot of the program as it is and ensures that we use the correct value of i and only call the function after the time 
            # that was specified in the self.root.after call
            self.root.after(int(self.df_stimuli.loc[i,'ITI']), lambda: self.time_to_contact(i))
        else: 
            # if we have gone through every trial then end the program.
            self.stop_program()

    # defining the TTC state method, argument are self and i. i is passed from TTC to keep track of what stimuli we are on.
    def time_to_contact(self, i):
        if self.running:
            # Change program state to TTC
            self.state = "TTC"
            # start reading licks, we pass the same i into this function that we used in the previous function to
            # keep track of where we are storing the licks in the data table
            self.read_licks(i)
            # update state timer header
            self.state_time_label_header.configure(text=(self.state + " Time:"))
            # Update the state start time to current time
            self.state_start_time = time.time()
            # move the door down  
            self.arduinoMotor.write(b'DOWN\n')
            # flush the arduinos serial line after sending command to ensure command is sent immediately and is clear of data for next command
            self.arduinoMotor.flush()  
            # Create a list of the stimuli dictionary values, will give list of stimuli. 
            stim_var_list = list(self.stimuli_vars.values())
            # for every variable in the list, we need to check if it matches the current simuli that we are producing to the rat
            for index, string_var in enumerate(stim_var_list):
                if string_var.get() == self.df_stimuli.loc[i,'Stimulus 1']:
                    # once we find the stimulus in the list that we are giving on port one, save that position in the list so that we 
                    # can send this position to the motor arduino to tell it which solenoid valve needs to open
                    self.stim1_position = str(index + 1)
            # repeat process for the second stimulus
            for index, string_var in enumerate(stim_var_list):
                if string_var.get() == self.df_stimuli.loc[i,'Stimulus 2']:
                    self.stim2_position = str(index + 1)

            # concatinate the positions with the commands that are used to tell the arduino which side we are opening the valve for. 
            # SIDE_ONE tells the arduino we need to open a valve for side one, it will then read the next line to find which valve to open.
            # valves are numbered 1-8 so "SIDE_ONE\n1\n" tells the arduino to open valve one for side one. 
            self.command = "SIDE_ONE\n" + str(self.stim1_position) + "\nSIDE_TWO\n" + str(self.stim2_position) + "\n"
            # send the command
            self.arduinoMotor.write(self.command.encode('utf-8'))
            # flush serial to ensure command is sent instantly, and serial is clear for next command
            self.arduinoMotor.flush()
            # write the time to contact to the program information box
            self.append_data("Time to Contact: " + str(self.df_stimuli.loc[i,'TTC'] / 1000) + "s\n")
            # self.root.after tells the program to wait a certain amount of time, and then after that time to do the function that follows it. 
            # So here, we wait the amount of time specified for the TTC in the ith row of the table. Then we call save_licks with the i that we've been using.
            # using lambda takes a snapshot of the program as it is and ensures that we use the correct value of i and only call the function after the time 
            # that was specified in the self.root.after call
            # then we store the id of the self.root.after in the corresponding id variable so that we can cancel the call when we need to.
            self.after_sample_id = self.root.after(int(self.df_stimuli.loc[i, 'TTC']), lambda: self.save_licks(i))

    # define sample time method, i is again passed to keep track of trial and stimuli
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

            # After the sample time specified in the ith row of the 'Sample Time' table, we will jump to the save licks function
            self.root.after(int(self.df_stimuli.loc[i, 'Sample Time']), lambda: self.save_licks(i))                     

    # define method that saves the licks to the data table and increments our iteration variable.       
    def save_licks(self, i):
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
            # call the self.root.after_cancel function and pass in the ID that was assigned to the function call
            self.root.after_cancel(self.update_licks_id)

            # try to redraw the program stimuli schdule window to update the information with number of licks, if it is open
            try:
                self.trial_blocks.redraw()
            # if the window is not open, it will throw an error, but we tell the program that its fine just keep going
            except:
                pass
            # Jump to ITI state to begin ITI for next trial by incrementing the i variable
            self.initial_time_interval(i+1)                                        

    # this method is called when a user clicks on the experiment control button on the main screen
    def experiment_control(self):
        try:
            # Try to lift the window to the top so the user can see it (it will fail if the window is closed)
            self.experiment_control_instance.lift()
        # catches the exception in the case that the window does not exist
        except (AttributeError, tk.TclError):
            # if the number of simuli is currently set to zero, tell the user that they need to add stmiuli before we can more forward
            if(self.num_stimuli.get() == 0):
               messagebox.showinfo("Stimuli Not changed from 0", "No stimuli have been added, please close the window, set number of stimuli and try again")
            # otherwise create the window frame and add content to it. 
            else: 
                # the instance of the window is created by calling the instance generator function and passing in the name and the size of the window
                self.experiment_control_instance = self.window_instance_generator("Experiment Control","1000x800")
                
                # Create the notebook (method of creating tabs at the top of the window)
                notebook = ttk.Notebook(self.experiment_control_instance)
                # create a fresh frame to use for the first tabl 
                tab1 = ttk.Frame(notebook)
                # add the frame to the tab manager with the title desired
                notebook.add(tab1, text='Experiment Stimuli')

                # set the tab manager to expand its contents as the window is expanded by the user
                notebook.grid(sticky='nsew')                                                
                # set the instance to begin at (0,0) in the window, and setting weight to 1 sets all contents of the window to expand as the user expands the window
                self.experiment_control_instance.grid_rowconfigure(0, weight=1)
                self.experiment_control_instance.grid_columnconfigure(0, weight=1)

                # for ever stimuli that we will have in the program, create a text box that allows the user to enter the name of the stimuli
                for i in range(self.num_stimuli.get()):

                    # place the box in the first column if less that 4 stimuli, set to column 2 if 5 or above
                    column = 0 if i < 4 else 1
                    # spaces each row out 2 spaces to make room for both a label and a text entry box
                    # 0 % 4 = 0, 1 % 4 = 1, 2 % 4 = 2, etc
                    row = 2 * (i % 4)

                    # Labels/Entry boxes for Stimuli, adds to tab 1 with a label of the number of stimulus that it is
                    label = tk.Label(tab1, text=f"Stimulus {i+1}", bg="light blue", font=("Helvetica", 24))
                    # .grid is how items are placed using tkinter. Place in the row and column that we calculated earlier
                    label.grid(row=row, column=column, pady=10, padx=10, sticky='nsew')
                    # sets up an entry box that will assign its held value to its stimulus var number in the stimuli_vars dictionary
                    entry = tk.Entry(tab1, textvariable=self.stimuli_vars[f'stimuli_var_{i+1}'], font=("Helvetica", 24))
                    # placing the entry box 1 below the label box
                    entry.grid(row=row+1, column=column, pady=10, padx=10, sticky='nsew')

                # creating the second tab with a new frame
                tab2 = ttk.Frame(notebook)
                notebook.add(tab2, text='Program Stimuli Schedule')

                # Creating generate stimuli schedule button that calls the method to generate the program schedule when pressed 
                self.generate_stimulus = tk.Button(tab1,text="Generate Stimulus", command=lambda: self.create_trial_blocks(tab2, notebook, 0, 0), bg="green", font=("Helvetica", 24))
                # place the button after the last row
                self.generate_stimulus.grid(row=8, column=0, pady=10, padx=10, sticky='nsew', columnspan=2)
                # if blocks have been generated, then opening the experiment control window should show the df_stimuli dataframe in a table in the second tab 
                if(self.blocks_generated):
                    # creating the frame that will contain the data table
                    self.stimuli_frame = tk.Frame(tab2)     
                    # setting the place of the frame                       
                    self.stimuli_frame.grid(row=0, column=0, sticky='nsew') 

                    # setting the tab to expand when we expand the window 
                    tab2.grid_rowconfigure(0, weight=1)                            
                    tab2.grid_columnconfigure(0, weight=1)  

                    # creating the pandasTable table object and placing it in the stimuli frame, which is in tab 2
                    self.trial_blocks = Table(self.stimuli_frame, dataframe=self.df_stimuli, showtoolbar=True, showstatusbar=True, weight=1)
                    self.trial_blocks.autoResizeColumns()
                    self.trial_blocks.show()

    # this function is called when the lick data window is opened
    def lick_window(self):
        try:
            # Try to lift the window to the top so we can see it (it will fail if the window is closed)
            self.lick_window_instance.lift()
        except (AttributeError, tk.TclError):
            # if blocks have been generated, then generate the blank lick table
            if self.blocks_generated:
                # generate the instance of the window and pass the title of the window and size of the window. 
                self.lick_window_instance = self.window_instance_generator("Licks Data Table", "400x800")
                # create the frame that the table will be held in
                self.licks_frame = tk.Frame(self.lick_window_instance)
                self.licks_frame.grid(row=0, column=0, sticky='nsew')
                # create the table, using the data fro the licks_df
                self.stamped_licks = Table(self.licks_frame, dataframe=self.licks_df, showtoolbar=False, showstatusbar=False, weight=1)
                self.stamped_licks.autoResizeColumns()
                self.stamped_licks.show()
                # the licks data table now exists so set the bool to true so that we can tell the lick function to update the window when new licks are added
                self.stamped_exists = True

            else:
                # if blocks haven't been created yet, then there isn't a lick dataframe generated yet so tell user to generate blocks first
                messagebox.showinfo("Blocks Not Generated","Experiment blocks haven't been generated yet, please generate trial blocks and try again")

    # this function is designed to create new windows when we need them
    def window_instance_generator(self, name, size):
        # this line creates a new window that is shown on top of all others for the main application. 
        self.window_instance = tk.Toplevel(self.root)
        # set the size of the application to whatever size is passed as an argument
        self.window_instance.geometry(size)
        # set the title of the window to whatever argument is passed in the name position
        self.window_instance.title(name)
        # set the icon in the top left of the window to the file found at this path
        self.window_instance.iconbitmap('C:\\Users\\Samuelsen Data 4\\Documents\\Upgraded Experiment Rig\\Code\\Upgraded Experiment Rig Python Code\\rat.ico')
        # Set the contents of the window to expand as the user expands it
        self.window_instance.grid_rowconfigure(0, weight=1)
        self.window_instance.grid_columnconfigure(0, weight=1)

        # return the window to the variable that the user is assigning it to.
        return self.window_instance

    # Method to halt the program and set it to the off state, changing the button back to start.
    def stop_program(self):
        self.state = "OFF"
        self.state_time_label_header.configure(text=(self.state))
        self.running = False
        self.startButton.configure(text="Start", bg="green")

    # method that is called when the 'View data' button is pressed in the main window
    def data_window(self):
        try:
            # Try to lift the window on top of all windows (it will fail if the window is closed)
            self.data_window_instance.lift()
        except (AttributeError, tk.TclError):
            # cancel any previous calls to update the plot
            if self.update_plot_id is not None:
                self.root.after_cancel(self.update_plot_id)
            # if the program schedule has been generated, then create the window
            if self.blocks_generated:
                self.data_window_instance = self.window_instance_generator("Data", "800x600")

                # Create a figure and axes for the plot
                self.fig, self.axes = plt.subplots()
                # create a canvas that will hold the figure. The canvas is set to be held in the window instance
                self.canvas = FigureCanvasTkAgg(self.fig, master=self.data_window_instance)
                # Set the canvas to start at the top of the window instance and fill the window, expanding the content as the user expands the window 
                self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

                # Create a toolbar for the plot and pack it into the window
                toolbar = NavigationToolbar2Tk(self.canvas, self.data_window_instance)
                toolbar.update()

                # update the plot with data in this function call 
                self.update_plot()
            else:
                # if blocks haven't been generated, let the user know that they need to do that before they can use this page.
                messagebox.showinfo("Blocks Not Generated","Experiment blocks haven't been generated yet, please generate trial blocks and try again")

    # this is the function that will generate the full roster of stimuli for the duration of the program
    def create_trial_blocks(self, tab2, notebook, row_offset, col_offset):

        # the total number of trials equals the number of stimuli times the number of trial blocks that we want
        self.num_trials.set((self.num_stimuli.get() * self.num_trial_blocks.get()))         

        # clearing the lists here just in case we have already generated blocks, in this case we want to ensure we use new numbers, so we must clear out the existing ones
        self.ITI_intervals_final.clear()
        self.TTC_intervals_final.clear()
        self.sample_intervals_final.clear()
        self.ITI_random_intervals.clear()
        self.TTC_random_intervals.clear()
        self.sample_random_intervals.clear()

        # for every trial, generate a random interval, and add it to the constant value
        for entry in range(self.num_trials.get()):

            # Generating random intervals from +/- user entry
            # generating works by calling random.randint, the arguments passed are random.randint(low bound, high bound) 
            # so we use (-bound, bound) for our case
            self.ITI_random_intervals.append(random.randint(-(self.interval_vars['ITI_random_entry'].get()), (self.interval_vars['ITI_random_entry'].get())))
            self.TTC_random_intervals.append(random.randint(-(self.interval_vars['TTC_random_entry'].get()), (self.interval_vars['TTC_random_entry'].get())))
            self.sample_random_intervals.append(random.randint(-(self.interval_vars['sample_time_entry'].get()), (self.interval_vars['sample_time_entry'].get())))

            # Calculating final total intervals for each trial, adding random number to state constant
            self.ITI_intervals_final.append(self.interval_vars['ITI_var'].get() + self.ITI_random_intervals[entry])
            self.TTC_intervals_final.append(self.interval_vars['TTC_var'].get() + self.TTC_random_intervals[entry])
            self.sample_intervals_final.append(self.interval_vars['sample_time_var'].get() + self.sample_random_intervals[entry])

        # this checks every variable in the simuli_vars dictionary against the default value, if it is changed, then it is added to the list 
                            #var for iterator, (key, value) in enumerate(self.stimuli_vars.items() if variable not default then add to list)
        self.changed_vars = [v for i, (k, v) in enumerate(self.stimuli_vars.items()) if v.get() != f'stimuli_var_{i+1}']
                                                                                                   # f string used to incorporate var in string 
        # Handling the case that you generate the plan for a large num of stimuli and then change to a smaller number    
        if len(self.changed_vars) > self.num_stimuli.get():

        # Start at the number of stimuli you now have               
            start_index = self.num_stimuli.get()  
            # and then set the rest of stimuli past that value back to default to avoid error                          
            # create an index for each loop, loop through each key in stimuli_vars
            for index, key in enumerate(self.stimuli_vars):
                if index >= start_index:
                    # if the loop we are on is greater than the start index calculated, then set the value to the value held by the key.
                    self.stimuli_vars[key].set(key)

        # from our list of variables that were changed from their default values, pair them together in a new pairs list.
        # 1 is paired with 2. 3 with 4, etc
        try:
            # increment by 2 every loop to avoid placing the same stimuli in the list twice
            self.pairs = [(self.changed_vars[i], self.changed_vars[i+1]) for i in range(0, len(self.changed_vars), 2)]
        except:
            # if a stimulus has not been changed, this error message will be thrown to tell the user to change it and try again.
            messagebox.showinfo("Stimulus Not Changed","One or more of the default stimuli have not been changed, please change the default value and try again")
        # for each pair in pairs list, include each pair flipped
        self.pairs.extend([(pair[1], pair[0]) for pair in self.pairs])

        # if the stimuli frame is already open then destroy everything in it so we can write over it with a new one
        if hasattr(self, 'stimuli_frame'):                                                        
            # destroying table
            self.trial_blocks.destroy()
            # destroying frame
            self.stimuli_frame.destroy()
            # emptying list holding stimuli data
            self.df_list = []

        # if the user has changed the defualt values of num_blocks and changed variables, then generate the experiment schedule

        # filling pair information in the tables with trial numbers and random interval times
        # if the number of trial blocks is greater than 0 and we have changed more than one default stimulus
        if self.num_trial_blocks.get() != 0 and len(self.changed_vars) > 0:                                             
            for i in range(self.num_trial_blocks.get()):       
                # copy the entire list of pairs int pairs_copy                                                         
                pairs_copy = [(var1.get(), var2.get()) for var1, var2 in self.pairs]                                    
                # then shuffle the pairs so we get pseudo random generation 
                random.shuffle(pairs_copy)
                # recreate the pairs_copy list, now inluding entries of strings for trial block, trial number which are np.nan, and the pairs                                                                             
                pairs_copy = [(str(i+1), np.nan) + pair for k, pair in enumerate(pairs_copy)]
                # create the dataframe skeleton, include column headings 
                df = pd.DataFrame(pairs_copy, columns=['Trial Block', 'Trial Number', 'Stimulus 1', 'Stimulus 2'])  
                # we don't have any licks yet so, fill with blank or 'nan' values    
                df['Stimulus 1 Licks'] = np.nan                                                                         
                df['Stimulus 2 Licks'] = np.nan
                # add df to the list of data frames
                self.df_list.append(df)  
            # add the df list to the pandas df_stimuli table, ignoring index because we have multiple blocks implemented
            # if we leave the index, then the trial number column will repeat for every block that we added and throw off 
            # the data table                                                                           
            self.df_stimuli = pd.concat(self.df_list, ignore_index=True)                                                

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

            # Creating the main data table and adding the dataframe that we just created, adding a toolbar in and setting 
            # weight to 1 to make sure that it expands as the window expands

            self.trial_blocks = Table(self.stimuli_frame, dataframe=self.df_stimuli, showtoolbar=True, showstatusbar=True, weight=1)
            self.trial_blocks.autoResizeColumns()
            self.trial_blocks.show()

            self.blocks_generated = True      

            # setup the licks data frame that will hold the timestamps for the licks and which port was likced
            self.licks_df = pd.DataFrame(columns=['Trial Number', 'Port Licked', 'Time Stamp'])
            # set the row specified at .loc[len(self.licks_df)] which is zero at this time
            # so the zeroth row is set to np.nan so that the frame is not blank when the table is empty
            self.licks_df.loc[len(self.licks_df)] = np.nan  
        elif (len(self.changed_vars) == 0): 
            # if there have been no variables that have been changed, then inform the user to change them
            messagebox.showinfo("Stimuli Variables Not Yet Changed","Stimuli variables have not yet been changed, to continue please change defaults and try again.")
        elif (self.num_trial_blocks.get() == 0):
            # if number of trial blocks is zero, inform the user that they must change this
            messagebox.showinfo("Number of Trial Blocks 0","Number of trial blocks is currently still set to zero, please change the default value and try again.")
    
    # define method to update the plot in the 'view data' window
    def update_plot(self):

        # clear the old plot
        self.axes.clear()  

        # this line is continued on the next line
        # This sets up a bar plot, and gives data values for the x labels (stimulus 1, stimulus 2) and informs the program where to look for this data ([self.side_one_licks, self.side_two_licks])
        self.axes.bar([self.df_stimuli.loc[self.curr_trial_number-1, 'Stimulus 1'], self.df_stimuli.loc[self.curr_trial_number - 1, 'Stimulus 2']], [self.side_one_licks, self.side_two_licks]) 

        # Draw the plot
        self.canvas.draw()  

        # set the update plot funtion to call itself again, and set the id to the scheduling identifier so 
        # that we can cancel it later when we want to stop calling the function
        self.update_plot_id = self.root.after(50, self.update_plot)


    # this function is called when the main app window is closed, this is set on line 35
    def on_close(self):
        # stop calling the clock update function

        self.root.after_cancel(self.update_clock_id)

        # if we have called the update licks function at all, 
        # then cancel future calls

        if self.update_licks_id is not None:  
            self.root.after_cancel(self.update_licks_id)

        # if we opened a data window and have a plot, then cancel future calls and destroy the window

        if self.update_plot_id is not None:
            self.root.after_cancel(self.update_plot_id)
            self.data_window_instance.destroy()
        try:
            # if the Arduino connections are available, then close them
            self.arduinoLaser.close()
            self.arduinoMotor.close()
        except: 
            pass
        # destroy the root window and close the app
        self.root.destroy();
        self.root.quit()

    # Define the method for toggling the program state via the start/stop button
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

            # if we have opened a data window and have a update for the plot scheduled, then cancel it and close the window
            if self.update_plot_id is not None:
                self.root.after_cancel(self.update_plot_id)
                self.data_window_instance.destroy()
            # try to send the reset command to reboot both Arduino boards 
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
        # reset timers to hold 0  
        elapsed_time = 0 
        self.time_label.configure(text="{:.3f}s".format(elapsed_time))
        state_elapsed_time = 0
        self.state_time_label.configure(text="{:.3f}s".format(state_elapsed_time))

    # Define the method for updating the clock
    def update_clock(self):
        # If the program is running, update the elapsed time
        if self.running:
            # total elapsed time is current minus program start time
            elapsed_time = time.time() - self.start_time
            # update the main screen label and set the number of decimal points to 3 
            self.time_label.configure(text="{:.3f}s".format(elapsed_time))
            # state elapsed time is current time minus the time we entered the state 
            state_elapsed_time = time.time() - self.state_start_time
            # update the main screen label and set the number of decimal points to 3
            self.state_time_label.configure(text="{:.3f}s".format(state_elapsed_time))
        # Call this method again after 100 ms
        self.update_clock_id = self.root.after(50, self.update_clock)
        
    # Define the method for reading data from the optical fiber Arduino
    def read_licks(self, i):
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

    # Define the method for appending data to the scrolled text widget
    def append_data(self, data):
        self.data_text.insert(tk.END, data)
        # Scroll the scrolled text widget to the end of the data
        self.data_text.see(tk.END)

    # method that brings up the windows file save dialogue menu to save the two data tables to external files
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
