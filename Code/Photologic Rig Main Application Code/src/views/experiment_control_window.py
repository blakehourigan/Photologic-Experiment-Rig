import tkinter as tk
import logging
from tkinter import ttk
from typing import Dict, List

from views.gui_common import GUIUtils

# Get the logger in use to log info here
logger = logging.getLogger()


class ExperimentCtlWindow(tk.Toplevel):
    # this class requires stimuli related data and a callback to generate the
    # schedule when the 'generate schedule button is pressed"
    # also going to need num stimuli data from exp_var_entries in exp process data
    def __init__(self):
        super().__init__()
        self.title("Stimuli / Valves")
        self.protocol("WM_DELETE_WINDOW", lambda: self.withdraw())
        # lambda requires event here, because it captures the keypress event in case you wanna pass that to the fucntion,
        # but we don't so we do not use it. still, it is required to capture it
        self.bind("<Control-w>", lambda event: self.withdraw())
        self.resizable(False, False)

        # set grid row and col zero to expand to fill the available space
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.canvas = (
            None  # Initialize canvas here to ensure it's available for binding
        )

        self.init_content()

        # on init, we just want to create the window so that we don't have to later, but then we want to hide it
        # until the user chooses to show this window
        self.withdraw()

        logger.info("Experiment Control Window created, but hidden for now.")

    def init_content(self) -> None:
        try:
            # Create the notebook (method of creating tabs at the bottom of the window), and set items to expand in all directions if window is resized
            self.stimuli_frame = ttk.Frame(self)
            self.stimuli_frame.grid(sticky="nsew")

            self.populate_stimuli_frame()

            GUIUtils.create_button(
                self, "Generate Schedule", print("hi"), "green", 0, 0
            )
            self.update_idletasks()

            # Center the window on the screen
            GUIUtils.center_window(self)

            logger.info("Filled contents of experiment control window.")
        except Exception as e:
            logger.error(f"Error filling experiment control window: {e}")
            raise

    def fill_reverse_stimuli(self, source_var, mapped_var):
        try:
            new_value = source_var.get()
            mapped_var.set(new_value)  # Update the mapped variable with the new value
            logger.debug(f"Filled reverse stimuli: {new_value}")
        except Exception as e:
            logger.error(f"Error filling reverse stimuli: {e}")
            raise

    def populate_stimuli_frame(self) -> None:
        try:
            row = 1
            self.ui_components: Dict[str, List[tk.Widget]] = {
                "frames": [],
                "labels": [],
                "entries": [],
            }

            self.stimuli_entry_frame = tk.Frame(
                self.stimuli_frame, highlightthickness=2, highlightbackground="black"
            )
            self.stimuli_entry_frame.grid(
                row=0, column=0, pady=5, padx=5, sticky="nsew"
            )
            self.stimuli_entry_frame.grid_rowconfigure(0, weight=1)

            side_one_label = tk.Label(
                self.stimuli_entry_frame,
                text="Side One",
                bg="light blue",
                font=("Helvetica", 24),
                highlightthickness=2,
                highlightbackground="dark blue",
            )
            side_one_label.grid(row=0, column=0, pady=5)
            side_two_label = tk.Label(
                self.stimuli_entry_frame,
                pady=0,
                text="Side Two",
                bg="light blue",
                font=("Helvetica", 24),
                highlightthickness=2,
                highlightbackground="dark blue",
            )
            side_two_label.grid(row=0, column=1, pady=5)

            for i in range(self.controller.get_num_stimuli() // 2):
                column = 0

                frame, label, entry = GUIUtils.create_labeled_entry(
                    self.stimuli_entry_frame,
                    f"Valve {i + 1}",
                    self.controller.data_mgr.stimuli_vars[f"Valve {i + 1} substance"],
                    row,
                    column,
                )

                source_var = self.controller.data_mgr.stimuli_vars[
                    f"Valve {i + 1} substance"
                ]
                mapped_var = self.controller.data_mgr.stimuli_vars[
                    f"Valve {i + 5} substance"
                ]

                self.controller.data_mgr.stimuli_vars[
                    f"Valve {i + 1} substance"
                ].trace_add(
                    "write",
                    lambda name,
                    index,
                    mode,
                    source_var=source_var,
                    mapped_var=mapped_var: self.fill_reverse_stimuli(
                        source_var, mapped_var
                    ),
                )
                self.ui_components["frames"].append(frame)
                self.ui_components["labels"].append(label)
                self.ui_components["entries"].append(entry)

                row += 1

            row = 1
            for i in range(self.controller.get_num_stimuli() // 2):
                column = 1
                frame, label, entry = GUIUtils.create_labeled_entry(
                    self.stimuli_entry_frame,
                    f"Valve {i + 5}",
                    self.controller.data_mgr.stimuli_vars[f"Valve {i + 5} substance"],
                    row,
                    column,
                )

                source_var = self.controller.data_mgr.stimuli_vars[
                    f"Valve {i + 5} substance"
                ]
                mapped_var = self.controller.data_mgr.stimuli_vars[
                    f"Valve {i + 1} substance"
                ]

                self.controller.data_mgr.stimuli_vars[
                    f"Valve {i + 5} substance"
                ].trace_add(
                    "write",
                    lambda name,
                    index,
                    mode,
                    source_var=source_var,
                    mapped_var=mapped_var: self.fill_reverse_stimuli(
                        source_var, mapped_var
                    ),
                )
                self.ui_components["frames"].append(frame)
                self.ui_components["labels"].append(label)
                self.ui_components["entries"].append(entry)

                row += 1

            logger.info("Stimuli frame populated.")
        except Exception as e:
            logger.error(f"Error populating stimuli frame: {e}")
            raise
