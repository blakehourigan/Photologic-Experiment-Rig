class valveTestLogic:
    def __init__(self, controller) -> None:
        self.controller = controller
        
        self.tubes_filled=False

    def run_valve_test(self, num_valves):
        """_controller function to run the testing sequence on given valves_
        """
        self.valves_to_test = num_valves
        self.valve_index = 1
        self.test_run_index = 0
        self.test_valve_sequence(num_valves)
        

    def test_valve_sequence(self, num_valves):
        """the test sequence that each valve will undergo
        """
        
        for i in range(num_valves):
            # Open and close the current valve
            self.open_valve(self.valve_index)
        
        # Check if all valves have been tested
        if self.valve_index > num_valves:
            print("Valve testing completed.")
            return


                

    def calculate_current_cylinder_Volume(self) -> float:
        """_ calculate cylinder volume based on the current height of the liquid_
        """
        volume = self.volume - self.controller.valve_testing_window.desired_volume.get()
        return volume

    def open_valve(self, valve):
        self.controller.arduino_mgr.open_one_valve(valve, "SIDE_ONE")
        print("open")
        self.controller.valve_testing_window.top.after(
            int(self.opening_time * 1000), lambda: self.close_valve(valve)
        )

    def close_valve(self, valve):
        self.controller.arduino_mgr.close_one_valve(valve, "SIDE_ONE")
        print("close")
        # Update the test run index and valve index
        self.test_run_index += 1
        if self.test_run_index >= self.controller.valve_testing_window.number_test_runs.get():
            self.valve_index += 1
            self.test_run_index = 0

        # Update cylinder volume, height and opening time
        self.volume = self.calculate_current_cylinder_Volume()
        self.height_surface_to_opening = self.calculate_height_of_liquid()
        #self.opening_time = self.calculate_valve_opening_time()

        print(f"Valve {valve} opening time: {self.opening_time}")
        print(f"Valve {valve} volume: {self.volume}")
        print(f"Valve {valve} height: {self.height_surface_to_opening}")
        print("\n\n")

        # Schedule the next test run
        self.controller.valve_testing_window.top.after(
            1000,  # Give some time before starting the next test run
            self.test_valve_sequence
        )
        
    def run_valves(self):
        self.controller.valve_testing_window.change_run_button_state()
        
        for i in range(1,5):
            self.controller.arduino_mgr.open_one_valve(i, "SIDE_ONE")
            self.controller.arduino_mgr.open_one_valve(i, "SIDE_TWO")


    def stop_valves(self):
        self.controller.valve_testing_window.change_run_button_state()
        
        for i in range(1,5):
            self.controller.arduino_mgr.close_one_valve(i, "SIDE_ONE")
            self.controller.arduino_mgr.close_one_valve(i, "SIDE_TWO")