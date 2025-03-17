#ifndef REPORTING_H

#define REPORTING_H

#include <Arduino.h>
#include <stdint.h>

// amount of microseconds that a valve duration cannot exceed. If it is
// exceeded, the lick will be thrown out.
const uint32_t MAXIMUM_SAMPLE_VALVE_DURATION = 100000;

struct lickTimeDetails {
  unsigned long lick_begin_time;
  unsigned long lick_end_time;
  unsigned long lick_duration;

  unsigned long onset_rel_to_start;
  unsigned long onset_rel_to_trial;
};

struct valveTimeDetails {
  unsigned long valve_open_time;
  unsigned long valve_close_time;
  unsigned long valve_duration;
};

struct doorMotorTimeDetails {
  unsigned long movement_start;
  unsigned long movement_end;
  unsigned long movement_duration;

  unsigned long end_rel_to_start;
  unsigned long end_rel_to_trial;

  char *movement_type;
};

// amount of time in ms from break break to beam restoration that a lick
// must occupy to be considered a lick
const uint8_t LICK_THRESHOLD = 10;

void report_motor_movement(String previous_command,
                           doorMotorTimeDetails motor_time,
                           unsigned long program_start_time,
                           unsigned long trial_start_time);

void report_ttc_lick(uint8_t side, lickTimeDetails lick_time,
                     unsigned long program_start_time,
                     unsigned long trial_start);

void report_sample_lick(uint8_t side, lickTimeDetails lick_time,
                        valveTimeDetails valve_time,
                        unsigned long program_start_time,
                        unsigned long trial_start_time);
#endif // !REPORTING_H
