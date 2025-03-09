#include "optical_detection.h"
#include <Arduino.h>
#include <Vector.h>
#include <avr/io.h>
#include <avr/wdt.h>

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
