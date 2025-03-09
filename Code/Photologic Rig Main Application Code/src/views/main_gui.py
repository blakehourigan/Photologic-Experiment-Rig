from tkinter import ttk
import tkinter as tk
import time
import logging

from views.gui_common import GUIUtils

# import other GUI classes that can spawn from main GUI
from views.rasterized_data_window import RasterizedDataWindow
from views.experiment_control_window import ExperimentCtlWindow
from views.event_window import EventWindow
from views.valve_testing_window import ValveTestWindow
from views.program_schedule_window import ProgramScheduleWindow
from views.valve_control_window import ValveControlWindow


# Get the logger in use for the app
logger = logging.getLogger()


# using tk.Tk here says that this class is going to be a tkinter app. when we call super().__init__() this actuall creates the tkinter main window
# then we can use it as if it were root - e.g self.title("title") sets the root window title
class MainGUI(tk.Tk):
    def __init__(self, exp_data, trigger_state_change) -> None:
        # init the Tk instance to create a GUI
        super().__init__()
        # self.scheduled_tasks is a dict where keys are short task descriptions (e.g ttc_to_iti) and the values are
        # the ids for that tkinter .after call, so we know exactly how to cancel a scheduled task
        self.scheduled_tasks = {}

        self.exp_data = exp_data

        self.trigger_state_change = trigger_state_change

        # set basic window attributes such as title and size
        self.title("Samuelsen Lab Photologic Rig")

        # set main window size to 80% of width & height of display
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        desired_wind_width = int(screen_width * 0.8)
        desired_wind_height = int(screen_height * 0.8)
        self.geometry(
            "{}x{}+{}+{}".format(desired_wind_width, desired_wind_height, 0, 0)
        )

        # bind <Control-w> keyboard shortcut to close the window for convenience
        self.bind("<Control-w>", lambda event: self.on_close())

        # defines the function to run when the window is closed by the window manager
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        # get path of program icon image and set it
        icon_path = GUIUtils.get_window_icon_path()
        GUIUtils.set_program_icon(self, icon_path=icon_path)

        # set cols and rows to expand to fill space in main gui
        for i in range(5):
            self.grid_rowconfigure(i, weight=1)

        self.grid_columnconfigure(0, weight=1)

        self.setup_tkinter_variables()
        self.build_gui_widgets()

        # create all secondary windows early so that loading when program is running is fast
        self.preload_secondary_windows()

        logger.info("MainGUI initialized.")

    def preload_secondary_windows(self):
        """
        This function builds all secondary windows (windows that require a button push to view) and gets them ready
        to be switched to when the user clicks the corresponding button
        """
        # define the data that ExperimentCtlWindow() needs to function
        stimuli_data = self.exp_data.stimuli_data
        event_data = self.exp_data.event_data

        self.windows = {
            "Experiment Control": ExperimentCtlWindow(
                self.exp_data, stimuli_data, event_data, self.trigger_state_change
            ),
            "Program Schedule": ProgramScheduleWindow(
                self.exp_data,
                stimuli_data,
            ),
            "Raster Plot": (
                RasterizedDataWindow(1, self.exp_data),
                RasterizedDataWindow(2, self.exp_data),
            ),
            "Event Data": EventWindow(event_data),
            "Valve Testing": ValveTestWindow(),
            "Valve Control": ValveControlWindow(),
        }

    def show_secondary_window(self, window):
        if isinstance(self.windows[window], tuple):
            for instance in self.windows[window]:
                instance.deiconify()
        else:
            self.windows[window].show()

    def hide_secondary_window(self, window):
        self.windows[window].withdraw()

    def setup_tkinter_variables(self):
        # tkinter variables for time related
        # modifications in the experiment
        self.tkinter_entries = {
            "ITI_var": tk.IntVar(),
            "TTC_var": tk.IntVar(),
            "sample_var": tk.IntVar(),
            "ITI_random_entry": tk.IntVar(),
            "TTC_random_entry": tk.IntVar(),
            "sample_random_entry": tk.IntVar(),
        }

        # fill the tkinter entry boxes with their default values as configured in self.exp_data
        for key in self.tkinter_entries.keys():
            self.tkinter_entries[key].set(self.exp_data.get_default_value(key))

        # we add traces to all of our tkinter variables so that on value update
        # we sent those updates to the corresponding model (data storage location)
        for key, value in self.tkinter_entries.items():
            value.trace_add(
                "write",
                lambda *args, key=key, value=value: self.exp_data.update_model(
                    key, GUIUtils.safe_tkinter_get(value)
                ),
            )

        # tkinter variables for other variables in the experiment such as num stimuli
        # or number of trial blocks
        self.exp_var_entries = {
            "Num Trial Blocks": tk.IntVar(),
            "Num Stimuli": tk.IntVar(),
        }

        # fill the exp_var entry boxes with their default values as configured in self.exp_data
        for key in self.exp_var_entries.keys():
            self.exp_var_entries[key].set(self.exp_data.get_default_value(key))

        for key, value in self.exp_var_entries.items():
            value.trace_add(
                "write",
                lambda *args, key=key, value=value: self.exp_data.update_model(
                    key, GUIUtils.safe_tkinter_get(value)
                ),
            )

    def build_gui_widgets(self) -> None:
        try:
            self.display_timers()
            self.entry_widgets()
            self.display_main_control_buttons()
            self.lower_control_buttons()
            self.display_status_widget()
            logger.info("GUI setup completed.")
        except Exception as e:
            logger.error(f"Error setting up GUI: {e}")
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

            self.start_button_frame, self.start_button = GUIUtils.create_button(
                self.main_control_button_frame,
                "Start",
                lambda: self.trigger_state_change("START"),
                "green",
                0,
                0,
            )

            self.reset_button_frame, _ = GUIUtils.create_button(
                self.main_control_button_frame,
                "Reset",
                lambda: self.trigger_state_change("RESET"),
                "grey",
                0,
                1,
            )
            logger.info("Main control buttons displayed.")
        except Exception as e:
            logger.error(f"Error displaying main control buttons: {e}")
            raise

    def display_timers(self) -> None:
        try:
            self.timers_frame = tk.Frame(
                self, highlightthickness=2, highlightbackground="Black"
            )
            self.timers_frame.grid(row=1, column=0, sticky="nsew")
            for i in range(2):
                self.timers_frame.grid_columnconfigure(i, weight=1)

            self.main_timer_frame, _, self.main_timer_text = GUIUtils.create_timer(
                self.timers_frame, "Time Elapsed:", "0.0s", 0, 0
            )
            self.main_timer_min_sec_text = tk.Label(
                self.main_timer_frame, text="", bg="light blue", font=("Helvetica", 24)
            )
            self.main_timer_min_sec_text.grid(row=0, column=2)

            self.maximum_total_time_frame, _, self.maximum_total_time = (
                GUIUtils.create_timer(
                    self.timers_frame, "Maximum Total Time:", "0 Minutes, 0 S", 0, 1
                )
            )
            self.maximum_total_time_frame.grid(sticky="e")

            self.state_timer_frame, _, self.state_timer_text = GUIUtils.create_timer(
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
            self.ITI_Interval_Frame, _, _ = GUIUtils.create_labeled_entry(
                parent=self.entry_widgets_frame,
                label_text="ITI Time",
                text_var=self.tkinter_entries["ITI_var"],
                row=0,
                column=0,
            )

            self.TTC_Interval_Frame, _, _ = GUIUtils.create_labeled_entry(
                parent=self.entry_widgets_frame,
                label_text="TTC Time",
                text_var=self.tkinter_entries["TTC_var"],
                row=0,
                column=1,
            )
            self.Sample_Interval_Frame, _, _ = GUIUtils.create_labeled_entry(
                parent=self.entry_widgets_frame,
                label_text="Sample Time",
                text_var=self.tkinter_entries["sample_var"],
                row=0,
                column=2,
            )
            self.num_trial_blocks_frame, _, _ = GUIUtils.create_labeled_entry(
                parent=self.entry_widgets_frame,
                label_text="# Trial Blocks",
                text_var=self.exp_var_entries["Num Trial Blocks"],
                row=0,
                column=3,
            )

            # Similarly for random plus/minus intervals and the number of stimuli
            self.ITI_Random_Interval_frame, _, _ = GUIUtils.create_labeled_entry(
                parent=self.entry_widgets_frame,
                label_text="+/- ITI",
                text_var=self.tkinter_entries["ITI_random_entry"],
                row=1,
                column=0,
            )
            self.TTC_Random_Interval_frame, _, _ = GUIUtils.create_labeled_entry(
                parent=self.entry_widgets_frame,
                label_text="+/- TTC",
                text_var=self.tkinter_entries["TTC_random_entry"],
                row=1,
                column=1,
            )
            self.Sample_Interval_Random_Frame, _, _ = GUIUtils.create_labeled_entry(
                parent=self.entry_widgets_frame,
                label_text="+/- Sample",
                text_var=self.tkinter_entries["sample_random_entry"],
                row=1,
                column=2,
            )
            self.num_stimuli_frame, _, _ = GUIUtils.create_labeled_entry(
                parent=self.entry_widgets_frame,
                label_text="# Stimuli",
                text_var=self.exp_var_entries["Num Stimuli"],
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

            self.test_valves_button_frame, _ = GUIUtils.create_button(
                parent=self.lower_control_buttons_frame,
                button_text="Calibrate Valves",
                command=lambda: self.show_secondary_window("Valve Testing"),
                bg="grey",
                row=0,
                column=0,
            )
            self.valve_control_button_frame, _ = GUIUtils.create_button(
                parent=self.lower_control_buttons_frame,
                button_text="Valve Control",
                command=lambda: self.show_secondary_window("Valve Control"),
                bg="grey",
                row=0,
                column=1,
            )
            self.program_schedule_button_frame, _ = GUIUtils.create_button(
                parent=self.lower_control_buttons_frame,
                button_text="Program Schedule",
                command=lambda: self.show_secondary_window("Program Schedule"),
                bg="grey",
                row=0,
                column=2,
            )
            self.exp_ctrl_button_frame = GUIUtils.create_button(
                parent=self.lower_control_buttons_frame,
                button_text="Valve / Stimuli",
                command=lambda: self.show_secondary_window("Experiment Control"),
                bg="grey",
                row=1,
                column=0,
            )
            self.lick_window_button_frame = GUIUtils.create_button(
                parent=self.lower_control_buttons_frame,
                button_text="Event Data",
                command=lambda: self.show_secondary_window("Event Data"),
                bg="grey",
                row=1,
                column=1,
            )
            self.raster_plot_button_frame = GUIUtils.create_button(
                parent=self.lower_control_buttons_frame,
                button_text="Rasterized Data",
                command=lambda: self.show_secondary_window("Raster Plot"),
                bg="grey",
                row=1,
                column=2,
            )
            self.save_data_button_frame = GUIUtils.create_button(
                parent=self.lower_control_buttons_frame,
                button_text="Save Data",
                command=lambda: self.save_button_handler(),
                bg="grey",
                row=1,
                column=3,
            )
            logger.info("Lower control buttons displayed.")
        except Exception as e:
            logger.error(f"Error displaying lower control buttons: {e}")
            raise

    def save_button_handler(self):
        sched_df = self.exp_data.program_schedule_df
        event_df = self.exp_data.event_data.event_dataframe

        if sched_df.empty or event_df.empty:
            response = GUIUtils.askyesno(
                "Hmm...",
                "The program schedule window appears to be empty... save anyway?",
            )

            if response:
                self.exp_data.save_all_data()
        else:
            self.exp_data.save_all_data()

    def update_clock_label(self) -> None:
        try:
            elapsed_time = time.time() - self.exp_data.start_time
            state_elapsed_time = time.time() - self.exp_data.state_start_time

            min, sec = self.exp_data.convert_seconds_to_minutes_seconds(elapsed_time)

            self.main_timer_text.configure(text="{:.1f}s".format(elapsed_time))
            self.main_timer_min_sec_text.configure(
                text="| {:.0f} Minutes, {:.1f} S".format(min, sec)
            )

            self.state_timer_text.configure(text="{:.1f}s".format(state_elapsed_time))

            clock_update_task = self.after(100, self.update_clock_label)
            self.scheduled_tasks["CLOCK UPDATE"] = clock_update_task
        except Exception as e:
            logger.error(f"Error updating clock label: {e}")
            raise

    def update_max_time(self) -> None:
        try:
            minutes, seconds = self.exp_data.calculate_max_runtime()

            self.maximum_total_time.configure(
                text="{:.0f} Minutes, {:.1f} S".format(minutes, seconds)
            )
        except Exception as e:
            logger.error(f"Error updating max time: {e}")
            raise

    def update_on_new_trial(self, side_1_stimulus, side_2_stimulus) -> None:
        """
        updates the program schedule window highlighting and updates
        the main_gui window with current trial number and updates progress bar

        """
        try:
            trial_number = self.exp_data.current_trial_number
            total_trials = self.exp_data.exp_var_entries["Num Trials"]

            self.trials_completed_label.configure(
                text=f"{trial_number} / {total_trials} Trials Completed"
            )
            self.stimuli_label.configure(
                text=f"Side One: {side_1_stimulus} | VS | Side Two: {side_2_stimulus}"
            )

            self.trial_number_label.configure(text=f"Trial Number: {trial_number}")

            self.windows["Program Schedule"].refresh_start_trial(trial_number)

            self.update_progress_bar(trial_number, total_trials)

            logger.info(f"Updated GUI for new trial {trial_number}.")
        except Exception as e:
            logger.error(f"Error updating GUI for new trial: {e}")
            raise

    def update_progress_bar(self, trial_number, total_trials, reset=False):
        try:
            if reset:
                self.progress["value"] = 0
            else:
                # Set the new value for the progress
                self.progress["value"] = (trial_number / total_trials) * 100
            logger.info("Progress bar updated.")
        except Exception as e:
            logger.error(f"Error updating progress bar: {e}")
            raise

    def update_on_state_change(self, state_time_value, state) -> None:
        try:
            self.update_full_state_time(state_time_value)
            self.update_status(state)
            logger.info(f"Updated GUI on state change to {state}.")
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
            logger.info(f"Full state time updated to {full_state_time}.")
        except Exception as e:
            logger.error(f"Error updating full state time: {e}")
            raise

    def update_on_stop(self) -> None:
        try:
            self.state_timer_text.configure(text="0.0s")

            self.update_on_state_change(0, "Idle")
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
            logger.info("Updated GUI on reset.")
        except Exception as e:
            logger.error(f"Error updating GUI on reset: {e}")
            raise

    def on_close(self):
        try:
            # get rid of all .after calls
            self.quit()
            self.destroy()
            logger.info("Application closed.")
        except Exception as e:
            logger.error(f"Error closing application: {e}")
            raise
