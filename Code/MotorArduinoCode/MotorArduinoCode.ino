#include <AccelStepper.h>
#include <avr/wdt.h>
#include "./src/exp_init/exp_init.h"
#include "./src/optical_detection/optical_detection.h"
#include <Vector.h>

const unsigned long BAUD_RATE = 115200;

// door stepper motor constants
const int STEPPER_UP_POSITION = 0;
const int STEPPER_DOWN_POSITION = 6000;
const int MAX_SPEED = 5500; 
const int ACCELERATION = 5500;

const uint8_t DIR_PIN = 53;
const uint8_t STEP_PIN = 51;

const uint8_t SIDE_ONE = 0;
const uint8_t SIDE_TWO = 1;

AccelStepper stepper = AccelStepper(1, STEP_PIN, DIR_PIN);

void complete_motor_movement(String previous_command, uint16_t &current_trial, bool & motor_running){
  /* 
  This function is called when the door finishes a movement operation. It takes the previous command as 
  a parameter and tells the python controller that a movement has completed and which type of movement 
  that was, so that we can mark these movements down in the lick dataframe. If the movement was up, 
  that means a trial just ended and we can increment to the next trial.
  */
  String command_description = "\0";

  if (previous_command.equals("UP")){
    //// Door is finished moving up, we are now on the next trial
    current_trial++; 
    Serial.println("MOTOR MOVED UP");
  }
  else if(previous_command.equals("DOWN")){
    Serial.println("MOTOR MOVED DOWN");
  }
  motor_running = false;
}

void setup() 
{
  Serial.begin(BAUD_RATE);

  stepper.setMaxSpeed(MAX_SPEED);
  stepper.setAcceleration(ACCELERATION);

  // Set pins 22-29 as outputs (side one valves)
  DDRA |= (255); 
  // Set pins 30-37 as outputs (side two valves)
  DDRC |= (255); 
  
  // set the data direction register to output on pin 5 of the C register
  DDRL |= (1 << LED_BIT_SIDE1);
  // set the data direction register to output on pin 4 of the A register
  DDRL |= (1 << LED_BIT_SIDE2);

  // side one led is on portc pin 5
  PORTL |= (1 << LED_BIT_SIDE1);
  // side two led bit is on portA pin 4
  PORTL |= (1 << LED_BIT_SIDE2);

  int inputPins[] = {2, 8, 9, 10, 11, 12};

  for(unsigned int i = 0; i < sizeof(inputPins) / sizeof(inputPins[0]); i++) 
  {
    pinMode(inputPins[i], INPUT_PULLUP);
  }
}

void loop() {
  String command = "\0";
  // define all variables used in experiment runtime scope  
  static String previous_command = "\0";

  static ScheduleVectors schedules;
  static bool schedule_received = false;
  
  static ValveDurations durations;
  static bool durations_received = false;
  
  // stores whether motor should open valves or not
  static bool open_valves = false;

  static bool motor_running = false; 
  static bool experiment_started = false;
  // since we support up to 320 trials, 
  // we need more than 2^8 = 255 we use 
  // 16 bit int which provides vals up to 2^16 -1 = 65535
  static uint16_t current_trial = 0;
  
  static unsigned long program_start_time = 0; 

  static bool side_1_pin_state = 0;
  static bool side_2_pin_state = 0;

  static bool side_1_previous_state = 1;
  static bool side_2_previous_state = 1;
 
  // check motor running first to avoid unneccessary calls to stepper.distanceToGo()
  if (motor_running && stepper.distanceToGo() == 0) {
    complete_motor_movement(previous_command, current_trial, motor_running);
  }

  side_1_pin_state = (PINL & (1 << OPTICAL_DETECTOR_BIT_SIDE1));
  side_2_pin_state = (PINL & (1 << OPTICAL_DETECTOR_BIT_SIDE2));
  
  if(schedule_received){
    detect_licks(SIDE_ONE, side_1_pin_state, side_1_previous_state, current_trial, durations.side_one_dur_vec, schedules.side_one_sched_vec, open_valves);
    detect_licks(SIDE_TWO, side_2_pin_state, side_2_previous_state, current_trial, durations.side_two_dur_vec, schedules.side_two_sched_vec, open_valves);
  }

  update_leds(side_1_pin_state, side_2_pin_state);

  if (Serial.available() > 0) {
    // read until the newline char 
    command = Serial.readStringUntil('\n');
  }
  // only process command cases if one has been recieved from the controller
  if (!command.equals("\0")){
    // tell door motor to move up
    if (command.equals("UP")) {
      noInterrupts();
      stepper.moveTo(STEPPER_UP_POSITION);
      interrupts();
      //Serial.println("Stepper moving up.");
      previous_command = command;
      motor_running = true;
    }
    // tell door motor to move down
    else if (command.equals("DOWN")){
      stepper.moveTo(STEPPER_DOWN_POSITION);
      //Serial.println("Stepper moving down.");
      previous_command = command;
      motor_running = true;
    }
    // reset the board
    else if (command.equals("RESET")){
      wdt_enable(WDTO_1S);
    }

    else if (command.equals("WHO ARE YOU")){
      Serial.println("MOTOR");
    }
    else if (command.equals("TEST VOL")){
      //test_volume(full_command[2]);
    }
    else if (command.equals("OPEN SPEC")){
      // int porta_value = 0;
      // int portc_value = 0;
      // if (sscanf(full_command.c_str(), "O,%d,%d", &porta_value, &portc_value) == 2) 
      // {
      //   // If both numbers are successfully parsed, assign them to the ports
      //   // Assign the first number to PORTA
      //   PORTA = porta_value; 
      //   // Assign the second number to PORTC
      //   PORTC = portc_value; 
      //   Serial.print("Set PORTA to: "); Serial.println(porta_value);
      //   Serial.print("Set PORTC to: "); Serial.println(portc_value);
      // } else 
      // {
      //   // If parsing fails, log an error or handle the case appropriately
      //   Serial.println("Error parsing PORT values");
      // }
    }
    // mark t=0 time for the arduino side
    else if (command.equals("T=0")){
      program_start_time = millis();

      experiment_started = true;
    }
    // receive valve durations from the python controller
    else if (command.equals("REC DURATIONS")){
      durations = receive_durations();
      durations_received = true;
    }
    // handle recieving program schedule
    else if (command.equals("REC SCHED")){
      schedules = receive_schedules();
      schedule_received = true;
    }
    // handle recieving program variables (num_stim, num_trials)
    else if (command.equals("REC VAR")){
      receive_exp_variables();
    }
    else if (command.equals("VER SCHED")){
      schedule_verification(schedules);
    }
    else if (command.equals("VER DURATIONS")){
      durations_verification(durations);
    }
    // begin opening valves from this point forward
    else if (command.equals("BEGIN OPEN VALVES")) {
      open_valves = true;
    }
    // stop opening valves
    else if (command.equals("STOP OPEN VALVES")) {
      open_valves = false;
    }
    else {
      Serial.print("Unknown command received: ");
      if (command == "\0"){
        Serial.println("null command");
      }
      Serial.println(command);
    }
  }
  stepper.run();
}

