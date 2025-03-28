"""
`main_gui` is the module which all program GUI elements originate from. We first initialize the primary app window, then initialize and hide
all secondary windows so that they will not take resources being created later.

"""

from tkinter import ttk
import tkinter as tk
import time
import logging
from typing import Callable

# used for type hinting
from controllers.arduino_control import ArduinoManager
from models.experiment_process_data import ExperimentProcessData
# used for type hinting

from views.gui_common import GUIUtils

# import other GUI classes that can spawn from main GUI
from views.rasterized_data_window import RasterizedDataWindow
from views.experiment_control_window import ExperimentCtlWindow
from views.event_window import EventWindow
from views.valve_testing.valve_testing_window import ValveTestWindow

from views.program_schedule_window import ProgramScheduleWindow
from views.valve_control_window import ValveControlWindow


logger = logging.getLogger()
"""Get the logger in use for the app."""


class MainGUI(tk.Tk):
    """
    The creator and controller of all GUI related items and actions for the program. Inherits from tk.Tk to create a tk.root()
    from which tk.TopLevel windows can be sprouted and tk.after scheduling calls can be made.

    Attributes
    ----------
    - **exp_data** (*ExperimentProcessData*): An instance of `models.experiment_process_data` ExperimentProcessData,
    this attribute allows for access and modification of experiment variables, and access for to more specific models like
    `models.event_data` and `models.arduino_data`.
    - **arduino_controller** (*ArduinoManager*): An instance of `controllers.arduino_control` ArduinoManager, this allows for communication between this program and the
    Arduino board.
    - **trigger** (*Callback method*): trigger is the callback method from `app_logic` module `StateMachine` class, it allows the
    GUI to attempt state transitions.
    - **scheduled_tasks** (*dict[str,str]*): self.scheduled_tasks is a dict where keys are short task descriptions (e.g ttc_to_iti) and the values are
        the str ids for tkinter.after scheduling calls. This allows for tracking and cancellations of scheduled tasks.
    - (**windows**) (*dict*): A dictionary that holds window titles as keys, and instances of GUI sublasses as values. Allows for easy access of windows and their methods
        and attributes given a title.

    Methods
    -------
    - `setup_basic_window_attr`()
        This method sets basic window attributes like title, icon, and expansion settings.
    - `setup_tkinter_variables`()
        GUI (Tkinter) variables and acutal stored data for the program are decoupled to separate concerns. Here we link them such that when the GUI variables are updated,
        the data stored in the model is also updated.
    - `build_gui_widgets`()
        Setup all widgets to be placed in the MainGUI window.
    - `preload_secondary_windows`()
        This method loads all secondary windows and all content available at start time. This was done to reduce strain on system while program is running. Windows always
        exist and are simply hidden when not shown to user.
    - `show_secondary_window`()
        Takes a window description string for the `windows` dictionary. Access is given to the instance of the class for the description, where the windows `show` method is
        called.
    - `hide_secondary_window`()
        The opposing function to `show_secondary_window`. Hides the window specified as the `window` argument.
    - `create_top_control_buttons`()
        Create frames and buttons for top bar start an reset buttons.
    - `create_timers`()
        Create start and state start timer labels.
    - `create_status_widgets`()
        Create state status widgets such as state label, num trials progress bar and label, etc.
    - `create_entry_widgets`()
        Build entry widget and frames for ITI, TTC, Sample times, Num Trials, Num Stimuli.
    - `create_lower_control_buttons`()
        Create lower control buttons for opening windows and saving data.
    - `save_button_handler`()
        Define behavior for saving all data to xlsx files.
    - `update_clock_label`()
        Hold logic for updating GUI clocks every 100ms.
    - `update_max_time`()
        Calculate max program runtime.
    - `update_on_new_trial`()
        Define GUI objects to update each iteration (new ITI state) of program.
    - `update_on_state_change`()
        Define GUI objects to update upon each state (state timer, label, etc).
    - `update_on_stop`()
        Update GUI objects to reflect "IDLE" program state once stopped.
    - `on_close`()
        Defines GUI shutdown behavior when primary window is closed.
    """

    def __init__(
        self,
        exp_data: ExperimentProcessData,
        trigger: Callable[[str], None],
        arduino_controller: ArduinoManager,
    ) -> None:
        """
        Initialize the MainGUI window. Build all frames and widgets required by the main window *and* loads all secondary windows that can
        be opened by the lower control buttons. These are hidden after generation and deiconified (shown) when the button is pressed.

        Parameters
        ----------
        - **exp_data** (*ExperimentProcessData*): A reference to the `models.experiment_process_data` ExperimentProcessData instance,
        this is used to model data based on user GUI interaction.
        - **trigger** (*Callback method*): This callback is passed in so that this state can trigger state transitions from GUI objects
        throughout the class.
        - **arduino_controller** (*ArduinoManager*): A reference to the `controllers.arduino_control` Arduino controller instance,
        this is the method by which the Arduino is communicated with in the program. `views.valve_testing.valve_testing_window`
        ValveTestWindow, and `views.valve_control_window` require references here to communicate with Arduino to calibrate and open/close
        valves. This is also used in `on_close` to stop the Arduino listener thread to avoid thread errors on window close.
        """
        # init tk.Tk to use this class as a tk.root.
        super().__init__()

        self.exp_data = exp_data
        self.arduino_controller = arduino_controller
        self.trigger = trigger

        self.scheduled_tasks: dict[str, str] = {}

        self.setup_basic_window_attr()
        self.setup_tkinter_variables()
        self.build_gui_widgets()

        # update_idletasks so that window knows what elements are inside and what width and height they require,
        # then scale and center the window.
        self.update_idletasks()
        GUIUtils.center_window(self)

        # create all secondary windows early so that loading when program is running is fast
        self.preload_secondary_windows()

        logger.info("MainGUI initialized.")

    def setup_basic_window_attr(self):
        """
        Set basic window attributes such as title, size, window icon, protocol for closing the window, etc.
        We also bind <Control-w> keyboard shortcut to close the window for convenience. Finally,
        we set the grid rows and columns to expand and contract as window gets larger or smaller (weight=1).
        """

        self.title("Samuelsen Lab Photologic Rig")
        self.bind("<Control-w>", lambda event: self.on_close())
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        icon_path = GUIUtils.get_window_icon_path()
        GUIUtils.set_program_icon(self, icon_path=icon_path)

        # set cols and rows to expand to fill space in main gui
        for i in range(5):
            self.grid_rowconfigure(i, weight=1)

        self.grid_columnconfigure(0, weight=1)

    def setup_tkinter_variables(self) -> None:
        """
        Tkinter variables for tkinter entries are created here. These are the variables updated on user input. Default values
        are set by finding the default value in `models.experiment_process_data`. Traces are added to each variable which update
        the model upon an update (write) to the Tkinter variable.
        """
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
        """
        Build all GUI widgets by calling respective functions for each type of widget listed here.
        """
        try:
            self.create_top_control_buttons()
            self.create_timers()
            self.create_status_widgets()
            self.create_entry_widgets()
            self.create_lower_control_buttons()
            logger.info("GUI setup completed.")
        except Exception as e:
            logger.error(f"Error setting up GUI: {e}")
            raise

    def preload_secondary_windows(self) -> None:
        """
        Build all secondary windows (windows that require a button push to view) and get them ready
        to be opened (deiconified in tkinter terms) when the user clicks the corresponding button.
        """
        # define the data that ExperimentCtlWindow() needs to function
        stimuli_data = self.exp_data.stimuli_data
        event_data = self.exp_data.event_data

        self.windows = {
            "Experiment Control": ExperimentCtlWindow(
                self.exp_data, stimuli_data, self.trigger
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
            "Valve Testing": ValveTestWindow(self.arduino_controller),
            "Valve Control": ValveControlWindow(self.arduino_controller),
        }

    def show_secondary_window(self, window: str) -> None:
        """
        Show the window corresponding to a button press or other event calling this method. Accesses class attribute `windows` to gain
        accesss to the desired instance and call the class `show` method.

        Parameters
        ----------
        - **window** (*str*): A key to the `windows` dictionary. This will return an instance of the corresponding class to the provided
        'key' (window).
        """
        if isinstance(self.windows[window], tuple):
            for instance in self.windows[window]:
                instance.deiconify()
        else:
            df = self.exp_data.program_schedule_df
            if window == "Valve Testing" and not df.empty:
                GUIUtils.display_error(
                    "CANNOT DISPLAY WINDOW",
                    "Since the schedule has been generated, valve testing has been disabled for this experiment. Reset the application to test again.",
                )
                return

            self.windows[window].show()

    def hide_secondary_window(self, window: str) -> None:
        """
        Performs the opposite action of `show_secondary_window`. Hides the window without destroyoing it by calling tkinter method
        'withdraw' on the tk.TopLevel (class/`windows` dict value) instance.

        Parameters
        ----------
        - **window** (*str*): A key to the `windows` dictionary. This will return an instance of the corresponding class to the provided
        'key' (window).
        """
        self.windows[window].withdraw()

    def create_top_control_buttons(self) -> None:
        """
        Creates frame to contain top control buttons, then utilizes `views.gui_common` `GUIUtils` methods to create buttons for
        'Start/Stop' and 'Reset' button functions.
        """
        try:
            self.main_control_button_frame = GUIUtils.create_basic_frame(
                self, row=0, column=0, rows=1, cols=2
            )

            self.start_button_frame, self.start_button = GUIUtils.create_button(
                self.main_control_button_frame,
                button_text="Start",
                command=lambda: self.trigger("START"),
                bg="green",
                row=0,
                column=0,
            )

            self.reset_button_frame, _ = GUIUtils.create_button(
                self.main_control_button_frame,
                button_text="Reset",
                command=lambda: self.trigger("RESET"),
                bg="grey",
                row=0,
                column=1,
            )
            logger.info("Main control buttons displayed.")
        except Exception as e:
            logger.error(f"Error displaying main control buttons: {e}")
            raise

    def create_timers(self) -> None:
        """
        Creates frame to contain program timer, max runtime timer, and state timer. Then builds both timers and places them into the frame.
        """
        try:
            self.timers_frame = GUIUtils.create_basic_frame(
                self, row=1, column=0, rows=1, cols=2
            )

            self.main_timer_frame, _, self.main_timer_text = GUIUtils.create_timer(
                self.timers_frame, "Time Elapsed:", "0.0s", 0, 0
            )
            self.main_timer_min_sec_text = tk.Label(
                self.main_timer_frame, text="", bg="light blue", font=("Helvetica", 24)
            )
            self.main_timer_min_sec_text.grid(row=0, column=2)

            ######  BEGIN max total time frame #####
            self.maximum_total_time_frame, _, self.maximum_total_time = (
                GUIUtils.create_timer(
                    self.timers_frame, "Maximum Total Time:", "0 Minutes, 0 S", 0, 1
                )
            )
            self.maximum_total_time_frame.grid(sticky="e")

            ######  BEGIN state time frame #####
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

            logger.info("Timers created.")
        except Exception as e:
            logger.error(f"Error displaying timers: {e}")
            raise

    def create_status_widgets(self) -> None:
        """
        Creates frames for status widgets (state label, trial number/progress bar, current stimuli, etc), builds these widgets and places them
        into their respective frames.
        """
        try:
            self.status_frame = GUIUtils.create_basic_frame(
                self, row=2, column=0, rows=1, cols=2
            )

            self.program_status_statistic_frame = GUIUtils.create_basic_frame(
                self.status_frame, row=0, column=0, rows=1, cols=1
            )

            self.stimuli_information_frame = GUIUtils.create_basic_frame(
                self.status_frame, row=0, column=1, rows=1, cols=1
            )

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
            logger.info("Status widgets displayed.")
        except Exception as e:
            logger.error(f"Error displaying status widget: {e}")
            raise

    def create_entry_widgets(self) -> None:
        """
        Creates frame to store labels and entries for ITI, TTC, Sample times using `views.gui_common` GUIUtils static class methods.
        """
        try:
            self.entry_widgets_frame = GUIUtils.create_basic_frame(
                self, row=3, column=0, rows=1, cols=4
            )

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

    def create_lower_control_buttons(self) -> None:
        """
        Creates frame for lower control buttons (those that open windows and save data) and sets their command to open (deiconify) their
        respective window.
        """
        try:
            self.lower_control_buttons_frame = GUIUtils.create_basic_frame(
                self, row=4, column=0, rows=1, cols=4
            )

            self.test_valves_button_frame, _ = GUIUtils.create_button(
                parent=self.lower_control_buttons_frame,
                button_text="Valve Testing / Prime Valves",
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
            logger.info("Lower control buttons created.")
        except Exception as e:
            logger.error(f"Error displaying lower control buttons: {e}")
            raise

    def save_button_handler(self) -> None:
        """
        Here we define behavior for clicking the 'Save Data' button. If either main dataframe is empty, we inform the user of this, otherwise
        we call the `save_all_data` method from `models.experiment_process_data`.
        """
        sched_df = self.exp_data.program_schedule_df
        event_df = self.exp_data.event_data.event_dataframe

        if sched_df.empty or event_df.empty:
            response = GUIUtils.askyesno(
                "Hmm...",
                "One some of your data appears missing or empty... save anyway?",
            )

            if response:
                self.exp_data.save_all_data()
        else:
            self.exp_data.save_all_data()

    def update_clock_label(self) -> None:
        """
        This method defines logic to update primary timers such as main program timer and state timer. Max time is only updated once, but this
        operation is separated from this method. This task is scheduled via a tkinter.after call to execute every 100ms so that the main timer
        is responsive without overwhelming the main thread.
        """
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
        """
        This method updates the maximum runtime timer by retreiving this value from `models.experiment_process_data` and configuring the
        timer label.
        """
        try:
            minutes, seconds = self.exp_data.calculate_max_runtime()

            self.maximum_total_time.configure(
                text="{:.0f} Minutes, {:.1f} S".format(minutes, seconds)
            )
        except Exception as e:
            logger.error(f"Error updating max time: {e}")
            raise

    def update_on_new_trial(self, side_1_stimulus: str, side_2_stimulus: str) -> None:
        """
        Updates the new trial items such as program schedule window current trial highlighting and updates
        the main_gui status information widgets with current trial number and updates progress bar.

        Parameters
        ----------
        - **side_1_stimulus** (*str*): This parameter is of type string and is generally pulled from the program schedule dataframe in
        `app_logic` 'StateMachine' to provide the new stimulus for the upcoming trial for side one.
        - **side_2_stimulus** (*str*): This parameter mirrors `side_1_stimulus` in all aspects except that this one reflects the stmulus for
        side two.
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

            # Set the new value for the progress bar
            self.progress["value"] = (trial_number / total_trials) * 100

            logger.info(f"Updated GUI for new trial {trial_number}.")
        except Exception as e:
            logger.error(f"Error updating GUI for new trial: {e}")
            raise

    def update_on_state_change(self, state_duration_ms: float, state: str) -> None:
        """
        Here we define the GUI objects that need to be updated upon a state change. This includes the current state label as
        well as the state timer.

        Parameters
        ----------
        - **state_duration_ms** (*float*): Provides the duration of this state in ms. Is generally pulled from the program schedule df for
        the current trial. Converted to seconds by dividing the parameter by 1000.0.
        - **state** (*str*): Provides the current to program state to update state label to inform user that program has changed state.
        """
        try:
            ### clear full state time ###
            self.full_state_time_text.configure(text="/ {:.1f}s".format(0))

            ### UPDATE full state time ###
            state_duration_seconds = state_duration_ms / 1000.0
            self.full_state_time_text.configure(
                text="/ {:.1f}s".format(state_duration_seconds)
            )

            self.status_label.configure(text=f"Status: {state}")

            logger.info(f"Updated GUI on state change to {state}.")
        except Exception as e:
            logger.error(f"Error updating GUI on state change: {e}")
            raise

    def update_on_stop(self) -> None:
        """
        Here we define the GUI objects that need to be updated when the program is stopped for any reason. This includes the current
        state label (change to "IDLE), and removing state timer information.
        """

        try:
            self.state_timer_text.configure(text="0.0s")

            self.full_state_time_text.configure(text=" / 0.0s")

            self.status_label.configure(text="Status: IDLE")

        except Exception as e:
            logger.error(f"Error updating GUI on stop: {e}")
            raise

    def on_close(self):
        """
        This method is called any time the main program window is closed via the red X or <C-w> shortcut. We stop the listener thread if it
        is running, then quit() the tkinter mainloop and destroy() the window and all descendent widgets.
        """
        try:
            if self.arduino_controller.listener_thread is not None:
                # stop the listener thread so that it will not block exit
                self.arduino_controller.stop_listener_thread()

            # quit the mainloop and destroy the application
            self.quit()
            self.destroy()

            logger.info("Mainloop terminated, widgets destroyed, application closed.")
        except Exception as e:
            logger.error(f"Error closing application: {e}")
            raise
