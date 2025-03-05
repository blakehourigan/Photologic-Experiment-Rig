import logging
import json
import time
import toml
import numpy as np
from pathlib import Path

from views.gui_common import GUIUtils

# Get the logger in use for the app
logger = logging.getLogger()


class ArduinoData:
    def __init__(self, exp_data):
        self.exp_data = exp_data
        self.valve_indexes_side_one = []
        self.valve_indexes_side_two = []

    def save_durations(self):
        pass

    def load_durations(self, reset_durations=False):
        """
        This method loads data in from the valve_durations.toml file located in assets. By default,
        it will load the last used durations becuase this is what is most often utilized. Optionally,
        the user can reset all these values to default values of 24125ms if the reset_durations
        parameter flag is set to true.
        """
        toml_dir = Path(__file__).parent.parent.parent.resolve()
        toml_path = toml_dir / "assets" / "valve_durations.toml"

        with open(toml_path, "r") as f:
            toml_file = toml.load(f)

        default_durations = toml_file["default_durations"]
        print(default_durations)

        # create 2 np arrays 8 n long with np.int32s
        dur_side_one = np.full(8, np.int32(0))
        dur_side_two = np.full(8, np.int32(0))

        for key, value in default_durations.items():
            if key == "side_one_durations":
                for i, duration in enumerate(value):
                    dur_side_one[i] = duration
            elif key == "side_two_durations":
                for i, duration in enumerate(value):
                    dur_side_two[i] = duration

        return dur_side_one, dur_side_two

    def load_schedule_indices(self):
        stimuli_data = self.exp_data.stimuli_data
        schedule_df = self.exp_data.program_schedule_df

        num_stimuli = self.exp_data.exp_var_entries["Num Stimuli"]
        num_trials = self.exp_data.exp_var_entries["Num Trials"]

        sched_side_one = np.full(num_trials, np.int8(0))
        sched_side_two = np.full(num_trials, np.int8(0))

        # get unique stim names. this will give us all names on side one.
        # finding the index of a given stimuli appearing in a trial on side
        # one will easily allow us to find the paired index. We've already done
        # this before in exp_process_data
        names = list(stimuli_data.stimuli_vars.values())
        unique_names = names[: num_stimuli // 2]

        side_one_trial_stimuli = schedule_df["Port 1"].to_numpy()

        for i, trial_stim in enumerate(side_one_trial_stimuli):
            index = unique_names.index(trial_stim)
            sd_two_index = self.exp_data.get_paired_index(index, num_stimuli)
            sched_side_one[i] = index
            sched_side_two[i] = sd_two_index

        return sched_side_one, sched_side_two

    def write_to_json_file(self, arduino_data, filename="arduino_data.json"):
        with open(filename, "w") as file:
            json.dump(arduino_data, file, indent=4)

    def read_json_file(self, filename="../arduino_data.json"):
        with open(filename, "r") as file:
            return json.load(file)

    def load_configuration(
        self, filename="../arduino_data.json", config_name="default"
    ):
        # Function to load a specific configuration
        data = self.read_json_file(filename)
        if config_name in data:
            return data[config_name]
        else:
            raise ValueError(f"Configuration '{config_name}' not found in {filename}")

    def save_configuration(
        # Function to save a specific configuration
        self,
        filename="arduino_data.json",
        config_name="last_used",
        config_data=None,
    ):
        data = self.read_json_file(filename)
        data[config_name] = config_data
        self.write_to_json_file(data, filename)

    def verify_schedule(self, motor_arduino, side_one_schec, side_two_sched):
        num_trials = self.exp_data.exp_var_entries["Num Trials"]
        ver1 = np.zeros((num_trials,), dtype=np.int8)
        ver2 = np.zeros((num_trials,), dtype=np.int8)

        # wait for the data to arrive
        while motor_arduino.in_waiting < 1:
            continue
        for i in range(50):
            ver1[i] = motor_arduino.read()
        for i in range(50):
            ver2[i] = motor_arduino.read()

        print(ver1)
        print(ver2)

        sd_one_eq = np.array_equal(side_one_schec, ver1)
        sd_two_eq = np.array_equal(side_two_sched, ver2)

        if sd_one_eq and sd_two_eq:
            logger.info("Motor arduino valve trial schedules verified")
        else:
            GUIUtils.display_error(
                "Verification Error",
                "Schedule generated locally is not identical to that recieved from the motor arduino. If this error persists over many attempts, contact support.",
            )

    def handle_licks(self, data, lick_data, state):
        if data == "<Stimulus One>":
            lick_data.side_one_licks += 1
            lick_data.total_licks += 1
        elif data == "<Stimulus Two>":
            lick_data.side_two_licks += 1
            lick_data.total_licks += 1

        # Remove the first and last characters (<, >)
        modified_data = data[1:-1]
        self.record_lick_data(modified_data, state)

    def process_laser(self, data, state, trigger):
        lick_data = self.exp_data.lick_data
        match state:
            case "TTC":
                self.handle_licks(data, lick_data, state)

                # insert the values held in licks for respective sides in a shorter variable name
                side_one = self.exp_data.lick_data.side_one_licks
                side_two = self.exp_data.lick_data.side_two_licks
                # if 3 or more licks in a ttc time, jump straight to sample
                if side_one > 2 or side_two > 2:
                    trigger("SAMPLE")

            case "SAMPLE":
                self.handle_licks(data, lick_data, state)

    def process_motor(self, data):
        if data == "<Finished Pair>":
            self.valve_test_logic.append_to_volumes()

        elif "Testing Complete" in data:
            self.valve_test_logic.begin_updating_opening_times(data)

        elif "SCHEDULE VERIFICATION" in data:
            ###### REDO THIS #####
            cleaned_data = data.replace("SCHEDULE VERIFICATION", "").strip()

            self.verify_arduino_schedule(
                self.data_mgr.side_one_indexes,
                self.data_mgr.side_two_indexes,
                cleaned_data,
            )
            ###### REDO THIS #####
        elif "Time Stamp Data" in data:
            cleaned_data = data.replace("Time Stamp Data", "").strip()

            motor_timestamps = self.parse_timestamps(cleaned_data)

            self.exp_data.lick_data.insert_trial_start_stop(motor_timestamps)

    def process_data(self, source, data, state, trigger):
        """
        Process data received from the Arduino.
        """
        try:
            match source:
                case "laser":
                    self.process_laser(data, state, trigger)

                case "motor":
                    self.process_motor(data)
        except Exception as e:
            logging.error(f"Error processing data from {source}: {e}")
            raise

    def record_lick_data(self, stimulus, state):
        """Record lick data to the dataframe."""
        try:
            licks_data = self.exp_data.lick_data
            licks_dataframe = licks_data.licks_dataframe
            total_licks = licks_data.total_licks
            trial_number = self.exp_data.current_trial_number
            start_time = self.exp_data.start_time

            lick_time = round(time.time() - start_time, 3)

            port = None
            if stimulus == "Stimulus One":
                port = 1
            else:
                port = 2

            licks_dataframe.loc[total_licks, "Trial Number"] = trial_number

            licks_dataframe.loc[total_licks, "Licked Port"] = port

            licks_dataframe.loc[total_licks, "Time Stamp"] = lick_time

            licks_dataframe.loc[total_licks, "State"] = state

            logging.info(f"Lick data recorded for: {stimulus}")
        except Exception as e:
            logging.error(f"Error recording lick data: {e}")
            raise

    def get_current_json_config(self) -> dict:
        return self.load_configuration(config_name="last_used")

    @staticmethod
    def parse_timestamps(timestamp_string):
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
