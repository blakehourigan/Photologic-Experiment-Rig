## VALVE CONTROL Motor Arduino Code 
This dir contains code that is designed to actuate the experiment stimuli valves. The lick_handler method is called from MotorArduinoCode.ino
and is passes a valve number (0-7), a PORT, and a duration. The code then decides which valve to actuate given valve_num, num_stimuli, and PORT.

The code will delay here for the duration passed in to the file, then will untoggle all valves and return control to MotorArduinoCode.ino.
