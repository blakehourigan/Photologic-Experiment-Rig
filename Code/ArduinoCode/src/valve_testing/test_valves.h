#ifndef TEST_VALVESH
#define TEST_VALVESH

#include "./../exp_init/exp_init.h"

struct TestParams {
  uint8_t num_valves_side_one;
  uint8_t num_valves_side_two;

  uint16_t max_test_actuations;

  Vector<uint8_t> side_one_sched;
  Vector<uint8_t> side_two_sched;
};

void run_valve_test(DurationsArray side_one_dur_vec,
                    DurationsArray side_two_dur_vec);

TestParams receive_test_params();
TestParams receive_test_schedules();

#endif // TEST_VALVESH
