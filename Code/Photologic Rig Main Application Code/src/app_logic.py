"""
'app_logic' is the primary module in the Photologic-Experiment-Rig codebase. It contains the
StateMachine class which holds the logic for each 'state' an experiment can be in.

Before performing any actions, the StateMachine class initializes the instances of `models.experiment_process_data`,
`controllers.arduino_control`, and `views.main_gui` classes.
Launching main_gui initializes a tkinter root and allows for a GUI to be created for the program.

This module is launched from main to make restarting the program easier, which is done by destroying the
instance of state machine and launcing a new one.
"""

# external imports
import time
import threading
import logging
import toml
import queue
from typing import Callable
import datetime
from logging import FileHandler

# imports for locally used modules and classes
from models.experiment_process_data import ExperimentProcessData
from views.gui_common import GUIUtils
import system_config
from views.main_gui import MainGUI

# these are just use for type hinting here
from controllers.arduino_control import ArduinoManager

logger = logging.getLogger()
"""Logger used to log program runtime details for debugging"""
logger.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
"""The console handler is used to print errors to the console"""
console_handler.setLevel(logging.ERROR)
console_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
)
logger.addHandler(console_handler)

RIG_CONFIG = system_config.get_rig_config()
"""
This utilizes `system_config` module to obtain a constant path for this machine regardless of OS to the Rig Files foler 
at the current users documents folder.
"""

with open(RIG_CONFIG, "r") as f:
    DOOR_CONFIG = toml.load(f)["door_motor_config"]

DOOR_MOVE_TIME = DOOR_CONFIG["DOOR_MOVE_TIME"]
"""Constant value stored in the door_motor_config section of `RIG CONFIG` config"""


now = datetime.datetime.now()
# configure logfile details such as name and the level at which information should be added to the log (INFO here)
logfile_name = f"{now.hour}_{now.minute}_{now.second} - {now.date()} experiment log"
logfile_path = system_config.get_log_path(logfile_name)

file_handler = FileHandler(logfile_path)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
)
logger.addHandler(file_handler)


class StateMachine:
    """
    This class is the heart of the program. Defines and handles program state transitions.
    It coordinates co-operation between view (gui) and models (data). We inherit a TkinterApp class to include
    attributes of a tkinter app such as gui, arduino controller, etc.

    Attributes
    ----------
    - **exp_data** (*ExperimentProcessData*): An instance of `models.experiment_process_data` ExperimentProcessData, this attribute allows for access and
    modification of experiment variables, and access for to more specific models like `models.event_data` and `models.arduino_data`.
    - **arduino_controller** (*ArduinoManager*): An instance of `controllers.arduino_control` ArduinoManager, this allows for communication between this program and the
    Arduino board.
    - **main_gui** (*MainGUI*): An instance of `views.main_gui` MainGUI, this allows for the creation and modification of all GUI attributes in the program. All GUI windows
    are created and managed here.
    - **state** (*str*): Contains the current state the program is in.
    - **prev_state** (*str*): Contains the state the program was previously in. Useful to restore state in case of erroneous transitions.
    - **app_result** (*list*): Mutable list with one element. Is a reference to list defined in `main`.
    - **transitions**  (*dict*): Program state transition table.

    Methods
    -------
    - `trigger`(event)
        Handles state transition events. Decides if a transition is valid and warns user of destructive transitions. If valid,
        passes state to `execute_state` method.
    - `execute_state`(new_state: str)
        Takes the state passed from trigger event and decides appropriate action.
    - `process_queue`(data_queue)
        Processes incoming data from the Arduino board. Reads from queue that is added to by `controllers.arduino_control` module
        `listen_for_serial` method.
    - `reject_actions`(event)
        A static method that handles the rejection of actions that cannot be performed given a certain state transition.
    """

    def __init__(self, result_container):
        """init method for `StateMachine`. Takes `main` module `result_container`.
        the 'super' parent class which is the gui"""

        self.exp_data = ExperimentProcessData()

        self.arduino_controller = ArduinoManager(self.exp_data)

        self.main_gui = MainGUI(self.exp_data, self.trigger, self.arduino_controller)
        logging.info("GUI started successfully.")

        self.state = "IDLE"
        """Default state for program is set at IDLE"""

        self.prev_state = None
        """Default previous state for program is set to None. Utilized in `trigger`."""

        self.app_result = result_container
        """
        Here we store a reference to `main` module `result_container` to store decision of whether to restart the 
        program or just terminate the current instance.
        """

        self.transitions = {
            ("IDLE", "GENERATE SCHEDULE"): "GENERATE SCHEDULE",
            (
                "GENERATE SCHEDULE",
                "IDLE",
            ): "IDLE",
            ("IDLE", "START"): "START PROGRAM",
            ("IDLE", "RESET"): "RESET PROGRAM",
            ("STOP PROGRAM", "RESET"): "RESET PROGRAM",
            ("START PROGRAM", "ITI"): "ITI",
            ("ITI", "DOOR OPEN"): "OPENING DOOR",
            ("OPENING DOOR", "TTC"): "TTC",
            ("TTC", "SAMPLE"): "SAMPLE",  # -> if rat engages in trial
            ("TTC", "TRIAL END"): "TRIAL END",  # -> if rat does NOT engage
            ("SAMPLE", "TRIAL END"): "TRIAL END",
            ("TRIAL END", "ITI"): "ITI",  # -> save trial data, update gui, door up
            ("ITI", "STOP"): "STOP PROGRAM",  # can move to 'stop' state in all states
            ("OPENING DOOR", "STOP"): "STOP PROGRAM",
            ("TTC", "STOP"): "STOP PROGRAM",
            ("SAMPLE", "STOP"): "STOP PROGRAM",
            ("TRIAL END", "STOP"): "STOP PROGRAM",
        }
        """State transition table defines all transitions that the program can possibly take"""

        # don't start the mainloop until AFTER the gui is setup so that the app_result property
        # is available if reset is desired
        self.main_gui.mainloop()

    def trigger(self, event):
        """
        This function takes a requested state and decides if the transition from this state is allowed.

        Parameters
        ----------
        - **event** (*str*): Contains the desired state to move to.
        """

        transition = (self.state, event)
        self.prev_state = self.state
        new_state = None

        logger.info(f"state transition -> {transition}")

        # checking if the attemped transition is valid according to the table
        if transition in self.transitions:
            new_state = self.transitions[transition]
        else:
            # if the key is not in the transition table, handle rejection based on desired state
            self.reject_actions(event)

        # if the key was in the transition table, and the new state wants to reset the program, that means this is a valid action at this time. MAKE SURE the
        # user REALLY wants to do that
        if new_state == "RESET PROGRAM":
            response = GUIUtils.askyesno(
                "============WARNING============",
                "THIS ACTION WILL ERASE ALL DATA CURRENTLY STORED FOR THIS EXPERIMENT... ARE YOU SURE YOU WANT TO CONTINUE?",
            )
            # if true, go ahead with the reset, if false return to prev_state
            if not response:
                new_state = self.prev_state

        # if attempt to start program with no experiment schedule, tell user to do that
        if new_state == "START PROGRAM":
            if self.exp_data.program_schedule_df.empty:
                GUIUtils.display_error(
                    "Experiement Schedule Not Yet Generated!!!",
                    "Please generate the program schedule before attempting to start the experiment. You can do this by clicking the 'Valve / Stimuli' button in the main screen.",
                )
                new_state = self.prev_state

        # if we have a new state, perform the associated action for that state
        if new_state:
            logger.info(f"new state -> {new_state}")
            self.execute_state(new_state)

    def execute_state(self, new_state: str) -> None:
        """
        Executes the action corresponding to new_state. if the action is defined under state_target,
        that action will be taken in a new thread to avoid overloading the main tkinter thread. otherwise
        it is executed immediately in the main thread.

        Parameters
        ----------
        - **new_state** (*str*): Contains the desired state to move to. Used to locate the desired action.
        """

        thread_target = None

        match new_state:
            case "START PROGRAM":

                def thread_target():
                    StartProgram(
                        self.exp_data,
                        self.main_gui,
                        self.arduino_controller,
                        self.trigger,
                    )
            case "RESET PROGRAM":
                ResetProgram(self.main_gui, self.app_result, self.arduino_controller)
            case "STOP PROGRAM":
                StopProgram(self.main_gui, self.arduino_controller, self.trigger)
            case "GENERATE SCHEDULE":
                # because this will run in main thread, we need to return early to avoid self.state
                # assignment confusion
                self.state = new_state
                GenerateSchedule(
                    self.main_gui,
                    self.arduino_controller,
                    self.process_queue,
                    self.trigger,
                )
                return
            case "ITI":

                def thread_target():
                    InitialTimeInterval(
                        self.exp_data,
                        self.main_gui,
                        new_state,
                        self.trigger,
                    )
            case "OPENING DOOR":

                def thread_target():
                    OpeningDoor(
                        self.exp_data,
                        self.main_gui,
                        self.arduino_controller,
                        new_state,
                        self.trigger,
                    )
            case "TTC":

                def thread_target():
                    TimeToContact(
                        self.exp_data,
                        self.arduino_controller,
                        self.main_gui,
                        new_state,
                        self.trigger,
                    )
            case "SAMPLE":

                def thread_target():
                    SampleTime(
                        self.exp_data,
                        self.main_gui,
                        self.arduino_controller,
                        new_state,
                        self.trigger,
                    )
            case "TRIAL END":

                def thread_target():
                    TrialEnd(
                        self.exp_data,
                        self.main_gui,
                        self.arduino_controller,
                        self.prev_state,
                        self.trigger,
                    )

        self.prev_state = self.state
        self.state = new_state

        if thread_target:
            threading.Thread(target=thread_target).start()

    def process_queue(self, data_queue: queue.Queue[tuple[str, str]]) -> None:
        """
        Process the data queue. Pulls in data from the thread that is reading data from the arduinos constantly. if there is anything
        in the queue at time of function call, we will stay here until its all been dealt with.

        Parameters
        ----------
        - **data_queue** (*tuple[str, str]*): This is a shared queue between a thread initiated in the `controllers.arduino_control` module's
        `listen_for_serial` method. That thread constantly reads info from Arduino so it is not missed, and the main thread calls this process method
        to process accumulated data to avoid overloading the thread.
        """

        arduino_data = self.exp_data.arduino_data
        try:
            while not data_queue.empty():
                source, data = data_queue.get()
                arduino_data.process_data(source, data, self.state, self.trigger)

            # run this command every 250ms
            queue_ps_id = self.main_gui.after(
                250, lambda: self.process_queue(data_queue)
            )
            self.main_gui.scheduled_tasks["PROCESS QUEUE"] = queue_ps_id
        except Exception as e:
            logging.error(f"Error processing data queue: {e}")
            raise

    @staticmethod
    def reject_actions(event):
        """
        This method handles the rejection of the 'START' and 'RESET' actions. These are rejected when there is no state transition for their current state.
        This is usually during program runtime for reset or before schedule generation for start.

        Parameters
        ----------
        - **event** (*str*): This is the desired state being rejected here.
        """
        match event:
            case "RESET":
                GUIUtils.display_error(
                    "CANNOT PERFORM THIS ACTION",
                    "RESET cannot be performed during runtime. Stop the program to reset.",
                )
            # if key is not in table but we try to start (for example, STOP PROGRAM -> START) we do NOT want to allow this until a full reset has been completed
            case "START":
                GUIUtils.display_error(
                    "CANNOT PERFORM THIS ACTION",
                    "Experiement has already been executed. Before running another, you need to RESET the application to ensure all data is reset to defaults",
                )
            case _:
                return


class GenerateSchedule:
    """
    This class handles the schedule generation state. It is called once the user has input the amount of simuli for this experiment, the
    number of trial blocks, changed the names of the stimuli in each cylinder/valve in the 'Valve / Stimuli' window, and pressed generate schedule.

    The main things handled here are the updating of gui objects that needed the previously discussed info to be created (e.g raster plots need
    total trials, program schedule window needed the experiment data, etc.)
    """

    def __init__(
        self,
        main_gui: MainGUI,
        arduino_controller: ArduinoManager,
        process_queue: Callable[[queue.Queue[tuple[str, str]]], None],
        trigger: Callable[[str], None],
    ):
        """
        Initialize and handle the GenerateSchedule class state.

        Parameters
        ----------
        - **main_gui** (*MainGUI*): A reference to the `views.main_gui` MainGUI instance, this is used to update elements inside the GUI window(s). Here we use it to
        update show the program schedule and create raster plots.
        - **arduino_controller** (*ArduinoManager*): A reference to the `controllers.arduino_control` Arduino controller instance, this is the method by which the Arduino is communicated
        with in the program. Used to send schedules, variables, and valve durations here.
        - **process_queue** (*Callback method*): This callback method is passed here so that the Arduino listener process thread can be started once the listener thread
        is running. It does NOT run prior to this so that sending individual bytes (send schedule, etc.) is performed without having data stolen away by the constantly running
        listener thread.
        - **trigger** (*Callback method*): This callback is passed in so that this state can trigger a transition back to `IDLE` when it is finished with its work.
        """

        # show the program sched window via the callback passed into the class at initialization
        main_gui.show_secondary_window("Program Schedule")

        # create plots using generated number of trials as max Y values
        for window in main_gui.windows["Raster Plot"]:
            window.create_plot()

        # send exp variables, schedule, and valve open durations stored in arduino_data.toml to the arduino
        arduino_controller.send_experiment_variables()
        arduino_controller.send_schedule_data()
        arduino_controller.send_valve_durations()

        # start Arduino process queue and listener thread so we know when Arduino tries to tell us something
        process_queue(arduino_controller.data_queue)

        arduino_controller.listener_thread = threading.Thread(
            target=arduino_controller.listen_for_serial
        )

        arduino_controller.listener_thread.start()

        logger.info("Started listening thread for Arduino serial input.")

        # transition back to idle
        trigger("IDLE")


class StartProgram:
    """
    This class handles the remaining set-up steps to prepare for experiment runtime. It then triggers the experiment.
    """

    def __init__(
        self,
        exp_data: ExperimentProcessData,
        main_gui: MainGUI,
        arduino_controller: ArduinoManager,
        trigger: Callable[[str], None],
    ):
        """
        Parameters
        ----------
        - **exp_data** (*ExperimentProcessData*): Reference to the `models.experiment_process_data`. Here we use it to mark experiment and state start times.
        - **main_gui** (*MainGUI*): A reference to `views.main_gui` MainGUI instance, this is used to update elements inside the GUI window(s). Here we use it to
        update clock labels and max program runtime.
        - **arduino_controller** (*ArduinoManager*): A reference to the `controllers.arduino_control` instance, this is the method by which the Arduino is communicated
        with in the program. Used to tell Arduino that program begins now.
        - **trigger** (*Callback method*): This callback is passed in so that this state can trigger a transition to `ITI` when it is finished with its work.
        """
        try:
            # update experiment data model program start time and state start time variables with current time
            exp_data.start_time = time.time()
            exp_data.state_start_time = time.time()

            # tell Arduino that experiment starts now so it knows how to calculate timestamps
            start_command = "T=0\n".encode("utf-8")
            arduino_controller.send_command(command=start_command)

            main_gui.update_clock_label()
            main_gui.update_max_time()

            # change the green start button into a red stop button, update the associated command
            main_gui.start_button.configure(
                text="Stop", bg="red", command=lambda: trigger("STOP")
            )

            logging.info("==========EXPERIMENT BEGINS NOW==========")

            trigger("ITI")
        except Exception as e:
            logging.error(f"Error starting program: {e}")
            raise


class StopProgram:
    """
    Stops and updates program to reflect `IDLE` state.

    Methods
    -------
    - `finalize_program`(main_gui, arduino_controller)
        This method waits until the door closes for the last time, then cancels the last scheduled task, stops the listener thread, closes Arduino connections, and
        instructs the user to save their data.
    """

    def __init__(
        self,
        main_gui: MainGUI,
        arduino_controller: ArduinoManager,
        trigger: Callable[[str], None],
    ) -> None:
        """
        Parameters
        ----------
        - **main_gui** (*MainGUI*): A reference to `views.main_gui` MainGUI instance, this is used to update elements inside the GUI window(s). Here we use it to
        call update_on_stop, configure the start/stop button back to start, and cancel tkinter scheduled tasks.
        - **arduino_controller** (*ArduinoManager*): A reference to the `controllers.arduino_control` instance, this is the method by which the Arduino is communicated
        with in the program. Used to reset Arduino and clear all left-over experiment data.
        - **trigger** (*Callback method*): This callback is passed in so the start button can be configured to command a `START` state.
        """
        try:
            main_gui.update_on_stop()
            # change the command back to start for the start button. (STOP PROGRAM, START) is not a defined transition, so the
            # trigger function will call reject_actions to let the user know the program has already ran and they need to reset the app.
            main_gui.start_button.configure(
                text="Start", bg="green", command=lambda: trigger("START")
            )

            # stop all scheduled tasks EXCEPT for the process queue, we are still waiting for the last door close timestamp
            for desc, sched_task in main_gui.scheduled_tasks.items():
                if desc != "PROCESS QUEUE":
                    main_gui.after_cancel(sched_task)

            # schedule finalization after door will be down
            main_gui.scheduled_tasks["FINALIZE"] = main_gui.after(
                5000, lambda: self.finalize_program(main_gui, arduino_controller)
            )

            logging.info("Program stopped... waiting to finalize...")
        except Exception as e:
            logging.error(f"Error stopping program: {e}")
            raise

    def finalize_program(
        self, main_gui: MainGUI, arduino_controller: ArduinoManager
    ) -> None:
        """
        Finalize the program by resetting the Arduino board, offer to save the data frames into xlsx files.

        Parameters
        ----------
        - **main_gui** (*MainGUI*): A reference to `views.main_gui` MainGUI instance, this is used to update elements inside the GUI window(s). Here we use it to
        cancel the last tkinter.after call.
        - **arduino_controller** (*ArduinoManager*): A reference to the `controllers.arduino_control` instance, this is the method by which the Arduino is communicated
        with in the program. Used to reset Arduino board and close the connection to it.
        """
        try:
            # stop the arduino listener so that the program can shut down
            # and not be blocked
            arduino_controller.stop_listener_thread()

            queue_id = main_gui.scheduled_tasks["PROCESS QUEUE"]
            main_gui.after_cancel(queue_id)

            arduino_controller.close_connection()

            main_gui.save_button_handler()

            logging.info("Program finalized, arduino boards reset.")
        except Exception as e:
            logging.error(f"Error completing program: {e}")
            raise


class ResetProgram:
    """
    Handle resetting the program on click of the reset button. This class has no instance variable or methods.
    """

    def __init__(
        self, main_gui: MainGUI, app_result: list, arduino_controller: ArduinoManager
    ) -> None:
        try:
            # these two calls will stop the gui, halting the programs mainloop.
            main_gui.quit()
            main_gui.destroy()

            # cancel all scheduled tasks
            for sched_task in main_gui.scheduled_tasks.values():
                main_gui.after_cancel(sched_task)
            # if we have an listener thread and arduino connected, stop the thread and close the connection.
            if arduino_controller.listener_thread is not None:
                arduino_controller.stop_listener_thread()
            if arduino_controller.arduino is not None:
                arduino_controller.close_connection()

            # set first bit in app_result list to 1 to instruct main to restart.
            app_result[0] = 1

        except Exception as e:
            logging.error(f"Error resetting the program: {e}")


class InitialTimeInterval:
    """
    State class for initial time interval experiment state.
    """

    def __init__(
        self,
        exp_data: ExperimentProcessData,
        main_gui: MainGUI,
        state: str,
        trigger: Callable[[str], None],
    ) -> None:
        """
        This function transitions the program into the `ITI` state. It does this by resetting lick counts, setting new state time,
        updating the models, and setting the .after call to transition to TTC.

        Parameters
        ----------
        - **exp_data** (*ExperimentProcessData*): Reference to the `models.experiment_process_data`. Here we use it to get a reference to event_data to set trial
        licks to 0, get logical trial number, and get state duration time.
        - **main_gui** (*MainGUI*): A reference to `views.main_gui` MainGUI instance, this is used to update elements inside the GUI window(s). Here we use it to
        update GUI with new trial information and configure the state timer.
        - **state** (*str*): State is used to update GUI with current state and grab the state duration time from the program schedule df.
        - **trigger** (*Callback method*): This callback is passed in so the `OPENING DOOR` state can be triggered after the `ITI` time has passed.
        """
        try:
            # get a reference to the event_data from exp_data.
            event_data = exp_data.event_data

            # set trial licks to 0 for both sides
            event_data.side_one_licks = 0
            event_data.side_two_licks = 0

            # logical df rows will always be 1 behind the current trial because of zero based indexing in dataframes vs
            # 1 based for trials
            logical_trial = exp_data.current_trial_number - 1

            # Call gui updates needed every trial (e.g program schedule window highlighting, progress bar, trial stimuli, etc)
            # make sure we convert received vals to str to avoid type errors
            main_gui.update_on_new_trial(
                str(exp_data.program_schedule_df.loc[logical_trial, "Port 1"]),
                str(exp_data.program_schedule_df.loc[logical_trial, "Port 2"]),
            )

            # clear state timer and reset the state start time
            main_gui.state_timer_text.configure(text=(state + "Time:"))
            exp_data.state_start_time = time.time()

            initial_time_interval = exp_data.program_schedule_df.loc[
                logical_trial, state
            ]

            main_gui.update_on_state_change(initial_time_interval, state)

            # tell tkinter main loop that we want to trigger DOOR OPEN state after initial_time_interval milliseconds
            iti_ttc_transition = main_gui.after(
                int(initial_time_interval),
                lambda: trigger("DOOR OPEN"),
            )

            # add the transition to scheduled tasks dict so that
            main_gui.scheduled_tasks["ITI TO DOOR OPEN"] = iti_ttc_transition

            logging.info(
                f"STATE CHANGE: ITI BEGINS NOW for trial -> {exp_data.current_trial_number}, completes in {initial_time_interval}."
            )
        except Exception as e:
            logging.error(f"Error in initial time interval: {e}")
            raise


class OpeningDoor:
    """
    Intermediate state between `ITI` and `TTC`.
    """

    # we are going to need to pass in the arduino controller as well
    def __init__(
        self,
        exp_data: ExperimentProcessData,
        main_gui: MainGUI,
        arduino_controller: ArduinoManager,
        state: str,
        trigger: Callable[[str], None],
    ):
        """
        In the initialization steps for this state we command the door down, then wait `DOOR_MOVE_TIME` to move to the `TTC` state.
        """
        # send comment to arduino to move the door down
        down_command = "DOWN\n".encode("utf-8")
        arduino_controller.send_command(command=down_command)

        # after the door is down, then we will begin the ttc state logic, found in run_ttc
        main_gui.after(DOOR_MOVE_TIME, lambda: trigger("TTC"))

        # state start time begins
        exp_data.state_start_time = time.time()

        # show current_time / door close time to avoid confusion
        main_gui.update_on_state_change(DOOR_MOVE_TIME, state)


class TimeToContact:
    """
    State class for time to contact experiment state
    """

    def __init__(
        self,
        exp_data: ExperimentProcessData,
        arduino_controller: ArduinoManager,
        main_gui: MainGUI,
        state: str,
        trigger: Callable[[str], None],
    ):
        """
        This function transitions the program into the `TTC` state. We can only reach this state from `OPENING DOOR`.

        We transition into `TTC` by resetting the state timer, instructing the Arduino that the trial has started, and scheduling a transition into
        `TRIAL END` if the rat does not engage in this trial. This is cancelled in sample time if 3 licks or more from `TTC` are detected in the `models.arduino_data`
        module's `handle_licks` method.

        Parameters
        ----------
        - **exp_data** (*ExperimentProcessData*): Reference to the `models.experiment_process_data`. Here we use it to get a reference to event_data to reset state time
        and find `TTC` state time.
        - **arduino_controller** (*ArduinoManager*): A reference to the `controllers.arduino_control` instance, this is the method by which the Arduino is communicated
        with in the program. Used here to tell Arduino board trial has begun.
        - **main_gui** (*MainGUI*): A reference to `views.main_gui` MainGUI instance, this is used to update elements inside the GUI window(s). Here we use it to
        update GUI with new state time.
        - **state** (*str*): State is used to update GUI with current state and grab the state duration time from the program schedule df.
        - **trigger** (*Callback method*): This callback is passed in so the `TRIAL END` state can be triggered if trial is not engaged.
        """
        try:
            logging.info(
                f"STATE CHANGE: DOOR OPEN -> TTC NOW for trial -> {exp_data.current_trial_number}."
            )

            logical_trial = exp_data.current_trial_number - 1

            # tell the arduino that the trial begins now, becuase the rats are able to licks beginning now
            command = "TRIAL START\n".encode("utf-8")
            arduino_controller.send_command(command)

            main_gui.state_timer_text.configure(text=(state + " Time:"))

            # state time starts now, as does trial because lick availabilty starts now
            exp_data.state_start_time = time.time()
            exp_data.trial_start_time = time.time()

            # find the amount of time available for TTC for this trial
            time_to_contact = exp_data.program_schedule_df.loc[logical_trial, state]

            main_gui.update_on_state_change(time_to_contact, state)

            # set a state change to occur after the time_to_contact time, this will be cancelled if the laser arduino
            # sends 3 licks befote the TTC_time
            ttc_iti_transition = main_gui.after(
                int(time_to_contact), lambda: trigger("TRIAL END")
            )

            # store this task id so that it can be cancelled if the sample time transition is taken.
            main_gui.scheduled_tasks["TTC TO TRIAL END"] = ttc_iti_transition

            logging.info(
                f"STATE CHANGE: TTC BEGINS NOW for trial -> {exp_data.current_trial_number}, completes in {time_to_contact}."
            )
        except Exception as e:
            logging.error(f"Error in TTC state start: {e}")
            raise


class SampleTime:
    """
    Sample state class to handle setup of `Sample` state.
    """

    def __init__(
        self,
        exp_data: ExperimentProcessData,
        main_gui: MainGUI,
        arduino_controller: ArduinoManager,
        state: str,
        trigger: Callable[[str], None],
    ):
        """
        This function transitions the program into the `SAMPLE` state. We can only reach this state from `TTC` if 3 licks or more are detected in `TTC`.

        We transition into `SAMPLE` by resetting licks to zero to count only sample time licks for trial, updating the actual `TTC` time taken before engaging in the
        trial, cancelling the scheduled `TTC` to `TRIAL END` transition, instructing Arduino to begin opening valves when licks occur, and updating state start time.

        Parameters
        ----------
        - **exp_data** (*ExperimentProcessData*): Reference to the `models.experiment_process_data`. Here we use it to get a reference to event_data to reset state time
        and find `SAMPLE` state time, reset trial lick data.
        - **main_gui** (*MainGUI*): A reference to `views.main_gui` MainGUI instance, this is used to update elements inside the GUI window(s). Here we use it to
        update GUI with new state info and cancel `TTC` to `TRIAL END` transition.
        - **arduino_controller** (*ArduinoManager*): A reference to the `controllers.arduino_control` instance, this is the method by which the Arduino is communicated
        with in the program. Used here to tell Arduino to begin opening valves when licks are detected.
        - **state** (*str*): State is used to update GUI with current state and grab the state duration time from the program schedule df.
        - **trigger** (*Callback method*): This callback is passed in so the `TRIAL END` state can be triggered after `SAMPLE` time.

        Methods
        -------
        - `update_ttc_time`(exp_data, logical_trial)
        Updates program schedule dataframe with actual time used in the `TTC` state.
        """
        try:
            logical_trial = exp_data.current_trial_number - 1

            event_data = exp_data.event_data

            # reset trial licks to count only sample licks
            event_data.side_one_licks = 0
            event_data.side_two_licks = 0

            self.update_ttc_time(exp_data, logical_trial)

            # since the trial was engaged, cancel the planned transition from ttc to trial end. program has branched to new state
            main_gui.after_cancel(main_gui.scheduled_tasks["TTC TO TRIAL END"])

            # Tell the laser arduino to begin accepting licks and opening valves
            # resetting the lick counters for both spouts
            # tell the laser to begin opening valves on licks
            open_command = "BEGIN OPEN VALVES\n".encode("utf-8")
            arduino_controller.send_command(command=open_command)

            exp_data.state_start_time = time.time()

            sample_interval_value = exp_data.program_schedule_df.loc[
                logical_trial, state
            ]

            main_gui.update_on_state_change(sample_interval_value, state)

            main_gui.after(
                int(sample_interval_value),
                lambda: trigger("TRIAL END"),
            )

            logging.info(
                f"STATE CHANGE: SAMPLE BEGINS NOW for trial-> {exp_data.current_trial_number}, completes in {sample_interval_value}."
            )
        except Exception as e:
            logging.error(
                f"Error in sample time trial no. {exp_data.current_trial_number}: {e}"
            )
            raise

    def update_ttc_time(
        self, exp_data: ExperimentProcessData, logical_trial: int
    ) -> None:
        """
        If we reach this code that means the rat licked at least 3 times in `TTC` state
        so we didn't take all the allocated time. update program schedule window with actual time taken
        """
        ttc_time = (time.time() - exp_data.state_start_time) * 1000

        exp_data.program_schedule_df.loc[logical_trial, "TTC Actual"] = round(
            ttc_time, 3
        )


class TrialEnd:
    """
    Handle end of trial operations such as data storage and GUI updates with gathered trial data.

    Methods
    -------
    - `arduino_trial_end`(arduino_controller): Handle Arduino end of trial, send door up, stop accepting licks.
    - `end_trial`(exp_data: ExperimentProcessData): Determine if this trial is the last, if not increment trial number in `models.experiment_process_data`.
    - `handle_from_ttc`(logical_trial, trigger), exp_data): Call `update_ttc_actual` to update TTC time. Trigger transition to `ITI`.
    - `update_schedule_licks`(logical_trial, exp_data) -> None: Update program schedule df with licks for this trial on each port.
    - `update_raster_plots`(exp_data, logical_trial, main_gui) -> None: Update raster plot with licks from this trial.
    """

    def __init__(
        self,
        exp_data: ExperimentProcessData,
        main_gui: MainGUI,
        arduino_controller: ArduinoManager,
        prev_state: str,
        trigger: Callable[[str], None],
    ) -> None:
        """
        This function transitions the program into the `SAMPLE` state. We can only reach this state from `TTC` if 3 licks or more are detected in `TTC`.

        We transition into `SAMPLE` by resetting licks to zero to count only sample time licks for trial, updating the actual `TTC` time taken before engaging in the
        trial, cancelling the scheduled `TTC` to `TRIAL END` transition, instructing Arduino to begin opening valves when licks occur, and updating state start time.

        Parameters
        ----------
        - **exp_data** (*ExperimentProcessData*): Reference to the `models.experiment_process_data`. Here we use it to update program df with trial licks, increment trial,
        check if current trial is the final trial, and other data operations.
        - **main_gui** (*MainGUI*): A reference to `views.main_gui` MainGUI instance, this is used to update elements inside the GUI window(s). Here we use it to
        update program schedule and populate raster plots with trial licks.
        - **arduino_controller** (*ArduinoManager*): A reference to the `controllers.arduino_control` instance, this is the method by which the Arduino is communicated
        with in the program. Used here to tell Arduino to stop opening valves when licks are detected.
        - **prev_state** (*str*): prev_state is used to decide which end of trial operations should be executed.
        - **trigger** (*Callback method*): This callback is passed in so the `ITI` state can be triggered after `TRIAL END` logic is complete.

        Methods
        -------
        - `update_ttc_time`(exp_data, logical_trial)
        Updates program schedule dataframe with actual time used in the `TTC` state.
        """

        # use the same logical trial for all functions current_trial_number - 1
        # to account for 1 indexing
        logical_trial = exp_data.current_trial_number - 1

        self.arduino_trial_end(arduino_controller)

        #######TRIAL NUMBER IS INCREMENTED INSIDE OF END_TRIAL#######
        if self.end_trial(exp_data):
            program_schedule = main_gui.windows["Program Schedule"]
            # if the experiment is over update the licks for the final trial
            self.update_schedule_licks(logical_trial, exp_data)
            program_schedule.refresh_end_trial(logical_trial)

            trigger("STOP")
            # return from the call / kill the working thread
            return

        # update licks for this trial
        self.update_schedule_licks(logical_trial, exp_data)

        match prev_state:
            case "TTC":
                self.update_ttc_actual(logical_trial, exp_data)
                trigger("ITI")
            case "SAMPLE":
                self.update_raster_plots(exp_data, logical_trial, main_gui)
                trigger("ITI")
            case _:
                # cases not explicitly defined go here
                logger.error("UNDEFINED PREVIOUS TRANSITION IN TRIAL END STATE")

        main_gui.windows["Program Schedule"].refresh_end_trial(logical_trial)

    def arduino_trial_end(self, arduino_controller: ArduinoManager) -> None:
        """
        Send rig door up and tell Arduino to stop accepting licks.
        """
        up_command = "UP\n".encode("utf-8")
        arduino_controller.send_command(command=up_command)

        stop_command = "STOP OPEN VALVES\n".encode("utf-8")
        arduino_controller.send_command(command=stop_command)

    def end_trial(self, exp_data: ExperimentProcessData) -> bool:
        """
        This method checks if current trial is the last trial. If it is, we return true to the calling code.
        If false, we increment current_trial_number, return false, and proceed to next trial.
        """
        current_trial = exp_data.current_trial_number
        max_trials = exp_data.exp_var_entries["Num Trials"]

        if current_trial >= max_trials:
            return True

        exp_data.current_trial_number += 1
        return False

    def update_ttc_actual(
        self, logical_trial: int, exp_data: ExperimentProcessData
    ) -> None:
        """
        Update the actual ttc time take in the program schedule with the max time value,
        since we reached trial end we know we took the max time allowed
        """
        program_df = exp_data.program_schedule_df

        ttc_column_value = program_df.loc[logical_trial, "TTC"]
        program_df.loc[logical_trial, "TTC Actual"] = ttc_column_value

    def update_schedule_licks(
        self, logical_trial: int, exp_data: ExperimentProcessData
    ) -> None:
        """Update the licks for each side in the program schedule df for this trial"""
        program_df = exp_data.program_schedule_df
        event_data = exp_data.event_data

        licks_sd_one = event_data.side_one_licks
        licks_sd_two = event_data.side_two_licks

        program_df.loc[logical_trial, "Port 1 Licks"] = licks_sd_one

        program_df.loc[logical_trial, "Port 2 Licks"] = licks_sd_two

    def update_raster_plots(
        self, exp_data: ExperimentProcessData, logical_trial: int, main_gui: MainGUI
    ) -> None:
        """Instruct raster windows to update with new lick timestamps"""
        # gather lick timestamp data from the event data model
        lick_stamps = exp_data.event_data.get_lick_timestamps(logical_trial)

        # send it to raster windows
        for i, window in enumerate(main_gui.windows["Raster Plot"]):
            window.update_plot(lick_stamps[i], logical_trial)
