import logging
import numpy as np

logger = logging.getLogger(__name__)


class StimuliData:
    def __init__(self) -> None:
        """filling the dataframe with the values that we have at this time"""
        self.stimuli_vars = {
            f"Valve {1} Substance": "Valve 1 Substance",
            f"Valve {2} Substance": "Valve 2 Substance",
            f"Valve {3} Substance": "Valve 3 Substance",
            f"Valve {4} Substance": "Valve 4 Substance",
            f"Valve {5} Substance": "Valve 5 Substance",
            f"Valve {6} Substance": "Valve 6 Substance",
            f"Valve {7} Substance": "Valve 7 Substance",
            f"Valve {8} Substance": "Valve 8 Substance",
        }

    def update_model(self, variable_name, value) -> None:
        """
        This function will be called when a tkiner entry is updated in the gui
        to update the standard variables held in the model classes there
        """
        # if the variable name for the tkinter entry item that we are updating is
        # in the exp_data interval variables dictionary, update that entry
        # with the value in the tkinter variable
        if value is not None:
            if variable_name in self.stimuli_vars.keys():
                self.stimuli_vars[variable_name] = value

    def get_default_value(self, variable_name: str) -> str:
        """
        this function is very similar to update_model, but as name implies it only
        retrieves from the model and does no updating. called only once for each tkinter variable
        in main gui
        """
        if variable_name in self.stimuli_vars.keys():
            return self.stimuli_vars[variable_name]
        else:
            return ""

    def pair_stimuli(self, stimulus_1, stimulus_2):
        """Preparing to send the data to the motor arduino"""
        try:
            paired_stimuli = list(zip(stimulus_1, stimulus_2))
            logger.info("Stimuli paired.")
            return paired_stimuli
        except Exception as e:
            logger.error(f"Error pairing stimuli: {e}")
            raise
