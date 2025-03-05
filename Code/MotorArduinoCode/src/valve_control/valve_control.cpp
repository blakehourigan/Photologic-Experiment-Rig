#include "valve_control.h"
#include "Arduino.h"

void valve_control::toggle_solenoid(int valve_num, volatile uint8_t *PORT) {
  *PORT = (1 << valve_num);

  Serial.print("Toggled valve ");
  Serial.println(valve_num);
}

void valve_control::untoggle_solenoids() {
  PORTA = 0;
  PORTC = 0;

  Serial.println("Solenoids untoggled.");
}

void valve_control::lick_handler(int valve_number, long int valve_duration,
                                 volatile uint8_t *PORT) {

  Serial.print("Read valve duration: ");
  Serial.println(valve_duration);

  int quotient = valve_duration / 10000;
  int remaining_delay = valve_duration - (quotient * 10000);

  toggle_solenoid(valve_number, PORT);

  for (int i = 0; i < quotient; i++) {
    delayMicroseconds(10000);
  }

  delayMicroseconds(remaining_delay);

  untoggle_solenoids();
}
