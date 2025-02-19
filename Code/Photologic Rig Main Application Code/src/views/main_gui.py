from tkinter import messagebox, ttk
import tkinter as tk
import time
import logging


# Get the logger from the controller
logger = logging.getLogger()


# using tk.Tk here says that this class is going to be a tkinter app. when we call super().__init__() this actuall creates the tkinter main window
# then we can use it as if it were root - e.g self.title("title") sets the root window title
class MainGUI(tk.Tk):
    def __init__(self, gui_requirements) -> None:
        # init the Tk instance to create a GUI
        super().__init__()
        self.gui_requirements = gui_requirements
        self.setup_window()
        self.setup_gui()

        logger.info("MainGUI initialized.")

    def setup_gui(self) -> None:
        try:
            self.setup_grid()
            # self.display_timers()
            # self.entry_widgets()
            self.display_main_control_buttons()
            # self.lower_control_buttons()
            self.display_status_widget()
            self.update_size()
            logger.info("GUI setup completed.")
        except Exception as e:
            logger.error(f"Error setting up GUI: {e}")
            raise

    def setup_window(self) -> None:
        try:
            self.minsize(800, 600)  # Set minimum window size to 800x600 pixels
            self.title("Samuelsen Lab Photologic Rig")
            self.bind("<Control-w>", lambda e: self.destroy())
            # icon_path = self.controller.experiment_config.get_window_icon_path()

            # GUIUtils.set_program_icon(self.root, icon_path=icon_path)
            self.protocol("WM_DELETE_WINDOW", self.on_close)
            logger.info("Main window setup completed.")
        except Exception as e:
            logger.error(f"Error setting up main window: {e}")
            raise

    def update_size(self) -> None:
        try:
            self.update_idletasks()  # Ensure all widgets are updated
            screen_width = self.winfo_screenwidth()  # Get screen width
            screen_height = self.winfo_screenheight()  # Get screen height

            # Calculate desired size as a fraction of screen size for demonstration
            desired_width = int(screen_width * 0.8)  # 80% of the screen width
            desired_height = int(screen_height * 0.8)  # 80% of the screen height

            # Center the window on the screen
            x_position = (screen_width - desired_width) // 2
            y_position = (screen_height - desired_height) // 2

            # Apply the new geometry
            self.geometry(
                "{}x{}+{}+{}".format(
                    desired_width, desired_height, x_position, y_position
                )
            )
            logger.info("Window size updated.")
        except Exception as e:
            logger.error(f"Error updating window size: {e}")
            raise

    def setup_grid(self) -> None:
        try:
            # Configure the GUI grid expand settings
            for i in range(4):
                self.grid_rowconfigure(i, weight=1)
            # Configure all columns to have equal weight
            self.grid_columnconfigure(0, weight=1)
            logger.info("Grid setup completed.")
        except Exception as e:
            logger.error(f"Error setting up grid: {e}")
            raise

    def create_button(self, parent, button_text, command, bg, row, column):
        try:
            frame = tk.Frame(parent, highlightthickness=1, highlightbackground="black")
            frame.grid(row=row, column=column, padx=5, pady=5, sticky="nsew")

            button = tk.Button(
                frame, text=button_text, command=command, bg=bg, font=("Helvetica", 24)
            )
            button.grid(row=0, sticky="nsew", ipadx=10, ipady=10)

            frame.grid_columnconfigure(0, weight=1)
            logger.debug(f"Button '{button_text}' created.")
            return frame, button
        except Exception as e:
            logger.error(f"Error creating button '{button_text}': {e}")
            raise

    def create_status_frame(self, parent, row, column, sticky):
        try:
            frame = tk.Frame(parent, highlightthickness=1, highlightbackground="black")
            frame.grid(row=row, column=column, padx=5, pady=5, sticky=sticky)
            frame.grid_columnconfigure(0, weight=1)
            logger.debug("Status frame created.")
            return frame
        except Exception as e:
            logger.error(f"Error creating status frame: {e}")
            raise

    def create_labeled_entry(
        self,
        parent: tk.Frame,
        label_text: str,
        text_var: tk.IntVar,
        row: int,
        column: int,
    ) -> tuple[tk.Frame, tk.Label, tk.Entry]:
        try:
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
            logger.debug(f"Labeled entry '{label_text}' created.")
            return frame, label, entry
        except Exception as e:
            logger.error(f"Error creating labeled entry '{label_text}': {e}")
            raise

    def display_main_control_buttons(self) -> None:
        try:
            # main button frame creation and customization
            self.main_control_button_frame = tk.Frame(
                master=self, highlightthickness=2, highlightbackground="black"
            )
            # configured to begin at row 0 of the parent (main app) and sticky to take up all available space
            self.main_control_button_frame.grid(row=0, column=0, pady=5, sticky="nsew")
            self.main_control_button_frame.grid_rowconfigure(0, weight=0)

            self.main_control_button_frame.grid_columnconfigure(0, weight=1)
            self.main_control_button_frame.grid_columnconfigure(1, weight=1)

            self.start_button_frame, self.start_button = self.create_button(
                self.main_control_button_frame,
                "Start",
                self.gui_requirements["start button"],
                "green",
                0,
                0,
            )

            self.reset_button_frame, _ = self.create_button(
                self.main_control_button_frame,
                "Reset",
                self.gui_requirements["reset button"],
                "grey",
                0,
                1,
            )
            logger.info("Main control buttons displayed.")
        except Exception as e:
            logger.error(f"Error displaying main control buttons: {e}")
            raise

    def create_timer(self, parent, timer_name, default_text, row, column):
        try:
            frame = tk.Frame(
                parent, highlightthickness=1, highlightbackground="dark blue"
            )
            frame.grid(row=row, column=column, padx=10, pady=5, sticky="nsw")

            label = tk.Label(
                frame, text=timer_name, bg="light blue", font=("Helvetica", 24)
            )
            label.grid(row=0, column=0)

            time_label = tk.Label(
                frame, text=default_text, bg="light blue", font=("Helvetica", 24)
            )
            time_label.grid(row=0, column=1)

            logger.debug(f"Timer '{timer_name}' created.")
            return frame, label, time_label
        except Exception as e:
            logger.error(f"Error creating timer '{timer_name}': {e}")
            raise

    def display_timers(self) -> None:
        try:
            self.timers_frame = tk.Frame(
                self, highlightthickness=2, highlightbackground="Black"
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

            self.maximum_total_time_frame, _, self.maximum_total_time = (
                self.create_timer(
                    self.timers_frame, "Maximum Total Time:", "0 Minutes, 0 S", 0, 1
                )
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
            logger.info("Timers displayed.")
        except Exception as e:
            logger.error(f"Error displaying timers: {e}")
            raise

    def display_status_widget(self):
        try:
            self.status_frame = tk.Frame(
                self, highlightthickness=2, highlightbackground="black"
            )
            self.status_frame.grid(row=2, column=0, pady=5, sticky="nsew")
            self.status_frame.grid_rowconfigure(0, weight=1)

            for i in range(2):
                self.status_frame.grid_columnconfigure(i, weight=1)

            self.program_status_statistic_frame = self.create_status_frame(
                self.status_frame, row=0, column=0, sticky="nsew"
            )
            self.program_status_statistic_frame.grid_rowconfigure(0, weight=1)

            self.stimuli_information_frame = self.create_status_frame(
                self.status_frame, row=0, column=1, sticky="nsew"
            )
            self.stimuli_information_frame.grid_rowconfigure(0, weight=1)

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
            logger.info("Status widget displayed.")
        except Exception as e:
            logger.error(f"Error displaying status widget: {e}")
            raise

    def entry_widgets(self) -> None:
        try:
            self.entry_widgets_frame = tk.Frame(
                self, highlightthickness=2, highlightbackground="black"
            )
            self.entry_widgets_frame.grid(row=3, column=0, pady=5, sticky="nsew")
            for i in range(4):
                self.entry_widgets_frame.grid_columnconfigure(i, weight=1)

            # Simplify the creation of labeled entries
            self.ITI_Interval_Frame, _, _ = self.create_labeled_entry(
                parent=self.entry_widgets_frame,
                label_text="ITI Time",
                text_var=self.controller.data_mgr.interval_vars["ITI_var"],
                row=0,
                column=0,
            )

            self.TTC_Interval_Frame, _, _ = self.create_labeled_entry(
                parent=self.entry_widgets_frame,
                label_text="TTC Time",
                text_var=self.controller.data_mgr.interval_vars["TTC_var"],
                row=0,
                column=1,
            )
            self.Sample_Interval_Frame, _, _ = self.create_labeled_entry(
                parent=self.entry_widgets_frame,
                label_text="Sample Time",
                text_var=self.controller.data_mgr.interval_vars["sample_var"],
                row=0,
                column=2,
            )
            self.num_trial_blocks_frame, _, _ = self.create_labeled_entry(
                parent=self.entry_widgets_frame,
                label_text="# Trial Blocks",
                text_var=self.controller.get_num_trial_blocks_variable_reference(),
                row=0,
                column=3,
            )

            # Similarly for random plus/minus intervals and the number of stimuli
            self.ITI_Random_Interval_frame, _, _ = self.create_labeled_entry(
                parent=self.entry_widgets_frame,
                label_text="+/- ITI",
                text_var=self.controller.data_mgr.interval_vars["ITI_random_entry"],
                row=1,
                column=0,
            )
            self.TTC_Random_Interval_frame, _, _ = self.create_labeled_entry(
                parent=self.entry_widgets_frame,
                label_text="+/- TTC",
                text_var=self.controller.data_mgr.interval_vars["TTC_random_entry"],
                row=1,
                column=1,
            )
            self.Sample_Interval_Random_Frame, _, _ = self.create_labeled_entry(
                parent=self.entry_widgets_frame,
                label_text="+/- Sample",
                text_var=self.controller.data_mgr.interval_vars["sample_random_entry"],
                row=1,
                column=2,
            )
            self.num_stimuli_frame, _, _ = self.create_labeled_entry(
                parent=self.entry_widgets_frame,
                label_text="# Stimuli",
                text_var=self.controller.get_num_stimuli_variable_reference(),
                row=1,
                column=3,
            )
            logger.info("Entry widgets displayed.")
        except Exception as e:
            logger.error(f"Error displaying entry widgets: {e}")
            raise

    def lower_control_buttons(self):
        try:
            self.lower_control_buttons_frame = tk.Frame(
                self, highlightthickness=2, highlightbackground="black"
            )
            self.lower_control_buttons_frame.grid(row=4, sticky="nsew")
            self.lower_control_buttons_frame.grid_rowconfigure(0, weight=0)
            for i in range(4):
                self.lower_control_buttons_frame.grid_columnconfigure(i, weight=1)

            self.test_valves_button_frame, _ = self.create_button(
                parent=self.lower_control_buttons_frame,
                button_text="Calibrate Valves",
                command=lambda: self.controller.valve_testing_window.show_window(),
                bg="grey",
                row=0,
                column=0,
            )
            self.valve_control_button_frame, _ = self.create_button(
                parent=self.lower_control_buttons_frame,
                button_text="Valve Control",
                command=lambda: self.controller.open_valve_control_window(),
                bg="grey",
                row=0,
                column=1,
            )
            self.program_schedule_button_frame, _ = self.create_button(
                parent=self.lower_control_buttons_frame,
                button_text="Program Schedule",
                command=lambda: self.controller.show_stimuli_table(),
                bg="grey",
                row=0,
                column=2,
            )
            self.exp_ctrl_button_frame = self.create_button(
                parent=self.lower_control_buttons_frame,
                button_text="Valve / Stimuli",
                command=lambda: self.controller.experiment_ctl_wind.show_window(self),
                bg="grey",
                row=1,
                column=0,
            )
            self.lick_window_button_frame = self.create_button(
                parent=self.lower_control_buttons_frame,
                button_text="Lick Data",
                command=self.controller.licks_window.show_window,
                bg="grey",
                row=1,
                column=1,
            )
            self.raster_plot_button_frame = self.create_button(
                parent=self.lower_control_buttons_frame,
                button_text="Rasterized Data",
                command=self.controller.open_rasterized_data_windows,
                bg="grey",
                row=1,
                column=2,
            )
            self.save_data_button_frame = self.create_button(
                parent=self.lower_control_buttons_frame,
                button_text="Save Data",
                command=self.controller.data_mgr.save_data_to_xlsx,
                bg="grey",
                row=1,
                column=3,
            )
            logger.info("Lower control buttons displayed.")
        except Exception as e:
            logger.error(f"Error displaying lower control buttons: {e}")
            raise

    def display_error(self, error, message):
        try:
            messagebox.showinfo(error, message)
            logger.error(f"Error displayed: {error} - {message}")
        except Exception as e:
            logger.error(f"Error displaying error message: {e}")
            raise

    def update_clock_label(self) -> None:
        try:
            elapsed_time = time.time() - self.controller.data_mgr.start_time
            state_elapsed_time = time.time() - self.controller.data_mgr.state_start_time

            min, sec = self.convert_seconds_to_minutes_seconds(elapsed_time)

            self.main_timer_text.configure(text="{:.1f}s".format(elapsed_time))
            self.main_timer_min_sec_text.configure(
                text="| {:.0f} Minutes, {:.1f} S".format(min, sec)
            )

            self.state_timer_text.configure(text="{:.1f}s".format(state_elapsed_time))

            clock_id = self.after(100, self.update_clock_label)
            self.controller.after_ids.append(clock_id)
            logger.debug("Clock label updated.")
        except Exception as e:
            logger.error(f"Error updating clock label: {e}")
            raise

    def update_max_time(self, minutes, seconds) -> None:
        try:
            self.maximum_total_time.configure(
                text="{:.0f} Minutes, {:.1f} S".format(minutes, seconds)
            )
            logger.debug(
                f"Max time updated to {minutes} minutes and {seconds} seconds."
            )
        except Exception as e:
            logger.error(f"Error updating max time: {e}")
            raise

    def update_on_new_trial(self, side_1_stimulus, side_2_stimulus) -> None:
        try:
            trial_number = self.controller.data_mgr.current_trial_number

            self.trials_completed_label.configure(
                text=f"{trial_number} / {self.controller.get_num_trials()} Trials Completed"
            )
            self.stimuli_label.configure(
                text=f"Side One: {side_1_stimulus} | VS | Side Two: {side_2_stimulus}"
            )

            self.trial_number_label.configure(text=f"Trial Number: {trial_number}")

            self.update_progress_bar()

            self.controller.program_schedule_window.update_row_color(trial_number)
            self.controller.program_schedule_window.update_licks_and_TTC_actual(
                trial_number
            )
            logger.debug(f"Updated GUI for new trial {trial_number}.")
        except Exception as e:
            logger.error(f"Error updating GUI for new trial: {e}")
            raise

    def update_progress_bar(self, reset=False):
        try:
            if reset:
                self.progress["value"] = 0
            else:
                self.progress["value"] = (
                    self.controller.data_mgr.current_trial_number
                    / self.controller.get_num_trials()
                ) * 100  # Set the new value for the progress
            self.progress.update_idletasks()  # Update the progress bar display
            logger.debug("Progress bar updated.")
        except Exception as e:
            logger.error(f"Error updating progress bar: {e}")
            raise

    def update_on_state_change(self, state_time_value, state) -> None:
        try:
            self.update_full_state_time(state_time_value)
            self.update_status(state)
            logger.debug(f"Updated GUI on state change to {state}.")
        except Exception as e:
            logger.error(f"Error updating GUI on state change: {e}")
            raise

    def update_status(self, state) -> None:
        try:
            self.status_label.configure(text=f"Status: {state}")
            logger.debug(f"Status updated to {state}.")
        except Exception as e:
            logger.error(f"Error updating status: {e}")
            raise

    def clear_state_time(self) -> None:
        try:
            self.full_state_time_text.configure(text="/ {:.1f}s".format(0))
            logger.debug("State time cleared.")
        except Exception as e:
            logger.error(f"Error clearing state time: {e}")
            raise

    def update_full_state_time(self, state_time_value) -> None:
        try:
            full_state_time = state_time_value
            self.full_state_time_text.configure(
                text="/ {:.1f}s".format(full_state_time / 1000.0)
            )
            logger.debug(f"Full state time updated to {full_state_time}.")
        except Exception as e:
            logger.error(f"Error updating full state time: {e}")
            raise

    def update_on_stop(self) -> None:
        try:
            self.state_timer_text.configure(text="0.0s")
            self.start_button.configure(text="Start", bg="green")
            self.update_on_state_change(0, "Idle")
            logger.debug("Updated GUI on stop.")
        except Exception as e:
            logger.error(f"Error updating GUI on stop: {e}")
            raise

    def update_on_reset(self) -> None:
        try:
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
            logger.debug("Updated GUI on reset.")
        except Exception as e:
            logger.error(f"Error updating GUI on reset: {e}")
            raise

    def on_close(self):
        try:
            for after_id in self.controller.after_ids:
                self.after_cancel(after_id)
            self.after_cancel(self.controller.queue_id)
            self.controller.arduino_mgr.stop()
            self.destroy()
            self.quit()
            logger.info("Application closed.")
        except Exception as e:
            logger.error(f"Error closing application: {e}")
            raise
