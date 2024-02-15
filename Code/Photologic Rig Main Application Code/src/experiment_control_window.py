import tkinter as tk
from tkinter import ttk
from typing import Dict, List

class ExperimentCtlWindow:
    def __init__(self, controller):
        self.controller = controller
        
        self.top = None
        
        self.num_tabs = 0
        
    def create_window(self, master) -> tk.Toplevel:
        top = tk.Toplevel(master)
        top.title("Experiment Control")
        top.bind ("<Control-w>", lambda e: top.destroy())  # Close the window when the user presses ctl + w
        top.resizable(False, False)  # This makes the Toplevel window not resizable
        self.update_size()
        return top    
    
    def create_tab(self, notebook, tab_title) -> ttk.Frame:
        tab = ttk.Frame(notebook)
        notebook.add(tab, text=tab_title)
        # Configure the frame's grid to expand and fill the space
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(0, weight=1)
        return tab
    
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
            
    def update_main_table_cell(self, row, column, new_value):
        # Adjust indices for zero-based indexing
        row_index = row - 1
        column_index = column - 1

        # Check if the specified cell exists
        if row_index < len(self.cell_labels) and column_index < len(self.cell_labels[row_index]):
            self.cell_labels[row_index][column_index].configure(text=new_value)
        else:
            print("Cell at row", row, "column", column, "doesn't exist.")

    def configure_tk_obj_grid(self, obj):
        # setting the tab to expand when we expand the window 
        obj.grid_rowconfigure(0, weight=1)                            
        obj.grid_columnconfigure(0, weight=1)  
        
            
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

                self.button_frame = tk.Frame(self.exp_stimuli_tab, highlightthickness=2, highlightbackground='black')
                self.button_frame.grid(row=1, column=0, pady=5, sticky="nsew")
                self.button_frame.grid_columnconfigure(0,weight=1)
                self.button_frame.grid_rowconfigure(0,weight=1)

                # stimuli schedule button that calls the function to generate the program schedule when pressed 
                self.generate_stimulus = tk.Button(self.button_frame, text="Generate Stimulus", command=lambda: self.controller.data_mgr.initialize_stimuli_dataframe(), bg="green", font=("Helvetica", 24))
                self.generate_stimulus.grid(row=0, column=0, pady=5, padx=5, sticky='nsew')
                
                if(self.controller.data_mgr.blocks_generated):
                    self.show_stimuli_table()
                self.update_size()
                
    def populate_stimuli_tab(self, tab) -> None:
        row = 1
        self.ui_components: Dict[str, List[tk.Widget]]

        self.ui_components = {'frames': [], 'labels': [], 'entries': []}
        
        self.stimuli_entry_frame = tk.Frame(tab, highlightthickness=2, highlightbackground='black')
        self.stimuli_entry_frame.grid(row=0, column=0, pady=5, padx=5, sticky="nsew")
        self.stimuli_entry_frame.grid_rowconfigure(0, weight=1) 
        
        for i in range(2):
            self.stimuli_entry_frame.grid_columnconfigure(i, weight=1) 
            
        side_one_label = tk.Label(self.stimuli_entry_frame, text="Side One", bg="light blue", font=("Helvetica", 24), highlightthickness=2, highlightbackground='dark blue')
        side_one_label.grid(row=0, column=0)
        side_two_label = tk.Label(self.stimuli_entry_frame, pady=0, text="Side Two", bg="light blue", font=("Helvetica", 24), highlightthickness=2, highlightbackground='dark blue')
        side_two_label.grid(row=0, column=1)
           
        for i in range(self.controller.data_mgr.num_stimuli.get()):
            # place the box in the first column if less that 4 stimuli, set to column 2 if 5 or above
            column = 0 if (i < self.controller.data_mgr.num_stimuli.get() / 2 ) else 1
            if (i == self.controller.data_mgr.num_stimuli.get() / 2) :
                row = 1
            frame, label, entry = self.create_labeled_entry(self.stimuli_entry_frame, f"Valve {i+1}", self.controller.data_mgr.stimuli_vars[f'Valve {i+1} substance'], row, column)

            self.ui_components['frames'].append(frame)
            self.ui_components['labels'].append(label)
            self.ui_components['entries'].append(entry)
            
            row += 1 
            
    def show_stimuli_table(self):
        # creating the frame that will contain the data table
        self.stimuli_frame = tk.Frame(self.stim_sched_tab)
        
        # setting the place of the frame                       
        self.stimuli_frame.grid(row=0, column=0, sticky="nsew")
        self.configure_tk_obj_grid(self.stim_sched_tab)

        # get the dataframe from your controller
        df = self.controller.data_mgr.stimuli_dataframe

        # Initialize the storage for cell label references
        self.header_labels = []
        self.cell_labels = []

        # create labels for the column headers
        for j, col in enumerate(df.columns):
            header_label = tk.Label(self.stimuli_frame, text=col, bg='light blue', fg='black', 
                                    font=('Helvetica', 10, 'bold'), highlightthickness=2, 
                                    highlightbackground='black', highlightcolor='black')
            header_label.grid(row=0, column=j, sticky='nsew')
            self.header_labels.append(header_label)

        # create labels for the cells in the dataframe
        for i, row in enumerate(df.itertuples(index=False), start=1):
            row_labels = []  # Create a list to store the labels for this row
            for j, value in enumerate(row):
                cell_label = tk.Label(self.stimuli_frame, text=value, bg='white', fg='black', 
                                    font=('Helvetica', 10), highlightthickness=1, 
                                    highlightbackground='black', highlightcolor='black')
                cell_label.grid(row=i, column=j, sticky='nsew')
                row_labels.append(cell_label)
            self.cell_labels.append(row_labels)  # Add the list of row labels to the main list

        # configure column weights to make the labels expandable
        for col in range(len(df.columns)):
            self.stimuli_frame.grid_columnconfigure(col, weight=1)

        # configure row weights for all rows including header
        for row in range(len(df)+1):
            self.stimuli_frame.grid_rowconfigure(row, weight=1)        



    def on_window_close(self) -> None:
        """Handle the close event when the user clicks the X button on the window."""
        if self.top is not None:
            self.top.destroy()
            self.top = None