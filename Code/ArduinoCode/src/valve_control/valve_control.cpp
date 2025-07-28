#include "valve_control.h"
#include "../exp_init/exp_init.h"
#include "Arduino.h"

// the print statements in this file are commented out for performance sake. Can
// be un-commented for debugging purposes.

bool close_valve(valveTimeDetails valve_time, SideData *side_data,
                 uint16_t current_trial) {

  uint8_t valve_num = side_data->experiment_schedule.schedule[current_trial];

  unsigned long allotted_duration =
      side_data->valve_durations.durations[valve_num];

  unsigned long current_time = micros();

  if ((current_time - valve_time.valve_open_time) > allotted_duration) {
    // reset all valve pins to zero to turn them off
    close_all();
    return true;
  }
  return false;
}

void close_all() {

  PORTA = 0;
  PORTC = 0;
}

void open_single_valve(volatile uint8_t *PORT, uint8_t valve_number) {
  // open the valve on the desired port
  *PORT = (1 << valve_number);
}

void close_single_valve(volatile uint8_t *PORT, uint8_t valve_number) {
  // close the valve on the desired port at the valve number
  *PORT &= ~(1 << valve_number);
}

void control_specific_valves() {
  // wait for the states of all 8 CURRENT valves to arrive
  while (Serial.available() < CURRENT_TOTAL_VALVES) {
  }

  uint8_t req_valve_states[CURRENT_TOTAL_VALVES];

  for (int i = 0; i < CURRENT_TOTAL_VALVES; i++) {
    req_valve_states[i] = Serial.read();
  }

  //  perform requested actions for side one (PORTA pins)
  for (int i = 0; i < CURRENT_VALVES_PER_SIDE; i++) {
    if (req_valve_states[i] == 1) {
      // set signal high for this pin
      PORTA |= (1 << i);
    } else {
      // set signal low for this pin
      PORTA &= ~(1 << i);
    }
    //  repeat for side two offset by valves per side (PORTC pins)
    if (req_valve_states[i + CURRENT_VALVES_PER_SIDE] == 1) {
      // set signal high for this pin
      PORTC |= (1 << i);
    } else {
      // set signal low for this pin
      PORTC &= ~(1 << i);
    }
  }
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

  valve_number = side_data->experiment_schedule.schedule[current_trial];

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
  Serial.println("valve opened");

  // open the valve on the desired port
  *PORT = (1 << valve_number);
}
