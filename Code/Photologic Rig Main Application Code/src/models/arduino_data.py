class ArduinoData:
    def __init__(self):
        pass

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

        # Function to load a specific configuration

    def load_configuration(self, filename="arduino_data.json", config_name="default"):
        data = self.read_json_file(filename)
        if config_name in data:
            return data[config_name]
        else:
            raise ValueError(f"Configuration '{config_name}' not found in {filename}")

    # Function to save a specific configuration
    def save_configuration(
        self, filename="arduino_data.json", config_name="last_used", config_data=None
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
            logger.warning("Lists are not identical.")
            self.controller.display_gui_error(
                "Verification Error", "Lists are not identical."
            )
