import logging
import numpy as np
from typing import Tuple, List
from models.stimuli_data import StimuliData

logger = logging.getLogger(__name__)


class ExperimentProcessData:
    """
    Summary line.

    Extended description of class.

    Attributes:
        attr1 (int): Description of `attr1`.
        attr2 (str): Description of `attr2`.

    Methods:
        method1(param1): Description of method1.
    """

    def __init__(self):
        self.running = False
        self.experiment_completed = False
        self.state = "OFF"
        self.blocks_generated = False

        self.start_time = 0.0
        self.state_start_time = 0.0

        self.pairs: list[Tuple] = []
        self.num_trial_blocks = 10
        self.num_stimuli = 4

        self.current_trial_number = 1
        self.current_iteration = 0

        self.stimuli_data = StimuliData()

        self.ITI_intervals_final: list[int] = []
        self.TTC_intervals_final: list[int] = []

        self.TTC_lick_threshold = 3
        self.sample_intervals_final: list[int] = []

        self.interval_vars = {
            "ITI_var": 30,
            "TTC_var": 15,
            "sample_var": 15,
            "ITI_random_entry": 5000,
            "TTC_random_entry": 0,
            "sample_random_entry": 0,
        }

        self.num_trials = 0

    def convert_seconds_to_minutes_seconds(self, total_seconds):
        try:
            minutes = total_seconds // 60  # Integer division to get whole minutes
            seconds = total_seconds % 60  # Modulo to get remaining seconds
            logger.debug(
                f"Converted {total_seconds} to {minutes} minutes and {seconds} seconds."
            )
            return minutes, seconds
        except Exception as e:
            logger.error(f"Error converting seconds to minutes and seconds: {e}")
            raise

    def calculate_max_runtime(self):
        self.num_trials = (self.num_stimuli // 2) * self.num_trial_blocks
        max_time = self.create_random_intervals()
        minutes, seconds = self.convert_seconds_to_minutes_seconds(max_time / 1000)

    def get_paired_index(self, i, total_entries):
        if total_entries == 2:
            return 1 - i
        elif total_entries == 4:
            return total_entries - i - 1
        elif total_entries == 8:
            if i % 2 == 0:
                return (i + 5) % total_entries
            else:
                return (i + 3) % total_entries
        else:
            raise ValueError("Unexpected number of entries")

    def create_trial_blocks(self):
        """this is the function that will generate the full roster of stimuli for the duration of the program"""
        try:
            # the above is a separate function, whose return value should be used in the main app to do the below

            # self.controller.main_gui.update_max_time(minutes, seconds)

            #########################################################
            self.changed_vars = [
                stimulus
                for i, (key, stimulus) in enumerate(
                    self.stimuli_data.stimuli_vars.items()
                )
                if stimulus != f"Valve {i + 1} substance"
            ]

            if len(self.changed_vars) > self.num_stimuli:
                start_index = self.num_stimuli
                for index, key in enumerate(self.stimuli_data.stimuli_vars):
                    if index >= start_index:
                        self.stimuli_data.stimuli_vars[key] = key

            if self.changed_vars:
                self.pairs = []
                total_entries = len(self.changed_vars)
                for i in range(total_entries // 2):
                    pair_index = self.get_paired_index(i, total_entries)
                    self.pairs.append(
                        (self.changed_vars[i], self.changed_vars[pair_index])
                    )
            else:
                print("badbadnotgood")
                # self.controller.display_gui_error(
                #    "Stimulus Not Changed",
                #    "One or more of the default stimuli have not been changed, please change the default value and try again",
                # )
            logger.info("Trial blocks created.")
        except Exception as e:
            logger.error(f"Error creating trial blocks: {e}")
            raise

    def create_random_intervals(self) -> int:
        try:
            self.ITI_intervals_final.clear()
            self.TTC_intervals_final.clear()
            self.sample_intervals_final.clear()

            for entry in range(self.num_trials):
                for interval_type in ["ITI", "TTC", "sample"]:
                    random_entry_key = f"{interval_type}_random_entry"
                    var_key = f"{interval_type}_var"
                    final_intervals_key = f"{interval_type}_intervals_final"

                    random_interval = np.random.randint(
                        -self.interval_vars[random_entry_key],
                        self.interval_vars[random_entry_key] + 1,
                    )

                    final_interval = self.interval_vars[var_key] + random_interval

                    if not hasattr(self, final_intervals_key):
                        setattr(self, final_intervals_key, [])
                    getattr(self, final_intervals_key).append(final_interval)

            max_time = (
                sum(self.ITI_intervals_final)
                + sum(self.TTC_intervals_final)
                + sum(self.sample_intervals_final)
            )

            logger.info("Random intervals created.")
            return max_time
        except Exception as e:
            logger.error(f"Error creating random intervals: {e}")
            raise

    def generate_pairs(self) -> Tuple[list, list]:
        try:
            pseudo_random_lineup: List[tuple] = []
            stimulus_1: List[str] = []
            stimulus_2: List[str] = []

            for _ in range(self.num_trial_blocks):
                if self.num_trial_blocks != 0 and self.changed_vars:
                    pairs_copy = [tuple(pair) for pair in self.pairs]
                    np.random.shuffle(pairs_copy)
                    pseudo_random_lineup.extend(pairs_copy)

                elif len(self.changed_vars) == 0:
                    print("badbadnotgood")
                    # self.controller.display_gui_error(
                    #    "Stimuli Variables Not Yet Changed",
                    #    "Stimuli variables have not yet been changed, to continue please change defaults and try again.",
                    # )

            for entry in pseudo_random_lineup:
                stimulus_1.append(entry[0])
                stimulus_2.append(entry[1])

            return stimulus_1, stimulus_2
        except Exception as e:
            logger.error(f"Error generating pairs: {e}")
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
