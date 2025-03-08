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

void update_leds(bool side_1_pin_state, bool side_2_pin_state) {
  switch (side_1_pin_state) {
  case true:
    // Turn on LED for side 1
    PORTL |= (1 << LED_BIT_SIDE1);
    break;
  case false:
    // Turn off LED for side 1, indicating a lick
    PORTL &= ~(1 << LED_BIT_SIDE1);
    break;
  }
  switch (side_2_pin_state) {
  case true:
    // Turn on LED for side 2
    PORTL |= (1 << LED_BIT_SIDE2);
    break;
  case false:
    // Turn off LED for side 2, indicating a lick
    PORTL &= ~(1 << LED_BIT_SIDE2);
    break;
  }
}

bool lick_started(SideData side_data) {
  if (side_data.current_input_state == 0 &&
      side_data.previous_input_state == 1) {
    side_data.previous_input_state = 0;
    return true;
  }
  return false;
}

bool lick_ended(SideData *side_data) {
  if (side_data->current_input_state == 1 &&
      side_data->previous_input_state == 0) {
    // tongue has cleared the beam, lick occurance ended

    side_data->previous_input_state = 1;
    return true;
  }
  return false;
}

void report_ttc_lick(uint8_t side, unsigned long lick_time) {
  /* Function to report lick occurance and occompanying details such as lick
   * side, length of time tongue broke the beam.
   * we use pipes '|' to separate different data points.
   */
  Serial.print(side);
  Serial.print("|");
  Serial.println(lick_time);
}

void report_sample_lick(uint8_t side, unsigned long lick_time,
                        unsigned long valve_time, unsigned long rel_to_start) {
  /* Function to report lick occurance and occompanying details such as lick
   * side, length of time tongue broke the beam, duration of the valve opening
   * we use pipes '|' to separate different data points.
   */

  Serial.print(side);
  Serial.print("|");
  Serial.print(lick_time);
  Serial.print("|");
  // printline to force data out
  Serial.print(valve_time);
  Serial.print("|");
  Serial.println(rel_to_start);
}
