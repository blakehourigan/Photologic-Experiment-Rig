import tkinter as tk
from tkinter import ttk
import platform 
from typing import Dict, List

class ExperimentCtlWindow:
    def __init__(self, controller):
        self.controller = controller
        
        self.system = platform.system()
        
        self.top = None
        self.canvas = None  # Initialize canvas here to ensure it's available for binding
        self.num_tabs = 0
        
    def create_window(self, master) -> tk.Toplevel:
        self.top = tk.Toplevel(master)
        self.top.title("Experiment Control")
        self.top.bind("<Control-w>", lambda e: self.top.destroy())
        self.top.resizable(False, False)
        self.update_size()

        return self.top
    
    def create_tab(self, notebook, tab_title) -> ttk.Frame:
        tab = ttk.Frame(notebook)
        notebook.add(tab, text=tab_title)
        # Configure the frame's grid to expand and fill the space
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(0, weight=1)
        return tab
    
    def update_size(self, event=None) -> None:
        """Adjusts the window width based on the contents of the currently selected tab, keeping the height constant."""
        if self.top is not None and event is not None:
            # Make sure the update is due to tab change and we have the notebook widget
            notebook = event.widget
            current_tab = notebook.nametowidget(notebook.select())

            self.top.update_idletasks()  # Ensure the current layout is processed

            # Specifically target the stimuli_frame for width calculation if it's the current tab
            if hasattr(self, 'stimuli_frame') and self.stimuli_frame.winfo_ismapped():
                # Use the stimuli_frame to calculate width
                desired_width = self.stimuli_frame.winfo_reqwidth()
            else:
                # Default behavior for other tabs
                desired_width = current_tab.winfo_reqwidth()

            # Keep the current window height
            current_height = self.top.winfo_height()

            # Add some extra space for width if needed
            extra_width = 20
            new_width = desired_width + extra_width

            # Adjust the window size with the new width and current height
            self.top.geometry(f"{new_width}x{current_height}")

            # Optionally re-center the window if desired
            screen_width = self.top.winfo_screenwidth()
            screen_height = self.top.winfo_screenheight()
            x_position = (screen_width - new_width) // 2
            y_position = (screen_height - current_height) // 2
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
        side_one_label.grid(row=0, column=0, pady=5)
        side_two_label = tk.Label(self.stimuli_entry_frame, pady=0, text="Side Two", bg="light blue", font=("Helvetica", 24), highlightthickness=2, highlightbackground='dark blue')
        side_two_label.grid(row=0, column=1, pady=5)
           
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

    def on_window_close(self) -> None:
        """Handle the close event when the user clicks the X button on the window."""
        if self.top is not None:
            self.top.destroy()
            self.top = None