import tkinter as tk
from tkinter import ttk

from views.gui_common import GUIUtils


class LicksWindow(tk.Toplevel):
    # inject the licks dataframe when we create the class so we have access to that data
    def __init__(self, licks_data) -> None:
        super().__init__()
        # reference to licks model
        self.licks_data = licks_data

        self.title("Licks Data")
        self.bind("<Control-w>", lambda event: self.withdraw())
        # Bind closing the window to self.withdraw()
        self.protocol("WM_DELETE_WINDOW", self.withdraw())

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
        # df we are working with is self.licks_data.licks_dataframe, get rid of self prefix and such to save room
        df = self.licks_data.licks_dataframe
        # num rows in that df currently
        len_licks_df = len(df)

        last_item = self.last_item

        # Insert data from the DataFrame. iterrows() returns an iterator over the rows of a df of form (index, series (of data))
        for i in range(last_item, len_licks_df):
            row_content = df.iloc[i]

            item_iid = f"item {i}"
            nan_item_iid = "item 0"

            # if the current item iid that we are evaluating exists already, don't worry about it
            if self.timestamped_licks.exists(nan_item_iid):
                self.timestamped_licks.delete(nan_item_iid)
                continue

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
        self.timestamped_licks = ttk.Treeview(self.licks_frame, show="headings")

        self.timestamped_licks["columns"] = list(
            self.licks_data.licks_dataframe.columns
        )

        # Configure the columns
        for col in self.timestamped_licks["columns"]:
            self.timestamped_licks.heading(col, text=col)

        self.update_table()

        self.timestamped_licks.pack(fill="both", expand=True)
