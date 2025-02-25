import time
import logging
from logging.handlers import RotatingFileHandler

# Model (data) classe / sub-classes are init'd internally to this class
from models.experiment_process_data import ExperimentProcessData

# GUI classes
from views.main_gui import MainGUI
from views.gui_common import GUIUtils

# controller classes
from controllers.arduino_control import ArduinoManager

# number of milliseconds it takes for the door to close
DOOR_MOTOR_CLOSE_TIME = 2238


# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# Console handler for errors
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.ERROR)
console_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
)
logger.addHandler(console_handler)

# Rotating file handler for all logs, this means that once maxBytes is exceeded, the data rolls over into a new file.
# for example, data will begin in app.log, then will roll over into app1.log
file_handler = RotatingFileHandler("app.log", maxBytes=10 * 1024 * 1024, backupCount=3)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
)
logger.addHandler(file_handler)


class TkinterApp:
    def __init__(self) -> None:
        self.after_ids: list[str] = []

        try:
            # init exp_data, licks_data, stimuli_data, arduino_data
            self.init_models()
            # self.init_controllers()
            # self.arduino_controller.send_arduino_json_data()

            # this requirements dict provides dependencies for the gui. it is defined as follows:
            # key: value where key = item the associated value will be used with, and value is
            # the function or variable that a key needs
            self.init_view(self.exp_data, self.trigger)
            logging.info("GUI started successfully.")
        except Exception as e:
            logging.error(f"Initialization error: {e}")
            raise

    def init_models(self):
        self.exp_data = ExperimentProcessData()

        logging.info("Data Classes initialized.")

    def init_controllers(self):
        """Initialize managers."""
        self.arduino_controller = ArduinoManager(self)

        logging.info("Controllers initialized.")

    def init_view(self, exp_data, trigger):
        # instantiating MainGUI sets up our gui and the objects needed
        self.main_gui = MainGUI(exp_data, trigger)

        logging.info("View (GUI) initialized.")


class StateMachine(TkinterApp):
    def __init__(self, result_container):
        # init the 'super' parent class which is the gui
        super().__init__()
        # default state is idle
        self.state = "IDLE"
        # used to make decision of whether to restart the program
        self.app_result = result_container
        # define state transitions that the program can possibly take
        self.transitions = {
            ("IDLE", "START"): "START PROGRAM",
            ("IDLE", "RESET"): "RESET PROGRAM",
            ("START", "ITI"): "RESET PROGRAM",
            ("ITI", "TTC"): "TTC",
            ("TTC", "SAMPLE"): "SAMPLE",
            ("SAMPLE", "UPDATE MODEL"): "SAMPLE",
            ("UPDATE MODEL", "STOP"): "STOP PROGRAM",
        }

        # don't start the mainloop until AFTER the gui is setup so that the app_result property
        # is available if reset is desired
        self.main_gui.mainloop()

    def trigger(self, event):
        key = (self.state, event)

        if key in self.transitions:
            new_state = self.transitions[key]
        elif event == "RESET":
            GUIUtils.display_error(
                "CANNOT PERFORM THIS ACTION",
                "RESET cannot be performed during runtime. Stop the program to reset.",
            )
        else:
            return

        match new_state:
            case "START PROGRAM":
                StartProgram(self.exp_data)
            case "RESET PROGRAM":
                self.reset_program()
            case "ITI":
                InitialTimeInterval(0)

    def reset_program(self) -> None:
        """
        Handle resetting the program on click of the reset button. askyesno will confirm the uesr wants to erase all data.
        if yes, we will quit the mainloop of the gui and destroy it and then update the app return value at index 0 passed
        in from the main module this will begin a new StateMachine instance, effectively restarting the prgram.
        """
        try:
            response = GUIUtils.askyesno(
                "============WARNING============",
                "THIS ACTION WILL ERASE ALL DATA CURRENTLY STORED FOR THIS EXPERIMENT... ARE YOU SURE YOU WANT TO CONTINUE?",
            )
            if response:
                self.main_gui.quit()
                self.main_gui.destroy()
                self.app_result[0] = 1
        except Exception as e:
            logging.error(f"Error in reset button handler: {e}")

    def ITI_TTC_Transition(self, iteration: int) -> None:
        logging.info(f"ITI to TTC transition started for iteration {iteration}.")
        try:
            self.send_command_to_arduino(
                arduino="motor", command="<D>"
            )  # tell motor arduino to move the door down
            self.main_gui.root.after(
                DOOR_MOTOR_CLOSE_TIME, lambda: self.time_to_contact(iteration)
            )
            self.data_mgr.state_start_time = time.time()  # state start time begins
            self.main_gui.clear_state_time()
            logging.debug(f"ITI to TTC transition completed for iteration {iteration}.")
        except Exception as e:
            logging.error(f"Error in ITI to TTC transition: {e}")
            raise
        raise


class StartProgram:
    def __init__(self, exp_data):
        try:
            self.exp_data = exp_data

            if self.exp_data.program_schedule_df.empty:
                GUIUtils.display_error(
                    "Blocks not Generated",
                    "Please generate blocks before starting the program.",
                )

                return

            self.exp_data.start_time = time.time()
            self.exp_data.state_start_time = time.time()

            self.send_command_to_arduino(arduino="motor", command="<0>")

            self.main_gui.update_clock_label()
            self.main_gui.start_button.configure(text="Stop", bg="red")

            logging.info("==========EXPERIMENT BEGINS NOW==========")
        except Exception as e:
            logging.error(f"Error starting program: {e}")
            raise


class InitialTimeInterval:
    def __init__(self, iteration: int) -> None:
        """Handle the initial time interval state of the experiment."""
        logging.info(f"Initial time interval started for iteration {iteration}.")
        try:
            if iteration > 0:
                lick_stamps_side_one, lick_stamps_side_two = (
                    self.data_mgr.get_lick_timestamps(iteration)
                )
                self.data_mgr.side_one_trial_licks.append(lick_stamps_side_one)
                self.data_mgr.side_two_trial_licks.append(lick_stamps_side_two)
                if self.data_window.side1_window is not None:
                    self.data_window.update_plot(
                        self.data_window.side1_window, lick_stamps_side_one, iteration
                    )
                if self.data_window.side2_window is not None:
                    self.data_window.update_plot(
                        self.data_window.side2_window, lick_stamps_side_two, iteration
                    )

            self.data_mgr.current_iteration = iteration

            if self.data_mgr.current_trial_number > self.get_num_trials():
                self.experiment_completed = True
                self.program_schedule_window.update_licks(iteration + 1)
                self.program_schedule_window.update_ttc_actual(iteration + 1)
                self.stop_program()
            elif self.running:
                self.state = "ITI"
                self.data_mgr.side_one_licks = 0
                self.data_mgr.side_two_licks = 0
                self.main_gui.state_timer_text.configure(text=(self.state + " Time:"))
                self.data_mgr.state_start_time = time.time()
                self.main_gui.update_on_new_trial(
                    self.data_mgr.stimuli_dataframe.loc[iteration, "Port 1"],
                    self.data_mgr.stimuli_dataframe.loc[iteration, "Port 2"],
                )
                ITI_Value = self.data_mgr.check_dataframe_entry_isfloat(
                    iteration, "ITI"
                )
                self.main_gui.update_on_state_change(ITI_Value, self.state)
                self.main_gui.root.after(
                    int(ITI_Value), lambda: self.ITI_TTC_Transition(iteration)
                )
            logging.debug(f"Initial time interval completed for iteration {iteration}.")
        except Exception as e:
            logging.error(f"Error in initial time interval: {e}")
            raise

    def time_to_contact(self, iteration: int):
        """Handle the time to contact state."""
        logging.info(f"STATE CHANGE: TTC BEGINS NOW for iteration -> {iteration}.")
        try:
            if self.running:
                self.state = "TTC"
                self.main_gui.state_timer_text.configure(text=(self.state + " Time:"))
                self.data_mgr.state_start_time = time.time()
                TTC_Value = self.data_mgr.check_dataframe_entry_isfloat(
                    iteration, "TTC"
                )
                self.main_gui.update_on_state_change(TTC_Value, self.state)
                self.after_sample_id = self.main_gui.root.after(
                    int(TTC_Value), lambda: self.data_mgr.save_licks(iteration)
                )
                self.after_ids.append(self.after_sample_id)
            logging.debug(f"Time to contact completed for iteration {iteration}.")
        except Exception as e:
            logging.error(f"Error in time to contact: {e}")
            raise

    def start_new_sample(self, iteration):
        """Start a new sample after checking licks during the TTC state."""
        logging.debug(f"Starting new sample for iteration {iteration}.")
        try:
            self.data_mgr.stimuli_dataframe.loc[
                self.data_mgr.current_trial_number - 1, "TTC Actual"
            ] = (time.time() - self.data_mgr.state_start_time) * 1000
            self.main_gui.root.after_cancel(self.after_sample_id)
            self.data_mgr.side_one_licks = 0
            self.data_mgr.side_two_licks = 0
            self.sample_time(iteration)
            logging.debug(f"New sample started for iteration {iteration}.")
        except Exception as e:
            logging.error(f"Error starting new sample: {e}")
            raise

    def sample_time(self, iteration: int):
        """Handle the sample time state."""
        logging.debug(f"Sample time started for iteration {iteration}.")
        try:
            if self.running:
                self.state = "Sample"
                self.send_command_to_arduino(
                    arduino="laser", command="B"
                )  # Tell the laser arduino to begin accepting licks and opening valves
                self.data_mgr.state_start_time = time.time()
                sample_interval_value = self.data_mgr.check_dataframe_entry_isfloat(
                    iteration, "Sample Time"
                )
                self.main_gui.update_on_state_change(sample_interval_value, self.state)
                self.main_gui.root.after(
                    int(sample_interval_value),
                    lambda: self.data_mgr.save_licks(iteration),
                )
            logging.debug(f"Sample time completed for iteration {iteration}.")
        except Exception as e:
            logging.error(f"Error in sample time: {e}")
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
                if (
                    self.data_mgr.side_one_licks > 2 or self.data_mgr.side_two_licks > 2
                ) and self.state == "TTC":
                    self.start_new_sample(self.data_mgr.current_iteration)
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
        logging.debug(f"Recording lick data: {stimulus}")
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
            logging.debug(f"Lick data recorded: {stimulus}")
        except Exception as e:
            logging.error(f"Error recording lick data: {e}")
            raise

    def stop_program(self) -> None:
        """
        Method to halt the program and set it to the off state.
        """
        try:
            self.state = "OFF"
            self.running = False
            self.main_gui.update_on_stop()

            for after_id in self.after_ids:
                self.after_cancel(after_id)

            # finalize the program after 5 seconds because the door has not gone down yet. we still want the arduino
            # to record the time that the door goes up last
            self.after(5000, self.complete_program)

            self.data_mgr.current_trial_number = 1
            logging.info("Program stopped.")
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
            self.send_command_to_arduino(arduino="motor", command="<9>")

            self.arduino_mgr.reset_arduinos()

            self.main_gui.save_button_handler()

            logging.info("Program finalized, arduino boards reset.")
        except Exception as e:
            logging.error(f"Error completing program: {e}")
            raise

    def run(self, restart_override=False) -> int:
        if restart_override:
            return 1
        return 0
