import tkinter as tk
# from tkinter import ttk
import platform 

class ProgramScheduleWindow:
    def __init__(self, controller):
        self.controller = controller
        
        self.system = platform.system()
        
        self.top = None
        self.canvas = None  # Initialize canvas here to ensure it's available for binding scroll actions
        self.num_tabs = 0
        
    def create_window(self, master) -> tk.Toplevel:
        self.destroy_window()  # Ensure any existing window is destroyed before creating a new one to avoid error
        self.top = tk.Toplevel(master)
        self.top.title("Program Schedule")
        self.top.bind("<Control-w>", lambda e: self.top.destroy())
        self.top.resizable(False, False)

        # Global scroll event binding called here to bind to whole window instead of only scroll widget
        self.bind_scroll_event()

        return self.top
    
    def bind_scroll_event(self):
        # Bind scroll event to the whole window
        if self.system == 'Windows':
            self.top.bind("<MouseWheel>", self.on_mousewheel)
        else:
            # Linux and MacOS
            self.top.bind("<Button-4>", self.on_mousewheel)
            self.top.bind("<Button-5>", self.on_mousewheel)
            
    def on_mousewheel(self, event):
        if self.canvas:
            delta = -1 * (event.delta // 120) if self.system == 'Windows' else -1 * event.delta
            self.canvas.yview_scroll(int(delta), "units")
            
                
    def update_licks_and_TTC_actual(self, current_trial):
        # Adjust indices for zero-based indexing
        if self.top.winfo_exists():
            row_index = current_trial - 1 

            df = self.controller.data_mgr.stimuli_dataframe
            if row_index - 1 >= 0:
                # side 1 licks update
                self.cell_labels[row_index-1][4].configure(text=df.loc[row_index-1, "Side 1 Licks"])
                # sode 2 licks update
                self.cell_labels[row_index-1][5].configure(text=df.loc[row_index-1, "Side 2 Licks"])
                # ttc actual update
                self.cell_labels[row_index-1][9].configure(text=df.loc[row_index-1, "TTC Actual"])
                
                self.top.update_idletasks()
                self.top.update()

            
    def update_row_color(self, current_trial):
        """Function to update row color """
        # Adjust indices for zero-based indexing
        row_index = current_trial - 1
        if self.top.winfo_exists():
            if current_trial == 1:
                for i in range(10):
                    self.cell_labels[row_index][i].configure(bg='yellow')
            else:
                for i in range(10):
                    self.cell_labels[row_index - 1][i].configure(bg='white')
                for i in range(10):
                    self.cell_labels[row_index][i].configure(bg='yellow')
            self.top.update_idletasks()
            self.top.update()

                
    def configure_tk_obj_grid(self, obj):
        # sets the object passed to expand when the window is expanded  
        obj.grid_rowconfigure(0, weight=1)                            
        obj.grid_columnconfigure(0, weight=1)  
        
    def center_window(self, width, height):
        # Get the screen dimensions
        screen_width = self.top.winfo_screenwidth()
        screen_height = self.top.winfo_screenheight()

        # Calculate the x and y coordinates to center the window
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)

        # Set the window's position
        self.top.geometry(f'{width}x{height}+{x}+{y}')

    def destroy_window(self):
        if self.top:
            self.top.destroy()
        self.top = None
        self.canvas = None
        self.stimuli_frame = None
        self.header_labels = []
        self.cell_labels = []

    def show_stimuli_table(self):
        if self.controller.data_mgr.blocks_generated:

            if not self.top or not self.top.winfo_exists():
                self.create_window(self.controller.main_gui.root)

            if not self.canvas:
                canvas_frame = tk.Frame(self.top)
                canvas_frame.grid(row=0, column=0, sticky="nsew")

                self.canvas = tk.Canvas(canvas_frame)
                scrollbar = tk.Scrollbar(canvas_frame, orient="vertical", command=self.canvas.yview)
                
                self.canvas.configure(yscrollcommand=scrollbar.set)

                self.canvas.grid(row=0, column=0, sticky="nsew")
                scrollbar.grid(row=0, column=1, sticky="ns")

                self.top.grid_rowconfigure(0, weight=1)
                self.top.grid_columnconfigure(0, weight=1)

                self.stimuli_frame = tk.Frame(self.canvas)
                self.canvas.create_window((0, 0), window=self.stimuli_frame, anchor="nw")

            # Populate the stimuli_frame with schedule
            self.populate_stimuli_table()

            self.stimuli_frame.update_idletasks()
            self.canvas.config(scrollregion=self.canvas.bbox("all"))

            # Calculate the width for the canvas and scrollbar
            canvas_width = self.stimuli_frame.winfo_reqwidth()
            scrollbar_width = scrollbar.winfo_width()
            total_width = canvas_width + scrollbar_width

            # Use height required for the frame unlesss its greater than 500 px, then just use 500px 
            canvas_height = self.stimuli_frame.winfo_reqheight()
            
            if canvas_height <= 500:
                height = canvas_height + 50 # add 50 for some padding
            else: 
                height = 500

            # Adjust the canvas size 
            self.canvas.config(width=canvas_width, height=height)

            # Now, center the window 
            self.center_window(total_width, height)
        else:
            self.controller.main_gui.display_error(
                "Blocks not Generated",
                "Please generate blocks before starting the program.",
            )
        if self.controller.running:
            self.update_row_color(self.controller.data_mgr.current_trial_number)    # if the program is running, then highlight the current trial row 

    def populate_stimuli_table(self):
        df = self.controller.data_mgr.stimuli_dataframe
        self.header_labels = []
        self.cell_labels = []

        # Create labels for the column headers
        for j, col in enumerate(df.columns):
            header_label = tk.Label(self.stimuli_frame, text=col, bg='light blue', fg='black', font=('Helvetica', 10, 'bold'), highlightthickness=2, highlightbackground='dark blue')
            header_label.grid(row=0, column=j, sticky='nsew', padx=5, pady=2.5)
            self.header_labels.append(header_label)

        total_columns = len(df.columns)  # Get the total number of columns for spanning the separator
        current_row = 1  # Start at 1 to account for the header row

        # Create cells for each row of data
        for i, row in enumerate(df.itertuples(index=False), start=1):
            row_labels = []
            for j, value in enumerate(row):
                cell_label = tk.Label(self.stimuli_frame, text=value, bg='white', fg='black', font=('Helvetica', 10), highlightthickness=1, highlightbackground='black')
                cell_label.grid(row=current_row, column=j, sticky='nsew', padx=5, pady=2.5)
                row_labels.append(cell_label)
            self.cell_labels.append(row_labels)
            current_row += 1  # Move to the next row
            
            # Insert a horizontal line below every two rows
            if i % (self.controller.data_mgr.num_stimuli.get() / 2) == 0:
                separator_frame = tk.Frame(self.stimuli_frame, height=2, bg='black')
                separator_frame.grid(row=current_row, column=0, columnspan=total_columns, sticky='ew', padx=5)
                self.stimuli_frame.grid_rowconfigure(current_row, minsize=2)
                current_row += 1  # Increment the current row to account for the separator

        # Make sure the last separator is not placed outside the data rows
        if len(df) % 2 == 0:
            self.stimuli_frame.grid_rowconfigure(current_row-1, minsize=0)


