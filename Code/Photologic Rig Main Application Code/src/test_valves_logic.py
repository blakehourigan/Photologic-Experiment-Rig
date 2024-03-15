class valveTestLogic:
    def __init__(self, controller) -> None:
        self.controller = controller

    def run_valve_test(self, num_valves):
        """_controller function to run the testing sequence on given valves_
        """
        self.valves_to_test = num_valves
        self.start_valve_test_sequence(num_valves)
        



    def start_valve_test_sequence(self, num_valves):
        """the test sequence that each valve will undergo
        """
        command = 'T'
        self.controller.arduino_mgr.send_command_to_motor(command)
        
        print(num_valves)
        num_valves = str(num_valves) + '\n'
        command = num_valves
        self.controller.arduino_mgr.send_command_to_motor(command)

        while True:
            if self.motor_arduino.in_waiting:
                line = self.motor_arduino.readline().decode('utf-8').rstrip()
                if line == "Finished loop":
                    self.controller.valve_testing_window.ask_continue()
                    command = "continue\n"
                    self.controller.arduino_mgr.send_command_to_motor(command)

        """     
        amt_dispensed = self.controller.valve_testing_window.desired_volume
        command = amt_dispensed
        self.controller.arduino_mgr.send_command_to_motor(command)"""