#ifndef OPTICAL_DET_H

#define OPTICAL_DET_H

#include <Vector.h>
#include <cstdint>

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

// Variables to store start and end time of licks
extern unsigned long lick_start_time;
extern unsigned long lick_end_time;
extern unsigned long last_debounce_time;

extern unsigned long last_debounce_time;

struct SideData {
  uint8_t SIDE;
  uint16_t &current_trial;
  bool current_input_state;
  bool previous_input_state;
  Vector<unsigned long> &valve_durations;
  Vector<uint8_t> &experiment_schedule;
};

void update_leds(bool side_1_pin_state, bool side_two_pin_state);

void signal_side_and_port(uint8_t side);

void detect_licks(SideData side_data);

void send_lick_details(uint8_t side, unsigned long lick_time);

#endif // !OPTICAL_DET_H
