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
        side_one_volumes = []
        side_two_volumes = []
        
        side_one_durations = []
        side_two_durations = []
        
        command = 'T'
        self.controller.arduino_mgr.send_command_to_motor(command)
        
        num_valves_send = str(num_valves.get()) + '\n'
        command = num_valves_send
        self.controller.arduino_mgr.send_command_to_motor(command)
    
        valve = 1
    
        while True:
            if self.controller.arduino_mgr.motor_arduino.in_waiting:
                line = self.controller.arduino_mgr.motor_arduino.readline().decode('utf-8').rstrip()
                if line == "Finished loop":
                    side_one_volumes.append(self.controller.valve_testing_window.input_popup(valve))
                    side_two_volumes.append(self.controller.valve_testing_window.input_popup(valve + 4))
                    if self.controller.valve_testing_window.ask_continue():    
                        pass
                    else:
                        self.controller.valve_testing_window.tesing_aborted()
                        break
                    command = "continue\n"
                    self.controller.arduino_mgr.send_command_to_motor(command)
                    valve += 1
                elif line == "start":
                    command = "continue\n"
                    self.controller.arduino_mgr.send_command_to_motor(command)
                elif line == "side one":
                    while(self.controller.arduino_mgr.motor_arduino.in_waiting):
                        line = self.controller.arduino_mgr.motor_arduino.readline().decode('utf-8').rstrip()
                        if line == "end side one":
                            break
                        else:
                            side_one_durations.append(int(line))

                elif line == "side two":
                    while(self.controller.arduino_mgr.motor_arduino.in_waiting):
                        line = self.controller.arduino_mgr.motor_arduino.readline().decode('utf-8').rstrip()
                        if line == "end side two":
                            break
                        else:
                            side_two_durations.append(int(line))
                    break
        
        print(side_one_durations, end="\n")
        print(side_two_durations, end="\n")
        
        print(side_one_volumes)
        print(side_two_volumes)
        self.update_and_send_opening_times(num_valves, side_one_durations, side_one_volumes, 1)
        self.update_and_send_opening_times(num_valves, side_two_durations, side_two_volumes, 2)
                      
    def update_and_send_opening_times(self, num_valves, durations, volumes, side):
        opening_time = 0
        
        desired_volume = self.controller.valve_testing_window.desired_volume
        
        command = "V"
        self.controller.arduino_mgr.send_command_to_motor(command)
        
        command = str(side)
        self.controller.arduino_mgr.send_command_to_motor(command)
        
        for i in range(num_valves.get()/2):
            v_per_open_previous = (volumes[i] / 500)
            
            opening_time = durations[i] * (desired_volume / v_per_open_previous)
            print(opening_time)
            self.controller.arduino_mgr.send_command_to_motor(opening_time)

            
            
            