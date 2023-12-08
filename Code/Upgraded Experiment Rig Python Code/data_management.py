from tkinter import filedialog
import pandas as pd
import numpy as np
import random
import tkinter as tk

class DataManager:
    def __init__(self, controller) -> None:
        self.stimuli_dataframe = pd.DataFrame()
        self.licks_dataframe = pd.DataFrame()
        self.controller = controller
        self.logic = controller.logic

        self.stimuli_vars = {f'stimuli_var_{i+1}': tk.StringVar() for i in range(8)}
        for key in self.stimuli_vars:
            self.stimuli_vars[key].set(key)
            
        # initialize lists to hold original pairs and the list that will hold our dataframes.

        self.pairs = []
        self.df_list = []

        # Initialize variables that will keep track of the total number of trials we will have, the total number of trial blocks that the user wants to run
        # and the total number of stimuli. These are of type IntVar because they are used in the GUI. 

        self.num_trials = tk.IntVar(value=0)
        self.num_trial_blocks = tk.IntVar(value=4)
        self.num_stimuli = tk.IntVar(value=4)
        
        # initializing variable for iteration through the trials in the program

        self.curr_trial_number = 1


        self._blocks_generated = False

        self.stamped_exists = False

        self.data_window_open = False
        
        self.interval_vars = \
        {
            'ITI_var': tk.IntVar(value=30000),
            'TTC_var': tk.IntVar(value=15000),
            'sample_var': tk.IntVar(value=15000),
            'ITI_random_entry': tk.IntVar(value=5000),
            'TTC_random_entry': tk.IntVar(value=5000),
            'sample_random_entry': tk.IntVar(value=5000),
        }
        
        # initializing the lists that will hold the final calculated random interval values 

        self.ITI_intervals_final = []
        self.TTC_intervals_final = []
        self.sample_intervals_final = []
        
        # Initialize the time, licks to 0
        
        self.start_time = 0.0
        self.state_start_time = 0.0
        
        self.side_one_licks = 0
        self.side_two_licks = 0
        self.total_licks = 0
        
    
    
    def create_trial_blocks(self):
        """ this is the function that will generate the full roster of stimuli for the duration of the program """
        
        # the total number of trials equals the number of stimuli times the number of trial blocks that we want
        self.num_trials.set((self.num_stimuli.get() * self.num_trial_blocks.get()))         

        # clearing the lists here just in case we have already generated blocks, in this case we want to ensure we use new numbers, so we must clear out the existing ones
        self.ITI_intervals_final.clear()
        self.TTC_intervals_final.clear()
        self.sample_intervals_final.clear()
        
        # Assuming 'num_entries' is the number of entries (rows) you need to process
        for entry in range(self.num_trials.get()):
            for interval_type in ['ITI', 'TTC', 'sample']:
                random_entry_key = f'{interval_type}_random_entry'
                var_key = f'{interval_type}_var'
                final_intervals_key = f'{interval_type}_intervals_final'

                # Generate a random interval
                random_interval = random.randint(-self.interval_vars[random_entry_key].get(), 
                                                self.interval_vars[random_entry_key].get())
                
                # Calculate the final interval by adding the random interval to the state constant
                final_interval = self.interval_vars[var_key].get() + random_interval

                # Append the final interval to the corresponding list
                if not hasattr(self, final_intervals_key):
                    setattr(self, final_intervals_key, [])
                getattr(self, final_intervals_key).append(final_interval)


        """this checks every variable in the simuli_vars dictionary against the default value, if it is changed, then it is added to the list 
                            var for iterator, (key, value) in enumerate(self.stimuli_vars.items() if variable not default then add to list)"""
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
            self.controller.display_error("Stimulus Not Changed","One or more of the default stimuli have not been changed, please change the default value and try again")
        # for each pair in pairs list, include each pair flipped
        self.pairs.extend([(pair[1], pair[0]) for pair in self.pairs])

        
    def generate_trial_blocks(self) -> pd.DataFrame:  
        self.create_trial_blocks()  
        # if the user has changed the defualt values of num_blocks and changed variables, then generate the experiment schedule
        
        if self.num_trial_blocks.get() != 0 and len(self.changed_vars) > 0:                                             
            for i in range(self.controller.data_mgr.num_trial_blocks.get()):       
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
            # add the df list to the pandas stimuli_dataframe table, ignoring index because we have multiple blocks implemented
            # if we leave the index, then the trial number column will repeat for every block that we added and throw off 
            # the data table                                                                           
            self.stimuli_dataframe = pd.concat(self.df_list, ignore_index=True)                                                

            # fill the tables with the values of all random intervals that were previously generated
            # from their respective lists  
            self.initialize_stimuli_dataframe()

        elif (len(self.changed_vars) == 0): 
            # if there have been no variables that have been changed, then inform the user to change them
            self.controller.display_error("Stimuli Variables Not Yet Changed","Stimuli variables have not yet been changed, to continue please change defaults and try again.")
        elif (self.logic.num_trial_blocks.get() == 0):
            # if number of trial blocks is zero, inform the user that they must change this
            self.controller.display_error("Number of Trial Blocks 0","Number of trial blocks is currently still set to zero, please change the default value and try again.")
        
        self.blocks_generated = True 
        self.controller.experiment_ctl_wind.show_stimuli_table()
        return self.stimuli_dataframe

    def initialize_stimuli_dataframe(self):
        """filling the dataframe with the values of the random intervals that were previously generated
        """
        print(type(self.ITI_intervals_final[0]))
        for i in range(len(self.stimuli_dataframe)):
            self.stimuli_dataframe.loc[i, 'ITI'] = float(self.ITI_intervals_final[i])
            self.stimuli_dataframe.loc[i, 'TTC'] = float(self.TTC_intervals_final[i])
            self.stimuli_dataframe.loc[i, 'Sample Time'] = float(self.sample_intervals_final[i])
            self.stimuli_dataframe.loc[i, 'Trial Number'] = int(i + 1)

        print(type(self.stimuli_dataframe['ITI'][0]))

        # Ensure 'ITI', 'TTC', and 'Sample Time' columns are of a numeric type
        self.stimuli_dataframe['ITI'] = self.stimuli_dataframe['ITI'].astype(int)
        self.stimuli_dataframe['TTC'] = self.stimuli_dataframe['TTC'].astype(int)
        self.stimuli_dataframe['Sample Time'] = self.stimuli_dataframe['Sample Time'].astype(int)

        # Create new column for the actual time elapsed in Time to contact state to be filled during program execution
        self.stimuli_dataframe['TTC Actual'] = np.nan

    def initalize_licks_dataframe(self):
        """ setup the licks data frame that will hold the timestamps for the licks and which port was licked
            and create an empty first row to avoid a blank table when the program is first run
        """
        self.licks_dataframe = pd.DataFrame([np.nan], columns=['Trial Number', 'Port Licked', 'Time Stamp'])
        

    def save_data_to_xlsx(self) -> None:
        # method that brings up the windows file save dialogue menu to save the two data tables to external files
        try:
            file_name = filedialog.asksaveasfilename(defaultextension='.xlsx',
                                                 filetypes=[('Excel Files', '*.xlsx')],
                                                 initialfile='lineup',
                                                 title='Save Excel file')

            self.stimuli_dataframe.to_excel(file_name, index=False)

            licks_file_name = filedialog.asksaveasfilename(defaultextension='.xlsx',
                                                 filetypes=[('Excel Files', '*.xlsx')],
                                                 initialfile='lineup',
                                                 title='Save Excel file')

            self.licks_dataframe.to_excel(licks_file_name, index=False)
        except:
            self.controller.display_error("Blocks Not Generated","Experiment blocks haven't been generated yet, please generate trial blocks and try again")


    def find_stimuli_positions(self, i) -> tuple:
        # Create a list of the stimuli dictionary values, will give list of stimuli. 
        stim_var_list = list(self.stimuli_vars.values())
        for index, string_var in enumerate(stim_var_list):
            if string_var.get() == self.stimuli_dataframe.loc[i,'Stimulus 1']:
                self.stim1_position = str(index + 1)

            # repeat process for the second stimulus
            elif string_var.get() == self.stimuli_dataframe.loc[i,'Stimulus 2']:
                self.stim2_position = str(index + 1)
                
        return self.stim1_position, self.stim2_position


    @property
    def blocks_generated(self):
        return self._blocks_generated

    @blocks_generated.setter
    def blocks_generated(self, value):
        # You can add validation or additional logic here
        self._blocks_generated = value