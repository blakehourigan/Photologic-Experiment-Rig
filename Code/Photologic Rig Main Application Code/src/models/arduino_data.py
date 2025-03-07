import logging
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

        VALVES_PER_SIDE = 8

        with open(toml_path, "r") as f:
            toml_file = toml.load(f)

        default_durations = toml_file["selected_durations"]

        # create 2 np arrays 8 n long with np.int32s
        dur_side_one = np.full(VALVES_PER_SIDE, np.int32(0))
        dur_side_two = np.full(VALVES_PER_SIDE, np.int32(0))

        # keys here are names of durations i.e side_one_dur or side_two_dur, values
        # are lists of durations, VALVES_PER_SIDE long. Will produce two lists
        # VALVES_PER_SIDE long so that each valve in the rig is assigned a duration.
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

    def handle_licks(self, data, lick_data, state):
        if data[:12] == "STIMULUS ONE":
            lick_data.side_one_licks += 1
        elif data[:12] == "STIMULUS TWO":
            lick_data.side_two_licks += 1
        duration = np.float64(data[13:])

        self.record_lick_data(data, duration, state)

    def process_data(self, source, data, state, trigger):
        """
        Process data received from the Arduino.
        """
        try:
            lick_data = self.exp_data.lick_data
            if data == "MOTOR MOVED DOWN":
                # MOTOR MOVED DOWN | RELATIVE TO START | RELATIVE TO TRIAL
                lick_data = self.exp_data.lick_data

                current_trial = self.exp_data.current_trial_number

                start_time = self.exp_data.start_time
                trial_start_time = self.exp_data.trial_start_time

                time_since_start = round(time.time() - start_time, 3)
                time_since_trial_start = round(time.time() - trial_start_time, 3)

                lick_data.insert_row_into_df(
                    current_trial,
                    None,
                    None,
                    time_since_start,
                    time_since_trial_start,
                    "MOTOR DOWN",
                )

            elif data == "MOTOR MOVED UP":
                lick_data = self.exp_data.lick_data

                current_trial = self.exp_data.current_trial_number

                start_time = self.exp_data.start_time
                trial_start_time = self.exp_data.trial_start_time

                time_since_start = round(time.time() - start_time, 3)
                time_since_trial_start = round(time.time() - trial_start_time, 3)

                lick_data.insert_row_into_df(
                    current_trial,
                    None,
                    None,
                    time_since_start,
                    time_since_trial_start,
                    "MOTOR UP",
                )

            elif data == "FINISHED PAIR":
                self.valve_test_logic.append_to_volumes()
            elif "TESTING COMPLETE" in data:
                self.valve_test_logic.begin_updating_opening_times(data)
            else:
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

        except Exception as e:
            logging.error(f"Error processing data from {source}: {e}")
            raise

    def record_lick_data(self, stimulus, duration, state):
        """Record lick data to the dataframe."""
        try:
            lick_data = self.exp_data.lick_data

            current_trial = self.exp_data.current_trial_number

            start_time = self.exp_data.start_time
            trial_start_time = self.exp_data.trial_start_time

            time_since_start = round(time.time() - start_time, 3)
            time_since_trial_start = round(time.time() - trial_start_time, 3)

            port = None
            if stimulus == "Stimulus One":
                port = 1
            else:
                port = 2

            # insert the lick record into the dataframe
            lick_data.insert_row_into_df(
                current_trial,
                port,
                duration,
                time_since_start,
                time_since_trial_start,
                state,
            )

            logging.info(f"Lick data recorded for: {stimulus}")
        except Exception as e:
            logging.error(f"Error recording lick data: {e}")
            raise
