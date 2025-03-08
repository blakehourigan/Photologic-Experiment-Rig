#ifndef EXP_INIT_H

#define EXP_INIT_H

#include <Vector.h>

// maximum # of valves per side
// so that we know how many durations we need
const int MAX_VALVES_PER_SIDE = 8;

// max sched size of 320 elements (trials)
const uint16_t MAX_SCHEDULE_SIZE = 320;
const uint16_t MAX_DURATION_SIZE = 320;

struct ExperimentVariables {
  uint8_t num_stimuli;
  uint8_t num_trials;
};

struct ScheduleVectors {
  Vector<uint8_t> side_one_sched_vec;
  Vector<uint8_t> side_two_sched_vec;
  bool schedules_recieved = false;
};

struct ValveDurations {
  Vector<unsigned long> side_one_dur_vec;
  Vector<unsigned long> side_two_dur_vec;
  bool durations_recieved = false;
};

void receive_exp_variables();

ScheduleVectors receive_schedules();

ValveDurations receive_durations();

void schedule_verification(ScheduleVectors schedules);

void durations_verification(ValveDurations durations);

#endif // EXP_INIT_H!
