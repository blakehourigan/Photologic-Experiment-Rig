"""
This module defines the StimuliData class, responsible for managing the names
or identifiers assigned to the substances associated with each valve.

It provides a simple dictionary-based storage for these names and methods to
update them based on GUI input and retrieve their current values. It also
includes a helper method for pairing stimuli names.
"""

import logging

logger = logging.getLogger(__name__)


class StimuliData:
    """
    Manages the names or identifiers associated with stimuli delivered by each valve.

    This class holds a dictionary mapping a standardized key (e.g., "Valve 1 Substance")
    to the user-defined name for the substance in that valve (e.g., "Quinine", "Water").
    It facilitates updating these names from the GUI and retrieving them when needed,
    for example, during schedule generation or data logging.

    Attributes
    ----------
    - **`stimuli_vars`** (*dict[str, str]*): Dictionary storing the substance name for each valve.
        Keys are formatted like "Valve X Substance", and values are the user-defined names.

    Methods
    -------
    - `update_model`(...)
        Updates the substance name in `stimuli_vars` for a given valve based on GUI input.
    - `get_default_value`(...)
        Retrieves the current substance name for a given valve key.
    """

    def __init__(self) -> None:
        """
        Initializes the StimuliData object.

        Creates the `stimuli_vars` dictionary and populates it with default
        placeholder names for each of the 8 possible valves currently supported (e.g., "Valve 1 Substance").
        """
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

    def update_model(self, variable_name: str, value: str | None) -> None:
        """
        Updates the stored substance name for a specific valve.

        Checks if the provided `variable_name` exists as a key in the
        `stimuli_vars` dictionary. If it exists and the `value` is not None,
        it updates the dictionary entry with the new name.

        Parameters
        ----------
        - **variable_name** (*str*): The key identifying the valve whose substance name is being updated (e.g., "Valve 3 Substance").
        - **value** (*str | None*): The new substance name (string) provided by the user, or None if the input was empty/invalid.
        """
        if value is not None:
            if variable_name in self.stimuli_vars.keys():
                self.stimuli_vars[variable_name] = value

    def get_default_value(self, variable_name: str) -> str:
        """
        Retrieves the current substance name associated with a valve key.

        Used primarily to populate GUI fields with their initial/current values.

        Parameters
        ----------
        - **variable_name** (*str*): The key identifying the valve whose substance name is requested (e.g., "Valve 1 Substance").

        Returns
        -------
        - *str*: The current substance name associated with the key, or an empty string ("") if the key is not found in `stimuli_vars`.
        """
        if variable_name in self.stimuli_vars.keys():
            return self.stimuli_vars[variable_name]
        else:
            return ""
