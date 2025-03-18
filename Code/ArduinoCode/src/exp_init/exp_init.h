#ifndef EXP_INIT_H

#define EXP_INIT_H

#include <Arduino.h>
#include <stdint.h>

// maximum # of valves per side
// so that we know how many durations we need

const int MAX_VALVES_PER_SIDE = 8;
const int CURRENT_TOTAL_VALVES = 8;
const int CURRENT_VALVES_PER_SIDE = CURRENT_TOTAL_VALVES / 2;

// max sched size of 320 elements (trials)
const uint16_t MAX_SCHEDULE_SIZE = 320;
const uint16_t MAX_DURATION_SIZE = 320;

struct ExperimentVariables {
  uint8_t num_stimuli;
  uint8_t num_trials;
};

struct ExpScheduleArray {
  uint8_t schedule[MAX_SCHEDULE_SIZE];
  uint16_t len = 0;

  void append(uint8_t val) {
    if (this->len < MAX_SCHEDULE_SIZE) {
      this->schedule[this->len] = val;
    }
    this->len++;
  };
};

struct ValveSchedules {
  ExpScheduleArray side_one;
  ExpScheduleArray side_two;
  bool schedules_recieved = false;
};

struct DurationsArray {
  unsigned long durations[MAX_VALVES_PER_SIDE];
  uint8_t len = 0;

  // define struct associated method append, which
  // will add the argument to the array as long as we do not
  // exceed the max allowed len
  void append(unsigned long val) {
    if (this->len < MAX_VALVES_PER_SIDE) {
      this->durations[this->len] = val;
    }
    this->len++;
  };
};

struct ValveDurations {
  DurationsArray side_one;
  DurationsArray side_two;
  bool durations_recieved = false;
};

void receive_exp_variables();

ValveSchedules receive_schedules();

ValveDurations receive_durations();

void schedule_verification(ValveSchedules &schedules);

void durations_verification(ValveDurations &durations);

#endif // EXP_INIT_H!
