from tk_app import TkinterApp
import time
import threading
import logging

from views.gui_common import GUIUtils

# number of milliseconds it takes for the door to close
DOOR_MOTOR_CLOSE_TIME = 2238

logger = logging.getLogger(__name__)


class StateMachine(TkinterApp):
    """
    This class is the heart of the program. It inherits TkinterApp to create a gui, then defines and handles program state transitions.
    It coordinates co-operation between view (gui), models (data), and controllers (arduino).
    """

    def __init__(self, result_container):
        # init the 'super' parent class which is the gui
        super().__init__()
        # default state is idle
        self.state = "IDLE"
        self.prev_state = None
        # used to make decision of whether to restart the program
        self.app_result = result_container
        # define state transitions that the program can possibly take
        self.transitions = {
            ("IDLE", "START"): "START PROGRAM",
            ("IDLE", "RESET"): "RESET PROGRAM",
            ("STOP", "RESET"): "RESET PROGRAM",
            ("START PROGRAM", "ITI"): "ITI",
            ("ITI", "TTC"): "TTC",
            ("TTC", "SAMPLE"): "SAMPLE",
            ("TTC", "ITI"): "ITI",
            ("SAMPLE", "ITI"): "ITI",
            ("ITI", "STOP"): "STOP PROGRAM",
            ("TTC", "STOP"): "STOP PROGRAM",
            ("SAMPLE", "STOP"): "STOP PROGRAM",
            ("UPDATE MODEL", "STOP"): "STOP PROGRAM",
        }

        # don't start the mainloop until AFTER the gui is setup so that the app_result property
        # is available if reset is desired
        self.main_gui.mainloop()

    def trigger(self, event):
        transition = (self.state, event)
        self.prev_state = self.state
        new_state = None

        print(transition)
        # checking if the attemped transition is valid according to the table
        if transition in self.transitions:
            new_state = self.transitions[transition]
        # if the key is not in the transition table and we requested a reset, don't do that yet
        elif event == "RESET":
            GUIUtils.display_error(
                "CANNOT PERFORM THIS ACTION",
                "RESET cannot be performed during runtime. Stop the program to reset.",
            )
        # if key is not in table but we try to start (for example, STOP PROGRAM -> START) we do NOT want to allow this until a full reset has been completed
        elif event == "START":
            GUIUtils.display_error(
                "CANNOT PERFORM THIS ACTION",
                "Experiement has already been executed. Before running another, you need to RESET the application to ensure all data is reset to defaults",
            )
        else:
            return

        response = None
        # if the key was in the transition table, and the new state wants to reset the program, that means this is a valid action at this time. MAKE SURE the
        # user REALLY wants to do that
        if new_state == "RESET PROGRAM":
            response = GUIUtils.askyesno(
                "============WARNING============",
                "THIS ACTION WILL ERASE ALL DATA CURRENTLY STORED FOR THIS EXPERIMENT... ARE YOU SURE YOU WANT TO CONTINUE?",
            )
            # if true, go ahead with the reset, if no return to prev_state
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

        # if we have a new state, do the thing associated with that state
        if new_state:
            print(new_state)
            self.execute_state(new_state)

    def execute_state(self, new_state):
        """
        takes the key for the transition table (from_state, to_state) and resulting_state, and executes
        the action corresponding to new_state, based upon key
        """
        state_target = None
        match new_state:
            case "START PROGRAM":

                def state_target():
                    StartProgram(self.exp_data, self.main_gui, self.trigger)
            case "RESET PROGRAM":
                self.reset_program()
            case "STOP PROGRAM":
                self.stop_program()
            case "ITI":
                # if the experiment is over update the licks and ttc time for the last trial?

                #    self.program_schedule_window.update_licks(logical_trial + 1)
                #    self.program_schedule_window.update_ttc_actual(logical_trial + 1)
                def state_target():
                    InitialTimeInterval(
                        self.exp_data,
                        self.prev_state,
                        new_state,
                        self.main_gui,
                        self.trigger,
                    )
            case "TTC":
                TimeToContact(self.exp_data, self.main_gui, new_state, self.trigger)
            case "SAMPLE":
                SampleTime(self.exp_data, self.main_gui, new_state, self.trigger)

        self.prev_state = self.state
        self.state = new_state

        if state_target:
            threading.Thread(target=state_target()).start()

    def reset_program(self) -> None:
        """
        Handle resetting the program on click of the reset button. askyesno will confirm the uesr wants to erase all data.
        if yes, we will quit the mainloop of the gui and destroy it and then update the app return value at index 0 passed
        in from the main module this will begin a new StateMachine instance, effectively restarting the prgram.
        """
        try:
            self.main_gui.quit()
            self.main_gui.destroy()
            self.app_result[0] = 1

        except Exception as e:
            logging.error(f"Error in reset button handler: {e}")

    def stop_program(self) -> None:
        """
        updates GUI to reflect IDLE state,
        """
        try:
            self.main_gui.update_on_stop()

            for desc, sched_task in self.main_gui.scheduled_tasks.items():
                self.main_gui.after_cancel(sched_task)

            # finalize the program after 5 seconds because the door has not gone down yet. we still want the arduino
            # to record the time that the door goes up last
            self.main_gui.after(5000, self.complete_program)

            # set flag that program has run now, restart required for another run

            logging.info("Experiement Stopped.")
        except Exception as e:
            logging.error(f"Error stopping program: {e}")
            raise

    def complete_program(self) -> None:
        """
        Finalize the program by telling motor arduino to send the door up/down timestamps that it has, reset both Arduino boards,
        offer to save the .
        """
        try:
            #
            # self.arduino_controller.send_command_to_motor("<9>")

            # self.arduino_mgr.reset_arduinos()

            self.main_gui.save_button_handler()

            logging.info("Program finalized, arduino boards reset.")
        except Exception as e:
            logging.error(f"Error completing program: {e}")
            raise

    def process_queue(self, data_queue):
        """
        Process the data queue.
        """
        try:
            while not data_queue.empty():
                source, data = data_queue.get()
                self.process_data(source, data)

            # run this command every 100 ms
            self.queue_ps_id = self.after(100, self.process_queue)
        except Exception as e:
            logging.error(f"Error processing data queue: {e}")
            raise

    def parse_timestamps(self, timestamp_string):
        """
        Parse timestamps sent from the Arduino data.
        """
        try:
            entries = timestamp_string.split("><")
            # Remove the leading '<' from the first entry
            entries[0] = entries[0][1:]
            # Remove the trailing '>' from the last entry
            entries[-1] = entries[-1][:-1]
            parsed_entries = []

            for entry in entries:
                parts = entry.split(",")
                command = parts[0]
                trial_number = int(parts[1])
                occurrence_time = int(parts[2])
                timestamp = {
                    "command": command,
                    "trial_number": trial_number,
                    "occurrence_time": occurrence_time,
                }
                parsed_entries.append(timestamp)

            logging.info(f"Timestamps parsed: {parsed_entries}")
            return parsed_entries
        except Exception as e:
            logging.error(f"Error parsing timestamps: {e}")
            raise

    def process_data(self, source, data):
        """
        Process data received from the Arduino.
        """
        try:
            if source == "laser":
                if (data == "<Stimulus One>" or data == "<Stimulus Two>") and (
                    self.state in ["TTC", "Sample"]
                ):
                    if data == "<Stimulus One>":
                        self.data_mgr.side_one_licks += 1
                        self.data_mgr.total_licks += 1
                    elif data == "<Stimulus Two>":
                        self.data_mgr.side_two_licks += 1
                        self.data_mgr.total_licks += 1

                    # Remove the first and last characters
                    modified_data = data[1:-1]
                    self.record_lick_data(modified_data)
                # if 3 or more licks in a ttc time, jump straight to sample
                if (
                    self.data_mgr.side_one_licks > 2 or self.data_mgr.side_two_licks > 2
                ) and self.state == "TTC":
                    self.trigger("SAMPLE")
                    # self.start_new_sample()
            elif source == "motor":
                if data == "<Finished Pair>":
                    self.valve_test_logic.append_to_volumes()

                elif "Testing Complete" in data:
                    self.valve_test_logic.begin_updating_opening_times(data)

                elif "SCHEDULE VERIFICATION" in data:
                    cleaned_data = data.replace("SCHEDULE VERIFICATION", "").strip()
                    self.data_mgr.verify_arduino_schedule(
                        self.data_mgr.side_one_indexes,
                        self.data_mgr.side_two_indexes,
                        cleaned_data,
                    )
                elif "Time Stamp Data" in data:
                    cleaned_data = data.replace("Time Stamp Data", "").strip()

                    motor_timestamps = self.parse_timestamps(cleaned_data)

                    self.data_mgr.insert_trial_start_stop_into_licks_dataframe(
                        motor_timestamps
                    )

            logging.info(f"Data processed from {source}: {data}")
        except Exception as e:
            logging.error(f"Error processing data from {source}: {e}")
            raise

    def record_lick_data(self, stimulus):
        """Record lick data to the dataframe."""
        try:
            data_mgr = self.data_mgr
            licks_dataframe = data_mgr.licks_dataframe
            total_licks = data_mgr.total_licks

            stimulus = "1" if stimulus == "Stimulus One" else "2"
            licks_dataframe.loc[total_licks, "Trial Number"] = (
                data_mgr.current_trial_number
            )
            licks_dataframe.loc[total_licks, "Licked Port"] = int(stimulus)
            licks_dataframe.loc[total_licks, "Time Stamp"] = round(
                time.time() - data_mgr.start_time, 3
            )
            licks_dataframe.loc[total_licks, "State"] = self.state
            logging.info(f"Lick data recorded: {stimulus}")
        except Exception as e:
            logging.error(f"Error recording lick data: {e}")
            raise


class StartProgram:
    def __init__(self, exp_data, main_gui, trigger):
        try:
            self.exp_data = exp_data

            self.exp_data.start_time = time.time()
            self.exp_data.state_start_time = time.time()

            # self.arduino_controller.send_command_to_arduino(
            #    arduino="motor", command="<0>"
            # )

            main_gui.update_clock_label()
            main_gui.start_button.configure(
                text="Stop", bg="red", command=lambda: trigger("STOP")
            )

            logging.info("==========EXPERIMENT BEGINS NOW==========")
            trigger("ITI")
        except Exception as e:
            logging.error(f"Error starting program: {e}")
            raise


class InitialTimeInterval:
    """
    State class for initial time interval experiment state. This state can be slightly confusing because in its current capacity
    it handles not only initial time interval, but it also updates models/guis when some state that is NOT START transitions here.
    this is becuase I did not want to delay the ITI starting time, so we come here and set the TTC transition to occur in the
    pre-determined ITI time, however, since we do nothing in that time and we're just waiting to transition, I thought it a perfect
    opportunity to update model / GUI tasks here.
    """

    def __init__(self, exp_data, prev_state, state, main_gui, trigger) -> None:
        self.state = state
        self.exp_data = exp_data
        self.lick_data = self.exp_data.lick_data
        self.main_gui = main_gui

        self.trigger = trigger

        # logical df rows will always be 1 behind the current trial because of zero based indexing in dataframes vs
        # 1 based for trials
        self.logical_trial = self.exp_data.current_trial_number - 1

        x = 1
        update_model = UpdateModel(self.exp_data, x)

        # end trial by incrementing self.exp_data.current_trial_num by one
        match prev_state:
            case "SAMPLE":
                # end_trial returns true if this is the last trial
                if update_model.end_trial():
                    self.trigger("STOP PROGRAM")

                self.logical_trial = self.exp_data.current_trial_number - 1

                # tell laser arduino that this is the end of trial, stop reading
                self.arduino_controller.send_command_to_laser("E")

                # tell motor arduino the door should move up now
                self.arduino_controller.send_command_to_motor("<U>")

                update_model.update_schedule_licks()

                lick_stamps_sd_one, lick_stamps_sd_two = self.update_model()
                self.update_raster(lick_stamps_sd_one, lick_stamps_sd_two)

                # if we just came from a sample state, then we can update the model and raster plots
                # with the data that we recieved during the trial while we wait for the ITI to complete
                self.execute_iti()
            case "TTC":
                update_model.update_ttc_actual()

                # end_trial returns true if this is the last trial
                if update_model.end_trial():
                    self.trigger("STOP PROGRAM")
                self.logical_trial = self.exp_data.current_trial_number - 1

                self.execute_iti()
            case _:
                # cases not explicitly defined go here
                self.execute_iti()

    def execute_iti(self):
        """
        This function transitions the program into the iti state. it does this by resetting lick counts, setting new state time,
        updating the models, and setting the .after call to transition to TTC.
        """
        try:
            self.lick_data.side_one_licks = 0
            self.lick_data.side_two_licks = 0

            self.main_gui.state_timer_text.configure(text=(self.state + "Time:"))
            self.exp_data.state_start_time = time.time()

            self.main_gui.update_on_new_trial(
                self.exp_data.program_schedule_df.loc[self.logical_trial, "Port 1"],
                self.exp_data.program_schedule_df.loc[self.logical_trial, "Port 2"],
            )

            initial_time_interval = self.exp_data.program_schedule_df.loc[
                self.logical_trial, self.state
            ]

            self.main_gui.update_on_state_change(initial_time_interval, self.state)

            # tell tkinter main loop that we want to call trigger with TTC parameter after initial_time_interval milliseconds
            self.main_gui.after(int(initial_time_interval), lambda: self.trigger("TTC"))

            logging.info(
                f"STATE CHANGE: ITI BEGINS NOW for trial -> {self.exp_data.current_trial_number}, completes in {initial_time_interval}."
            )
        except Exception as e:
            logging.error(f"Error in initial time interval: {e}")
            raise

    def update_model(self, logical_trial) -> (list, list):
        # end-of-trial call that just updates the gui
        # based on trial model changes

        # if we just finished a trial, and we're moving back around to the ITI, update
        # lick model,
        lick_stamps_side_one, lick_stamps_side_two = self.lick_data.get_lick_timestamps(
            logical_trial
        )

        self.lick_data.side_one_trial_licks.append(lick_stamps_side_one)
        self.lick_data.side_two_trial_licks.append(lick_stamps_side_two)
        return lick_stamps_side_one, lick_stamps_side_two

    def update_raster(self, lick_stamps_side_one, lick_stamps_side_two):
        """
        update raster with
        """
        for window in self.main_gui.windows["Raster Plot"]:
            window.update_plot()

        if self.data_window.side1_window is not None:
            self.data_window.update_plot(
                self.data_window.side1_window,
                lick_stamps_side_one,
                self.logical_trial,
            )

        if self.data_window.side2_window is not None:
            self.data_window.update_plot(
                self.data_window.side2_window,
                lick_stamps_side_two,
                self.logical_trial,
            )


class TimeToContact:
    """
    State class for time to contact experiment state
    """

    # we are going to need to pass in the arduino controller as well
    def __init__(self, exp_data, main_gui, state, trigger):
        # this is the initial transition state that occurs every single time we transition to TTC
        self.exp_data = exp_data
        self.main_gui = main_gui
        self.state = state
        self.trigger = trigger

        self.logical_trial = self.exp_data.current_trial_number - 1

        """ """
        try:
            # send comment to arduino to move the door down
            # self.arduino_controller.send_command_to_motor(command="<D>")

            # after the door is down, then we will begin the ttc state logic, found in run_ttc
            self.main_gui.after(DOOR_MOTOR_CLOSE_TIME, lambda: self.run_ttc())

            # state start time begins
            self.exp_data.state_start_time = time.time()
            self.main_gui.clear_state_time()

            # show current_time / door close time to avoid confusion
            self.main_gui.update_on_state_change(DOOR_MOTOR_CLOSE_TIME, self.state)

            logging.info(
                f"STATE CHANGE: ITI -> TTC NOW for trial -> {self.exp_data.current_trial_number}."
            )
        except Exception as e:
            logging.error(f"Error in ITI to TTC transition: {e}")
            raise

    def run_ttc(self):
        try:
            self.main_gui.state_timer_text.configure(text=(self.state + " Time:"))

            self.exp_data.state_start_time = time.time()

            # find the amount of time available for TTC for this trial
            time_to_contact = self.exp_data.program_schedule_df.loc[
                self.logical_trial, self.state
            ]

            self.main_gui.update_on_state_change(time_to_contact, self.state)

            # set a state change to occur after the time_to_contact time, this will be cancelled if the laser arduino
            # sends 3 licks befote the TTC_time
            ttc_iti_transition = self.main_gui.after(
                int(time_to_contact), lambda: self.trigger("ITI")
            )

            # store this task id so that it can be cancelled if the sample time transition is taken.
            self.main_gui.scheduled_tasks["TTC TO ITI"] = ttc_iti_transition

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

    def __init__(self, exp_data, main_gui, state, trigger):
        self.exp_data = exp_data
        self.lick_data = self.exp_data.lick_data
        self.main_gui = main_gui
        self.state = state

        self.logical_trial = self.exp_data.current_trial_number - 1

        try:
            self.update_ttc_time()

            # since the trial was engaged, cancel the planned transition from ttc to iti. program has branched to new state
            self.main_gui.after_cancel(self.main_gui.scheduled_tasks["TTC TO ITI"])

            # Tell the laser arduino to begin accepting licks and opening valves
            # resetting the lick counters for both spouts
            self.lick_data.side_one_licks = 0
            self.lick_data.side_two_licks = 0

            # tell the laser to begin accepting licks
            self.send_command_to_laser(command="B")

            self.exp_data.state_start_time = time.time()

            sample_interval_value = self.data_mgr.check_dataframe_entry_isfloat(
                self.logical_trial, self.state
            )

            self.main_gui.update_on_state_change(sample_interval_value, self.state)

            self.main_gui.after(
                int(sample_interval_value),
                lambda: trigger("ITI"),
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

        self.exp_data.program_schedule_df.loc[self.logical_trial, "TTC Actual"] = (
            ttc_time
        )


class UpdateModel:
    """
    This class contains methods used to update the model (data) classes at the end of every trial. it will match on previous state
    and update the data that needs updating based on that value.
    """

    def __init__(self, exp_data, arduino_controller):
        """define method that saves the licks to the data table and increments our iteration variable."""
        self.exp_data = exp_data
        self.arduino_controller = arduino_controller
        self.logical_trial = self.exp_data.current_trial_number - 1

        try:
            logger.info(
                f"UpdateModel instance created. Trial -> {self.exp_data.current_trial_number}."
            )
        except Exception as e:
            logger.error(
                f"Error saving licks for iteration {self.exp_data.current_trial_number}: {e}"
            )
            raise

    def end_trial(self) -> bool:
        self.exp_data.current_trial_number += 1
        if (
            self.exp_data.current_trial_number
            >= self.exp_data.exp_var_entries["Num Trials"]
        ):
            return True
        return False

    def update_ttc_actual(self):
        # if we just came from ttc, then update actual ttc time taken
        self.exp_data.program_schedule_df.loc[self.logical_trial, "TTC Actual"] = (
            self.exp_data.program_schedule_df.loc[self.logical_trial, "TTC"]
        )

    def update_schedule_licks(self):
        self.exp_data.program_schedule_df.loc[self.logical_trial, "Port 1 Licks"] = (
            self.side_one_licks
        )
        self.exp_data.program_schedule_df.loc[self.logical_trial, "Port 2 Licks"] = (
            self.side_two_licks
        )
