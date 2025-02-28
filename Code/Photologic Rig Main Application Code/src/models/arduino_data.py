import logging
import json
import time

from views.gui_common import GUIUtils

# Get the logger in use for the app
logger = logging.getLogger()


class ArduinoData:
    def __init__(self, exp_data):
        self.exp_data = exp_data

    def initialize_arduino_json(self) -> None:
        # Define initial configuration data
        default_data = {
            "side_one_schedule": [],
            "side_two_schedule": [],
            "current_trial": 1,
            "valve_durations_side_one": [
                25000,
                24125,
                24125,
                24125,
                24125,
                24125,
                24125,
                24125,
            ],
            "valve_durations_side_two": [
                25000,
                24125,
                24125,
                24125,
                24125,
                24125,
                24125,
                24125,
            ],
        }

        last_used_data = {
            "side_one_schedule": [],
            "side_two_schedule": [],
            "current_trial": 1,
            "valve_durations_side_one": [
                25000,
                24125,
                24125,
                24125,
                24125,
                24125,
                24125,
                24125,
            ],
            "valve_durations_side_two": [
                25000,
                24125,
                24125,
                24125,
                24125,
                24125,
                24125,
                24125,
            ],
        }

        # Create a dictionary with named configurations
        arduino_data_initial = {"default": default_data, "last_used": last_used_data}

        self.write_to_json_file(arduino_data=arduino_data_initial)

    def write_to_json_file(self, arduino_data, filename="arduino_data.json"):
        with open(filename, "w") as file:
            json.dump(arduino_data, file, indent=4)

    def read_json_file(self, filename="arduino_data.json"):
        with open(filename, "r") as file:
            return json.load(file)

    def load_configuration(self, filename="arduino_data.json", config_name="default"):
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

    def verify_arduino_schedule(self, side_one_indexes, side_two_indexes, verification):
        middle_index = len(verification) // 2
        side_one_verification_str = verification[:middle_index]
        side_two_verification_str = verification[middle_index:]

        side_one_verification = [
            int(x) for x in side_one_verification_str.split(",") if x.strip().isdigit()
        ]
        side_two_verification = [
            int(x) for x in side_two_verification_str.split(",") if x.strip().isdigit()
        ]

        are_equal_side_one = all(
            side_one_indexes[i] == side_one_verification[i]
            for i in range(len(side_one_indexes))
        )
        are_equal_side_two = all(
            side_two_indexes[i] == side_two_verification[i]
            for i in range(len(side_two_indexes))
        )

        if are_equal_side_one and are_equal_side_two:
            logger.info("Both lists are identical, Schedule Send Complete.")
        else:
            logger.error("Lists are not identical.")

            GUIUtils.display_error("Verification Error", "Lists are not identical.")

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

    def process_laser(self, data, state):
        lick_data = self.exp_data.lick_data

        match state:
            case "TTC":
                self.handle_licks(data, lick_data, state)

                # insert the values held in licks for respective sides in a shorter variable name
                side_one = self.exp_data.lick_data.side_one_licks
                side_two = self.exp_data.lick_data.side_two_licks
                # if 3 or more licks in a ttc time, jump straight to sample
                if side_one > 2 or side_two > 2:
                    self.trigger("SAMPLE")

            case "SAMPLE":
                self.handle_licks(data)

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

            self.exp_data.insert_trial_start_stop_into_licks_dataframe(motor_timestamps)

    def process_data(self, source, data, state):
        """
        Process data received from the Arduino.
        """
        try:
            match source:
                case "laser":
                    self.process_laser(data, state)

                case "motor":
                    self.process_motor()
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
