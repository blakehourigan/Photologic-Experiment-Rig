from calendar import c
import tkinter as tk
from tkinter import messagebox
from pandastable import Table

class LicksWindow:
    def __init__(self, controller) -> None:
        self.controller = controller
        
        self.top = None
        
    def show_window(self) -> None:
        if self.top is not None and self.top.winfo_exists():
            self.top.lift() 
        else: 
            self.create_window()
    
    def create_window(self) -> None:
        if self.controller.data_mgr.blocks_generated:
            self.top = tk.Toplevel(self.controller.main_gui.root)
            self.top.protocol("WM_DELETE_WINDOW", self.on_window_close)  # Bind the close event
            
            # create the frame that the table will be held in
            self.licks_frame = tk.Frame(self.top)
            self.licks_frame.grid(row=0, column=0, sticky='nsew')
            
            # create the table, using the data fro the licks_df
            self.stamped_licks = Table(self.licks_frame, dataframe=self.controller.data_mgr.licks_dataframe, showtoolbar=False, showstatusbar=False, weight=1)
            self.stamped_licks.autoResizeColumns()
            self.stamped_licks.show()
            
            # the licks data table now exists so set the bool to true so that we can tell the lick function to update the window when new licks are added
            self.stamped_exists = True
        else:
            # if blocks haven't been created yet, then there isn't a lick dataframe generated yet so tell user to generate blocks first
            messagebox.showinfo("Blocks Not Generated","Experiment blocks haven't been generated yet, please generate trial blocks and try again")

    def on_window_close(self) -> None:
        """Handle the close event when the user clicks the X button on the window."""
        if self.top is not None:
            self.top.destroy()
            self.top = None
    
        

          
            