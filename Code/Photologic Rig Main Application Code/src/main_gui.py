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
        self.display_status_widget()
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
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

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
        for i in range(4):
            self.root.grid_rowconfigure(i, weight=1)

        # Configure all columns to have equal weight
        self.root.grid_columnconfigure(0, weight=1)

    def create_button(self, parent, button_text, command, bg, row, column):
        frame = tk.Frame(parent, highlightthickness=1, highlightbackground="black")
        frame.grid(row=row, column=column, padx=5, pady=5, sticky="nsew")

        button = tk.Button(
            frame, text=button_text, command=command, bg=bg, font=("Helvetica", 24)
        )
        button.grid(row=0, sticky="nsew", ipadx=10, ipady=10)

        frame.grid_columnconfigure(0, weight=1)
        return frame, button

    def create_status_frame(self, parent, row, column, sticky):
        """
        Helper function to create and return a frame with standard configuration
        and custom grid placement options.
        """
        frame = tk.Frame(parent, highlightthickness=1, highlightbackground="black")
        frame.grid(row=row, column=column, padx=5, pady=5, sticky=sticky)
        frame.grid_columnconfigure(0, weight=1)
        return frame

    def create_labeled_entry(
        self,
        parent: tk.Frame,
        label_text: str,
        text_var: tk.StringVar,
        row: int,
        column: int,
    ) -> tuple[tk.Frame, tk.Label, tk.Entry]:
        frame = tk.Frame(parent)
        frame.grid(row=row, column=column, padx=5, sticky="nsew")

        label = tk.Label(
            frame,
            text=label_text,
            bg="light blue",
            font=("Helvetica", 24),
            highlightthickness=1,
            highlightbackground="dark blue",
        )
        label.grid(row=0, pady=10)

        entry = tk.Entry(
            frame,
            textvariable=text_var,
            font=("Helvetica", 24),
            highlightthickness=1,
            highlightbackground="black",
        )
        entry.grid(row=1, sticky="nsew")

        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=1)
        return frame, label, entry

    def display_main_control_buttons(self) -> None:
        # setup master frame for the main control buttons on row zero in main frame
        self.main_control_button_frame = tk.Frame(
            self.root, highlightthickness=2, highlightbackground="black"
        )
        self.main_control_button_frame.grid(row=0, column=0, pady=5, sticky="nsew")
        self.main_control_button_frame.grid_rowconfigure(0, weight=0)
        for i in range(2):
            self.main_control_button_frame.grid_columnconfigure(i, weight=1)

        self.start_button_frame, self.start_button = self.create_button(
            self.main_control_button_frame,
            "Start",
            self.controller.start_button_handler,
            "green",
            0,
            0,
        )

        self.reset_button_frame, _ = self.create_button(
            self.main_control_button_frame,
            "Reset",
            self.controller.reset_button_handler,
            "grey",
            0,
            1,
        )

    def create_timer(self, parent, timer_name, default_text, row, column):
        frame = tk.Frame(parent, highlightthickness=1, highlightbackground="dark blue")
        frame.grid(
            row=row,
            column=column,
            padx=10,
            pady=5,
            sticky="nsw",
        )

        label = tk.Label(
            frame, text=timer_name, bg="light blue", font=("Helvetica", 24)
        )
        label.grid(row=0, column=0)

        time_label = tk.Label(
            frame, text=default_text, bg="light blue", font=("Helvetica", 24)
        )
        time_label.grid(row=0, column=1)

        return frame, label, time_label

    def display_timers(self) -> None:
        self.timers_frame = tk.Frame(
            self.root, highlightthickness=2, highlightbackground="Black"
        )
        self.timers_frame.grid(row=1, column=0, sticky="nsew")
        for i in range(2):
            self.timers_frame.grid_columnconfigure(i, weight=1)

        self.main_timer_frame, _, self.main_timer_text = self.create_timer(
            self.timers_frame, "Time Elapsed:", "0.0s", 0, 0
        )
        self.main_timer_min_sec_text = tk.Label(
            self.main_timer_frame, text="", bg="light blue", font=("Helvetica", 24)
        )
        self.main_timer_min_sec_text.grid(row=0, column=2)

        self.maximum_total_time_frame, _, self.maximum_total_time = self.create_timer(
            self.timers_frame, "Maximum Total Time:", "0 Minutes, 0 S", 0, 1
        )
        self.maximum_total_time_frame.grid(sticky="e")

        self.state_timer_frame, _, self.state_timer_text = self.create_timer(
            self.timers_frame, "State Time:", "0.0s", 1, 0
        )
        self.full_state_time_text = tk.Label(
            self.state_timer_frame,
            text="/ 0.0s",
            bg="light blue",
            font=("Helvetica", 24),
        )
        self.full_state_time_text.grid(row=0, column=2)

    def display_status_widget(self):
        # Create main status frame
        self.status_frame = tk.Frame(
            self.root, highlightthickness=2, highlightbackground="black"
        )
        self.status_frame.grid(row=2, column=0, pady=5, sticky="nsew")
        self.status_frame.grid_rowconfigure(0, weight=1)

        for i in range(2):
            self.status_frame.grid_columnconfigure(i, weight=1)

        # Create sub-frames within the main status frame
        self.program_status_statistic_frame = self.create_status_frame(
            self.status_frame, row=0, column=0, sticky="nsew"
        )
        self.program_status_statistic_frame.grid_rowconfigure(0, weight=1)

        self.stimuli_information_frame = self.create_status_frame(
            self.status_frame, row=0, column=1, sticky="nsew"
        )
        self.stimuli_information_frame.grid_rowconfigure(0, weight=1)

        # Create labels and progress bar within the program_status_statistic_frame
        self.status_label = tk.Label(
            self.program_status_statistic_frame,
            text="Status: Idle",
            font=("Helvetica", 24),
            bg="light blue",
            highlightthickness=1,
            highlightbackground="dark blue",
        )
        self.status_label.grid(row=0, column=0)

        self.trials_completed_label = tk.Label(
            self.program_status_statistic_frame,
            text="0 / 0 Trials Completed",
            font=("Helvetica", 20),
            bg="light blue",
            highlightthickness=1,
            highlightbackground="dark blue",
        )
        self.trials_completed_label.grid(row=1, column=0)

        self.progress = ttk.Progressbar(
            self.program_status_statistic_frame,
            orient="horizontal",
            length=300,
            mode="determinate",
            value=0,
        )
        self.progress.grid(row=2, column=0, pady=5)

        self.stimuli_label = tk.Label(
            self.stimuli_information_frame,
            text="Side One | VS | Side Two",
            font=("Helvetica", 24),
            bg="light blue",
            highlightthickness=1,
            highlightbackground="dark blue",
        )
        self.stimuli_label.grid(row=0, column=0, pady=5)

        self.trial_number_label = tk.Label(
            self.stimuli_information_frame,
            text="Trial Number: ",
            font=("Helvetica", 24),
            bg="light blue",
            highlightthickness=1,
            highlightbackground="dark blue",
        )
        self.trial_number_label.grid(row=1, column=0, pady=5)

    def entry_widgets(self) -> None:
        self.entry_widgets_frame = tk.Frame(
            self.root, highlightthickness=2, highlightbackground="black"
        )
        self.entry_widgets_frame.grid(row=3, column=0, pady=5, sticky="nsew")
        for i in range(4):
            self.entry_widgets_frame.grid_columnconfigure(i, weight=1)

        # Simplify the creation of labeled entries
        self.ITI_Interval_Frame, _, _ = self.create_labeled_entry(
            self.entry_widgets_frame,
            "ITI Time",
            self.controller.data_mgr.interval_vars["ITI_var"],
            0,
            0,
        )
        self.TTC_Interval_Frame, _, _ = self.create_labeled_entry(
            self.entry_widgets_frame,
            "TTC Time",
            self.controller.data_mgr.interval_vars["TTC_var"],
            0,
            1,
        )
        self.Sample_Interval_Frame, _, _ = self.create_labeled_entry(
            self.entry_widgets_frame,
            "Sample Time",
            self.controller.data_mgr.interval_vars["sample_var"],
            0,
            2,
        )
        self.num_trial_blocks_frame, _, _ = self.create_labeled_entry(
            self.entry_widgets_frame,
            "# Trial Blocks",
            self.controller.data_mgr.num_trial_blocks,
            0,
            3,
        )

        # Similarly for random plus/minus intervals and the number of stimuli
        self.ITI_Random_Interval_frame, _, _ = self.create_labeled_entry(
            self.entry_widgets_frame,
            "+/- ITI",
            self.controller.data_mgr.interval_vars["ITI_random_entry"],
            1,
            0,
        )
        self.TTC_Random_Interval_frame, _, _ = self.create_labeled_entry(
            self.entry_widgets_frame,
            "+/- TTC",
            self.controller.data_mgr.interval_vars["TTC_random_entry"],
            1,
            1,
        )
        self.Sample_Interval_Random_Frame, _, _ = self.create_labeled_entry(
            self.entry_widgets_frame,
            "+/- Sample",
            self.controller.data_mgr.interval_vars["sample_random_entry"],
            1,
            2,
        )
        self.num_stimuli_frame, _, _ = self.create_labeled_entry(
            self.entry_widgets_frame,
            "# Stimuli",
            self.controller.data_mgr.num_stimuli,
            1,
            3,
        )

    def lower_control_buttons(self):
        # setup the master frame that will hold the lower buttons
        self.lower_control_buttons_frame = tk.Frame(
            self.root, highlightthickness=2, highlightbackground="black"
        )
        self.lower_control_buttons_frame.grid(row=4, sticky="nsew")
        self.lower_control_buttons_frame.grid_rowconfigure(0, weight=0)
        for i in range(4):
            self.lower_control_buttons_frame.grid_columnconfigure(i, weight=1)

        # Create a new frame for each new button, and store the button inside of that frame
        self.test_valves_button_frame, _ = self.create_button(
            self.lower_control_buttons_frame,
            "Test Valves",
            lambda: self.controller.valve_testing_window.show_window(),
            "grey",
            0,
            0,
        )
        self.valve_control_button_frame, _ = self.create_button(
            self.lower_control_buttons_frame,
            "Valve Control",
            lambda: self.controller.open_valve_control_window(),
            "grey",
            0,
            1,
        )
        self.program_schedule_button_frame, _ = self.create_button(
            self.lower_control_buttons_frame,
            "Program Schedule",
            lambda: self.controller.program_schedule_window.show_stimuli_table(),
            "grey",
            0,
            2,
        )
        self.exp_ctrl_button_frame = self.create_button(
            self.lower_control_buttons_frame,
            "Valves / Stimuli",
            lambda: self.controller.experiment_ctl_wind.show_window(self.root),
            "grey",
            1,
            0,
        )
        self.lick_window_button_frame = self.create_button(
            self.lower_control_buttons_frame,
            "Lick Data",
            self.controller.licks_window.show_window,
            "grey",
            1,
            1,
        )
        self.data_window_button_frame = self.create_button(
            self.lower_control_buttons_frame,
            "Rasterized Data",
            self.controller.data_window.show_window,
            "grey",
            1,
            2,
        )
        self.save_data_button_frame = self.create_button(
            self.lower_control_buttons_frame,
            "Save Data",
            self.controller.data_mgr.save_data_to_xlsx,
            "grey",
            1,
            3,
        )

    def display_error(self, error, message):
        messagebox.showinfo(error, message)

    def convert_seconds_to_minutes_seconds(self, total_seconds):
        """Converts a given number of seconds to minutes and seconds."""
        minutes = total_seconds // 60  # Integer division to get whole minutes
        seconds = total_seconds % 60  # Modulo to get remaining seconds

        return minutes, seconds

    def update_clock_label(self) -> None:
        # Calculate elapsed times
        elapsed_time = time.time() - self.controller.data_mgr.start_time
        state_elapsed_time = time.time() - self.controller.data_mgr.state_start_time

        min, sec = self.convert_seconds_to_minutes_seconds(elapsed_time)

        # Update the main screen label and set the number of decimal points to 1
        self.main_timer_text.configure(text="{:.1f}s".format(elapsed_time))
        self.main_timer_min_sec_text.configure(
            text="| {:.0f} Minutes, {:.1f} S".format(min, sec)
        )

        # Update the state screen label and set the number of decimal points to 1
        self.state_timer_text.configure(text="{:.1f}s".format(state_elapsed_time))

        # Schedule the next call of this method
        clock_id = self.root.after(100, self.update_clock_label)
        self.controller.after_ids.append(clock_id)

    def update_max_time(self, minutes, seconds) -> None:
        self.maximum_total_time.configure(
            text="{:.0f} Minutes, {:.1f} S".format(minutes, seconds)
        )

    def update_on_new_trial(self, side_1_stimulus, side_2_stimulus) -> None:
        trial_number = self.controller.data_mgr.current_trial_number

        self.trials_completed_label.configure(
            text="{} / {} Trials Completed".format(
                trial_number, self.controller.data_mgr.num_trials.get()
            )
        )
        self.stimuli_label.configure(
            text="Side One: {} | VS | Side Two: {}".format(
                side_1_stimulus, side_2_stimulus
            )
        )

        self.trial_number_label.configure(text="Trial Number: {}".format(trial_number))

        self.update_progress_bar()

        self.controller.program_schedule_window.update_row_color(trial_number)
        self.controller.program_schedule_window.update_licks_and_TTC_actual(
            trial_number
        )

    def update_progress_bar(self, reset=False):
        if reset:
            self.progress["value"] = 0
        else:
            self.progress["value"] = (
                self.controller.data_mgr.current_trial_number
                / self.controller.data_mgr.num_trials.get()
            ) * 100  # Set the new value for the progress
        self.progress.update_idletasks()  # Update the progress bar display

    def update_on_state_change(self, state_time_value, state) -> None:
        self.update_full_state_time(state_time_value)
        self.update_status(state)

    def update_status(self, state) -> None:
        self.status_label.configure(text="Status: {}".format(state))

    def clear_state_time(self) -> None:
        self.full_state_time_text.configure(
            text="/ {:.1f}s".format(0)
        )

    def update_full_state_time(self, state_time_value) -> None:
        full_state_time = state_time_value

        self.full_state_time_text.configure(
            text="/ {:.1f}s".format(full_state_time / 1000.0)
        )

    def update_on_stop(self) -> None:
        # set the state timer label
        self.state_timer_text.configure(text="0.0s")

        # Turn the program execution button back to the green start button
        self.start_button.configure(text="Start", bg="green")

        self.update_on_state_change(0, "Idle")

    def update_on_reset(self) -> None:
        elapsed_time, state_elapsed_time = 0, 0  # reset the elapsed time variables
        self.main_timer_text.configure(text="{:.1f}s".format(elapsed_time))
        self.state_timer_text.configure(text="{:.3f}s".format(state_elapsed_time))

        self.main_timer_min_sec_text.configure(text="| 0 Minutes, 0 S")

        self.maximum_total_time.configure(text="0 Minutes, 0 S")
        self.trials_completed_label.configure(text="0 / 0 Trials Completed")
        self.stimuli_label.configure(text="Side One | VS | Side Two")
        self.trial_number_label.configure(text="Trial Number: 0")
        self.update_progress_bar(True)

        self.update_on_state_change(0, "Idle")
        
    def on_close(self):
        # Cancel all after tasks
        for after_id in self.controller.after_ids:
            self.root.after_cancel(after_id)

        # Stop the listener thread in AduinoManager
        self.controller.arduino_mgr.stop()

        self.root.destroy()
        self.root.quit()
