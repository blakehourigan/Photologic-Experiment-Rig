from tkinter import filedialog
import pandas as pd
import numpy as np
import random

class DataManager:
    def __init__(self, controller):
        self.stimuli_dataframe = None
        self.licks_dataframe = pd.DataFrame()
        self.controller = controller
        
    def generate_trial_blocks(self) -> pd.DataFrame:    
        # if the user has changed the defualt values of num_blocks and changed variables, then generate the experiment schedule
        
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
            # add the df list to the pandas stimuli_dataframe table, ignoring index because we have multiple blocks implemented
            # if we leave the index, then the trial number column will repeat for every block that we added and throw off 
            # the data table                                                                           
            self.stimuli_dataframe = pd.concat(self.df_list, ignore_index=True)                                                

            # fill the tables with the values of all random intervals that were previously generated
            # from their respective lists 

            for i in range(len(self.stimuli_dataframe)):
                self.stimuli_dataframe.loc[i, 'ITI'] = self.ITI_intervals_final[i]
                self.stimuli_dataframe.loc[i, 'TTC'] = self.TTC_intervals_final[i]
                self.stimuli_dataframe.loc[i, 'Sample Time'] = self.sample_intervals_final[i]
                self.stimuli_dataframe.loc[i, 'Trial Number'] = int(i + 1) 

            # Create new column for the actual time elapsed in Time to contact state to be filled during program execution
            self.stimuli_dataframe['TTC Actual'] = np.nan
        elif (len(self.changed_vars) == 0): 
            # if there have been no variables that have been changed, then inform the user to change them
            self.controller.display_error("Stimuli Variables Not Yet Changed","Stimuli variables have not yet been changed, to continue please change defaults and try again.")
        elif (self.num_trial_blocks.get() == 0):
            # if number of trial blocks is zero, inform the user that they must change this
            self.controller.display_error("Number of Trial Blocks 0","Number of trial blocks is currently still set to zero, please change the default value and try again.")

        return self.stimuli_dataframe

        # creating the frame that will contain the data table
        self.stimuli_frame = tk.Frame(tab2)     
        # setting the place of the frame                       
        self.stimuli_frame.grid(row=0, column=0, sticky='nsew') 

        # setting the tab to expand when we expand the window 
        tab2.grid_rowconfigure(0, weight=1)                            
        tab2.grid_columnconfigure(0, weight=1)  

        # Creating the main data table and adding the dataframe that we just created, adding a toolbar in and setting 
        # weight to 1 to make sure that it expands as the window expands

        self.trial_blocks = Table(self.stimuli_frame, dataframe=self.stimuli_dataframe, showtoolbar=True, showstatusbar=True, weight=1)
        self.trial_blocks.autoResizeColumns()
        self.trial_blocks.show()

        self.blocks_generated = True      

        # setup the licks data frame that will hold the timestamps for the licks and which port was likced
        self.licks_dataframe = pd.DataFrame(columns=['Trial Number', 'Port Licked', 'Time Stamp'])
        # set the row specified at .loc[len(self.licks_dataframe)] which is zero at this time
        # so the zeroth row is set to np.nan so that the frame is not blank when the table is empty
        self.licks_dataframe.loc[len(self.licks_dataframe)] = np.nan  

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
