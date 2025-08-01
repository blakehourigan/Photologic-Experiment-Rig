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
  
  DDRB |= (1 << PB4); // digital pin 10 | sends start signal to capacitive arduino.
  DDRH |= (1 << PH5);
  DDRH |= (1 << PH6);

  PORTB &= ~(1 << PB4); // digital 10 | 1 sends start signal
  PORTH &= ~(1 << PH5); // digital 8 | capacitive arduino lick enable set to 0 initially
  PORTH &= ~(1 << PH6); // digital 9 | 1 resets the board (resets lick counters)
  

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

  static bool accept_licks = false;
  
  // use this variable to know if trial start valve opening is occuring. 
  // in other words: do i need to worry about closing the valves? 
  static bool valve_open_trial_start = false;
  // since we support up to 320 trials, 
  // we need more than 2^8 = 255 we use 
  // 16 bit int which provides vals up to 2^16 -1 = 65535
  static uint16_t current_trial = 0;
  
  static unsigned long program_start_time = 0; 
  static unsigned long trial_start_time = 0;
  
  static unsigned long last_poll = 0;
  static unsigned long last_lick_end = 0;
  
  static unsigned long sent_reset_time = 0;
  static unsigned long sent_start_time = 0;

  static bool side_one_pin_state = 0;
  static bool side_one_previous_state = 1;

  static bool side_two_pin_state = 0;
  static bool side_two_previous_state = 1;
  
  // start the time structs off with empty values
  static lickTimeDetails lick_time = {};
  static doorMotorTimeDetails motor_time = {};
  static valveTimeDetails valve_time = {};
  
  // valve time storage for the trial start valve actuations
  static valveTimeDetails trial_start_valve_side_one = {};
  static valveTimeDetails trial_start_valve_side_two = {};

  // side one data variables, used in optical/valve functions like
  // open_valve, close_valve, etc
  static SideData side_one_data{
  SIDE_ONE,
  side_one_pin_state,
  side_one_previous_state,
  durations.side_one,
  schedules.side_one,
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
  
  // if reset pin has been high for 3ms or longer reset it. 
  bool reset_pin_high = (PINH & (1 << PH6)) != 0;
  if (reset_pin_high && ((millis() - sent_reset_time) > 2)){
    PORTH &= ~(1 << PH6); // digital 9 | 1 resets the board (resets lick counters)
  }
  
  // if reset pin has been high for 3ms or longer reset it. 
  bool start_pin_high = (PINB & (1 << PB4)) != 0;
  if (start_pin_high && ((millis() - sent_start_time) > 2)){
    PORTB &= ~(1 << PB4); // digital 10, clear start signal bit
  }
  
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
      
      PORTH &= ~(1 << PH6); // digital 9 | capacitive arduino reset set to 0 initially, 1 resets
      PORTH |= (1 << PH5); // digital 8 | enable lick counting in sample state
    }
    else if (command.equals("STOP OPEN VALVES")) {
      // stop opening valves
      open_valves = false; 
      
      PORTH &= ~(1 << PH5); // digital 8 | disable lick counting 
      PORTH |= (1 << PH6); // digital 9 | 1 resets the board (resets lick counters)
      
      sent_reset_time = millis();
    }
    else if (command.equals("TRIAL START")){
      trial_start_time = millis(); 
      accept_licks = true;
      valve_open_trial_start = true;
  
      /// open valve for current trial on each spout, disabled for now. need to add ability to enable this as an option
      /// in the controller software. 
      //open_valve(&side_one_data, current_trial);
      //valve_time.valve_open_time = micros();
      //trial_start_valve_side_one.valve_open_time = micros();
      //
      //open_valve(&side_two_data, current_trial);
      //trial_start_valve_side_two.valve_open_time = micros();
    }
    else if (command.equals("T=0")){
      // mark t=0 time for the arduino side
      program_start_time = millis();
      PORTB |= (1 << PB4);

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
      prime_valves();             
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

  //if(valve_open_trial_start){
  //  close_valve(trial_start_valve_side_one, &side_one_data, current_trial);
  //  close_valve(trial_start_valve_side_two, &side_two_data, current_trial);
  //}

  // check if motor_running first to avoid unneccessary calls to stepper.distanceToGo()
  if (motor_running && stepper.distanceToGo() == 0) {
    // at this stage we have filled movement_start, movement_type, and now movement_end
    motor_time.movement_end = millis();
    report_motor_movement(previous_command, motor_time, program_start_time, trial_start_time);

    if(previous_command.equals("UP")){
      current_trial++;
      accept_licks = false;
    }
    motor_running = false;
  }

  // read current optical sensor pin values, ONLY EVERY 5 MILLISECONDS. We do this to avoid picking up 
  // rapidly changing noise on beam break onset or offset. This was a solution to gh issue #30
  if(millis() - last_poll > 5){
    side_one_previous_state = side_one_pin_state;
    side_two_previous_state = side_two_pin_state;

    side_one_pin_state = (PINL & (1 << OPTICAL_DETECTOR_BIT_SIDE1));
    side_two_pin_state = (PINL & (1 << OPTICAL_DETECTOR_BIT_SIDE2));
    
    last_poll = millis();
  }


  // only if the schedule and durations have been recieved should we detect licks and open valves
  if(schedules.schedules_recieved && durations.durations_recieved){
    // utilized for a sample lick. we only move on from a lick once both valve close time AND 
    // lick finish time have been marked.
    static bool handling_lick = false;
    static bool lick_marked = false;
    static bool valve_marked = false;

    // this is used to 'lock' a mode in so that if a lick begins in ttc it is 
    // guaranteed to finish there. same applies to 'sample' (open_valves)
    static bool ttc_lick = true;
    
    if (accept_licks && (!handling_lick)){
      // if no previous lick or valve movement is being handled
      bool lick_start_one = lick_started(&side_one_data); 
      bool lick_start_two = lick_started(&side_two_data);
    
      // reject licks if that start before 90 seconds after last lick has ended.
      if(millis() - last_lick_end > 90){
        if (lick_start_one || lick_start_two){
          if(lick_start_one){
            side_data = &side_one_data;
          }else{
            side_data = &side_two_data;
          }
          // record lick start time 
          lick_time.lick_begin_time = millis();
          handling_lick = true;

          ttc_lick=true;

          if (open_valves){
            ttc_lick =false;
            open_valve(side_data, current_trial);
            valve_time.valve_open_time = micros();
          }
        }
      }
    }
    else if(handling_lick){
      // check for lick end / valve end and record data
      if (ttc_lick) {
        // insert a close_all call here, because when we tell the arduino to stop opening valves 
        // (make open_valves false), we also cease closing them. This can stick a valve open. Closing all here should 
        // resolve this.
        // we also set lick_market and valve_marked to false to reset the slate for when we return to open_valves state.
        close_all();
        lick_marked = false;
        valve_marked = false;

        if (lick_ended(side_data)){ 
          lick_time.lick_end_time= millis();
          last_lick_end = lick_time.lick_end_time;
          // in the case that we WERE in open valves, but moved out of a sample time without
          handling_lick = false;
          report_ttc_lick(side_data->SIDE, lick_time, program_start_time, trial_start_time);

          lick_time = {};
        }
      }else if(!(ttc_lick)){
        // if open_valves is set, open valve and wait for it to close
        // to move on
        if (!lick_marked){ 
          if (lick_ended(side_data)){
            lick_time.lick_end_time= millis();
            last_lick_end = lick_time.lick_end_time;
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


  stepper.run();
}
