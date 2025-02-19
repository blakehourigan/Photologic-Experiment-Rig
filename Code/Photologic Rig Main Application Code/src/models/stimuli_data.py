from tkinter import filedialog
import pandas as pd
import logging
import numpy as np

logger = logging.getLogger(__name__)


class StimuliData:
    def __init__(self) -> None:
        """filling the dataframe with the values that we have at this time"""
        self.stimuli_vars = {
            f"Valve {1} substance": "",
            f"Valve {2} substance": "",
            f"Valve {3} substance": "",
            f"Valve {4} substance": "",
            f"Valve {5} substance": "",
            f"Valve {6} substance": "",
            f"Valve {7} substance": "",
            f"Valve {8} substance": "",
        }

    def build_frame(self):
        for key in self.stimuli_vars:
            self.stimuli_vars[key] = key

        logger.debug("Initializing stimuli dataframe.")

        stimuli_1, stimuli_2 = self.generate_pairs()

        block_size = int(self.num_stimuli / 2)

        data = {
            "Trial Block": np.repeat(
                range(1, self.num_trial_blocks + 1),
                block_size,
            ),
            "Trial Number": np.repeat(range(1, self.num_trials + 1), 1),
            "Port 1": stimuli_1,
            "Port 2": stimuli_2,
            "Port 1 Licks": np.full(self.num_trials, np.nan),
            "Port 2 Licks": np.full(self.num_trials, np.nan),
            "ITI": self.ITI_intervals_final,
            "TTC": self.TTC_intervals_final,
            "Sample Time": self.sample_intervals_final,
            "TTC Actual": np.full(self.num_trials, np.nan),
        }

        df = pd.DataFrame(data)
        self.stimuli_dataframe = df
        blocks_generated = True

    def pair_stimuli(self, stimulus_1, stimulus_2):
        """Preparing to send the data to the motor arduino"""
        try:
            paired_stimuli = list(zip(stimulus_1, stimulus_2))
            logger.info("Stimuli paired.")
            return paired_stimuli
        except Exception as e:
            logger.error(f"Error pairing stimuli: {e}")
            raise

    def save_data_to_xlsx(self) -> None:
        """Method to bring up the windows file save dialog menu to save the two data tables to external files"""
        try:
            file_name = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel Files", "*.xlsx")],
                initialfile="experiment schedule",
                title="Save Excel file",
            )

            if file_name:
                self.stimuli_dataframe.to_excel(file_name, index=False)
            else:
                logger.info("User cancelled saving the stimuli dataframe.")

            licks_file_name = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel Files", "*.xlsx")],
                initialfile="licks data",
                title="Save Excel file",
            )

            if licks_file_name:
                self.licks_dataframe.to_excel(licks_file_name, index=False)
            else:
                logger.info("User cancelled saving the licks dataframe.")

            logger.info("Data saved to xlsx files.")
        except Exception as e:
            logger.error(f"Error saving data to xlsx: {e}")
            raise
