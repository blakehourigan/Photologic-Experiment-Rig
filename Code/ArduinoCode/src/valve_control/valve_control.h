#ifndef VALVE_CONTROL_H
#define VALVE_CONTROL_H

#include "../optical_detection/optical_detection.h"
#include "../reporting/reporting.h"
#include <avr/wdt.h>

void open_single_valve(volatile uint8_t *PORT, uint8_t valve_number);

// method used for opening specific valves for arbitrary amounts of time
void control_specific_valves();

void open_valve(SideData *side_data, uint16_t current_trial);

bool close_valve(valveTimeDetails valve_time, SideData *side_data,
                 uint16_t current_trial);

void close_single_valve(volatile uint8_t *PORT, uint8_t valve_number);
void close_all();
#endif
