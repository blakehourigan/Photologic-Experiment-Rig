import tkinter as tk
from tkinter import ttk

from pandastable import Table

class ExperimentCtlWindow:
    def __init__(self, controller, logic, config):
        self.controller = controller
        self.logic = logic
        self.config = config
        
    def show_window(self, master):
        # if the number of simuli is currently set to zero, tell the user that they need to add stmiuli before we can more forward
        if(self.logic.num_stimuli.get() > 0):        
            # Create a new window for AI solutions
            top = tk.Toplevel(master)
            top.title(f"Experiment Control")
    
            top.geometry(self.config.experiment_ctl_gui_size)
            
            # Create the notebook (method of creating tabs at the top of the window)
            notebook = ttk.Notebook(top)
            # create a fresh frame to use for the first tabl 
            tab1 = ttk.Frame(notebook)
            # add the frame to the tab manager with the title desired
            notebook.add(tab1, text='Experiment Stimuli')

            # set the tab manager to expand its contents as the window is expanded by the user
            notebook.grid(sticky='nsew')                                                
            # set the instance to begin at (0,0) in the window, and setting weight to 1 sets all contents of the window to expand as the user expands the window
            top.grid_rowconfigure(0, weight=1)
            top.grid_columnconfigure(0, weight=1)

            # for ever stimuli that we will have in the program, create a text box that allows the user to enter the name of the stimuli
            for i in range(self.logic.num_stimuli.get()):

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
                entry = tk.Entry(tab1, textvariable=self.logic.stimuli_vars[f'stimuli_var_{i+1}'], font=("Helvetica", 24))
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
        # otherwise create the window frame and add content to it. 
        else: 
            self.controller.display_error("Stimuli Not changed from 0", "No stimuli have been added, please close the window, set number of stimuli and try again")
                
    def create_experiment_stimuli_tab(self, notebook):
        tab1 = ttk.Frame(notebook)
        notebook.add(tab1, text='Experiment Stimuli')
        self.populate_stimuli_tab(tab1)
        return tab1

    def populate_stimuli_tab(self, tab1):
        for i in range(self.logic.num_stimuli.get()):
        # [Add labels and entry boxes as per your existing code]
            pass