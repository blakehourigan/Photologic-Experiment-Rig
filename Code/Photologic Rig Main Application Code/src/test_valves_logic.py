from typing import List

class valveTestLogic:
    def __init__(self, controller) -> None:
        self.controller = controller
        self.side_one_volumes: List[int] = []
        self.side_two_volumes: List[int] = []
        self.side_one_durations: List[int] = []
        self.side_two_durations: List[int] = []
        
        self.completed_test_pairs = 0
        


        
    def run_valve_test(self, num_valves):
        """_controller function to run the testing sequence on given valves_
        """
        self.valves_to_test = num_valves
        self.start_valve_test_sequence(num_valves)
        
    def start_valve_test_sequence(self, num_valves):
        """the test sequence that each valve will undergo
        """
        self.side_one_volumes.clear()
        self.side_two_volumes.clear()
        self.side_one_durations.clear()
        self.side_two_durations.clear()

        self.completed_test_pairs = 0 
        self.num_valves = num_valves
    
        self.side_one_container_measurement = self.controller.valve_testing_window.input_popup(0)
        self.side_two_container_measurement = self.controller.valve_testing_window.input_popup(0)
        
        command = f'<T,{num_valves.get()}>'
        self.controller.arduino_mgr.send_command_to_motor(command)

    def append_to_volumes(self) -> None:
        self.side_one_volumes.append(self.controller.valve_testing_window.input_popup(self.completed_test_pairs + 1) - self.side_one_container_measurement)
        self.side_two_volumes.append(self.controller.valve_testing_window.input_popup(self.completed_test_pairs + 5) - self.side_two_container_measurement)
        
        if self.completed_test_pairs != self.controller.valve_testing_window.num_valves_to_test.get():
            if self.controller.valve_testing_window.ask_continue():    
                # after appending data, if it is not the final valve pair, then continue
                command = "<continue>"
                self.controller.arduino_mgr.send_command_to_motor(command)
            else:
                self.controller.valve_testing_window.tesing_aborted()
            self.completed_test_pairs += 1 
        
    def begin_updating_opening_times(self, duration_string) -> None:
        side_one_durations, side_two_durations = self.unpack_and_assign_durations(duration_string)
        side_one_opening_times = self.update_opening_times(self.num_valves.get(), side_one_durations, self.side_one_volumes)
        side_two_opening_times = self.update_opening_times(self.num_valves.get(), side_two_durations, self.side_two_volumes)
        
        side_one_str = ",".join(map(str, side_one_opening_times))
        side_two_str = ",".join(map(str, side_two_opening_times))

        command = f"<{side_one_str},{side_two_str}>"
        
        print(command)
        self.controller.arduino_mgr.send_command_to_motor(command)
                    
    def update_opening_times(self, num_valves, durations, volumes) -> List[int]:
        opening_times = []
                
        desired_volume = self.controller.valve_testing_window.desired_volume.get()
        
        print("volume",volumes)

        for i in range(num_valves // 2):

            v_per_open_previous = (volumes[i] / 1000)
            
            opening_times.append(round(int(durations[i]) * (desired_volume / v_per_open_previous)))
            
        if((num_valves // 2) < 8):
            for i in range(8 - (num_valves // 2)):
                opening_times.append(durations[i + (num_valves // 2)])
        
        
        return opening_times
    
    def unpack_and_assign_durations(self, duration_string):
        # Initialize empty lists for Side 1 and Side 2
        side_one_values = []
        side_two_values = []
        
        # Remove the starting '<' and ending '>' characters
        trimmed_str = duration_string[1:-1]
        
        # Split the string by commas and spaces to isolate values
        parts = [part.strip() for part in trimmed_str.split(',')]
        
        # Flags to determine which side's values are currently being read
        reading_side_one = False
        reading_side_two = False
        
        # Iterate through the parts to extract numbers
        for part in parts:
            if part == 'S1':
                reading_side_one = True
                reading_side_two = False
                continue
            elif part == 'S2':
                reading_side_two = True
                reading_side_one = False
                continue
            
            if reading_side_one:
                # Append value to side one array after converting to integer
                side_one_values.append(int(part))
            elif reading_side_two:
                # Append value to side two array after converting to integer
                side_two_values.append(int(part))
        
        # Return the two lists
        return side_one_values, side_two_values