import numpy as np
import pandas as pd
import logging

logger = logging.getLogger(__name__)


class LicksData:
    def __init__(self):
        # list of lists where each list inside the overall list is a trial full of lick timestamp data
        self.side_one_trial_licks: list[list[float]] = []
        self.side_two_trial_licks: list[list[float]] = []

        self.side_one_licks = 0
        self.side_two_licks = 0

        """
        setup the licks data frame that will hold the timestamps for the licks and which port was licked
        and create an empty first row to avoid a blank table when the program is first run
        """
        # add in trial relative stamp
        # add in lick duration
        self.licks_dataframe = pd.DataFrame(
            [[np.nan, np.nan, np.nan, np.nan, np.nan, ""]],
            columns=[
                "Trial Number",
                "Licked Port",
                "Lick Duration",
                "Time Stamp",
                "Trial Relative Stamp",
                "State",
            ],
        )
        logger.info("Licks dataframe initialized.")

    def insert_row_into_df(
        self, trial_num, port, duration, time_stamp, state_rel_stamp, state
    ):
        # current length in rows of the dataframe, this is where we are going
        # to insert our next element

        licks_df = self.licks_dataframe
        cur_len = len(licks_df)

        # optional params, only apply to licks, not motor stamps
        if port is not None:
            licks_df.loc[cur_len, "Licked Port"] = port
        if duration is not None:
            licks_df.loc[cur_len, "Lick Duration"] = duration

        licks_df.loc[cur_len, "Trial Number"] = trial_num
        licks_df.loc[cur_len, "Time Stamp"] = time_stamp
        licks_df.loc[cur_len, "Trial Relative Stamp"] = state_rel_stamp
        licks_df.loc[cur_len, "State"] = state

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
