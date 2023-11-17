import platform
import tkinter as tk 
from tkinter import PhotoImage, messagebox, scrolledtext

class MainGUI:
    def __init__(self, master, controller, config, logic) -> None:
        self.master = master
        self.controller = controller
        self.config = config
        self.logic = logic
        
        self.setup_window()
        self.setup_grid()
        self.display_labels()
        self.display_user_entry_widgets()
        self.display_buttons()
        self.create_frame()
        self.create_text_widget()

    def setup_window(self) -> None:
        # Set the initial size of the window
        self.master.geometry(self.config.main_gui_window_size)

        self.master.title("Upgraded Experiment Rig")
        icon_path = self.config.get_window_icon_path() 
        self.set_program_icon(icon_path)

    def set_program_icon(self, icon_path) -> None:
        os_name = platform.system()

        if os_name == 'Windows':
            self.master.iconbitmap(icon_path)
        else:
            # Use .png or .gif file directly
            photo = PhotoImage(file=icon_path)
            self.master.tk.call('wm', 'iconphoto', self.master._w, photo)
            
    def setup_grid(self) -> None:
        # Configure the GUI grid expand settings
        for i in range(8):
            self.master.grid_rowconfigure(i, weight=1 if i == 3 else 0)
        # The first column is also configured to expand
        self.master.grid_columnconfigure(0, weight=1)
            
    def display_labels(self) -> None:
        # Label headers
        self.time_label_header = tk.Label(text="Elapsed Time:", bg="light blue", font=("Helvetica", 24))
        self.time_label_header.grid(row=0, column=0, pady=10, padx=10, sticky='e')

        self.state_time_label_header = tk.Label(text=(self.logic.state), bg="light blue", font=("Helvetica", 24))
        self.state_time_label_header.grid(row=0, column=2, pady=10, padx=10, sticky='e')

        # Timer labels
        self.time_label = tk.Label(text="", bg="light blue", font=("Helvetica", 24))
        self.time_label.grid(row=0, column=1, pady=10, padx=10, sticky='w')

        self.state_time_label = tk.Label(text="", bg="light blue", font=("Helvetica", 24))
        self.state_time_label.grid(row=0, column=3, pady=10, padx=10, sticky='w')

        # Labels for Interval Entry widgets
        self.interval1_label = tk.Label(self.master, text="Initial Interval:", bg="light blue", font=("Helvetica", 24))
        self.interval1_label.grid(row=5, column=0, pady=10, padx=10, sticky='nsew')

        self.interval2_label = tk.Label(self.master, text="Time to Contact:", bg="light blue", font=("Helvetica", 24))
        self.interval2_label.grid(row=5, column=1, pady=10, padx=10, sticky='nsew')

        self.interval3_label = tk.Label(self.master, text="Time to Sample:", bg="light blue", font=("Helvetica", 24))
        self.interval3_label.grid(row=5, column=2, pady=10, padx=10, sticky='nsew')
        
        # Labels for Interval Entry widgets
        self.interval1_label = tk.Label(self.master, text="+/- (All times in ms)", bg="light blue", font=("Helvetica", 24))
        self.interval1_label.grid(row=7, column=0, pady=10, padx=10, sticky='nsew', columnspan=3)

        # Label for # of trials
        self.num_trials_label = tk.Label(self.master, text="Trial Blocks", bg="light blue", font=("Helvetica", 24))
        self.num_trials_label.grid(row=5, column=3, pady=10, padx=10, sticky='nsew')
        
        # Label for # stimuli
        self.num_stimuli_label = tk.Label(self.master, text="# of Stimuli", bg="light blue", font=("Helvetica", 24))
        self.num_stimuli_label.grid(row=7, column=3, pady=10, padx=10, sticky='nsew')
    
        # Program information label
        self.program_label = tk.Label(text="Program Information", bg="light blue", font=("Helvetica", 24))
        self.program_label.grid(row=2, column=0, pady=10, padx=10, sticky='nsew', columnspan=4)
    
    def display_user_entry_widgets(self) -> None:
        # Add Data Entry widgets for intervals
        self.interval1_entry = tk.Entry(self.master, textvariable=self.logic.interval_vars['ITI_var'], font=("Helvetica", 24))
        self.interval1_entry.grid(row=6, column=0, pady=10, padx=10, sticky='nsew')

        self.interval2_entry = tk.Entry(self.master, textvariable=self.logic.interval_vars['TTC_var'], font=("Helvetica", 24))
        self.interval2_entry.grid(row=6, column=1, pady=10, padx=10, sticky='nsew')

        self.interval3_entry = tk.Entry(self.master, textvariable=self.logic.interval_vars['sample_time_var'], font=("Helvetica", 24))
        self.interval3_entry.grid(row=6, column=2, pady=10, padx=10, sticky='nsew')
        
        # Entry for # of trials
        self.num_trial_blocks_entry = tk.Entry(self.master, textvariable=self.logic.num_trial_blocks, font=("Helvetica", 24))
        self.num_trial_blocks_entry.grid(row=6, column=3, pady=10, padx=10, sticky='nsew')
        
        # Entry for # of trials
        self.num_stimuli_entry = tk.Entry(self.master, textvariable=self.logic.num_stimuli, font=("Helvetica", 24))
        self.num_stimuli_entry.grid(row=8, column=3, pady=10, padx=10, sticky='nsew')

        # Add Data Entry widgets for random plus/minus intervals
        self.interval1Rand_entry = tk.Entry(self.master, textvariable=self.logic.interval_vars['ITI_random_entry'], font=("Helvetica", 24))
        self.interval1Rand_entry.grid(row=8, column=0, pady=10, padx=10, sticky='nsew')

        self.interval2Rand_entry = tk.Entry(self.master, textvariable=self.logic.interval_vars['TTC_random_entry'], font=("Helvetica", 24))
        self.interval2Rand_entry.grid(row=8, column=1, pady=10, padx=10, sticky='nsew')

        self.interval3Rand_entry = tk.Entry(self.master, textvariable=self.logic.interval_vars['sample_time_entry'], font=("Helvetica", 24))
        self.interval3Rand_entry.grid(row=8, column=2, pady=10, padx=10, sticky='nsew')
        
    def display_buttons(self) -> None:
        # Start/stop button
        self.startButton = tk.Button(text="Start", command=self.controller.start_button_handler, bg="green", font=("Helvetica", 24))
        self.startButton.grid(row=1, column=0, pady=10, padx=10, sticky='nsew', columnspan=2)

        # Clear screen button
        self.clear_button = tk.Button(text="Clear", command=self.controller.clear_button_handler, bg="grey", font=("Helvetica", 24))
        self.clear_button.grid(row=1, column=2, pady=10, padx=10, sticky='nsew', columnspan=2)
        
        # button to open the stimuli window
        self.experiment_control_button = tk.Button(text="Experiment CTL", command= lambda: self.controller.show_experiment_ctl_window(self.master), bg="grey", font=("Helvetica", 24))
        self.experiment_control_button.grid(row=10, column=0, pady=10, padx=10, sticky='nsew',columnspan=1)
        """
        self.lick_window_button = tk.Button(text="Lick Data", command=self.lick_window, bg="grey", font=("Helvetica", 24))
        self.lick_window_button.grid(row=10, column=1, pady=10, padx=10, sticky='nsew',columnspan=1)

        # button to open the data window
        self.data_window_button = tk.Button(text="View Data", command=self.data_window, bg="grey", font=("Helvetica", 24))
        self.data_window_button.grid(row=10, column=2, pady=10, padx=10, sticky='nsew')

        # button to save expirement data to excel sheets
        self.data_window_button = tk.Button(text="Save Data Externally", command=self.save_data, bg="grey", font=("Helvetica", 24))
        self.data_window_button.grid(row=10, column=3, pady=10, padx=10, sticky='nsew')
        """
    def create_frame(self) -> None:
        # Create a frame to contain the scrolled text widget and place it in the grid
        self.frame = tk.Frame(self.master)
        self.frame.grid(row=3, column=0, pady=10, padx=10, sticky='nsew', columnspan=4)

        # Configure the frame's column and row to expand as the window resizes
        self.frame.grid_columnconfigure(0, weight=1)
        self.frame.grid_rowconfigure(0, weight=1)
        
    def create_text_widget(self):
        # Create a frame to contain the scrolled text widget and place it in the grid
        self.frame = tk.Frame(self.master)
        self.frame.grid(row=3, column=0, pady=10, padx=10, sticky='nsew', columnspan=4)

        # Configure the frame's column and row to expand as the window resizes
        self.frame.grid_columnconfigure(0, weight=1)
        self.frame.grid_rowconfigure(0, weight=1)
        
        # Create a scrolled text widget for displaying data, place it in the frame, and set it to expand with the frame
        self.data_text = scrolledtext.ScrolledText(self.frame, font=("Helvetica", 24), height=10, width=30)
        self.data_text.grid(row=0, column=0, sticky='nsew')
        
    # Define the method for appending data to the scrolled text widget
    def append_data(self, data):
        self.data_text.insert(tk.END, data)
        # Scroll the scrolled text widget to the end of the data
        self.data_text.see(tk.END)
        
    def display_error(self, error, message):
        messagebox.showinfo(error, message)
            