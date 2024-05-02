from typing import List, Tuple

class valveTestLogic:
    def __init__(self, controller) -> None:
        self.controller = controller
        self.side_one_volumes: List[int] = []
        self.side_two_volumes: List[int] = []
        self.side_one_durations: List[int] = []
        self.side_two_durations: List[int] = []
        
        self.completed_test_pairs = 0

    def start_valve_test_sequence(self, num_valves):
        """the test sequence that each valve will undergo
        """
        # create a list of all the lists we use for the testing script, and clear each one of them to avoid problems with bad data
        for lst in [self.side_one_volumes, self.side_two_volumes, self.side_one_durations, self.side_two_durations]: 
            lst.clear()

        self.completed_test_pairs = 0 
        self.num_valves = num_valves
    
    
        # get the beaker measurements for the respective sides, set init to true to tell the popup to display the beaker measurement text.
        self.side_one_container_measurement = self.controller.valve_testing_window.input_popup(0, init = True, side = 1)
        self.side_two_container_measurement = self.controller.valve_testing_window.input_popup(0, init = True, side = 2)
                
        execute = self.check_container_measurements(self.side_one_container_measurement, self.side_two_container_measurement) # if the user did not cancel either prompt, then continue

        if execute:
            self.controller.send_command_to_arduino(arduino='motor', command= f'<T,{num_valves.get()}>')

    def append_to_volumes(self) -> None:
        self.side_one_volumes.append(self.controller.valve_testing_window.input_popup(self.completed_test_pairs + 1) - self.side_one_container_measurement)
        self.side_two_volumes.append(self.controller.valve_testing_window.input_popup(self.completed_test_pairs + 5) - self.side_two_container_measurement)
        
        execute = self.check_container_measurements(self.side_one_container_measurement, self.side_two_container_measurement) # if the user did not cancel either prompt, then continue
        
        if execute:
            if self.completed_test_pairs != self.controller.valve_testing_window.num_valves_to_test.get():
                if self.controller.valve_testing_window.ask_continue():    
                    # after appending data, if it is not the final valve pair, then continue
                    self.controller.send_command_to_arduino(arduino='motor', command="<continue>")
                else:
                    self.controller.valve_testing_window.testing_aborted()
                self.completed_test_pairs += 1 
        
    def begin_updating_opening_times(self, duration_string) -> None:
        side_one_durations, side_two_durations = self.unpack_and_assign_durations(duration_string)
        side_one_opening_times, side_one_ul_per_lick = self.update_opening_times(self.num_valves.get(), side_one_durations, self.side_one_volumes)
        side_two_opening_times, side_two_ul_per_lick = self.update_opening_times(self.num_valves.get(), side_two_durations, self.side_two_volumes)
        
        opening_times = side_one_opening_times
        opening_times.extend(side_two_opening_times)
        
        ul_dispensed = side_one_ul_per_lick
        ul_dispensed.extend(side_two_ul_per_lick)
        
        self.controller.valve_testing_window.set_valve_opening_times(opening_times)
        self.controller.valve_testing_window.set_ul_dispensed(ul_dispensed)
        self.controller.valve_testing_window.validate_and_update()
        
        side_one_str = ",".join(map(str, side_one_opening_times))
        side_two_str = ",".join(map(str, side_two_opening_times))
        
        self.controller.send_command_to_arduino(arduino='motor', command=f"<{side_one_str},{side_two_str}>")
                    
    def update_opening_times(self, num_valves, durations, volumes) -> Tuple[List[int], List[float]]:
        # this function is called once per side to update the opening times for each side of valves
        # use valve_opening_times varable from the gui window1
        opening_times = [] 
        ul_dispensed = []
        # get the desired volume entered in the testing window. This value is given in micro liter, divide by 1000 to get milliliters
        desired_volume = (self.controller.valve_testing_window.desired_volume.get()) / 1000

        for i in range(num_valves // 2):

            v_per_open_previous = (volumes[i] / 1000)
            ul_dispensed.append(v_per_open_previous)
            
            opening_times.append(round(int(durations[i]) * (desired_volume / v_per_open_previous)))
            
        if((num_valves // 2) < 8):
            for i in range(8 - (num_valves // 2)):
                opening_times.append(durations[i + (num_valves // 2)])
    

        return opening_times, ul_dispensed
    
    def unpack_and_assign_durations(self, duration_string):
        # Initialize empty lists for Side 1 and Side 2
        side_one_values = []
        side_two_values = []
        
        # Remove the starting '<' and ending '>' characters
        trimmed_str = duration_string[2:-1]
        
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
    
    def check_container_measurements(self, side_one, side_two) -> bool:
        execute = True
        if side_one == 0.0 or side_two == 0.0: 
            execute = False
        return execute