import numpy as np
import pandas as pd
import logging

logger = logging.getLogger(__name__)


class LicksData:
    def __init__(self):
        self.side_one_trial_licks: list[list[float]] = []
        self.side_two_trial_licks: list[list[float]] = []

        self.side_one_licks = 0
        self.side_two_licks = 0

        self.total_licks = 0

        """
        setup the licks data frame that will hold the timestamps for the licks and which port was licked
        and create an empty first row to avoid a blank table when the program is first run
        """
        self.licks_dataframe = pd.DataFrame(
            [[np.nan, np.nan, np.nan, np.nan]],
            columns=["Trial Number", "Licked Port", "Time Stamp", "State"],
        )
        logger.info("Licks dataframe initialized.")

    def get_lick_timestamps(self, logical_trial) -> (list, list):
        """
        Returns a list of timestamps for the given trial number and licked port.
        """
        # get the ACTUAL trial number, not logical_trial because that is how
        # trials are stored in licks df. 1-indexed, not 0-indexed
        trial_number = logical_trial + 1

        try:
            filtered_df_side_one = self.licks_dataframe[
                (self.licks_dataframe["Trial Number"] == trial_number)
                & (self.licks_dataframe["Licked Port"].isin([1.0]))
            ]

            filtered_df_side_two = self.licks_dataframe[
                (self.licks_dataframe["Trial Number"] == trial_number)
                & (self.licks_dataframe["Licked Port"].isin([2.0]))
            ]

            timestamps_side_one = filtered_df_side_one["Time Stamp"].tolist()
            timestamps_side_two = filtered_df_side_two["Time Stamp"].tolist()

            logger.info(f"Lick timestamps retrieved for trial {trial_number}.")
            return timestamps_side_one, timestamps_side_two
        except Exception as e:
            logger.error(f"Error getting lick timestamps for trial {trial_number}: {e}")
            raise

    def insert_trial_start_stop(self, motor_timestamps):
        try:
            arduino_start = next(
                (
                    entry
                    for entry in motor_timestamps
                    if entry["trial_number"] == 1 and entry["command"] == "0"
                ),
                None,
            )
            arduino_start = arduino_start["occurrence_time"] / 1000

            licks_columns = ["Trial Number", "Licked Port", "Time Stamp", "State"]
            trial_entries = []

            for dictionary in motor_timestamps:
                if dictionary["command"] == "U":
                    state_label = "SIGNAL MOTOR UP"
                elif dictionary["command"] == "D":
                    state_label = "SIGNAL MOTOR DOWN"
                elif dictionary["command"] == "0":
                    continue
                else:
                    state_label = dictionary["command"]

                occurrence_time = round((dictionary["occurrence_time"] / 1000), 3)
                trial = dictionary["trial_number"]
                trial_entry = pd.Series(
                    [trial, "NONE", occurrence_time, state_label], index=licks_columns
                )
                trial_entries.append(trial_entry)

            if self.licks_dataframe.empty:
                self.licks_dataframe = pd.DataFrame(
                    trial_entries, columns=licks_columns
                )
            else:
                self.licks_dataframe = pd.concat(
                    [
                        self.licks_dataframe,
                        pd.DataFrame(trial_entries, columns=licks_columns),
                    ],
                    ignore_index=True,
                )

            self.licks_dataframe = self.licks_dataframe.sort_values(by="Time Stamp")
            self.licks_dataframe = self.licks_dataframe.reset_index(drop=True)

            logger.info("Trial start/stop timestamps inserted into licks dataframe.")
        except Exception as e:
            logger.error(f"Error inserting trial start/stop into licks dataframe: {e}")
            raise
