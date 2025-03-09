#ifndef OPTICAL_DET_H

#define OPTICAL_DET_H

#include <Vector.h>

// digital 31, from photologic
#define OPTICAL_DETECTOR_BIT_SIDE1 PL0
// digital 33, to LED for side 1
#define LED_BIT_SIDE1 PL1

// side two definitions
// digital 23, from photologic
#define OPTICAL_DETECTOR_BIT_SIDE2 PL2
// digital 25, to led for side 2
#define LED_BIT_SIDE2 PL3

// Debounce time in milliseconds
const uint8_t DEBOUNCE_TIME = 50;

struct SideData {
  uint8_t SIDE;
  bool &current_input_state;
  bool &previous_input_state;
  Vector<unsigned long> &valve_durations;
  Vector<uint8_t> &experiment_schedule;
};

void update_leds(bool side_1_pin_state, bool side_two_pin_state);

bool lick_started(SideData side_data);
bool lick_ended(SideData *side_data);

#endif // !OPTICAL_DET_H
