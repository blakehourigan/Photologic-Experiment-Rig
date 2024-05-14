import tkinter as tk
from typing import Optional
from tkinter import messagebox
from tkinter import ttk

from gui_utils import GUIUtils

class LicksWindow:
    def __init__(self, controller) -> None:
        self.controller = controller
        
        self.top: Optional[tk.Toplevel] = None
        
    def show_window(self) -> None:
        if self.top is not None and self.top.winfo_exists():
            self.top.lift() 
        elif not self.controller.data_mgr.blocks_generated:
            # if blocks haven't been created yet, then there isn't a lick dataframe generated yet so tell user to generate blocks first
            messagebox.showinfo("Blocks Not Generated","Experiment blocks haven't been generated yet, please generate trial blocks and try again")
        else: 
            self.top = self.create_window()
            self.show_table()
            window_icon_path = self.controller.experiment_config.get_window_icon_path()
            GUIUtils.set_program_icon(self.top, icon_path=window_icon_path)
    
    def create_window(self) -> tk.Toplevel:
        top = tk.Toplevel(self.controller.main_gui.root)
        top.bind("<Control-w>", lambda e: top.destroy())  # Close the window when the user presses ctl + w
        top.protocol("WM_DELETE_WINDOW", self.on_window_close)  # Bind the close event
        
        return top

    def show_table(self) -> None:
        self.licks_frame = tk.Frame(self.top)
        self.licks_frame.grid(row=0, column=0, sticky='nsew')

        # Create a Treeview widget
        self.stamped_licks = ttk.Treeview(self.licks_frame, show='headings')  # Set show='headings'
        self.stamped_licks['columns'] = list(self.controller.data_mgr.licks_dataframe.columns)

        # Configure the columns
        for col in self.stamped_licks['columns']:
            self.stamped_licks.heading(col, text=col)

        # Insert data from the DataFrame
        for _, row in self.controller.data_mgr.licks_dataframe.iterrows():
            self.stamped_licks.insert('', 'end', values=list(row))

        self.stamped_licks.pack(fill='both', expand=True)
        
    def on_window_close(self) -> None:
        """Handle the close event when the user clicks the X button on the window."""
        if self.top is not None:
            self.top.destroy()
            self.top = None
    
        

          
            