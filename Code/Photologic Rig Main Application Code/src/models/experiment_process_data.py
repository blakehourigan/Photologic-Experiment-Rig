import logging
from tkinter import filedialog
import numpy as np
import pandas as pd
from typing import Tuple, List
import datetime

from models.stimuli_data import StimuliData
from models.event_data import EventData
from models.arduino_data import ArduinoData

logger = logging.getLogger(__name__)


class ExperimentProcessData:
    """
    Summary line.

    This class is the central data hub of the program. It holds program runtime variabes
    such as program state and time interval lists, as well as references to
    other data classes containing stimuli, lick, and arduino related data.
    The class was structured this way to provide clarity on what files and classes
    contain the information being searched for.

    Attributes:
        attr1 (int): Description of `attr1`.
        attr2 (str): Description of `attr2`.

    Methods:
        method1(param1): Description of method1.
    """

    def __init__(self):
        self.start_time = 0.0
        self.trial_start_time = 0.0
        self.state_start_time = 0.0

        # this number is centralized here so that all state classes can access and update it easily without
        # passing it through to each state every time a state change occurs
        self.current_trial_number = 1

        self.experiment_executed = False

        self.event_data = EventData()
        self.stimuli_data = StimuliData()
        self.arduino_data = ArduinoData(self)

        self.ITI_intervals_final = None
        self.TTC_intervals_final = None
        self.sample_intervals_final = None

        self.TTC_lick_threshold = 3

        self.interval_vars = {
            "ITI_var": 5000,
            "TTC_var": 5000,
            "sample_var": 5000,
            "ITI_random_entry": 0,
            "TTC_random_entry": 0,
            "sample_random_entry": 0,
        }
        self.exp_var_entries = {
            "Num Trial Blocks": 4,
            "Num Stimuli": 4,
            "Num Trials": 0,
        }
        self.program_schedule_df = pd.DataFrame()

    def update_model(self, variable_name, value) -> None:
        """
        This function will be called when a tkiner entry is updated in the gui
        to update the standard variables held in the model classes there
        """
        # if the variable name for the tkinter entry item that we are updating is
        # in the exp_data interval variables dictionary, update that entry
        # with the value in the tkinter variable
        if value is not None:
            if variable_name in self.interval_vars.keys():
                self.interval_vars[variable_name] = value
            elif variable_name in self.exp_var_entries.keys():
                # update other var types here
                self.exp_var_entries[variable_name] = value

    def get_default_value(self, variable_name) -> int:
        """
        this function is very similar to update_model, but as name implies it only
        retrieves from the model and does no updating. called only once for each tkinter variable
        in main gui
        """
        if variable_name in self.interval_vars.keys():
            return self.interval_vars[variable_name]
        elif variable_name in self.exp_var_entries.keys():
            # update other var types here
            return self.exp_var_entries[variable_name]

    def generate_schedule(self) -> None:
        """
        This is a primary function of the program. This function generates the pseudo random schedule for what stimuli will be presented in which
        trials. It generates the intervals for ITI, TTC, and sample time using base time plus generated random +/- variations as given by user
        in interface.
        """
        try:
            # set number of trials based on number of stimuli, and number of trial blocks set by user
            num_stimuli = self.exp_var_entries["Num Stimuli"]
            num_trial_blocks = self.exp_var_entries["Num Trial Blocks"]

            self.exp_var_entries["Num Trials"] = (num_stimuli // 2) * num_trial_blocks

            self.create_random_intervals()

            pairs = self.create_trial_blocks()

            # stimuli_1 & stimuli_2 are lists that hold the stimuli to be introduced for each trial on their respective side
            stimuli_side_one, stimuli_side_two = self.generate_pairs(pairs)

            # args needed -> stimuli_1, stimuli_2
            # these are lists of stimuli for each trial, for each side respectivelyc:w
            self.build_frame(
                stimuli_side_one,
                stimuli_side_two,
            )

        except Exception as e:
            logger.error(f"Error generating program schedule {e}.")

    def create_random_intervals(self) -> None:
        try:
            num_trials = self.exp_var_entries["Num Trials"]

            final_intervals = [None, None, None]

            interval_keys = ["ITI_var", "TTC_var", "sample_var"]

            random_interval_keys = [
                "ITI_random_entry",
                "TTC_random_entry",
                "sample_random_entry",
            ]

            # for each type of interval (iti, ttc, sample), generate final interval times
            for i in range(len(interval_keys)):
                base_val = self.interval_vars[interval_keys[i]]
                # this makes an array that is n=num_trials length of base_val
                base_intervals = np.repeat(base_val, num_trials)

                # get plus minus value for this interval type
                random_var = self.interval_vars[random_interval_keys[i]]

                if random_var == 0:
                    # if there is no value to add/subtract randomly, continue on
                    final_intervals[i] = base_intervals

                else:
                    # otherwise make num_trials amount of random integers and add them to the final_intervals
                    random_interval_arr = np.random.randint(
                        -random_var, random_var, num_trials
                    )

                    final_intervals[i] = np.add(base_intervals, random_interval_arr)

            # assign results for respective types to the model for storage and later use
            self.ITI_intervals_final = final_intervals[0]
            self.TTC_intervals_final = final_intervals[1]
            self.sample_intervals_final = final_intervals[2]

            logger.info("Random intervals created.")
        except Exception as e:
            logger.error(f"Error creating random intervals: {e}")
            raise

    def calculate_max_runtime(self) -> (int, int):
        max_time = (
            sum(self.ITI_intervals_final)
            + sum(self.TTC_intervals_final)
            + sum(self.sample_intervals_final)
        )
        minutes, seconds = self.convert_seconds_to_minutes_seconds(max_time / 1000)
        return (minutes, seconds)

    def create_trial_blocks(self) -> List:
        """
        This function generates all possible pairings that can occur in ONE TRIAL BLOCK given the input
        valve stimuli. For example, if we have valves 1 and 5 containing substance 1, and valves 2 and 6
        containing substance 2, this method will generate a list of two pairings that can occur in one trial block.
        We need each pairing to complete a block, so we generate [(substance 1, substance 2), (substance 2, substance 1)]
        as our output. This covers each possible pairing.          (valve 1),   (valve 6)      (valve 2),    (valve 5)
                                                0 indexing ---->     (0)          (5)             (1)         (4)
        """
        try:
            # creating pairs list which stores all possible pairs
            pairs = []
            num_stimuli = self.exp_var_entries["Num Stimuli"]
            block_sz = num_stimuli // 2

            stimuli_names = list(self.stimuli_data.stimuli_vars.values())

            for i in range(block_sz):
                pair_index = self.get_paired_index(i, num_stimuli)
                pairs.append((stimuli_names[i], stimuli_names[pair_index]))

            return pairs
        except Exception as e:
            logger.error(f"Error creating trial blocks: {e}")
            raise

    def generate_pairs(self, pairs) -> Tuple[list, list]:
        """
        This method takes the possible pairings given by create trial blocks and generates
        which substance will be on a given port for each trial of the experiment. To
        ensure pseudo randomness, we utilize np.random.shuffle on each pairing.
        """
        try:
            pseudo_random_lineup: List[tuple] = []

            stimulus_1: List[str] = []
            stimulus_2: List[str] = []

            for _ in range(self.exp_var_entries["Num Trial Blocks"]):
                pairs_copy = [tuple(pair) for pair in pairs]
                np.random.shuffle(pairs_copy)
                pseudo_random_lineup.extend(pairs_copy)

            for pair in pseudo_random_lineup:
                stimulus_1.append(pair[0])
                stimulus_2.append(pair[1])

            return stimulus_1, stimulus_2
        except Exception as e:
            logger.error(f"Error generating pairs: {e}")
            raise

    def build_frame(
        self,
        stimuli_1,
        stimuli_2,
    ) -> None:
        num_stimuli = self.exp_var_entries["Num Stimuli"]
        num_trials = self.exp_var_entries["Num Trials"]
        num_trial_blocks = self.exp_var_entries["Num Trial Blocks"]

        # each block must contain each PAIR -> num pairs = num_stim / 2
        block_size = int(num_stimuli / 2)
        try:
            data = {
                "Trial Block": np.repeat(
                    range(1, num_trial_blocks + 1),
                    block_size,
                ),
                "Trial Number": np.repeat(range(1, num_trials + 1), 1),
                "Port 1": stimuli_1,
                "Port 2": stimuli_2,
                "Port 1 Licks": np.full(num_trials, np.nan),
                "Port 2 Licks": np.full(num_trials, np.nan),
                "ITI": self.ITI_intervals_final,
                "TTC": self.TTC_intervals_final,
                "SAMPLE": self.sample_intervals_final,
                "TTC Actual": np.full(num_trials, np.nan),
            }

            self.program_schedule_df = pd.DataFrame(data)

            logger.info("Initialized stimuli dataframe.")
        except Exception as e:
            logger.debug(f"Error Building Stimuli Frame: {e}.")
            raise

    def save_all_data(self):
        dataframes = {
            "Experiment Schedule": self.program_schedule_df,
            "Individual Lick Data": self.event_data.event_dataframe,
        }

        for name, df_reference in dataframes.items():
            self.save_df_to_xlsx(name, df_reference)

    @staticmethod
    def get_paired_index(i, num_stimuli):
        match num_stimuli:
            case 2:
                # if num stim is 2, we are only running the same stimulus on both sides,
                # we will only see i=0 here, and its paired with its sibling i=4
                return i + 4
            case 4:
                # if num stim is 4, we are only running 2 stimuli per side,
                # we will see i=0 and i =1 here, paired with siblings i=5 & i=4 respectively
                match i:
                    case 0:  # valve 1
                        return i + 5  # (5) / valve 6
                    case 1:  # valve 2
                        return i + 3  # (4) / valve 5
            case 8:
                match i:
                    case 0:
                        return i + 5
                    case 1:
                        return i + 3
                    case 2:
                        return i + 5
                    case 3:
                        return i + 3
            case _:
                return None

    @staticmethod
    def save_df_to_xlsx(name, dataframe) -> None:
        """Method to bring up the windows file save dialog menu to save the two data tables to external files"""
        try:
            file_name = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel Files", "*.xlsx")],
                initialfile=f"{name}, {datetime.date.today()}",
                title="Save Excel file",
            )

            if file_name:
                dataframe.to_excel(file_name, index=False)
            else:
                logger.info("User cancelled saving the stimuli dataframe.")

            logger.info("Data saved to xlsx files.")
        except Exception as e:
            logger.error(f"Error saving data to xlsx: {e}")
            raise

    @staticmethod
    def convert_seconds_to_minutes_seconds(total_seconds):
        try:
            # Integer division to get whole minutes
            minutes = total_seconds // 60
            # Modulo to get remaining seconds
            seconds = total_seconds % 60
            return minutes, seconds
        except Exception as e:
            logger.error(f"Error converting seconds to minutes and seconds: {e}")
            raise

            # def calculate_randomness():
            #    consecutive_streaks: dict[int, int] = defaultdict(int)
            #    current_streak = 0

            # first_pair_counts: dict[tuple, int] = defaultdict(int)
            # last_first_pair = None
        #    if first_pair_strings == last_first_pair:
        #        current_streak += 1
        #    else:
        #        if current_streak > 0:
        #            consecutive_streaks[current_streak] += 1
        #        current_streak = 1
        #        last_first_pair = first_pair_strings

        #    if current_streak > 0:
        #        consecutive_streaks[current_streak] += 1

        #    first_pair_percentages = {
        #        pair: count / self.num_trial_blocks * 100
        #        for pair, count in first_pair_counts.items()
        #    }

        # first_pair_strings = tuple(var.get() for var in pairs_copy[0])
        # first_pair_counts[first_pair_strings] += 1

        #    logger.info("Percentages of each pair appearing first:")
        #    for pair, percentage in first_pair_percentages.items():
        #        logger.info(f"{pair}: {percentage:.2f}%")

        #    logger.info("\nConsecutive streaks of first pairs:")
        #    for streak_length, count in consecutive_streaks.items():
        #        logger.info(f"Streak of {streak_length}: {count} times")

        #    logger.info("Pairs generated.")
