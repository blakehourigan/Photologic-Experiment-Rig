#ifndef TEST_VALVESH
#define TEST_VALVESH

#include "../exp_init/exp_init.h"
#include <stdint.h>

// Valves need time to 'rest' before activated again to recognise they need to turn off before flipping back on. 70ms 
const int VALVE_TIMEOUT= 70;

// all valves have exactly the same 'prime' opening time of 40 ms
const int PRIME_OPEN_TIME = 40;

struct TestParams {
    uint8_t num_valves_side_one;
    uint8_t num_valves_side_two;

    uint16_t max_test_actuations;

    ExpScheduleArray side_one_sched;
    ExpScheduleArray side_two_sched;
};

void prime_valves();

void run_valve_test(DurationsArray side_one_dur, DurationsArray side_two_dur);

TestParams receive_test_params();
TestParams receive_test_schedules();

#endif // TEST_VALVESH
