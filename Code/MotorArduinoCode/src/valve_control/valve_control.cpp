#include "valve_control.h"
#include "Arduino.h"

// the print statements in this file are commented out for performance sake. Can
// be un-commented for debugging purposes.

void valve_control::toggle_solenoid(uint8_t valve_num, volatile uint8_t *PORT) {
  *PORT = (1 << valve_num);

  // Serial.print("attempted Toggle of valve: ");
  // Serial.println(valve_num);
}

void valve_control::untoggle_solenoids() {
  PORTA = 0;
  PORTC = 0;
}

void valve_control::lick_handler(uint8_t valve_number,
                                 unsigned long valve_duration,
                                 volatile uint8_t *PORT) {

  // Serial.print("Read valve duration: ");
  // Serial.println(valve_duration);

  int quotient = valve_duration / 10000;
  int remaining_delay = valve_duration - (quotient * 10000);

  toggle_solenoid(valve_number, PORT);

  for (int i = 0; i < quotient; i++) {
    delayMicroseconds(10000);
  }

  delayMicroseconds(remaining_delay);

  untoggle_solenoids();
}
