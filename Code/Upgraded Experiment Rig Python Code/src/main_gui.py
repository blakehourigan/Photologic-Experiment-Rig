import platform
import tkinter as tk
from tkinter import PhotoImage, messagebox, scrolledtext
import time

class MainGUI:
    def __init__(self, controller) -> None:
        self.controller = controller
        self.setup_window()

    def setup_gui(self) -> None:
        self.setup_grid()
        self.display_labels()
        self.display_user_entry_widgets()
        self.display_buttons()
        self.create_frame()
        self.create_text_widget()
        self.update_size()

    def setup_window(self) -> None:
        # Set the initial size of the window
        self.root = tk.Tk()
        self.root.title("Samuelsen Lab Photologic Rig")
        self.root.bind("<Control-w>", lambda e: self.root.destroy())  # Close the window when the user presses ctl + w
        icon_path = self.controller.config.get_window_icon_path()
        self.set_program_icon(icon_path)

    def update_size(self) -> None:
        """update the size of the window to fit the contents"""
        self.root.update_idletasks()
        width = self.root.winfo_reqwidth()
        height = self.root.winfo_reqheight()
        self.root.geometry("{}x{}".format(width, height))

    def set_program_icon(self, icon_path) -> None:
        os_name = platform.system()

        if os_name == "Windows":
            self.root.iconbitmap(icon_path)
        else:
            # Use .png or .gif file directly
            photo = PhotoImage(file=icon_path)
            self.root.tk.call("wm", "iconphoto", self.root._w, photo)  # type: ignore

    def setup_grid(self) -> None:
        # Configure the GUI grid expand settings
        for i in range(12):
            self.root.grid_rowconfigure(i, weight=1)
        # The first column is also configured to expand
        # Configure all columns to have equal weight
        for i in range(4):
            self.root.columnconfigure(i, weight=1)

    def display_labels(self) -> None:
        # Label headers
        self.time_label_header_frame = tk.Frame(self.root)
        self.time_label_header_frame.grid(row=0, column=0, pady=10, padx=10, sticky="e")
        self.time_label_header = tk.Label(
            self.time_label_header_frame,
            text="Elapsed Time",
            bg="light blue",
            font=("Helvetica", 24),
        )
        self.time_label_header.pack()

        self.state_time_label_header_frame = tk.Frame(self.root)
        self.state_time_label_header_frame.grid(
            row=0, column=2, pady=10, padx=10, sticky="e"
        )
        self.state_time_label_header = tk.Label(
            self.state_time_label_header_frame,
            text=(self.controller.state),
            bg="light blue",
            font=("Helvetica", 24),
        )
        self.state_time_label_header.pack()

        # Timer labels
        self.time_label_frame = tk.Frame(self.root)
        self.time_label_frame.grid(row=0, column=1, pady=10, padx=10, sticky="w")
        self.time_label = tk.Label(
            self.time_label_frame, text="", bg="light blue", font=("Helvetica", 24)
        )
        self.time_label.pack()

        self.state_time_label_frame = tk.Frame(self.root)
        self.state_time_label_frame.grid(row=0, column=3, pady=10, padx=10, sticky="w")
        self.state_time_label = tk.Label(
            self.state_time_label_frame,
            text="",
            bg="light blue",
            font=("Helvetica", 24),
        )
        self.state_time_label.pack()

        # Labels for Interval Entry widgets
        self.interval1_label_frame = tk.Frame(self.root)
        self.interval1_label_frame.grid(
            row=5, column=0, pady=10, padx=10, sticky="nsew"
        )
        self.interval1_label = tk.Label(
            self.interval1_label_frame,
            text="Initial Interval",
            bg="light blue",
            font=("Helvetica", 24),
        )
        self.interval1_label.pack()

        self.interval2_label_frame = tk.Frame(self.root)
        self.interval2_label_frame.grid(
            row=5, column=1, pady=10, padx=10, sticky="nsew"
        )
        self.interval2_label = tk.Label(
            self.interval2_label_frame,
            text="Time to Contact",
            bg="light blue",
            font=("Helvetica", 24),
        )
        self.interval2_label.pack()

        self.interval3_label_frame = tk.Frame(self.root)
        self.interval3_label_frame.grid(
            row=5, column=2, pady=10, padx=10, sticky="nsew"
        )
        self.interval3_label = tk.Label(
            self.interval3_label_frame,
            text="Time to Sample",
            bg="light blue",
            font=("Helvetica", 24),
        )
        self.interval3_label.pack()

        # plus/minus label for intervals
        self.plus_minus_times_label_frame = tk.Frame(self.root, width=600, height=50)
        self.plus_minus_times_label_frame.grid(
            row=7, column=0, pady=10, padx=10, sticky="ew", columnspan=3
        )
        self.plus_minus_times_label = tk.Label(
            self.plus_minus_times_label_frame,
            text="+/- (All times in ms)",
            bg="light blue",
            font=("Helvetica", 24),
        )
        self.plus_minus_times_label.pack(fill="x")

        # Label for # of trials
        self.num_trials_label_frame = tk.Frame(self.root)
        self.num_trials_label_frame.grid(
            row=5, column=3, pady=10, padx=10, sticky="nsew"
        )
        self.num_trials_label = tk.Label(
            self.num_trials_label_frame,
            text="Trial Blocks",
            bg="light blue",
            font=("Helvetica", 24),
        )
        self.num_trials_label.pack()

        # Label for # stimuli
        self.num_stimuli_label_frame = tk.Frame(self.root)
        self.num_stimuli_label_frame.grid(
            row=7, column=3, pady=10, padx=10, sticky="nsew"
        )
        self.num_stimuli_label = tk.Label(
            self.num_stimuli_label_frame,
            text="# of Stimuli",
            bg="light blue",
            font=("Helvetica", 24),
        )
        self.num_stimuli_label.pack()

        # Program information label
        self.program_label_frame = tk.Frame(self.root)
        self.program_label_frame.grid(
            row=2, column=0, pady=10, padx=10, sticky="nsew", columnspan=4
        )
        self.program_label = tk.Label(
            self.program_label_frame,
            text="Program Information",
            bg="light blue",
            font=("Helvetica", 24),
        )
        self.program_label.pack()

    def display_user_entry_widgets(self) -> None:
        # Add Data Entry widgets for intervals
        self.interval1_frame = tk.Frame(self.root, width=200, height=50)
        self.interval1_frame.grid_propagate(False)
        self.interval1_frame.grid(row=6, column=0, pady=10, padx=10, sticky="nsew")
        self.interval1_entry = tk.Entry(
            self.interval1_frame,
            textvariable=self.controller.data_mgr.interval_vars["ITI_var"],
            font=("Helvetica", 24),
        )
        self.interval1_entry.pack(fill="both", expand=True)

        self.interval2_frame = tk.Frame(self.root)
        self.interval2_frame.grid(row=6, column=1, pady=10, padx=10, sticky="nsew")
        self.interval2_entry = tk.Entry(
            self.interval2_frame,
            textvariable=self.controller.data_mgr.interval_vars["TTC_var"],
            font=("Helvetica", 24),
        )
        self.interval2_entry.pack(fill="both", expand=True)

        self.interval3_frame = tk.Frame(self.root)
        self.interval3_frame.grid(row=6, column=2, pady=10, padx=10, sticky="nsew")
        self.interval3_entry = tk.Entry(
            self.interval3_frame,
            textvariable=self.controller.data_mgr.interval_vars["sample_var"],
            font=("Helvetica", 24),
        )
        self.interval3_entry.pack(fill="both", expand=True)

        # Entry for # of trials
        self.num_trial_blocks_frame = tk.Frame(self.root)
        self.num_trial_blocks_frame.grid(
            row=6, column=3, pady=10, padx=10, sticky="nsew"
        )
        self.num_trial_blocks_entry = tk.Entry(
            self.num_trial_blocks_frame,
            textvariable=self.controller.data_mgr.num_trial_blocks,
            font=("Helvetica", 24),
        )
        self.num_trial_blocks_entry.pack(fill="both", expand=True)

        # Entry for # of trials
        self.num_stimuli_frame = tk.Frame(self.root)
        self.num_stimuli_frame.grid(row=9, column=3, pady=10, padx=10, sticky="nsew")
        self.num_stimuli_entry = tk.Entry(
            self.num_stimuli_frame,
            textvariable=self.controller.data_mgr.num_stimuli,
            font=("Helvetica", 24),
        )
        self.num_stimuli_entry.pack(fill="both", expand=True)

        # Add Data Entry widgets for random plus/minus intervals
        self.interval1Rand_frame = tk.Frame(self.root)
        self.interval1Rand_frame.grid(row=9, column=0, pady=10, padx=10, sticky="nsew")
        self.interval1Rand_entry = tk.Entry(
            self.interval1Rand_frame,
            textvariable=self.controller.data_mgr.interval_vars["ITI_random_entry"],
            font=("Helvetica", 24),
        )
        self.interval1Rand_entry.pack(fill="both", expand=True)

        self.interval2Rand_frame = tk.Frame(self.root)
        self.interval2Rand_frame.grid(row=9, column=1, pady=10, padx=10, sticky="nsew")
        self.interval2Rand_entry = tk.Entry(
            self.interval2Rand_frame,
            textvariable=self.controller.data_mgr.interval_vars["TTC_random_entry"],
            font=("Helvetica", 24),
        )
        self.interval2Rand_entry.pack(fill="both", expand=True)

        self.interval3Rand_frame = tk.Frame(self.root)
        self.interval3Rand_frame.grid(row=9, column=2, pady=10, padx=10, sticky="nsew")
        self.interval3Rand_entry = tk.Entry(
            self.interval3Rand_frame,
            textvariable=self.controller.data_mgr.interval_vars["sample_random_entry"],
            font=("Helvetica", 24),
        )
        self.interval3Rand_entry.pack(fill="both", expand=True)

    def display_buttons(self) -> None:
        # Start/stop button
        self.startButton_frame = tk.Frame(self.root, width=200, height=50)
        self.startButton_frame.grid_propagate(False)  # Disables resizing of frame
        self.startButton_frame.grid(
            row=1, column=0, pady=10, padx=10, sticky="nsew", columnspan=2
        )
        self.startButton = tk.Button(
            self.startButton_frame,
            text="Start",
            command=self.controller.start_button_handler,
            bg="green",
            font=("Helvetica", 24),
        )
        self.startButton.pack(fill="both", expand=True)

        # Clear button
        self.clear_button_frame = tk.Frame(self.root, width=200, height=50)
        self.clear_button_frame.grid_propagate(False)  # Disables resizing of frame
        self.clear_button_frame.grid(
            row=1, column=2, pady=10, padx=10, sticky="nsew", columnspan=2
        )
        self.clear_button = tk.Button(
            self.clear_button_frame,
            text="Clear",
            command=self.controller.clear_button_handler,
            bg="grey",
            font=("Helvetica", 24),
        )
        self.clear_button.pack(fill="both", expand=True)

        # Button to open the stimuli window
        self.test_valves_button_frame = tk.Frame(self.root, width=200, height=50)
        self.test_valves_button_frame.grid_propagate(False)  # Disables resizing of frame
        self.test_valves_button_frame.grid(
            row=10, column=0, pady=10, padx=10, sticky="nsew", columnspan=1
        )
        self.test_valves_button = tk.Button(
            self.test_valves_button_frame,
            text="Calibrate Valves",
            command=lambda: self.controller.test_valves(),
            bg="grey",
            font=("Helvetica", 24),
        )
        self.test_valves_button.pack(fill="both", expand=True)


        # Button to open the stimuli window
        self.exp_ctrl_button_frame = tk.Frame(self.root, width=200, height=50)
        self.exp_ctrl_button_frame.grid_propagate(False)  # Disables resizing of frame
        self.exp_ctrl_button_frame.grid(
            row=12, column=0, pady=10, padx=10, sticky="nsew", columnspan=1
        )
        self.experiment_control_button = tk.Button(
            self.exp_ctrl_button_frame,
            text="Experiment CTL",
            command=lambda: self.controller.experiment_ctl_wind.show_window(self.root),
            bg="grey",
            font=("Helvetica", 24),
        )
        self.experiment_control_button.pack(fill="both", expand=True)

        # Lick data button
        self.lick_window_button_frame = tk.Frame(self.root, width=200, height=50)
        self.lick_window_button_frame.grid_propagate(
            False
        )  # Disables resizing of frame
        self.lick_window_button_frame.grid(
            row=12, column=1, pady=10, padx=10, sticky="nsew", columnspan=1
        )
        self.lick_window_button = tk.Button(
            self.lick_window_button_frame,
            text="Lick Data",
            command=self.controller.licks_window.show_window,
            bg="grey",
            font=("Helvetica", 24),
        )
        self.lick_window_button.pack(fill="both", expand=True)

        # Button to open the data window
        self.data_window_button_frame = tk.Frame(self.root, width=200, height=50)
        self.data_window_button_frame.grid_propagate(
            False
        )  # Disables resizing of frame
        self.data_window_button_frame.grid(
            row=12, column=2, pady=10, padx=10, sticky="nsew"
        )
        self.data_window_button = tk.Button(
            self.data_window_button_frame,
            text="View Data",
            command=self.controller.data_window.show_window,
            bg="grey",
            font=("Helvetica", 24),
        )
        self.data_window_button.pack(fill="both", expand=True)

        # Button to save experiment data to excel sheets
        self.save_data_button_frame = tk.Frame(self.root, width=200, height=50)
        self.save_data_button_frame.grid_propagate(False)  # Disables resizing of frame
        self.save_data_button_frame.grid(
            row=12, column=3, pady=10, padx=10, sticky="nsew"
        )
        self.save_data_button = tk.Button(
            self.save_data_button_frame,
            text="Save Data Externally",
            command=self.controller.data_mgr.save_data_to_xlsx,
            bg="grey",
            font=("Helvetica", 24),
        )
        self.save_data_button.pack(fill="both", expand=True)

    def create_frame(self) -> None:
        # Create a frame to contain the scrolled text widget and place it in the grid
        self.frame = tk.Frame(self.root)
        self.frame.grid(row=3, column=0, pady=10, padx=10, sticky="nsew", columnspan=4)

        # Configure the frame's column and row to expand as the window resizes
        self.frame.grid_columnconfigure(0, weight=1)
        self.frame.grid_rowconfigure(0, weight=1)

    def create_text_widget(self):
        # Create a frame to contain the scrolled text widget and place it in the grid
        self.frame = tk.Frame(self.root)
        self.frame.grid(row=3, column=0, pady=10, padx=10, sticky="nsew", columnspan=4)

        # Configure the frame's column and row to expand as the window resizes
        self.frame.grid_columnconfigure(0, weight=1)
        self.frame.grid_rowconfigure(0, weight=1)

        # Create a scrolled text widget for displaying data, place it in the frame, and set it to expand with the frame
        self.data_text = scrolledtext.ScrolledText(
            self.frame, font=("Helvetica", 24), height=10, width=30
        )
        self.data_text.grid(row=0, column=0, sticky="nsew")

    # Define the method for appending data to the scrolled text widget
    def append_data(self, data):
        self.data_text.insert(tk.END, data)
        # Scroll the scrolled text widget to the end of the data
        self.data_text.see(tk.END)

    def display_error(self, error, message):
        messagebox.showinfo(error, message)

    def update_clock_label(self) -> None:
        # total elapsed time is current minus program start time
        elapsed_time = time.time() - self.controller.data_mgr.start_time

        # update the main screen label and set the number of decimal points to 3
        self.time_label.configure(text="{:.3f}s".format(elapsed_time))

        # state elapsed time is current time minus the time we entered the state
        state_elapsed_time = time.time() - self.controller.data_mgr.state_start_time

        # update the main screen label and set the number of decimal points to 3
        self.state_time_label.configure(text="{:.3f}s".format(state_elapsed_time))

        # Call this method again after 100 ms
        self.update_clock_id = self.root.after(50, lambda: self.update_clock_label())
        self.controller.after_ids.append(self.update_clock_id)
