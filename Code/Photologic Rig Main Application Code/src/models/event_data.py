"""
This module defines the EventData class, responsible for managing and storing
time-stamped event data collected during an experiment, primarily lick events
and motor movements.

It utilizes a pandas DataFrame as the data structure to store details
about each event, such as trial number, event state (program state for licks/motor direction for motor movemens),
duration, and timestamps relative to both the program start and the trial start.

It provides methods for initializing the DataFrame, inserting new event rows in a standardized way, and
retrieving specific data like lick timestamps for analysis.
"""

import pandas as pd
import logging

logger = logging.getLogger(__name__)


class EventData:
    """
    Manages experimental event data using a pandas DataFrame.

    This class initializes and maintains a DataFrame to store records of
    significant events occurring during an experiment, such as rat licks
    or motor movements. It keeps track of lick counts per side and provides
    methods to insert new event data rows and query existing data based on
    trial number.

    Attributes
    ----------
    - **`side_one_licks`** (*int*): Counter for the total number of licks detected on side one (Port 1) during a given trial.
    - **`side_two_licks`** (*int*): Counter for the total number of licks detected on side two (Port 2) during a given trial.
    - **`event_dataframe`** (*pd.DataFrame*): The core pandas DataFrame storing event records. Columns include:
        - `Trial Number` (*float64*): The 1-indexed trial in which the event occurred.
        - `Licked Port` (*float64*): The port number licked (1.0 or 2.0), or NaN for non-lick events.
        - `Event Duration` (*float64*): Duration of the event (e.g., lick contact time, motor movement time) in milliseconds. NaN if not applicable.
        - `Valve Duration` (*float64*): Duration the valve was open during a lick event (microseconds). NaN if not applicable.
        - `Time Stamp` (*float64*): Timestamp relative to the start of the entire program (seconds).
        - `Trial Relative Stamp` (*float64*): Timestamp relative to the start of the current trial (seconds).
        - `State` (*str*): String describing the experimental state or event type (e.g., "TTC", "SAMPLE", "MOTOR UP").

    Methods
    -------
    - `insert_row_into_df`(...)
        Adds a new row representing a single event to the `event_dataframe`.
    - `get_lick_timestamps`(...)
        Retrieves lists of lick timestamps for a specific trial, separated by port.
    """

    def __init__(self):
        """
        Initializes the EventData object.

        Sets up the `event_dataframe`, defining columns and expected data types
        for storing lick and motor event data. Initializes lick counters
        (`side_one_licks`, `side_two_licks`) to zero.
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
        trial_num: int,
        port: int | None,
        duration: float | None,
        time_stamp: float,
        trial_rel_stamp: float,
        state: str,
        valve_duration: float | None = None,
    ):
        """
        Inserts a new row representing a single event into the `event_dataframe`.

        Appends a new record to the end of the DataFrame. Handles optional parameters
        (port, duration, valve_duration) which may not be present for all event types
        (e.g., motor movements might not have a 'port').

        Parameters
        ----------
        - **trial_num** (*int*): The 1-indexed trial number during which the event occurred.
        - **port** (*int | None*): The port number associated with the event (e.g., 1 or 2 for licks), or None if not applicable.
        - **duration** (*float | None*): The duration of the event in milliseconds (e.g., lick contact time), or None if not applicable.
        - **time_stamp** (*float*): The timestamp of the event relative to the program start, in seconds.
        - **trial_rel_stamp** (*float*): The timestamp of the event relative to the start of the current trial, in seconds.
        - **state** (*str*): A string identifier for the event type (MOTOR) or experimental state (licks) (e.g., "TTC", "SAMPLE", "MOTOR DOWN").
        - **valve_duration** (*float | None, optional*): The duration the valve was open (microseconds) associated with this event, if applicable. Defaults to None.

        Raises
        ------
        - May propagate pandas-related errors if DataFrame operations fail unexpectedly.
        """
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
        event_df.loc[cur_len, "Trial Relative Stamp"] = trial_rel_stamp
        event_df.loc[cur_len, "State"] = state

    def get_lick_timestamps(self, logical_trial: int) -> tuple[list, list]:
        """
        Retrieves lists of lick timestamps for a specific trial, separated by port.

        Filters the `event_dataframe` based on the provided `logical_trial` number
        (0-indexed, converted to 1-indexed for filtering) and the 'Licked Port' column.
        Extracts the 'Time Stamp' (relative to program start) for each port. Used for filling the
        `RasterizedDataWindow` raster plots.

        Parameters
        ----------
        - **logical_trial** (*int*): The 0-indexed trial number for which to retrieve lick timestamps.

        Returns
        -------
        - *tuple[list[float], list[float]]*: A tuple containing two lists:
            - The first list contains timestamps (float, seconds) for licks on Port 1 during the specified trial.
            - The second list contains timestamps (float, seconds) for licks on Port 2 during the specified trial.

        Raises
        ------
        - Propagates potential pandas errors during filtering or data extraction (e.g., `KeyError` if columns are missing). Logs errors if exceptions occur.
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
