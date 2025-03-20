import logging
import datetime
import copy
import toml
import numpy as np
import system_config

# Get the logger in use for the app
logger = logging.getLogger()

rig_config = system_config.get_rig_config()

with open(rig_config, "r") as f:
    VALVE_CONFIG = toml.load(f)["valve_config"]

# pull total valves constant from toml config
TOTAL_POSSIBLE_VALVES = VALVE_CONFIG["TOTAL_POSSIBLE_VALVES"]
VALVES_PER_SIDE = TOTAL_POSSIBLE_VALVES // 2


class ArduinoData:
    def __init__(self, exp_data):
        self.exp_data = exp_data

    def find_first_not_filled(self, toml_file) -> int:
        first_available = 0
        for i in range(1, 4):
            archive = toml_file[f"archive_{i}"]
            if archive["filled"]:
                continue
            else:
                first_available = i
        return first_available

    def save_durations(self, side_one, side_two, type_durations):
        """
        Function to save durations into long term storage valve_durations.toml file.
        You must provide a type_durations paramter to specify where you are saving the durations.
        Can be either "selected" to set new primary durations, or "archive" to archive previous
        "selected" durations.
        """
        dur_path = system_config.get_valve_durations()

        with open(dur_path, "r") as f:
            toml_file = toml.load(f)

        if type_durations == "selected":
            selected_durations = toml_file["selected_durations"]

            # toml only knows how to deal with python native types (list, int, etc)
            # so we convert np arrays to lists
            selected_durations["date_used"] = datetime.datetime.now()
            selected_durations["side_one_durations"] = side_one.tolist()
            selected_durations["side_two_durations"] = side_two.tolist()

            # save the file with the updated content
            with open(dur_path, "w") as f:
                toml.dump(toml_file, f)
        elif type_durations == "archive":
            # find first archive not filled
            first_avail = self.find_first_not_filled(toml_file)
            match first_avail:
                case 1:
                    # 1 is available just insert
                    archive = toml_file["archive_1"]

                    archive["filled"] = True
                    archive["date_used"] = datetime.datetime.now()
                    archive["side_one_durations"] = side_one.tolist()
                    archive["side_two_durations"] = side_two.tolist()

                    with open(dur_path, "w") as f:
                        toml.dump(toml_file, f)
                case 2:
                    # move 1-> 2, insert 1
                    toml_file["archive_2"] = copy.deepcopy(toml_file["archive_1"])

                    archive_1 = toml_file["archive_1"]

                    archive_1["filled"] = True
                    archive_1["date_used"] = datetime.datetime.now()
                    archive_1["side_one_durations"] = side_one.tolist()
                    archive_1["side_two_durations"] = side_two.tolist()

                    with open(dur_path, "w") as f:
                        toml.dump(toml_file, f)

                case 3 | 0:
                    # case 3) 2 -> 3, 1-> 2, insert 1
                    # case 0 (no available archives) ) del / overwrite 3 (oldest), 2 -> 3, 1-> 2, insert 1
                    toml_file["archive_3"] = copy.deepcopy(toml_file["archive_2"])
                    toml_file["archive_2"] = copy.deepcopy(toml_file["archive_1"])

                    archive_1 = toml_file["archive_1"]

                    archive_1["filled"] = True
                    archive_1["date_used"] = datetime.datetime.now()
                    archive_1["side_one_durations"] = side_one.tolist()
                    archive_1["side_two_durations"] = side_two.tolist()

                    with open(dur_path, "w") as f:
                        toml.dump(toml_file, f)

    def load_durations(
        self, type_durations="selected_durations", reset_durations=False
    ):
        """
        This method loads data in from the valve_durations.toml file located in assets. By default,
        it will load the last used durations becuase this is what is most often utilized. Optionally,
        the user can reset all these values to default values of 24125ms if the reset_durations
        parameter flag is set to true.
        """
        valve_durations_toml = system_config.get_valve_durations()

        with open(valve_durations_toml, "r") as f:
            toml_file = toml.load(f)

        file_durations = toml_file[type_durations]

        # create 2 np arrays 8 n long with np.int32s
        dur_side_one = np.full(VALVES_PER_SIDE, np.int32(0))
        dur_side_two = np.full(VALVES_PER_SIDE, np.int32(0))

        # keys here are names of durations i.e side_one_dur or side_two_dur, values
        # are lists of durations, VALVES_PER_SIDE long. Will produce two lists
        # VALVES_PER_SIDE long so that each valve in the rig is assigned a duration.
        for key, value in file_durations.items():
            if key == "side_one_durations":
                for i, duration in enumerate(value):
                    dur_side_one[i] = duration
            elif key == "side_two_durations":
                for i, duration in enumerate(value):
                    dur_side_two[i] = duration

        date_used = file_durations["date_used"]

        return dur_side_one, dur_side_two, date_used

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

    def increment_licks(self, side, event_data):
        match side:
            case 0:
                event_data.side_one_licks += 1
            case 1:
                event_data.side_two_licks += 1
            case _:
                logger.error("invalid side")

    def handle_licks(self, split_data, event_data, state, trigger):
        side = None
        valve_duration = None
        match state:
            case "TTC":
                # split_data will have the below form for ttc
                # 0(side)|67(duration)|6541(stamp_rel_to_start)|6541(stamp_rel_to_trial)
                # 1|16|0|496570|41 from arduino
                side = np.int8(split_data[0])
                self.increment_licks(side, event_data)

                lick_duration = np.int32(split_data[1])
                time_rel_to_start = np.int32(split_data[2]) / 1000
                time_rel_to_trial = np.int32(split_data[3]) / 1000

                # insert the values held in licks for respective sides in a shorter variable name
                side_one = self.exp_data.event_data.side_one_licks
                side_two = self.exp_data.event_data.side_two_licks
                # if 3 or more licks in a ttc time, jump straight to sample
                if side_one > 2 or side_two > 2:
                    trigger("SAMPLE")
                self.record_event(
                    side, lick_duration, time_rel_to_start, time_rel_to_trial, state
                )

            case "SAMPLE":
                try:
                    # 0|87|26064|8327|8327
                    side = np.int8(split_data[0])
                    self.increment_licks(side, event_data)

                    lick_duration = np.int32(split_data[1])
                    valve_duration = np.int32(split_data[2])
                    time_rel_to_start = np.int32(split_data[3]) / 1000
                    time_rel_to_trial = np.int32(split_data[4]) / 1000

                    self.record_event(
                        side,
                        lick_duration,
                        time_rel_to_start,
                        time_rel_to_trial,
                        state,
                        valve_duration,
                    )

                except Exception as e:
                    logging.error(f"IMPROPER DATA.... IGNORING.....{e}")

    def record_event(
        self,
        side,
        duration,
        time_rel_to_start,
        time_rel_to_trial,
        state,
        valve_dur=None,
    ):
        """Record lick data to the dataframe."""
        try:
            event_data = self.exp_data.event_data
            current_trial = self.exp_data.current_trial_number
            # insert the lick record into the dataframe
            event_data.insert_row_into_df(
                current_trial,
                side + 1,
                duration,
                time_rel_to_start,
                time_rel_to_trial,
                state,
                valve_duration=(valve_dur if valve_dur else None),
            )

            logging.info(f"Lick data recorded for side: {side + 1}")
        except Exception as e:
            logging.error(f"Error recording lick data: {e}")
            raise

    def process_data(self, source, data, state, trigger):
        """
        Process data received from the Arduino.
        """
        event_data = self.exp_data.event_data
        split_data = data.split("|")
        try:
            if split_data[0] == "MOTOR":
                # data will arrive in the following format
                # MOTOR|DOWN|2338|7340|7340
                # MOTOR|MOVEMENT|DURATION|END_TIME_REL_TO_PROG_START|END_TIME_REL_TO_PROG_TRIAL_START
                event_data = self.exp_data.event_data

                current_trial = self.exp_data.current_trial_number

                event_data.insert_row_into_df(
                    current_trial,
                    None,
                    np.int32(split_data[2]),
                    (np.int32(split_data[3]) / 1000),
                    (np.int32(split_data[4]) / 1000),
                    f"MOTOR {split_data[1]}",
                )
            elif split_data[0] == "0" or split_data[0] == "1":
                self.handle_licks(split_data, event_data, state, trigger)

        except Exception as e:
            logging.error(f"Error processing data from {source}: {e}")
            raise
