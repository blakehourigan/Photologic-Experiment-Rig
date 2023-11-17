import tkinter as tk

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
            # state of the program is OFF
            self.state = "OFF"
            # set the state timer label
            main_gui.state_time_label_header.configure(text=(self.state))
            # set the running variable to false to halt execution in the state functions
            self.running = False
            # Turn the program execution button back to the green start button
            main_gui.startButton.configure(text="Start", bg="green")
            #self.root.after_cancel(self.update_clock_id)
            # if we have called the update licks function at all, then stop it from being called now, we're done with it 
            if self.update_licks_id is not None:  
                self.root.after_cancel(self.update_licks_id)

            # if we have opened a data window and have a update for the plot scheduled, then cancel it and close the window
            if self.update_plot_id is not None:
                self.main_gui.master.after_cancel(self.update_plot_id)
                #self.data_window_instance.destroy()
            # try to send the reset command to reboot both Arduino boards 

            arduino_mgr.reset_arduinos()
            self.curr_trial_number = 1
            
            
    def clear_button_logic(self, main_gui):
        # Clear the scrolled text widget
        main_gui.data_text.delete('1.0', tk.END)
        # reset timers to hold 0  
        elapsed_time = 0 
        main_gui.time_label.configure(text="{:.3f}s".format(elapsed_time))
        state_elapsed_time = 0
        main_gui.state_time_label.configure(text="{:.3f}s".format(state_elapsed_time))
            