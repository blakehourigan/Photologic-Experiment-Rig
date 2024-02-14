import tkinter as tk
from tkinter import ttk
from typing import Dict, List
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

                notebook.bind("<<NotebookTabChanged>>", self.update_size)

            
                self.exp_stimuli_tab = self.create_tab(notebook, "Experiment Stimuli Tab")
                self.populate_stimuli_tab(self.exp_stimuli_tab)

                self.stim_sched_tab = self.create_tab(notebook,'Program Stimuli Schedule')

                # stimuli schedule button that calls the function to generate the program schedule when pressed 
                self.generate_stimulus = tk.Button(self.exp_stimuli_tab, text="Generate Stimulus", command=lambda: self.controller.data_mgr.initialize_stimuli_dataframe(), bg="green", font=("Helvetica", 24))
                
                # place the button after the last row
                self.generate_stimulus.grid(row=8, column=0, pady=10, padx=10, sticky='nsew', columnspan=2)
                
                if(self.controller.data_mgr.blocks_generated):
                    self.show_stimuli_table()
                    self.update_table()
                self.update_size()
        
    def create_window(self, master) -> tk.Toplevel:
        top = tk.Toplevel(master)
        top.title("Experiment Control")
        top.bind ("<Control-w>", lambda e: top.destroy())  # Close the window when the user presses ctl + w
        self.update_size()
        return top

    def update_size(self, event=None) -> None:
        """Adjusts the window size based on the contents of the currently selected tab."""
        if self.top is not None and event is not None:
            # Make sure the update is due to tab change and we have the notebook widget
            notebook = event.widget
            current_tab = notebook.nametowidget(notebook.select())

            self.top.update_idletasks()  # Ensure the current layout is processed

            # Calculate the size based on the content of the current tab
            current_tab.update_idletasks()  # Make sure the tab's layout is up to date
            desired_width = current_tab.winfo_reqwidth()
            desired_height = current_tab.winfo_reqheight()

            # Add some extra space if needed, or handle margins/paddings
            extra_width = 20
            extra_height = 60  # Adjust based on your UI needs

            # Calculate new size including any extra space
            new_width = desired_width + extra_width
            new_height = desired_height + extra_height

            # Adjust the window size
            self.top.geometry(f"{new_width}x{new_height}")

            # Optionally re-center the window if desired
            screen_width = self.top.winfo_screenwidth()
            screen_height = self.top.winfo_screenheight()
            x_position = (screen_width - new_width) // 2
            y_position = (screen_height - new_height) // 2
            self.top.geometry(f"+{x_position}+{y_position}")



    def create_tab(self, notebook, tab_title) -> ttk.Frame:
        tab = ttk.Frame(notebook)
        notebook.add(tab, text=tab_title)
        return tab
   
    def create_labeled_entry(self, parent: tk.Frame, label_text: str, text_var: tk.StringVar, row: int, column: int) -> tuple[tk.Frame, tk.Label, tk.Entry]:        
        frame = tk.Frame(parent)
        frame.grid(row=row, column=column, padx=5, pady=5, sticky="nsew")

        label = tk.Label(frame, text=label_text, bg="light blue", font=("Helvetica", 24), highlightthickness=1, highlightbackground='dark blue')
        label.grid(row=0, pady=10)

        entry = tk.Entry(frame, textvariable=text_var, font=("Helvetica", 24), highlightthickness=1, highlightbackground='black')
        entry.grid(row=1, sticky="nsew")

        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=1)
        return frame, label, entry
    
    def populate_stimuli_tab(self, tab) -> None:
        row = 0
        self.ui_components: Dict[str, List[tk.Widget]]

        self.ui_components = {'frames': [], 'labels': [], 'entries': []}
        
        self.stimuli_entry_frame = tk.Frame(self.exp_stimuli_tab, highlightthickness=2, highlightbackground='black')
        self.stimuli_entry_frame.grid(row=0, column=0, pady=5, sticky="nsew")
        self.stimuli_entry_frame.grid_rowconfigure(0, weight=1) 
        for i in range(2):
            self.stimuli_entry_frame.grid_columnconfigure(i, weight=1) 
           
        for i in range(self.controller.data_mgr.num_stimuli.get()):
            # place the box in the first column if less that 4 stimuli, set to column 2 if 5 or above
            column = 0 if (i < self.controller.data_mgr.num_stimuli.get() / 2 ) else 1
            if (i == self.controller.data_mgr.num_stimuli.get() / 2) :
                row = 0 
            frame, label, entry = self.create_labeled_entry(self.stimuli_entry_frame, f"Valve {i+1}", self.controller.data_mgr.stimuli_vars[f'Valve {i+1} substance'], row, column)

            self.ui_components['frames'].append(frame)
            self.ui_components['labels'].append(label)
            self.ui_components['entries'].append(entry)
            
            row += 1 

 

    def entry_widgets(self) -> None:
        self.entry_widgets_frame = tk.Frame(self.top, highlightthickness=2, highlightbackground='black')
        self.entry_widgets_frame.grid(row=3, column=0, pady=5, sticky="nsew")
        for i in range(4):
            self.entry_widgets_frame.grid_columnconfigure(i, weight=1)

        # Simplify the creation of labeled entries
        self.ITI_Interval_Frame, _, _ = self.create_labeled_entry(self.entry_widgets_frame, "ITI Time", self.controller.data_mgr.interval_vars["ITI_var"], 0, 0)
        self.TTC_Interval_Frame, _, _ = self.create_labeled_entry(self.entry_widgets_frame, "TTC Time", self.controller.data_mgr.interval_vars["TTC_var"], 0, 1)
        self.Sample_Interval_Frame, _, _ = self.create_labeled_entry(self.entry_widgets_frame, "Sample Time", self.controller.data_mgr.interval_vars["sample_var"], 0, 2)
        self.num_trial_blocks_frame, _, _ = self.create_labeled_entry(self.entry_widgets_frame, "# Trial Blocks", self.controller.data_mgr.num_trial_blocks, 0, 3)

        # Similarly for random plus/minus intervals and the number of stimuli
        self.ITI_Random_Interval_frame, _, _ = self.create_labeled_entry(self.entry_widgets_frame, "+/- ITI", self.controller.data_mgr.interval_vars["ITI_random_entry"], 1, 0)
        self.TTC_Random_Interval_frame, _, _ = self.create_labeled_entry(self.entry_widgets_frame, "+/- TTC", self.controller.data_mgr.interval_vars["TTC_random_entry"], 1, 1)
        self.Sample_Interval_Random_Frame, _, _ = self.create_labeled_entry(self.entry_widgets_frame, "+/- Sample", self.controller.data_mgr.interval_vars["sample_random_entry"], 1, 2)
        self.num_stimuli_frame, _, _ = self.create_labeled_entry(self.entry_widgets_frame, "# Stimuli", self.controller.data_mgr.num_stimuli, 1, 3)
        
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
        """Display the stimuli table and resize window to fit the table."""
        # Assuming self.stimuli_frame and self.trial_blocks_table are already defined

        self.stimuli_frame.grid(row=0, column=0, sticky='nsew')
        self.configure_tk_obj_grid(self.stim_sched_tab)

        # Display the table
        self.trial_blocks_table.show()
        self.trial_blocks_table.adjustColumnWidths()

        # Resize the window after the table is shown
        self.resize_window_for_table()

    def resize_window_for_table(self):
        """Resize the window to ensure the full table is visible."""
        if self.top is not None:
            self.top.update_idletasks()  # Make sure all sizes are up-to-date

            # Calculate required size for the table
            table_width = self.trial_blocks_table.getTableWidth()
            table_height = self.trial_blocks_table.getTableHeight()

            # Add some extra space for margins, borders, or any other UI elements
            extra_width = 100  # Adjust based on your UI needs
            extra_height = 150  # Includes space for column headers, etc.

            # Set new window size to accommodate the full table
            new_width = table_width + extra_width
            new_height = table_height + extra_height

            # Update window geometry
            self.top.geometry(f"{new_width}x{new_height}")

            # Optionally re-center the window
            screen_width = self.top.winfo_screenwidth()
            screen_height = self.top.winfo_screenheight()
            x_position = (screen_width - new_width) // 2
            y_position = (screen_height - new_height) // 2
            self.top.geometry(f"+{x_position}+{y_position}")

        
    def update_table(self):
        self.trial_blocks_table.redraw()
        
        self.stimuli_frame.update_idletasks()
        
        self.stimuli_frame.after(250, self.update_table)
                
    def configure_tk_obj_grid(self, obj):
        # setting the tab to expand when we expand the window 
        obj.grid_rowconfigure(0, weight=1)                            
        obj.grid_columnconfigure(0, weight=1)  
        

    def on_window_close(self) -> None:
        """Handle the close event when the user clicks the X button on the window."""
        if self.top is not None:
            self.top.destroy()
            self.top = None