"""
'app_logic' is the primary module in the Photologic-Experiment-Rig codebase. It contains the
StateMachine class which holds the logic for each 'state' an experiment can be in.

Before performing any actions, the StateMachine class initializes the `src.TkinterApp` class, which launches
a tkinter root and allows for a GUI to be created for the program.

This module is launched from main to make restarting the program easier, which is done by destroying the
instance of state machine and launcing a new one.
"""

from tk_app import TkinterApp
import time
import threading
import logging
import toml

from views.gui_common import GUIUtils
import system_config

logger = logging.getLogger(__name__)
"""Created in TkinterApp, this is used to log warnings and errors in the program"""


RIG_CONFIG = system_config.get_rig_config()
"""This utilizes `system_config` module """
with open(RIG_CONFIG, "r") as f:
    DOOR_CONFIG = toml.load(f)["door_motor_config"]

# pull total valves constant from toml config
DOOR_MOVE_TIME = DOOR_CONFIG["DOOR_MOVE_TIME"]


class StateMachine(TkinterApp):
    """
    This class is the heart of the program. It inherits TkinterApp to create a gui, instantiate model (data) classes, and the arduino controller,
    then defines and handles program state transitions. It coordinates co-operation between view (gui) and models (data). State transitions are
    handled by the 'trigger' function.
    """

    def __init__(self, result_container):
        # init the 'super' parent class which is the gui
        super().__init__()
        # default state is idle
        self.state = "IDLE"
        self.prev_state = None
        # used to make decision of whether to restart the program or just terminate
        self.app_result = result_container
        # define state transitions that the program can possibly take
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

        # don't start the mainloop until AFTER the gui is setup so that the app_result property
        # is available if reset is desired
        self.main_gui.mainloop()

    def trigger(self, event):
        """This function takes a requested state and decides if the transition from this state is allowed."""
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

    def execute_state(self, new_state: str):
        """
        takes the key for the transition table (from_state, to_state) and resulting_state, and executes
        the action corresponding to new_state, based upon key. if the action is defined under state_target,
        that action will be taken in a new thread to avoid overloading the main tkinter thread. otherwise
        it is executed immediately in the main thread.
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
                        self.arduino_controller,
                        self.prev_state,
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

    def process_queue(self, data_queue):
        """
        Process the data queue. Pulls in data from the thread that is reading data from the arduinos constantly. if there is anything
        in the queue at time of function call, we will stay here until its all been dealt with.
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
    def __init__(self, main_gui, arduino_controller, process_queue, trigger):
        self.main_gui = main_gui
        self.arduino_controller = arduino_controller
        self.trigger_state_change = trigger

        # show the program sched window via the callback passed into the class at initialization
        self.main_gui.show_secondary_window("Program Schedule")

        for window in self.main_gui.windows["Raster Plot"]:
            window.create_plot()

        # send valve open durations stored in arduino_data.toml to the arduino
        self.arduino_controller.send_experiment_variables()
        self.arduino_controller.send_experiment_schedule()

        self.arduino_controller.send_valve_durations()

        process_queue(self.arduino_controller.data_queue)

        self.arduino_controller.listener_thread = threading.Thread(
            target=self.arduino_controller.listen_for_serial
        )

        self.arduino_controller.listener_thread.start()

        logger.info("Started listening thread for Arduino serial input.")
        self.trigger_state_change("IDLE")


class StartProgram:
    def __init__(self, exp_data, main_gui, arduino_controller, trigger):
        try:
            self.exp_data = exp_data
            self.exp_data.start_time = time.time()
            self.exp_data.state_start_time = time.time()

            self.main_gui = main_gui
            self.arduino_controller = arduino_controller

            start_command = "T=0\n".encode("utf-8")
            self.arduino_controller.send_command(command=start_command)

            self.main_gui.update_clock_label()

            # update main_guis max experiment runtime
            self.main_gui.update_max_time()

            # change the green start button into a red stop button, update the associated command
            self.main_gui.start_button.configure(
                text="Stop", bg="red", command=lambda: trigger("STOP")
            )

            logging.info("==========EXPERIMENT BEGINS NOW==========")
            trigger("ITI")
        except Exception as e:
            logging.error(f"Error starting program: {e}")
            raise


class StopProgram:
    """
    Updates GUI to reflect IDLE state,
    """

    def __init__(self, main_gui, arduino_controller, trigger) -> None:
        self.main_gui = main_gui
        self.arduino_controller = arduino_controller
        try:
            self.main_gui.update_on_stop()
            # change the command back to start for the start button. (STOP PROGRAM, START) is not a defined transition, so the
            # trigger function will call reject_actions to let the user know the program has already ran and they need to reset the app.
            self.main_gui.start_button.configure(
                text="Start", bg="green", command=lambda: trigger("START")
            )

            for desc, sched_task in self.main_gui.scheduled_tasks.items():
                if desc != "PROCESS QUEUE":
                    self.main_gui.after_cancel(sched_task)

            # finalize the program after 5 seconds because the door has not gone down yet. we still want the arduino
            # to record the time that the door goes up last
            self.main_gui.scheduled_tasks["FINALIZE"] = self.main_gui.after(
                5000, lambda: self.finalize_program()
            )
            logging.info("Program stopped... waiting to finalize...")
        except Exception as e:
            logging.error(f"Error stopping program: {e}")
            raise

    def finalize_program(self) -> None:
        """
        Finalize the program by telling arduino to send the door up/down timestamps that it has, reset both Arduino boards,
        offer to save the .
        """
        try:
            # stop the arduino listener so that the program can shut down
            # and not be blocked
            self.arduino_controller.stop_listener_thread()

            queue_id = self.main_gui.scheduled_tasks["PROCESS QUEUE"]
            self.main_gui.after_cancel(queue_id)

            self.arduino_controller.close_connection()

            self.main_gui.save_button_handler()

            logging.info("Program finalized, arduino boards reset.")
        except Exception as e:
            logging.error(f"Error completing program: {e}")
            raise


class ResetProgram:
    """
    Handle resetting the program on click of the reset button.
    """

    def __init__(self, main_gui, app_result, arduino_controller) -> None:
        try:
            # these two calls will stop the gui, halting the programs mainloop.

            main_gui.quit()
            main_gui.destroy()

            for desc, sched_task in main_gui.scheduled_tasks.items():
                main_gui.after_cancel(sched_task)
            if arduino_controller.listener_thread is not None:
                arduino_controller.stop_listener_thread()
            if arduino_controller.arduino is not None:
                arduino_controller.close_connection()

            # tell main.py to restart
            app_result[0] = 1

        except Exception as e:
            logging.error(f"Error resetting the program: {e}")


class InitialTimeInterval:
    """
    State class for initial time interval experiment state. Updates program schedule window with new trial highighting and info.
    """

    def __init__(
        self, exp_data, main_gui, arduino_controller, prev_state, state, trigger
    ) -> None:
        self.prev_state = prev_state
        self.exp_data = exp_data
        self.event_data = self.exp_data.event_data
        self.main_gui = main_gui
        self.arduino_controller = arduino_controller

        # logical df rows will always be 1 behind the current trial because of zero based indexing in dataframes vs
        # 1 based for trials
        self.logical_trial = self.exp_data.current_trial_number - 1

        # updates prog_sched highlihgting, main gui trial stimuli, progress bar
        self.main_gui.update_on_new_trial(
            self.exp_data.program_schedule_df.loc[self.logical_trial, "Port 1"],
            self.exp_data.program_schedule_df.loc[self.logical_trial, "Port 2"],
        )

        self.trigger_state_change = trigger
        self.state = state
        self.execute_iti()

    def execute_iti(self):
        """
        This function transitions the program into the iti state. it does this by resetting lick counts, setting new state time,
        updating the models, and setting the .after call to transition to TTC.
        """
        try:
            self.event_data.side_one_licks = 0
            self.event_data.side_two_licks = 0

            self.main_gui.state_timer_text.configure(text=(self.state + "Time:"))
            self.exp_data.state_start_time = time.time()

            initial_time_interval = self.exp_data.program_schedule_df.loc[
                self.logical_trial, self.state
            ]

            self.main_gui.update_on_state_change(initial_time_interval, self.state)

            # tell tkinter main loop that we want to call trigger with TTC parameter after initial_time_interval milliseconds
            iti_ttc_transition = self.main_gui.after(
                int(initial_time_interval),
                lambda: self.trigger_state_change("DOOR OPEN"),
            )

            self.main_gui.scheduled_tasks["ITI TO DOOR OPEN"] = iti_ttc_transition

            logging.info(
                f"STATE CHANGE: ITI BEGINS NOW for trial -> {self.exp_data.current_trial_number}, completes in {initial_time_interval}."
            )
        except Exception as e:
            logging.error(f"Error in initial time interval: {e}")
            raise


class OpeningDoor:
    # we are going to need to pass in the arduino controller as well
    def __init__(self, exp_data, main_gui, arduino_controller, state, trigger):
        self.exp_data = exp_data
        self.main_gui = main_gui
        self.arduino_controller = arduino_controller

        self.state = state
        self.trigger_state_change = trigger

        # send comment to arduino to move the door down
        down_command = "DOWN\n".encode("utf-8")
        self.arduino_controller.send_command(command=down_command)

        # after the door is down, then we will begin the ttc state logic, found in run_ttc
        self.main_gui.after(DOOR_MOVE_TIME, lambda: self.trigger_state_change("TTC"))

        # state start time begins
        self.exp_data.state_start_time = time.time()
        self.main_gui.clear_state_time()

        # show current_time / door close time to avoid confusion
        self.main_gui.update_on_state_change(DOOR_MOVE_TIME, self.state)


class TimeToContact:
    """
    State class for time to contact experiment state
    """

    def __init__(self, exp_data, arduino_controller, main_gui, state, trigger):
        """
        this is the initial transition state that occurs every single time we transition to TTC
        """
        self.exp_data = exp_data
        self.arduino_controller = arduino_controller
        self.main_gui = main_gui
        self.state = state
        self.trigger_state_change = trigger

        self.logical_trial = self.exp_data.current_trial_number - 1

        self.run_ttc()

        try:
            logging.info(
                f"STATE CHANGE: DOOR OPEN -> TTC NOW for trial -> {self.exp_data.current_trial_number}."
            )
        except Exception as e:
            logging.error(f"Error in ITI to TTC transition: {e}")
            raise

    def run_ttc(self):
        try:
            # tell the arduino that the trial begins now, becuase the rats are able to licks beginning now
            command = "TRIAL START\n".encode("utf-8")
            self.arduino_controller.send_command(command)

            self.main_gui.state_timer_text.configure(text=(self.state + " Time:"))

            # state time starts now, as does trial because lick availabilty starts now
            self.exp_data.state_start_time = time.time()
            self.exp_data.trial_start_time = time.time()

            # find the amount of time available for TTC for this trial
            time_to_contact = self.exp_data.program_schedule_df.loc[
                self.logical_trial, self.state
            ]

            self.main_gui.update_on_state_change(time_to_contact, self.state)

            # set a state change to occur after the time_to_contact time, this will be cancelled if the laser arduino
            # sends 3 licks befote the TTC_time
            ttc_iti_transition = self.main_gui.after(
                int(time_to_contact), lambda: self.trigger_state_change("TRIAL END")
            )

            # store this task id so that it can be cancelled if the sample time transition is taken.
            self.main_gui.scheduled_tasks["TTC TO TRIAL END"] = ttc_iti_transition

            logging.info(
                f"STATE CHANGE: TTC BEGINS NOW for trial -> {self.exp_data.current_trial_number}, completes in {time_to_contact}."
            )
        except Exception as e:
            logging.error(f"Error in time to contact: {e}")
            raise


class SampleTime:
    """
    Sample time state. Sample time will be setup and executed every time an inststance of the class is created.
    """

    def __init__(self, exp_data, main_gui, arduino_controller, state, trigger):
        self.exp_data = exp_data
        self.event_data = self.exp_data.event_data
        self.main_gui = main_gui
        self.arduino_controller = arduino_controller

        self.state = state
        self.logical_trial = self.exp_data.current_trial_number - 1

        try:
            self.update_ttc_time()

            # since the trial was engaged, cancel the planned transition from ttc to trial end. program has branched to new state
            self.main_gui.after_cancel(
                self.main_gui.scheduled_tasks["TTC TO TRIAL END"]
            )

            # Tell the laser arduino to begin accepting licks and opening valves
            # resetting the lick counters for both spouts
            # tell the laser to begin opening valves on licks
            open_command = "BEGIN OPEN VALVES\n".encode("utf-8")
            self.arduino_controller.send_command(command=open_command)

            self.event_data.side_one_licks = 0
            self.event_data.side_two_licks = 0

            self.exp_data.state_start_time = time.time()

            sample_interval_value = self.exp_data.program_schedule_df.loc[
                self.logical_trial, self.state
            ]

            self.main_gui.update_on_state_change(sample_interval_value, self.state)

            self.main_gui.after(
                int(sample_interval_value),
                lambda: trigger("TRIAL END"),
            )

            logging.info(
                f"STATE CHANGE: SAMPLE BEGINS NOW for trial-> {self.exp_data.current_trial_number}, completes in {sample_interval_value}."
            )
        except Exception as e:
            logging.error(
                f"Error in sample time trial no. {self.exp_data.current_trial_number}: {e}"
            )
            raise

    def update_ttc_time(self):
        # if we are coming from ttc that means the rat licked at least 3 times in ttc
        # so we didn't take all the allocated time. update program schedule window with actual time taken
        ttc_time = (time.time() - self.exp_data.state_start_time) * 1000

        self.exp_data.program_schedule_df.loc[self.logical_trial, "TTC Actual"] = round(
            ttc_time, 3
        )


class TrialEnd:
    def __init__(
        self, exp_data, main_gui, arduino_controller, prev_state, trigger
    ) -> None:
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

        match prev_state:
            case "TTC":
                self.handle_from_ttc(logical_trial, trigger, exp_data)
            case "SAMPLE":
                self.handle_from_sample(logical_trial, main_gui, exp_data, trigger)
            case _:
                # cases not explicitly defined go here
                logger.error("UNDEFINED PREVIOUS TRANSITION IN TRIAL END STATE")

        main_gui.windows["Program Schedule"].refresh_end_trial(logical_trial)

    def arduino_trial_end(self, arduino_controller):
        up_command = "UP\n".encode("utf-8")
        arduino_controller.send_command(command=up_command)

        stop_command = "STOP OPEN VALVES\n".encode("utf-8")
        arduino_controller.send_command(command=stop_command)

    def end_trial(self, exp_data) -> bool:
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

    def handle_from_ttc(self, logical_trial: int, trigger, exp_data) -> None:
        """
        Handle the case that we are ending a trial after a TTC state. Rat did not engage in this trial.
        """
        self.update_ttc_actual(logical_trial, exp_data)
        self.update_schedule_licks(logical_trial, exp_data)

        trigger("ITI")

    def handle_from_sample(self, logical_trial: int, main_gui, exp_data, trigger):
        """
        Handle the case that we are ending a trial after a Sample state. Rat engaged in this trial.
        TTC time is not handled here because it would be impossible to grab that time at this point.
        Differs in TTC becuase actual ttc == allocated time can be grabbed at any later time in the program.
        """

        self.update_schedule_licks(logical_trial, exp_data)

        self.update_raster_plots(exp_data, logical_trial, main_gui)

        trigger("ITI")

    def update_ttc_actual(self, logical_trial: int, exp_data) -> None:
        """
        Update the actual ttc time take in the program schedule with the max time value,
        since we reached trial end we know we took the max time allowed
        """
        program_df = exp_data.program_schedule_df

        ttc_column_value = program_df.loc[logical_trial, "TTC"]
        program_df.loc[logical_trial, "TTC Actual"] = ttc_column_value

    def update_schedule_licks(self, logical_trial: int, exp_data) -> None:
        """Update the licks for each side in the program schedule df for this trial"""
        program_df = exp_data.program_schedule_df
        event_data = exp_data.event_data

        licks_sd_one = event_data.side_one_licks
        licks_sd_two = event_data.side_two_licks

        program_df.loc[logical_trial, "Port 1 Licks"] = licks_sd_one

        program_df.loc[logical_trial, "Port 2 Licks"] = licks_sd_two

    def update_raster_plots(self, exp_data, logical_trial, main_gui) -> None:
        """instruct raster windows to update with new lick timestamps"""
        # gather lick timestamp data from the event data model
        lick_stamps = exp_data.event_data.get_lick_timestamps(logical_trial)

        # send it to raster windows
        for i, window in enumerate(main_gui.windows["Raster Plot"]):
            window.update_plot(lick_stamps[i], logical_trial)
