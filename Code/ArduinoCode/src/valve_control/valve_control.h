#ifndef VALVE_CONTROL_H
#define VALVE_CONTROL_H

#include "../optical_detection/optical_detection.h"
#include "../reporting/reporting.h"
#include <avr/wdt.h>

void open_valve_testing(volatile uint8_t *PORT, uint8_t valve_number);

void open_valve(SideData *side_data, uint16_t current_trial);

bool close_valve(valveTimeDetails valve_time, SideData *side_data,
                 uint16_t current_trial);

#endif
