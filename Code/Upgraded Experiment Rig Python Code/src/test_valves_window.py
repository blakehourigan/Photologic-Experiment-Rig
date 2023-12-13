from typing import Optional
import tkinter as tk

class valveTestWindow:
    def __init__(self, controller):
        self.controller = controller
        self.master = controller.main_gui.root
        
        self.top: Optional[tk.Toplevel] = None
        
        self.num_valves_to_test = tk.IntVar(value=0)

    def create_window(self, master) -> tk.Toplevel:
        # Create a new window for AI solutions  
        top = tk.Toplevel(master)
        top.title("Valve Testing")
        top.bind ("<Control-w>", lambda e: top.destroy())  # Close the window when the user presses ctl + w 
        return top
    
    def show_window(self) -> None:
        # if the number of simuli is currently set to zero, tell the user that they need to add stmiuli before we can more forward
        if(self.controller.data_mgr.num_stimuli.get() > 0): 
            if self.top is not None and self.top.winfo_exists():
                self.top.lift()       
            else:
                self.top = self.create_window(self.master)
                self.configure_tk_obj_grid(self.top)
                self.top.protocol("WM_DELETE_WINDOW", self.on_window_close)  # Bind the close event

                self.configure_grid()
                self.create_labels()
                self.create_entry_widgets()

        self.update_size()
        
    def configure_grid(self) -> None:
        if self.top is not None:
            for i in range(12):
                self.top.grid_rowconfigure(i, weight=1)
            # The first column is also configured to expand
            # Configure all columns to have equal weight
            for i in range(1):
                self.top.columnconfigure(i, weight=1)
        
    def create_labels(self) -> None:
        self.valve_testing_frame = tk.Frame(self.top, width=500, height=500)
        self.valve_testing_frame.grid(row=0, column=0, pady=10, padx=10, sticky="nsew")
        
        self.valve_testing_label = tk.Label(
        self.valve_testing_frame,
        text="Valve Testing",
        bg="light blue",
        font=("Helvetica", 24),
        )
        self.valve_testing_label.pack()
        
        self.number_valves_frame = tk.Frame(self.top, width=500, height=500)
        self.number_valves_frame.grid(row=1, column=0, pady=10, padx=10, sticky="nsew")
        
        self.number_valves_label = tk.Label(
        self.number_valves_frame,
        text="Number of Valves to Test",
        bg="light blue",
        font=("Helvetica", 16),
        wraplength=250
        )
        self.number_valves_label.pack()
        
    def create_entry_widgets(self) -> None:
        self.number_valves_entry_frame = tk.Frame(self.top, width=250, height=500)
        self.number_valves_entry_frame.grid(row=2, column=0, pady=10, padx=10, sticky="nsew")
        
        self.number_valves_entry = tk.Entry(
        self.number_valves_entry_frame,
        textvariable = self.num_valves_to_test, 
        font=("Helvetica", 18),
        width=15 
        )
        self.number_valves_entry.pack(expand=False, anchor="center")
                
    
    def on_window_close(self) -> None:
        """Handle the close event when the user clicks the X button on the window."""
        if self.top is not None:
            self.top.destroy()
            self.top = None
            
    def update_size(self) -> None:
        """update the size of the window to fit the contents
        """
        if self.top is not None:
            self.top.update_idletasks()
            width = self.top.winfo_reqwidth()
            height = self.top.winfo_reqheight()
            self.top.geometry('{}x{}'.format(width, height))
            
    def configure_tk_obj_grid(self, obj):
        # setting the tab to expand when we expand the window 
        obj.grid_rowconfigure(0, weight=1)                            
        obj.grid_columnconfigure(0, weight=1)  