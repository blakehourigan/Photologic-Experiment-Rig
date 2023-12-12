import time


class ExperimentLogic:
    def __init__(self, controller) -> None:
        self.controller = controller

    def read_licks(self, i):
        """Define the method for reading data from the optical fiber Arduino"""
        # try to read licks if there is a arduino connected
        available_data, data = self.controller.arduino_mgr.read_from_laser()

        data_mgr = self.controller.data_mgr
        licks_dataframe = data_mgr.licks_dataframe
        total_licks = data_mgr.total_licks

        if available_data:
            # Append the data to the scrolled text widget
            if "Stimulus One Lick" in data:
                # if we detect a lick on spout one, then add it to the lick data table
                # and add whether the lick was a TTC lick or a sample lick

                # format for this is self.dataFrame.loc[rowNumber, Column Title] = value
                data_mgr = self.controller.data_mgr
                licks_dataframe = data_mgr.licks_dataframe
                total_licks = data_mgr.total_licks

                licks_dataframe.loc[
                    total_licks, "Trial Number"
                ] = data_mgr.current_trial_number
                
                licks_dataframe.loc[total_licks, "Port Licked"] = "Stimulus 1"
                licks_dataframe.loc[total_licks, "Time Stamp"] = (
                    time.time() - data_mgr.start_time
                )
                licks_dataframe.loc[total_licks, "State"] = self.controller.state

                self.controller.data_mgr.side_one_licks += 1
                self.controller.data_mgr.total_licks += 1

            if "Stimulus Two Lick" in data:
                # if we detect a lick on spout one, then add it to the lick data table
                # and add whether the lick was a TTC lick or a sample lick

                # format for this is self.dataFrame.loc[rowNumber, Column Title] = value

                licks_dataframe.loc[
                    total_licks, "Trial Number"
                ] = data_mgr.current_trial_number

                licks_dataframe.loc[total_licks, "Port Licked"] = "Stimulus 2"
                licks_dataframe.loc[total_licks, "Time Stamp"] = (
                    time.time() - data_mgr.start_time
                )
                licks_dataframe.loc[total_licks, "State"] = self.controller.state

                self.controller.data_mgr.side_two_licks += 1
                self.controller.data_mgr.total_licks += 1

        # Call this method again every 100 ms
        self.update_licks_id = self.controller.main_gui.root.after(
            100, lambda: self.read_licks(i)
        )
        self.controller.after_ids.append(self.update_licks_id)

    def check_licks(self, iteration):
        """define method for checking licks during the TTC state"""
        # if we are in the TTC state and detect 3 or more licks from either side, then immediately jump to the sample time
        # state and continue the trial
        if (
            self.side_one_licks >= 3 or self.side_two_licks >= 3
        ) and self.controller.state == "TTC":
            self.controller.data_mgr.stimuli_dataframe.loc[
                self.controller.data_mgr.current_trial_number - 1, "TTC Actual"
            ] = (time.time() - self.controller.data_mgr.state_start_time) * 1000

            self.controller.main_gui.root.after_cancel(self.controller.after_sample_id)
            self.side_one_licks = 0
            self.side_two_licks = 0
            self.controller.sample_time(iteration)
