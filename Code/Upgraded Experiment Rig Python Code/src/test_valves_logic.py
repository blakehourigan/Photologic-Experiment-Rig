from math import pi, sqrt


class valveTestLogic:
    def __init__(self, controller) -> None:
        self.controller = controller

        self.cylinder_radius = 1.25  # radius of the cylinder in cm

        self.height_surface_to_opening = (
            14.0  # height from the opening to the top of the liquid in the cylinder
        )
        
        self.volume = 68.0  # volume of the cylinder assuming fill at lip (14cm)
        self.volume = (
            self.calculate_current_cylinder_Volume()
        )  # volume of the cylinder assuming fill at lip (14cm)

        self.TEFLON_TUBE_RADIUS = .0396875  # radius of the tube in cm
    

        self.opening_time = .5  # time to open the valve in seconds
        
        self.tubes_filled=False

    def run_valve_test(self):
        """_controller function to run the testing sequence on given valves_
        """
        self.valve_index = 1
        self.test_run_index = 0
        self.test_valve_sequence()
        

    def test_valve_sequence(self):
        """the test sequence that each valve will undergo
        """
        num_valves = self.controller.valve_testing_window.num_valves_to_test.get()
        # Check if all valves have been tested
        if self.valve_index > num_valves:
            print("Valve testing completed.")
            return

        # Open and close the current valve
        self.open_valve(self.valve_index)
                

    def calculate_current_cylinder_Volume(self) -> float:
        """_ calculate cylinder volume based on the current height of the liquid_
        """
        volume = self.volume - self.controller.valve_testing_window.desired_volume.get()
        return volume

    def calculate_height_of_liquid(self) -> float:
        """calculate the height of the liquid in the cylinder based on the current volume and the desired volume to dispense
        """
        desired_volume = self.controller.valve_testing_window.desired_volume.get()
        
        current_height = self.volume / (pi * self.cylinder_radius**2)
        
        dispensed_height = desired_volume / (pi * self.cylinder_radius**2)
        
        remaining_cylinder_height = current_height - dispensed_height
        
        return remaining_cylinder_height

    def calculate_valve_opening_time(self) -> float:
        """ calculate the time that the valve needs to be open based on the desired volume to dispense """
        desired_volume = self.controller.valve_testing_window.desired_volume.get()
        
        Q = self.calculate_volumetric_flow_rate()
        print(Q)

        time_to_open = desired_volume / Q  # time to open the valve in seconds
        print(time_to_open)
        return time_to_open

    def calculate_volumetric_flow_rate(self) -> float:
        GRAVITY = 980.665  # gravity in centimeters per second squared

        Q = (pi * self.TEFLON_TUBE_RADIUS ** 2) * sqrt(2* GRAVITY * 19)

        return Q  # volumetric flow rate in cm^3/s

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