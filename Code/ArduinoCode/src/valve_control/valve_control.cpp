#include "valve_control.h"
#include "../exp_init/exp_init.h"
#include "Arduino.h"
#include <cstdint>

// the print statements in this file are commented out for performance sake. Can
// be un-commented for debugging purposes.

bool close_valve(valveTimeDetails valve_time, SideData *side_data,
                 uint16_t current_trial) {

  uint8_t valve_num = side_data->experiment_schedule[current_trial];

  unsigned long allotted_duration = side_data->valve_durations[valve_num];

  unsigned long current_time = micros();

  if ((current_time - valve_time.valve_open_time) > allotted_duration) {
    // reset all valve pins to zero to turn them off
    PORTA = 0;
    PORTC = 0;

    return true;
  }
  return false;
}

void open_valve_testing(volatile uint8_t *PORT, uint8_t valve_number) {
  // open the valve on the desired port
  *PORT = (1 << valve_number);
}
void close_single_valve(volatile uint8_t *PORT, uint8_t valve_number) {
  // close the valve on the desired port at the valve number
  *PORT &= ~(1 << valve_number);
}

void open_valve(SideData *side_data, uint16_t current_trial) {
  /* Function takes in current side_data and current trial, determines
   * current port and valve, opens the valve.
   *
   * port is known based on side. we must offset the valve num for side 2 due to
   * the split between ports. subtract (MAX_VALVES_PER_SIDE / 2) from valve
   * num ==> valve num 5 becomes (5 - (8/2)) = 1 ==> first pin on PORTC is
   * actuated. This would change if the experiment moved to a 16 total valve
   * paradigm vs 8 total valves.
   */

  volatile uint8_t *PORT;
  uint8_t valve_number = 0;

  valve_number = side_data->experiment_schedule.at(current_trial);

  switch (side_data->SIDE) {
    // side 1 -> PORTA -> no shift
  case 0:
    PORT = &PORTA;
    break;
  case 1:
    // side 2 -> PORTC -> shift
    PORT = &PORTC;
    valve_number = valve_number - (MAX_VALVES_PER_SIDE / 2);
    break;
  }

  // open the valve on the desired port
  *PORT = (1 << valve_number);
}
