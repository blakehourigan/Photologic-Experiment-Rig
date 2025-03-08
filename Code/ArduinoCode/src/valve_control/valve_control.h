#ifndef VALVE_CONTROL_H
#define VALVE_CONTROL_H

#include "../optical_detection/optical_detection.h"
#include "../time_details/time_details.h"
#include <avr/wdt.h>

void open_valve(SideData *side_data, uint16_t current_trial);

bool close_valve(lickTimeDetails lick_time, SideData *side_data,
                 uint16_t current_trial);

#endif
