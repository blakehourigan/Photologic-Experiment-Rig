#ifndef TEST_VALVESH
#define TEST_VALVESH

#include "../exp_init/exp_init.h"
#include <stdint.h>

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
