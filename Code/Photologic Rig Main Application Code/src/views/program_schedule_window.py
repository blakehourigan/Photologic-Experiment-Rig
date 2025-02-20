import tkinter as tk
import platform

from views.gui_common import GUIUtils


class ProgramScheduleWindow(tk.Toplevel):
    def __init__(self):
        super().__init__()
        self.system = platform.system()

        self.title("Program Schedule")
        self.resizable(False, False)

        # bind control + w shortcut to hiding the window
        self.bind("<Control-w>", lambda event: self.withdraw())
        self.bind_scroll_event()

        # Initialize canvas here to ensure it's available for binding scroll actions
        self.canvas = None
        self.num_tabs = 0

        self.withdraw()

    def bind_scroll_event(self):
        # Bind scroll event to the whole window
        if self.system == "Windows":
            self.bind("<MouseWheel>", self.on_mousewheel)
        else:
            # Linux and MacOS
            self.bind("<Button-4>", self.on_mousewheel)
            self.bind("<Button-5>", self.on_mousewheel)

    def on_mousewheel(self, event):
        if self.canvas:
            delta = (
                -1 * (event.delta // 120)
                if self.system == "Windows"
                else -1 * event.delta
            )
            self.canvas.yview_scroll(int(delta), "units")

    def update_licks_and_TTC_actual(self, current_trial):
        # Adjust indices for zero-based indexing
        if self.winfo_exists():
            row_index = current_trial - 1

            df = self.controller.data_mgr.stimuli_dataframe
            if row_index - 1 >= 0:
                # side 1 licks update
                self.cell_labels[row_index - 1][4].configure(
                    text=df.loc[row_index - 1, "Port 1 Licks"]
                )
                # sode 2 licks update
                self.cell_labels[row_index - 1][5].configure(
                    text=df.loc[row_index - 1, "Port 2 Licks"]
                )
                # ttc actual update
                self.cell_labels[row_index - 1][9].configure(
                    text=df.loc[row_index - 1, "TTC Actual"]
                )

                self.update_idletasks()
                self.update()

    def update_row_color(self, current_trial):
        """Function to update row color"""
        # Adjust indices for zero-based indexing
        row_index = current_trial - 1
        if self.winfo_exists():
            if current_trial == 1:
                for i in range(10):
                    self.cell_labels[row_index][i].configure(bg="yellow")
            else:
                for i in range(10):
                    self.cell_labels[row_index - 1][i].configure(bg="white")
                for i in range(10):
                    self.cell_labels[row_index][i].configure(bg="yellow")
            self.update_idletasks()
            self.update()

    def show_stimuli_table(self):
        if not self.controller.data_mgr.blocks_generated:
            GUIUtils.display_error(
                "Blocks not Generated",
                "Please generate blocks before starting the program.",
            )
            return  # Exit early if blocks aren't generated

        if not self.canvas:
            # Setup the canvas and scrollbar only if not already setup
            canvas_frame = tk.Frame(self)
            canvas_frame.grid(row=0, column=0, sticky="nsew")

            self.canvas = tk.Canvas(canvas_frame)
            scrollbar = tk.Scrollbar(
                canvas_frame, orient="vertical", command=self.canvas.yview
            )

            self.canvas.configure(yscrollcommand=scrollbar.set)
            self.canvas.grid(row=0, column=0, sticky="nsew")
            scrollbar.grid(row=0, column=1, sticky="ns")

            self.grid_rowconfigure(0, weight=1)
            self.grid_columnconfigure(0, weight=1)

            self.stimuli_frame = tk.Frame(self.canvas)
            self.canvas.create_window((0, 0), window=self.stimuli_frame, anchor="nw")

        # Always populate or update the stimuli frame
        self.populate_stimuli_table()
        self.stimuli_frame.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

        # Calculate dimensions for canvas and scrollbar
        canvas_width = self.stimuli_frame.winfo_reqwidth()
        scrollbar_width = (
            scrollbar.winfo_width() if "scrollbar" in locals() else 20
        )  # Use a default width if scrollbar isn't defined
        total_width = canvas_width + scrollbar_width
        canvas_height = min(
            500, self.stimuli_frame.winfo_reqheight() + 50
        )  # max height 500px

        # Adjust the canvas size and center the window
        self.canvas.config(width=canvas_width, height=canvas_height)

        GUIUtils.center_window(self, total_width, canvas_height)

        if self.controller.running:
            self.update_row_color(self.controller.data_mgr.current_trial_number)

    def populate_stimuli_table(self):
        df = self.controller.data_mgr.stimuli_dataframe
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

        total_columns = len(
            df.columns
        )  # Get the total number of columns for spanning the separator
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
            if i % (self.controller.get_num_stimuli() / 2) == 0:
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
