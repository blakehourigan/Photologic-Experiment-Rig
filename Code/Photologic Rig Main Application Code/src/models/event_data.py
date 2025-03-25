import pandas as pd
import logging

logger = logging.getLogger(__name__)


class EventData:
    def __init__(self):
        """
        setup the licks data frame that will hold the timestamps for the licks and which port was licked
        and create an empty first row to avoid a blank table when the program is first run
        """

        self.side_one_licks = 0
        self.side_two_licks = 0

        self.event_dataframe = pd.DataFrame(
            {
                "Trial Number": pd.Series(dtype="float64"),
                "Licked Port": pd.Series(dtype="float64"),
                "Event Duration": pd.Series(dtype="float64"),
                "Valve Duration": pd.Series(dtype="float64"),
                "Time Stamp": pd.Series(dtype="float64"),
                "Trial Relative Stamp": pd.Series(dtype="float64"),
                "State": pd.Series(dtype="str"),
            }
        )

        logger.info("Licks dataframe initialized.")

    def insert_row_into_df(
        self,
        trial_num,
        port,
        duration,
        time_stamp,
        state_rel_stamp,
        state,
        valve_duration=None,
    ):
        # current length in rows of the dataframe, this is where we are going
        # to insert our next element

        event_df = self.event_dataframe
        cur_len = len(event_df)

        # optional params, only apply to licks, not motor stamps
        if port is not None:
            event_df.loc[cur_len, "Licked Port"] = port
        if duration is not None:
            event_df.loc[cur_len, "Event Duration"] = duration
        if valve_duration is not None:
            event_df.loc[cur_len, "Valve Duration"] = valve_duration

        event_df.loc[cur_len, "Trial Number"] = trial_num
        event_df.loc[cur_len, "Time Stamp"] = time_stamp
        event_df.loc[cur_len, "Trial Relative Stamp"] = state_rel_stamp
        event_df.loc[cur_len, "State"] = state

    def get_lick_timestamps(self, logical_trial: int) -> tuple[list, list]:
        """
        Returns a tuple of two lists. First list contains timestamps for port one,
        second list contains timestamps for port two.
        """
        # find the 1-indexed trial number, this is how they are stored in the df
        trial_number = logical_trial + 1

        try:
            filtered_df_side_one = self.event_dataframe[
                (self.event_dataframe["Trial Number"] == trial_number)
                & (self.event_dataframe["Licked Port"].isin([1.0]))
            ]

            filtered_df_side_two = self.event_dataframe[
                (self.event_dataframe["Trial Number"] == trial_number)
                & (self.event_dataframe["Licked Port"].isin([2.0]))
            ]

            timestamps_side_one = filtered_df_side_one["Time Stamp"].tolist()
            timestamps_side_two = filtered_df_side_two["Time Stamp"].tolist()

            logger.info(f"Lick timestamps retrieved for trial {trial_number}.")

            return timestamps_side_one, timestamps_side_two
        except Exception as e:
            logger.error(f"Error getting lick timestamps for trial {trial_number}: {e}")
            raise
