#include "optical_detection.h"
#include "../exp_init/exp_init.h"
#include "../valve_control/valve_control.h"
#include <Arduino.h>
#include <Vector.h>
#include <avr/io.h>
#include <avr/wdt.h>

// Variables to store start and end time of licks
unsigned long lick_start_time = 0;
unsigned long lick_end_time = 0;
unsigned long lick_time = 0;

unsigned long last_debounce_time = 0;

void update_leds(bool side_1_pin_state, bool side_2_pin_state) {
  if (side_1_pin_state) {
    // Turn on LED for side 1
    PORTL |= (1 << LED_BIT_SIDE1);
  } else {
    // Turn off LED for side 1, indicating a lick
    PORTL &= ~(1 << LED_BIT_SIDE1);
  }

  if (side_2_pin_state) {
    // Turn on LED for side 2
    PORTL |= (1 << LED_BIT_SIDE2);
  } else {
    // Turn off LED for side 2, indicating a lick
    PORTL &= ~(1 << LED_BIT_SIDE2);
  }
}

void handle_lick(uint8_t valve_side, uint16_t current_trial,
                 Vector<unsigned long> &side_dur_vec,
                 Vector<uint8_t> &side_sched_vec) {

  volatile uint8_t *PORT;

  uint8_t valve_num = 0;
  long int duration = 0;

  valve_num = side_sched_vec.at(current_trial);
  duration = side_dur_vec.at(valve_num);
  if (valve_side == 0) {
    PORT = &PORTA;
  } else {
    // port is already calculated previously, however since ports are split
    // between PORTA for side1 and PORTC for side 2 we must fix the pin num if
    // side 2. subtract valves / 2 from valve num -> valve num 5 becomes 5 -
    // (8/2) = 1 first pin on PORTC is actuated. The only thing that would
    // change this calculation is if total number of valves changed.

    PORT = &PORTC;
    valve_num = valve_num - (VALVES_PER_SIDE / 2);
  }

  lick_handler(valve_num, duration, PORT);
}

void detect_licks(uint8_t side, bool &current_state, bool &previous_state,
                  uint16_t current_trial, Vector<unsigned long> &side_dur_vec,
                  Vector<uint8_t> &side_sched_vec, bool open_valves) {

  unsigned long current_time = millis();

  // only perform this action if it has been 50ms or more since the last call
  unsigned long debounce_time = side_dur_vec[current_trial];

  static bool valve_open = false;

  if ((current_time - last_debounce_time) > (debounce_time / 1000)) {
    if (current_state == 0 && previous_state == 1) {
      // tongue has broken beam, lick begins
      lick_start_time = millis();

      if (open_valves) {
        handle_lick(side, current_trial, side_dur_vec, side_sched_vec);
      }
      // we set this var to true, so that untoggle_solenoids knows that it
      // should be checking if it should be closing valves
      valve_open = true;
      previous_state = 0;
      last_debounce_time = current_time;
    } else if (current_state == 1 && previous_state == 0) {
      // tongue has cleared the beam, lick ended
      lick_end_time = millis();
      lick_time = lick_end_time - lick_start_time;
      untoggle_solenoids();
      send_lick_details(side, lick_time);

      previous_state = 1;
      last_debounce_time = current_time;
    }
  }
  // if (valve_open) {
  //   untoggle_solenoids();
  // }
}

void send_lick_details(uint8_t side, unsigned long lick_time) {
  char side_indicator[50];

  const char *side_str;

  if (side == 0) {
    side_str = "ONE";
  } else if (side == 1) {
    side_str = "TWO";
  }

  sprintf(side_indicator, "STIMULUS %s", side_str);

  // we use println here becuase we read until newlines in the python program
  Serial.print(side_indicator);
  Serial.print("|");
  Serial.println(lick_time);
}
