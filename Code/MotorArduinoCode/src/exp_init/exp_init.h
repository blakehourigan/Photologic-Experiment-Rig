#ifndef EXP_INIT_H

#define EXP_INIT_H

#include <Vector.h>

// maximum # of valves per side
// so that we know how many durations we need
const int VALVES_PER_SIDE = 8;

// max sched size of 320 elements (trials)
const int MAX_SCHEDULE_SIZE = 320;
const int MAX_DURATION_SIZE = 320;

// experiment related variables
extern uint8_t num_stimuli;
extern uint8_t num_trials;

// each valve per side has one duration
extern unsigned long side_one_durations[VALVES_PER_SIDE];
extern unsigned long side_two_durations[VALVES_PER_SIDE];

// create vectors to hold this data to make it really easy to
// add to these arrays
extern Vector<unsigned long> side_one_dur_vec;
extern Vector<unsigned long> side_two_dur_vec;

// each schedule will have max sched size of 320 uint8_t
// will be able to contain sched of up to 16 valves with 40 trial blocks
// or 320 total trials (16/2 * 40 = 320)
extern uint8_t side_one_schedule[MAX_SCHEDULE_SIZE];
extern uint8_t side_two_schedule[MAX_SCHEDULE_SIZE];

extern Vector<uint8_t> side_one_sched_vec;
extern Vector<uint8_t> side_two_sched_vec;

void receive_exp_variables();

void receive_schedules();

void receive_durations();

void schedule_verification();

#endif // EXP_INIT_H!
