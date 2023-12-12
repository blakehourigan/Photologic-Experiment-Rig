from typing import Optional
import tkinter as tk

class valveTestWindow:
    def __init__(self, controller):
        self.controller = controller
        self.master = controller.main_gui.root
        
        self.top: Optional[tk.Toplevel] = None
    
    def show_window(self) -> None:
        # if the number of simuli is currently set to zero, tell the user that they need to add stmiuli before we can more forward
        if(self.controller.data_mgr.num_stimuli.get() > 0): 
            if self.top is not None and self.top.winfo_exists():
                self.top.lift()       
            else:
                self.top = self.create_window(self.master)
                self.configure_tk_obj_grid(self.top)
                self.top.protocol("WM_DELETE_WINDOW", self.on_window_close)  # Bind the close event
            
                frame = tk.Frame(self.top, width=500, height=500)
                frame.pack()
                
                self.update_size()
        
    def create_window(self, master) -> tk.Toplevel:
        # Create a new window for AI solutions  
        top = tk.Toplevel(master)
        top.title("Valve Testing")
        self.update_size()
        return top
    
    
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