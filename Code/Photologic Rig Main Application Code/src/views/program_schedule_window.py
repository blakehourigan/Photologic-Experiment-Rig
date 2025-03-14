import tkinter as tk
import platform

from views.gui_common import GUIUtils


class ProgramScheduleWindow(tk.Toplevel):
    def __init__(self, exp_process_data, stimuli_data):
        super().__init__()
        self.system = platform.system()
        self.stimuli_data = stimuli_data
        self.exp_data = exp_process_data

        self.data_initialized = False

        self.title("Program Schedule")

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.resizable(False, False)

        # bind control + w shortcut to hiding the window
        self.bind("<Control-w>", lambda event: self.withdraw())

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
        self.header_labels = None
        self.cell_labels = None

        self.withdraw()

    def refresh_end_trial(self, logical_trial):
        self.update_licks(logical_trial)
        self.update_ttc_actual(logical_trial)

        self.update_idletasks()

    def refresh_start_trial(self, current_trial):
        self.update_row_color(current_trial)

        self.update_idletasks()

    def update_ttc_actual(self, logical_trial):
        df = self.exp_data.program_schedule_df

        # ttc actual time taken update
        self.cell_labels[logical_trial][9].configure(
            text=df.loc[logical_trial, "TTC Actual"]
        )

    def update_licks(self, logical_trial):
        df = self.exp_data.program_schedule_df
        # side 1 licks update
        self.cell_labels[logical_trial][4].configure(
            text=df.loc[logical_trial, "Port 1 Licks"]
        )
        # side 2 licks update
        self.cell_labels[logical_trial][5].configure(
            text=df.loc[logical_trial, "Port 2 Licks"]
        )

    def update_row_color(self, current_trial):
        """Function to update row color"""
        # Adjust indices for zero-based indexing
        row_index = current_trial - 1
        if current_trial == 1:
            for i in range(10):
                self.cell_labels[row_index][i].configure(bg="yellow")
        else:
            for i in range(10):
                self.cell_labels[row_index - 1][i].configure(bg="white")
            for i in range(10):
                self.cell_labels[row_index][i].configure(bg="yellow")

    def show(self):
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
            self.data_initialized = True

            # self.update_row_color(self.controller.data_mgr.current_trial_number)
        self.deiconify()

    def populate_stimuli_table(self):
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
