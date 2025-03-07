#include "valve_control.h"
#include "Arduino.h"

// the print statements in this file are commented out for performance sake. Can
// be un-commented for debugging purposes.

void untoggle_solenoids() {
  PORTA = 0;
  PORTC = 0;
}

void lick_handler(uint8_t valve_number, unsigned long valve_duration,
                  volatile uint8_t *PORT) {

  // Serial.print("Read valve duration: ");
  // Serial.println(valve_duration);

  int quotient = valve_duration / 10000;
  int remaining_delay = valve_duration - (quotient * 10000);

  *PORT = (1 << valve_number);

  // for (int i = 0; i < quotient; i++) {
  //   delayMicroseconds(10000);
  // }

  // delayMicroseconds(remaining_delay);

  // untoggle_solenoids();
}
