"""
Defines the ProgramScheduleWindow class, a Tkinter Toplevel window.
Creates and displays the detailed experimental schedule in a scrollable table format.

This view presents the pre-generated trial sequence, stimuli details, and allows
for updates of trial outcomes (like lick counts and actual `TTC` state completion time)
as the experiment progresses. It relies on data provided by external objects
(like `models.experiment_process_data` ExperimentProcessData) to populate and update its content.
"""

import tkinter as tk

### Type Hinting###
from models.experiment_process_data import ExperimentProcessData
### Type Hinting###

from views.gui_common import GUIUtils


class ProgramScheduleWindow(tk.Toplevel):
    """
    A Toplevel window that displays the experimental program schedule as a table.

    This window visualizes the `program_schedule_df` DataFrame.
    Accomplished by creating a scrollable canvas containing a grid
    of Tkinter Labels representing the schedule data. It updates
    cell contents (licks, TTC) and highlights the currently active trial row
    based on calls from the main `app_logic` StateMachine.

    The window is initially hidden and populated only when `show()` is first called.

    Attributes
    ----------
    - **exp_data** (*ExperimentProcessData*): An instance that allows for access to experiment related data and methods. (E.g stimuli names,
      access trial lick data, etc.)
    - **canvas_frame** (*tk.Frame*): The main frame holding the canvas and scrollbar.
    - **canvas** (*tk.Canvas*): The widget providing the scrollable area for the table.
    - **scrollbar** (*tk.Scrollbar*): The scrollbar linked to the canvas.
    - **stimuli_frame** (*tk.Frame*): The frame placed inside the canvas, containing the grid of Label widgets that form the table.
    - **header_labels** (*list[tk.Label] OR None*): List of tk.Label widgets for the table column headers. `None` until populated.
    - **cell_labels** (*list[list[tk.Label]] OR  None*): A 2D list (list of rows, each row is a list of tk.Label widgets)
        representing the table data cells. `None` until populated.

    Methods
    -------
    - `refresh_end_trial(...)`
        Updates the display after a trial ends (licks, TTC).
    - `refresh_start_trial(...)`
        Updates the display when a new trial starts (row highlighting).
    - `update_ttc_actual(...)`
        Specifically updates the 'TTC Actual' cell for a given trial.
    - `update_licks(...)`
        Specifically updates the lick count cells ('Port 1 Licks', 'Port 2 Licks') for a given trial.
    - `update_row_color(...)`
        Highlights the current trial row in yellow and resets the previous row's color.
    - `show()`
        Makes the window visible. Populates the table with data on the first call if not already done.
    - `populate_stimuli_table()`
        Creates the header and data cell Label widgets within `stimuli_frame` based on `exp_data.program_schedule_df`.
    """

    def __init__(self, exp_process_data: ExperimentProcessData) -> None:
        super().__init__()
        self.exp_data = exp_process_data

        self.title("Program Schedule")

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.resizable(False, False)

        # bind control + w shortcut to hiding the window
        self.bind("<Control-w>", lambda event: self.withdraw())
        self.protocol("WM_DELETE_WINDOW", lambda: self.withdraw())

        # Setup the canvas and scrollbar
        self.canvas_frame = tk.Frame(self)
        self.canvas_frame.grid(row=0, column=0, sticky="nsew")
        self.canvas_frame.grid_rowconfigure(0, weight=1)
        self.canvas_frame.grid_columnconfigure(0, weight=1)

        self.canvas = tk.Canvas(self.canvas_frame)

        self.scrollbar = tk.Scrollbar(
            self.canvas_frame, orient="vertical", command=self.canvas.yview
        )

        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.scrollbar.grid(row=0, column=1, sticky="ns")

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.stimuli_frame = tk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.stimuli_frame, anchor="nw")

        # initialize stimuli table variables to None, this is used in show() method to
        # understand if window has been initialized yet
        self.header_labels: list[tk.Label] | None = None
        self.cell_labels: list[list[tk.Label]] | None = None

        self.withdraw()

    def refresh_end_trial(self, logical_trial: int) -> None:
        """
        Updates the table display with data from a completed trial.

        Specifically calls methods to update lick counts and the actual
        Trial Completion Time (TTC) for the given trial index. Forces an
        update of the display using update_idletasks.

        Parameters
        ----------
        - **logical_trial** (*int*): The zero-based index of the trial that just ended, corresponding to the row in the
            DataFrame and `cell_labels`.

        Raises
        ------
        - *AttributeError*: If `self.exp_data` or its `program_schedule_df` is not properly initialized.
        - *IndexError*: If `logical_trial` is out of bounds for `self.cell_labels`.
        - *KeyError*: If expected columns ('Port 1 Licks', etc.) are missing from the DataFrame.
        - *tk.TclError*: If there's an issue updating the Label widgets.
        """
        self.update_licks(logical_trial)
        self.update_ttc_actual(logical_trial)

        self.update_idletasks()

    def refresh_start_trial(self, current_trial: int) -> None:
        """
        Updates the table display to indicate the trial that is starting.

        Specifically highlights the row corresponding to the `current_trial`.
        Forces an update of the display.

        Parameters
        ----------
        - **current_trial** (*int*): The one-based number of the trial that is starting.

        Raises
        ------
        - *AttributeError*: If `self.cell_labels` is not initialized (i.e., table not populated).
        - *IndexError*: If `current_trial` (adjusted for zero-based index) is out of bounds.
        - *tk.TclError*: If there's an issue updating the Label widgets' background color.
        """
        self.update_row_color(current_trial)

        self.update_idletasks()

    def update_ttc_actual(self, logical_trial: int) -> None:
        """
        Updates the 'TTC Actual' cell for the specified trial row.

        Retrieves the value from `self.exp_data.program_schedule_df` and sets
        the text of the corresponding Label widget in `self.cell_labels`.

        Parameters
        ----------
        - **logical_trial** (*int*): The zero-based index of the trial row to update.

        Raises
        ------
        - *AttributeError*: If `self.exp_data` or `program_schedule_df` is None.
        - *IndexError*: If `logical_trial` or the column index (9) is out of bounds.
        - *KeyError*: If the column 'TTC Actual' does not exist in the DataFrame.
        - *tk.TclError*: If updating the Label text fails.
        """
        df = self.exp_data.program_schedule_df

        if self.cell_labels is None:
            return

        # ttc actual time taken update
        self.cell_labels[logical_trial][9].configure(
            text=df.loc[logical_trial, "TTC Actual"]
        )

    def update_licks(self, logical_trial: int) -> None:
        """
        Updates the 'Port 1 Licks' and 'Port 2 Licks' cells for the specified trial row.

        Retrieves values from `self.exp_data.program_schedule_df` and sets
        the text of the corresponding Label widgets in `self.cell_labels`.

        Parameters
        ----------
        - **logical_trial** (*int*): The zero-based index of the trial row to update.

        Raises
        ------
        - *AttributeError*: If `self.exp_data` or `program_schedule_df` is None.
        - *IndexError*: If `logical_trial` or column indices (4, 5) are out of bounds.
        - *KeyError*: If columns 'Port 1 Licks' or 'Port 2 Licks' do not exist.
        - *tk.TclError*: If updating the Label text fails.
        """

        if self.cell_labels is None:
            return

        df = self.exp_data.program_schedule_df
        # side 1 licks update
        self.cell_labels[logical_trial][4].configure(
            text=df.loc[logical_trial, "Port 1 Licks"]
        )
        # side 2 licks update
        self.cell_labels[logical_trial][5].configure(
            text=df.loc[logical_trial, "Port 2 Licks"]
        )

    def update_row_color(self, logical_trial: int) -> None:
        """
        Highlights the current trial row and resets the previous trial row's color.

        Sets the background color of all labels in the `current_trial` row (one-based)
        to yellow. If it's not the first trial, it also resets the background color
        of the previous trial's row labels to white.

        Parameters
        ----------
        - **logical_trial** (*int*): The zero-based number of the trial to highlight.

        Raises
        ------
        - *AttributeError*: If `self.cell_labels` is None.
        - *IndexError*: If `current_trial` (adjusted for zero-based index) is out of bounds for `self.cell_labels`.
        - *tk.TclError*: If configuring label background colors fails.
        """
        # Adjust indices for zero-based indexing
        if self.cell_labels is None:
            return

        if logical_trial == 1:
            for i in range(10):
                self.cell_labels[logical_trial][i].configure(bg="yellow")
        else:
            for i in range(10):
                self.cell_labels[logical_trial - 1][i].configure(bg="white")
            for i in range(10):
                self.cell_labels[logical_trial][i].configure(bg="yellow")

    def show(self) -> None:
        """
        Makes the window visible and populates the schedule table if not already done.

        Checks if the table labels (`header_labels`) have been created. If not, it
        attempts to populate the table using `populate_stimuli_table()`. Before
        populating, it checks if the required DataFrame (`program_schedule_df`) exists
        and displays an error via `GUIUtils.display_error` if it's missing.
        After successful population (or if already populated), it makes the window
        visible using `deiconify()`. It also sets the canvas size and scroll region
        after the first population.

        Raises
        ------
        - *AttributeError*: If `self.exp_data` is None or lacks `program_schedule_df` when checked.
        - *Exception*: Can propagate exceptions from `populate_stimuli_table()` during the initial population.
        """
        # if this is our first time calling the function, then grab the data and fill the table

        # if we have already initialized we don't need to do anything. updating the window is handled
        # by the main app when a trial ends
        if self.header_labels is None:
            if self.exp_data.program_schedule_df.empty:
                GUIUtils.display_error(
                    "Schedule Not Generated",
                    "The schedule has not yet been generated, try doing that in the Valve / Stimuli window first and come back!",
                )
                return
            self.populate_stimuli_table()
            # Calculate dimensions for canvas and scrollbar
            canvas_width = self.stimuli_frame.winfo_reqwidth()

            # max height 500px
            canvas_height = min(500, self.stimuli_frame.winfo_reqheight() + 50)

            # Adjust the canvas size and center the window
            self.canvas.config(scrollregion=self.canvas.bbox("all"))
            self.canvas.config(width=canvas_width, height=canvas_height)

            # self.update_row_color(self.controller.data_mgr.current_trial_number)
        self.deiconify()

    def populate_stimuli_table(self) -> None:
        """
        Creates and .grid()s the Tkinter Label widgets for the schedule table headers and data.

        Reads data from `self.exp_data.program_schedule_df`. Creates a header row
        and then iterates through the DataFrame rows, creating a Label for each cell.
        Stores the created labels in `self.header_labels` and `self.cell_labels`.
        Adds horizontal separators periodically based on experiment settings
        (Num Stimuli / 2). Assumes `self.stimuli_frame` exists.

        Raises
        ------
        - *AttributeError*: If `self.exp_data` or `program_schedule_df` is None or malformed.
        - *KeyError*: If `exp_data.exp_var_entries["Num Stimuli"]` is missing or invalid when calculating separator frequency.
        - *tk.TclError*: If widget creation or grid placement fails.
        - *TypeError*: If data types in the DataFrame are incompatible with Label text.
        """

        df = self.exp_data.program_schedule_df
        self.header_labels = []
        self.cell_labels = []

        # Create labels for the column headers
        for j, col in enumerate(df.columns):
            header_label = tk.Label(
                self.stimuli_frame,
                text=col,
                bg="light blue",
                fg="black",
                font=("Helvetica", 10, "bold"),
                highlightthickness=2,
                highlightbackground="dark blue",
            )
            header_label.grid(row=0, column=j, sticky="nsew", padx=5, pady=2.5)
            self.header_labels.append(header_label)

        # Get the total number of columns for spanning the separator
        total_columns = len(df.columns)
        current_row = 1  # Start at 1 to account for the header row

        # Create cells for each row of data
        for i, row in enumerate(df.itertuples(index=False), start=1):
            row_labels = []
            for j, value in enumerate(row):
                cell_label = tk.Label(
                    self.stimuli_frame,
                    text=value,
                    bg="white",
                    fg="black",
                    font=("Helvetica", 10),
                    highlightthickness=1,
                    highlightbackground="black",
                )
                cell_label.grid(
                    row=current_row, column=j, sticky="nsew", padx=5, pady=2.5
                )
                row_labels.append(cell_label)
            self.cell_labels.append(row_labels)
            current_row += 1  # Move to the next row

            # Insert a horizontal line below every two rows
            if i % (self.exp_data.exp_var_entries["Num Stimuli"] / 2) == 0:
                separator_frame = tk.Frame(self.stimuli_frame, height=2, bg="black")
                separator_frame.grid(
                    row=current_row,
                    column=0,
                    columnspan=total_columns,
                    sticky="ew",
                    padx=5,
                )
                self.stimuli_frame.grid_rowconfigure(current_row, minsize=2)
                current_row += (
                    1  # Increment the current row to account for the separator
                )

        # Make sure the last separator is not placed outside the data rows
        if len(df) % 2 == 0:
            self.stimuli_frame.grid_rowconfigure(current_row - 1, minsize=0)
        self.stimuli_frame.update_idletasks()
