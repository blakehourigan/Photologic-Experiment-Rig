#include "./src/optical_detection/optical_detection.h"
#include "./src/valve_control/valve_control.h"
#include "./src/valve_testing/test_valves.h"
#include "./src/reporting/reporting.h"
#include "./src/exp_init/exp_init.h"
#include <AccelStepper.h>
#include <avr/wdt.h>

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

void setup() {
  Serial.begin(BAUD_RATE);

  stepper.setMaxSpeed(MAX_SPEED);
  stepper.setAcceleration(ACCELERATION);

  // Set digital pins 22-29 (PORTA) as outputs (side one valves)
  DDRA = 255; 
  // Set digital pins 30-37 (PORTC) as outputs (side two valves)
  DDRC = 255; 
  
  // set the data direction register to output on pin 4 & pin 5 of the L register
  DDRL |= (1 << LED_BIT_SIDE1);
  DDRL |= (1 << LED_BIT_SIDE2);
  
  // turn each side's (yellow&red) lick indicator LEDs to on
  PORTL |= (1 << LED_BIT_SIDE1);
  PORTL |= (1 << LED_BIT_SIDE2);

}

void loop() {
  String command = "\0";
  // define all variables used in experiment runtime scope  
  static String previous_command = "\0";
  
  // structs that hold schedule and duration vectors for the experiment
  static ValveSchedules schedules;
  static ValveDurations durations;
  
  // stores whether motor should open valves or not
  static bool open_valves = false;

  static bool motor_running = false; 
  // since we support up to 320 trials, 
  // we need more than 2^8 = 255 we use 
  // 16 bit int which provides vals up to 2^16 -1 = 65535
  static uint16_t current_trial = 0;
  
  static unsigned long program_start_time = 0; 
  static unsigned long trial_start_time = 0;

  static bool side_one_pin_state = 0;
  static bool side_one_previous_state = 1;

  static bool side_two_pin_state = 0;
  static bool side_two_previous_state = 1;
  
  // start the time structs off with empty values
  static lickTimeDetails lick_time = {};
  static doorMotorTimeDetails motor_time = {};
  static valveTimeDetails valve_time = {};

  // side one data variables, used in optical/valve functions like
  // open_valve, close_valve, etc
  static SideData side_one_data{
  SIDE_ONE,
  side_one_pin_state,
  side_one_previous_state,
  durations.side_one,
  schedules.side_two,
  };
  
  // side two struct  
  static SideData side_two_data{
  SIDE_TWO,
  side_two_pin_state,
  side_two_previous_state,
  durations.side_two,
  schedules.side_two,
  };
  
  // a pointer to the side_data for the side that was licked most recently
  static SideData * side_data;
 
  // check if motor_running first to avoid unneccessary calls to stepper.distanceToGo()
  if (motor_running && stepper.distanceToGo() == 0) {
    // at this stage we have filled movement_start, movement_type, and now movement_end
    motor_time.movement_end = millis();
    report_motor_movement(previous_command, motor_time, program_start_time, trial_start_time);
    
    if(previous_command.equals("UP")){
      current_trial++;
    }
    motor_running = false;
  }
  
  // read current optical sensor pin values
  side_one_pin_state = (PINL & (1 << OPTICAL_DETECTOR_BIT_SIDE1));
  side_two_pin_state = (PINL & (1 << OPTICAL_DETECTOR_BIT_SIDE2));


  // only if the schedule and durations have been recieved should we detect licks and open valves
  if(schedules.schedules_recieved && durations.durations_recieved){
    // utilized for a sample lick. we only move on from a lick once both valve close time AND 
    // lick finish time have been marked.
    static bool handling_lick = false;
    static bool lick_marked = false;
    static bool valve_marked = false;

    if (!handling_lick){
      // if no previous lick or valve movement is being handled
        bool lick_start_one = lick_started(side_one_data);
        bool lick_start_two = lick_started(side_two_data);

        if (lick_start_one || lick_start_two){
          if(lick_start_one){
            side_data = &side_one_data;
            lick_start_one= false;
          }else{
            side_data = &side_two_data;
            lick_start_two = false;
          }
          // record lick start time 
          lick_time.lick_begin_time = millis();
          handling_lick = true;

          if (open_valves){
            open_valve(side_data, current_trial);
            valve_time.valve_open_time = micros();
          }
        }
      }
    else if(handling_lick){
      // check for lick end / valve end and record data
      if (!open_valves) {
        if (lick_ended(side_data)){ 
          lick_time.lick_end_time= millis();

          handling_lick = false;
          report_ttc_lick(side_data->SIDE, lick_time, program_start_time, trial_start_time);

          lick_time = {};
        }
      }else if(open_valves){
        // if open_valves is set, open valve and wait for it to close
        // to move on
        if (!lick_marked){ 
          if (lick_ended(side_data)){
            lick_time.lick_end_time= millis();
            lick_marked = true;
          }
        }
        if(!valve_marked){
          if(close_valve(valve_time, side_data, current_trial)){
            valve_time.valve_close_time = micros();
            valve_marked = true;
          }
        }
        if (lick_marked && valve_marked){ 
          // we've seen both lick end and valve end, okay to move on.
          // reset check variables, report lick, and unblock lick start
          lick_marked = false;
          valve_marked = false;
          handling_lick = false;

          report_sample_lick(side_data->SIDE, lick_time, valve_time, program_start_time, trial_start_time);
          lick_time = {};
        }
      }
    } 
  }
  // update the side leds that flash when a lick is detected on a side
  update_leds(side_one_pin_state, side_two_pin_state);

  if (Serial.available() > 0) {
    // read until the newline char 
    command = Serial.readStringUntil('\n');
  }
  // only process command cases if one has been recieved from the controller
  if (!command.equals("\0")){
    if (command.equals("BEGIN OPEN VALVES")) {
      // begin opening valves from this point forward, 
      // this is called when sample time begins
      open_valves = true;
    }
    else if (command.equals("STOP OPEN VALVES")) {
      // stop opening valves
      open_valves = false;
    }
    else if (command.equals("TRIAL START")){
      trial_start_time = millis(); 
    }
    else if (command.equals("T=0")){
      // mark t=0 time for the arduino side
      program_start_time = millis();

      trial_start_time = program_start_time;
    }
    else if (command.equals("UP")) {
      // tell door motor to move up
      noInterrupts();
      stepper.moveTo(STEPPER_UP_POSITION);
      interrupts();
      
      motor_time.movement_start = millis();
      motor_time.movement_type = "UP"; 

      previous_command = command;
      motor_running = true;
    }
    else if (command.equals("DOWN")){
      // tell door motor to move down
      stepper.moveTo(STEPPER_DOWN_POSITION);
      
      motor_time.movement_start = millis();
      motor_time.movement_type = "DOWN"; 

      previous_command = command;
      motor_running = true;
    }
    else if (command.equals("RESET")){
      // reset the board
      wdt_enable(WDTO_1S);
    }
    else if(command.equals("PRIME VALVES")){
        
        }
    else if (command.equals("TEST VOL")){
      run_valve_test(side_one_data.valve_durations, side_two_data.valve_durations);
    }
    else if (command.equals("OPEN SPECIFIC")){
      control_specific_valves(); 
    }
    else if (command.equals("REC DURATIONS")){
      // receive valve durations from the python controller
      durations = receive_durations();
    }
    else if (command.equals("REC SCHED")){
      // handle recieving program schedule
      schedules = receive_schedules();
    }
    else if (command.equals("REC VAR")){
      // handle recieving program variables (num_stim, num_trials)
      receive_exp_variables();
    }
    else if (command.equals("VER SCHED")){
      schedule_verification(schedules);
    }
    else if (command.equals("VER DURATIONS")){
      durations_verification(durations);
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

