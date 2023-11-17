import tkinter as tk

class ExperimentLogic:
    def __init__(self) -> None:
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