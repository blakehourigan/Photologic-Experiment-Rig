import platform
import tkinter as tk
from tkinter import PhotoImage, messagebox, ttk
import time


class MainGUI:
    def __init__(self, controller) -> None:
        self.controller = controller
        self.setup_window()

    def setup_gui(self) -> None:
        self.setup_grid()
        self.display_timers()
        self.entry_widgets()
        self.display_main_control_buttons()
        self.lower_control_buttons()
        self.create_frame()
        self.create_status_widget()
        self.update_size()

    def setup_window(self) -> None:
        # Set the initial size of the window
        self.root = tk.Tk()
        self.root.minsize(800, 600)  # Set minimum window size to 800x600 pixels
        self.root.title("Samuelsen Lab Photologic Rig")
        self.root.bind(
            "<Control-w>", lambda e: self.root.destroy()
        )  # Close the window when the user presses ctl + w
        icon_path = self.controller.config.get_window_icon_path()
        self.set_program_icon(icon_path)

    def update_size(self) -> None:
        """update the size of the window to fit the contents dynamically based on display size."""
        self.root.update_idletasks()  # Ensure all widgets are updated
        screen_width = self.root.winfo_screenwidth()  # Get screen width
        screen_height = self.root.winfo_screenheight()  # Get screen height

        # Calculate desired size as a fraction of screen size for demonstration
        desired_width = int(screen_width * 0.8)  # 80% of the screen width
        desired_height = int(screen_height * 0.8)  # 80% of the screen height

        # Center the window on the screen
        x_position = (screen_width - desired_width) // 2
        y_position = (screen_height - desired_height) // 2

        # Apply the new geometry
        self.root.geometry(
            "{}x{}+{}+{}".format(desired_width, desired_height, x_position, y_position)
        )

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
            self.root.grid_columnconfigure(i, weight=1)

    def create_timer(self, parent, timer_name, default_text, row, column):
        frame = tk.Frame(parent)
        frame.grid(row=row, column=column, padx=10, pady=5, sticky="nsew")

        label = tk.Label(frame, text=timer_name, bg="light blue", font=("Helvetica", 24))
        label.grid(row=0, column=0)

        time_label = tk.Label(frame, text=default_text, bg="light blue", font=("Helvetica", 24))
        time_label.grid(row=0, column=1) 

        # No need to configure row weight since all widgets are in the same row
        return frame, label, time_label

    def display_timers(self) -> None:
        self.timers_frame = tk.Frame(self.root)
        self.timers_frame.grid(row=1, column=0, sticky="nsew", columnspan=4)
        for i in range(2):
            self.timers_frame.grid_columnconfigure(i, weight=1)
            
        self.main_timer_frame, _, self.main_timer_text = self.create_timer(self.timers_frame, "Time Elapsed:", "0.000s", 0,0)
        self.state_timer_frame, _, self.state_timer_text = self.create_timer(self.timers_frame, "State Time:", "0.000s", 1,0)
            
        
        # self.timers_frame = tk.Frame(self.root)
        # self.timers_frame.grid(row=1, column=0, padx=5, sticky="ew")

        # self.main_timer_frame = tk.Frame(self.timers_frame)
        # self.main_timer_frame.grid(row=0)

        # self.time_label_header = tk.Label(
        #     self.main_timer_frame,
        #     text="Elapsed Time:",
        #     bg="light blue",
        #     font=("Helvetica", 24),
        # )

        # self.time_label = tk.Label(
        #     self.main_timer_frame, text="0.000s", bg="light blue", font=("Helvetica", 24)
        # )

        # self.time_label_header.grid(row=0, column=0)
        # self.time_label.grid(row=0, column=1, sticky='ew')

        # self.state_timer_frame = tk.Frame(self.timers_frame)
        # self.state_timer_frame.grid(
        #     row=1, column=0, pady=10, sticky="ew"
        # )
        # self.state_time_label_header = tk.Label(
        #     self.state_timer_frame,
        #     text=(self.controller.state) + ':',
        #     bg="light blue",
        #     font=("Helvetica", 24),
        # )
        # self.state_time_label_header.grid(row=0)
        
        # self.state_time_label = tk.Label(
        #     self.state_timer_frame,
        #     text="0.000s",
        #     bg="light blue",
        #     font=("Helvetica", 24),
        # )
        # self.state_time_label.grid(row=0, column=1)

        # # plus/minus label for intervals
        # self.plus_minus_times_label_frame = tk.Frame(self.root, width=600, height=50)
        # self.plus_minus_times_label_frame.grid(
        #     row=8, column=0, pady=10, padx=10, sticky="ew", columnspan=3
        # )
        # self.plus_minus_times_label = tk.Label(
        #     self.plus_minus_times_label_frame,
        #     text="+/- (All times in ms)",
        #     bg="light blue",
        #     font=("Helvetica", 24),
        # )
        # self.plus_minus_times_label.pack(fill="x")

        # # Label for # stimuli
        # self.num_stimuli_label_frame = tk.Frame(self.root)
        # self.num_stimuli_label_frame.grid(
        #     row=8, column=3, pady=10, padx=10, sticky="nsew"
        # )
        # self.num_stimuli_label = tk.Label(
        #     self.num_stimuli_label_frame,
        #     text="# of Stimuli",
        #     bg="light blue",
        #     font=("Helvetica", 24),
        # )
        # self.num_stimuli_label.pack()


    def create_labeled_entry(self, parent, label_text, text_var, row, column):
        frame = tk.Frame(parent)
        frame.grid(row=row, column=column, padx=5, sticky="nsew")

        label = tk.Label(frame, text=label_text, bg="light blue", font=("Helvetica", 24))
        label.grid(row=0, pady=10)

        entry = tk.Entry(frame, textvariable=text_var, font=("Helvetica", 24))
        entry.grid(row=1, sticky="nsew")

        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=1)
        return frame, label, entry

    def entry_widgets(self) -> None:
        self.entry_widgets_frame = tk.Frame(self.root)
        self.entry_widgets_frame.grid(row=4, column=0, sticky="nsew", columnspan=4)
        for i in range(4):
            self.entry_widgets_frame.grid_columnconfigure(i, weight=1)

        # Simplify the creation of labeled entries
        self.ITI_Interval_Frame, _, _ = self.create_labeled_entry(self.entry_widgets_frame, "Initial Interval", self.controller.data_mgr.interval_vars["ITI_var"], 0, 0)
        self.TTC_Interval_Frame, _, _ = self.create_labeled_entry(self.entry_widgets_frame, "Time to Contact", self.controller.data_mgr.interval_vars["TTC_var"], 0, 1)
        self.Sample_Interval_Frame, _, _ = self.create_labeled_entry(self.entry_widgets_frame, "Time to Sample", self.controller.data_mgr.interval_vars["sample_var"], 0, 2)
        self.num_trial_blocks_frame, _, _ = self.create_labeled_entry(self.entry_widgets_frame, "Trial Blocks", self.controller.data_mgr.num_trial_blocks, 0, 3)

        # Similarly for random plus/minus intervals and the number of stimuli
        self.ITI_Random_Interval_frame, _, _ = self.create_labeled_entry(self.entry_widgets_frame, "+/- ITI", self.controller.data_mgr.interval_vars["ITI_random_entry"], 1, 0)
        self.TTC_Random_Interval_frame, _, _ = self.create_labeled_entry(self.entry_widgets_frame, "+/- TTC", self.controller.data_mgr.interval_vars["TTC_random_entry"], 1, 1)
        self.Sample_Interval_Random_Frame, _, _ = self.create_labeled_entry(self.entry_widgets_frame, "+/- Sample", self.controller.data_mgr.interval_vars["sample_random_entry"], 1, 2)
        self.num_stimuli_frame, _, _ = self.create_labeled_entry(self.entry_widgets_frame, "Number of Stimuli", self.controller.data_mgr.num_stimuli, 1, 3)

    def create_button(self, parent, button_text, command, bg, row, column):
        frame = tk.Frame(parent)
        frame.grid(row=row, column=column, padx=5, sticky="nsew")

        button = tk.Button(frame, text=button_text, command=command, bg=bg, font=("Helvetica", 24))
        button.grid(row=0, pady=10)

        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=1)
        return frame, button

    def display_main_control_buttons(self) -> None:
        self.main_control_button_frame = tk.Frame(self.root)
        self.main_control_button_frame.grid(row=0, sticky='nsew')
        self.main_control_button_frame.grid_rowconfigure(0, weight=1)
        
        for i in range(2):
            self.main_control_button_frame.grid_columnconfigure(i, weight=1)
            
        self.start_button_frame, _ = self.create_button(self.main_control_button_frame, "Start", self.controller.start_button_handler, "green", 0, 0)

        self.reset_button_frame, _ = self.create_button(self.main_control_button_frame, "Reset", self.controller.start_button_handler, "grey", 0, 2)
 
    def lower_control_buttons(self):
        self.lower_control_buttons_frame = tk.Frame(self.root)
        self.lower_control_buttons_frame.grid(row=6, sticky='nsew')
        self.lower_control_buttons_frame.grid_rowconfigure(0, weight=1)

        # Button to open the stimuli window
        self.test_valves_button_frame, _ = self.create_button(self.lower_control_buttons_frame, "Test Valves", lambda: self.controller.test_valves(), "grey", 0,0)
        self.exp_ctrl_button_frame = self.create_button(self.lower_control_buttons_frame, "Experiment CTL", lambda: self.controller.experiment_ctl_wind.show_window(self.root), "grey", 1, 0)
        self.lick_window_button_frame = self.create_button(self.lower_control_buttons_frame, "Lick Data", self.controller.licks_window.show_window, "grey", 1, 1)
        self.data_window_button_frame = self.create_button(self.lower_control_buttons_frame, "View Data", self.controller.data_window.show_window, "grey", 1, 2)
        self.save_data_button_frame = self.create_button(self.lower_control_buttons_frame, "Save Data", self.controller.data_mgr.save_data_to_xlsx, "grey", 1, 3)
        
        
    def create_frame(self) -> None:
        # Create a frame to contain the scrolled text widget and place it in the grid
        self.frame = tk.Frame(self.root)
        self.frame.grid(row=3, column=0, pady=10, padx=10, sticky="nsew", columnspan=4)

        # Configure the frame's column and row to expand as the window resizes
        self.frame.grid_columnconfigure(0, weight=1)
        self.frame.grid_rowconfigure(0, weight=1)

    def create_status_widget(self):
        self.status_frame = tk.Frame(self.root)
        self.status_frame.grid(
            row=3, column=0, pady=5, padx=10, sticky="nsew", columnspan=2
        )
        self.status_frame.grid_columnconfigure(0, weight=1)

        self.stimuli_frame = tk.Frame(self.status_frame)
        self.stimuli_frame.grid(
            row=0, column=0, pady=10, padx=10, sticky="nsew", columnspan=4
        )
        self.stimuli_frame.grid_columnconfigure(0, weight=1)

        # Create labels for displaying status information in status_frame
        self.status_label = tk.Label(
            self.status_frame,
            text="Status: Idle",
            font=("Helvetica", 24),
            bg="light blue",
        )
        self.status_label.grid(row=0, column=0)

        self.detail_label = tk.Label(
            self.status_frame,
            text="0 / 0 Trials Completed",
            font=("Helvetica", 20),
            bg="light blue",
        )
        self.detail_label.grid(row=1, column=0)

        # Create a progress bar in status_frame
        self.progress = ttk.Progressbar(
            self.status_frame, orient="horizontal", length=500, mode="determinate"
        )
        self.progress.grid(row=2, column=0, pady=10)
        self.progress["value"] = 0  # Set initial progress value

        # Configure the frames to expand with the window
        self.status_frame.grid_rowconfigure([0, 1, 2], weight=1)

    def update_progress_bar(self):
        print("do something here")

    # Define the method for appending data to the scrolled text widget
    def append_data(self, data):  # this is gonna be deleted soon
        self.data_text.insert(tk.END, data)
        # Scroll the scrolled text widget to the end of the data
        self.data_text.see(tk.END)

    def display_error(self, error, message):
        messagebox.showinfo(error, message)

    def update_clock_label(self) -> None:
        # total elapsed time is current minus program start time
        elapsed_time = time.time() - self.controller.data_mgr.start_time

        # update the main screen label and set the number of decimal points to 3
        self.main_timer_text.configure(text="{:.3f}s".format(elapsed_time))

        # state elapsed time is current time minus the time we entered the state
        state_elapsed_time = time.time() - self.controller.data_mgr.state_start_time

        # update the main screen label and set the number of decimal points to 3
        self.state_timer_text.configure(text="{:.3f}s".format(state_elapsed_time))

        # Call this method again after 100 ms
        self.update_clock_id = self.root.after(50, lambda: self.update_clock_label())
        self.controller.after_ids.append(self.update_clock_id)
