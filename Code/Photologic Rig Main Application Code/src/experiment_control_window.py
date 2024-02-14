import tkinter as tk
from tkinter import ttk

from pandastable import Table # type: ignore

class ExperimentCtlWindow:
    def __init__(self, controller):
        self.controller = controller
        
        self.top = None
        
        self.num_tabs = 0
        
    def show_window(self, master) -> None:
        # if the number of simuli is currently set to zero, tell the user that they need to add stmiuli before we can more forward
        if(self.controller.data_mgr.num_stimuli.get() > 0): 
            if self.top is not None and self.top.winfo_exists():
                self.top.lift()       
            else:
                self.top = self.create_window(master)
                self.configure_tk_obj_grid(self.top)
                self.top.protocol("WM_DELETE_WINDOW", self.on_window_close)  # Bind the close event
            
                # Create the notebook (method of creating tabs at the bottom of the window), and set items to expand in all directions if window is resized  
                notebook = ttk.Notebook(self.top)
                notebook.grid(sticky='nsew')     
            
                exp_stimuli_tab = self.create_tab(notebook, "Experiment Stimuli Tab")
                self.populate_stimuli_tab(exp_stimuli_tab)

                self.stim_sched_tab = self.create_tab(notebook,'Program Stimuli Schedule')

                # stimuli schedule button that calls the function to generate the program schedule when pressed 
                self.generate_stimulus = tk.Button(exp_stimuli_tab, text="Generate Stimulus", command=lambda: self.controller.data_mgr.initialize_stimuli_dataframe(), bg="green", font=("Helvetica", 24))
                
                # place the button after the last row
                self.generate_stimulus.grid(row=8, column=0, pady=10, padx=10, sticky='nsew', columnspan=2)
                
                if(self.controller.data_mgr.blocks_generated):
                    self.show_stimuli_table()
                    self.update_table()
        
    def create_window(self, master) -> tk.Toplevel:
        top = tk.Toplevel(master)
        top.title("Experiment Control")
        top.bind ("<Control-w>", lambda e: top.destroy())  # Close the window when the user presses ctl + w
        self.update_size()
        return top

    def create_tab(self, notebook, tab_title) -> ttk.Frame:
        tab = ttk.Frame(notebook)
        notebook.add(tab, text=tab_title)
        return tab

    def populate_stimuli_tab(self, tab) -> None:
        row = 0 
        for i in range(self.controller.data_mgr.num_stimuli.get()):
            # place the box in the first column if less that 4 stimuli, set to column 2 if 5 or above
            column = 1 if (i % 2 != 0) else 0

            # Labels/Entry boxes for Stimuli, adds to tab 1 with a label of the number of stimulus that it is
            entry_frame = tk.Frame(tab, bg="light blue")
            entry_frame.grid(row=row, column=column, pady=10, padx=10, sticky='nsew')

            label = tk.Label(entry_frame, text=f"Valve {i+1}", bg="light blue", font=("Helvetica", 24))
            # .grid is how items are placed using tkinter. Place in the row and column that we calculated earlier
            label.pack()
            # sets up an entry box that will assign its held value to its stimulus var number in the stimuli_vars dictionary
            
            text_variable = self.controller.data_mgr.stimuli_vars[f'Valve {i+1} substance']
            text_variable.trace_add('write', lambda *args: self.fill_reverse_stimuli(args))
            
            entry = tk.Entry(entry_frame, textvariable=self.controller.data_mgr.stimuli_vars[f'Valve {i+1} substance'], font=("Helvetica", 24))
            
            
            # placing the entry box 1 below the label box
            entry.pack()
            
            row += 1 if (i % 2 != 0) else 0 
                
    def fill_reverse_stimuli(self, args):
        name, index, mode = args
        
        index = int(name[6:]) + 1

        if index % 2 == 0:
            change_var_index = index + 1
        else:
            change_var_index = index + 3
        

        var_to_change = self.controller.data_mgr.stimuli_vars[f'Valve {change_var_index} substance']
        
        callback_id = var_to_change.trace_info()[0][1]
        var_to_change.trace_vdelete('w', callback_id)
        
        var_to_change.set(self.controller.data_mgr.stimuli_vars[f'Valve {index} substance'].get())
        
        var_to_change.trace('w', callback_id)   
            
    def show_stimuli_table(self):
        # creating the frame that will contain the data table
        self.stimuli_frame = tk.Frame(self.stim_sched_tab)     
        
        # setting the place of the frame                       
        self.stimuli_frame.grid(row=0, column=0, sticky='nsew') 
            
        self.configure_tk_obj_grid(self.stim_sched_tab)

        self.trial_blocks_table = Table(self.stimuli_frame, dataframe=self.controller.data_mgr.stimuli_dataframe, showtoolbar=True, showstatusbar=True, weight=1)
        
        self.trial_blocks_table.show()
        self.trial_blocks_table.adjustColumnWidths()
        
    def update_table(self):
        self.trial_blocks_table.redraw()
        
        self.stimuli_frame.update_idletasks()
        
        self.stimuli_frame.after(250, self.update_table)
                
    def configure_tk_obj_grid(self, obj):
        # setting the tab to expand when we expand the window 
        obj.grid_rowconfigure(0, weight=1)                            
        obj.grid_columnconfigure(0, weight=1)  
        
    def update_size(self) -> None:
        """update the size of the window to fit the contents
        """
        if self.top is not None:
    
            """update the size of the window to fit the contents dynamically based on display size."""
            self.top.update_idletasks()  # Ensure all widgets are updated
            screen_width = self.top.winfo_screenwidth()  # Get screen width
            screen_height = self.top.winfo_screenheight()  # Get screen height

            # Calculate desired size as a fraction of screen size for demonstration
            desired_width = self.top.winfo_reqwidth()
            desired_height = self.top.winfo_reqheight()

            # Center the window on the screen
            x_position = (screen_width - desired_width) // 2
            y_position = (screen_height - desired_height) // 2

            # Apply the new geometry
            self.top.geometry(
                "{}x{}+{}+{}".format(desired_width, desired_height, x_position, y_position)
            )
            
            self.top.update_idletasks()
            self.top.geometry('{}x{}'.format(desired_width, desired_height))


    def on_window_close(self) -> None:
        """Handle the close event when the user clicks the X button on the window."""
        if self.top is not None:
            self.top.destroy()
            self.top = None