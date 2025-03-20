import tkinter as tk
from tkinter import ttk

from views.gui_common import GUIUtils


class EventWindow(tk.Toplevel):
    # inject the event dataframe when we create the class so we have access to that data
    def __init__(self, event_data) -> None:
        super().__init__()
        # reference to event model
        self.event_data = event_data

        self.title("Experiment Event Data")
        self.bind("<Control-w>", lambda event: self.withdraw())

        # Bind closing the window to self.withdraw() to hide the window but not destroy it
        self.protocol("WM_DELETE_WINDOW", lambda: self.withdraw())

        window_icon_path = GUIUtils.get_window_icon_path()
        GUIUtils.set_program_icon(self, icon_path=window_icon_path)

        # init last_item in the table to zero we haven't added anything into the table
        # this is used to efficiently update the table when program is running
        self.last_item = 0

        self.build_table()

        self.withdraw()

    def show(self):
        self.update_table()
        self.deiconify()

    def update_table(self):
        # df we are working with is self.event_data.event_dataframe, get rid of self prefix and such to save room
        df = self.event_data.event_dataframe
        # num rows in that df currently
        len_event_df = len(df)

        last_item = self.last_item

        # Insert data from the DataFrame. iterrows() returns an iterator over the rows of a df of form (index, series (of data))
        for i in range(last_item, len_event_df):
            row_content = df.iloc[i]

            item_iid = f"item {i}"

            self.timestamped_licks.insert(
                "", tk.END, iid=item_iid, values=list(row_content)
            )
        # update the last item with the LAST item that was added on this iteration, next time we will start
        # the loop with this, so that we don't unneccesarily update entries already there
        self.last_item = len(df)

    def build_table(self) -> None:
        self.licks_frame = tk.Frame(self)
        self.licks_frame.grid(row=0, column=0, sticky="nsew")

        # Create a Treeview widget
        # show='headings' ensures we only see columns with headings defined
        self.timestamped_licks = ttk.Treeview(
            self.licks_frame, show="headings", height=25
        )

        self.timestamped_licks["columns"] = list(
            self.event_data.event_dataframe.columns
        )

        # Configure the names of the colums to reflect the heaader labels
        for col in self.timestamped_licks["columns"]:
            self.timestamped_licks.heading(col, text=col)

        self.update_table()

        self.timestamped_licks.pack(fill="both", expand=True)
