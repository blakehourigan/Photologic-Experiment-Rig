import tkinter as tk
from tkinter import ttk

from pandastable import Table

class ExperimentCtlWindow:
    def __init__(self, controller, logic, config):
        self.controller = controller
        self.logic = logic
        self.config = config
        
        self.num_tabs = 0
        
    def show_window(self, master) -> None:
        # if the number of simuli is currently set to zero, tell the user that they need to add stmiuli before we can more forward
        if(self.logic.num_stimuli.get() > 0):        
            top = self.create_window(master)
            self.configure_tk_obj_grid(top)
            
            # Create the notebook (method of creating tabs at the bottom of the window), and set items to expand in all directions if window is resized  
            notebook = ttk.Notebook(top)
            notebook.grid(sticky='nsew')     
            
            exp_stimuli_tab = self.create_tab(notebook, "Experiment Stimuli Tab")
            self.populate_stimuli_tab(exp_stimuli_tab)

            stim_sched_tab = self.create_tab(notebook,'Program Stimuli Schedule')

            # stimuli schedule button that calls the function to generate the program schedule when pressed 
            self.generate_stimulus = tk.Button(exp_stimuli_tab, text="Generate Stimulus", command=lambda: self.controller.generate_trial_blocks_data_mgr(), bg="green", font=("Helvetica", 24))
            
            # place the button after the last row
            self.generate_stimulus.grid(row=8, column=0, pady=10, padx=10, sticky='nsew', columnspan=2)
            
            # if blocks have been generated, then opening the experiment control window should show the df_stimuli dataframe in a table in the second tab 
            if(self.logic.blocks_generated):
                # creating the frame that will contain the data table
                self.stimuli_frame = tk.Frame(stim_sched_tab)     
                
                # setting the place of the frame                       
                self.stimuli_frame.grid(row=0, column=0, sticky='nsew') 
                  
                self.configure_tk_obj_grid(stim_sched_tab)

                self.show_stimuli_table()
        else: 
            # if the user has not incremented the number of stimuli yet, tell them to
            self.controller.display_error("Stimuli Not changed from 0", "No stimuli have been added, please close the window, set number of stimuli and try again")
    
    def create_window(self, master) -> tk.Toplevel:
        # Create a new window for AI solutions  
        top = tk.Toplevel(master)
        top.title(f"Experiment Control")
        top.geometry(self.config.experiment_ctl_gui_size)
        return top

    def create_tab(self, notebook, tab_title) -> ttk.Frame:
        tab = ttk.Frame(notebook)
        notebook.add(tab, text=tab_title)
        return tab

    def populate_stimuli_tab(self, tab) -> None:
        for i in range(self.logic.num_stimuli.get()):
             # for every stimuli that we will have in the program, create a text box that allows the user to enter the name of the stimuli
            for i in range(self.logic.num_stimuli.get()):

                # place the box in the first column if less that 4 stimuli, set to column 2 if 5 or above
                column = 0 if i < 4 else 1
                
                # spaces each row out 2 spaces to make room for both a label and a text entry box
                # 0 % 4 = 0, 1 % 4 = 1, 2 % 4 = 2, etc
                row = 2 * (i % 4)

                # Labels/Entry boxes for Stimuli, adds to tab 1 with a label of the number of stimulus that it is
                
                label = tk.Label(tab, text=f"Stimulus {i+1}", bg="light blue", font=("Helvetica", 24))
                # .grid is how items are placed using tkinter. Place in the row and column that we calculated earlier
                
                label.grid(row=row, column=column, pady=10, padx=10, sticky='nsew')
                # sets up an entry box that will assign its held value to its stimulus var number in the stimuli_vars dictionary
                
                entry = tk.Entry(tab, textvariable=self.logic.stimuli_vars[f'stimuli_var_{i+1}'], font=("Helvetica", 24))
                
                # placing the entry box 1 below the label box
                entry.grid(row=row+1, column=column, pady=10, padx=10, sticky='nsew')
                
    def show_stimuli_table(self):
        self.trial_blocks = Table(self.stimuli_frame, dataframe=self.logic.stimuli_dataframe, showtoolbar=True, showstatusbar=True, weight=1)
        self.trial_blocks.autoResizeColumns()
        self.trial_blocks.show()
                
    def configure_tk_obj_grid(self, obj):
        # setting the tab to expand when we expand the window 
        obj.grid_rowconfigure(0, weight=1)                            
        obj.grid_columnconfigure(0, weight=1)  
        