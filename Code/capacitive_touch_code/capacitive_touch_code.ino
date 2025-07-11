#define PIN_MAX 1023

// ———————— LED pins ————————
const int port_1_led_pins[10] = {2, 3, 4, 5, 6, 7, 8, 9, 10, 11};
const int port_2_led_pins[10] = {22, 23, 24, 25, 26, 27, 28, 29, 30, 31};

// —————— Counters & state ——————
int port_1_val = 0;
int port_2_val = 0;

bool port_1_prev_state = false;
bool port_2_prev_state = false;

bool port_1_state = false;
bool port_2_state = false;




void setup() {
  Serial.begin(9600);
  // LED outputs
  for (int i = 0; i < 10; i++) {
    pinMode(port_1_led_pins[i], OUTPUT);
    pinMode(port_2_led_pins[i], OUTPUT);
  }
  // QT breakout pins (using PORTB bits 0 and 2)
  pinMode(53, INPUT);  // corresponds to PINB0
  pinMode(51, INPUT);  // corresponds to PINB2
  
  DDRG &= ~(1 << 2);
}

void display_binary_port_1(int value) {
  for (int i = 0; i < 10; i++) {
    digitalWrite(port_1_led_pins[i], (value >> i) & 1);
  }
}

void display_binary_port_2(int value) {
  for (int i = 0; i < 10; i++) {
    digitalWrite(port_2_led_pins[i], (value >> i) & 1);
  }
}

void loop() {
  static unsigned long last_poll = 0;
  static unsigned long last_lick_end = 0;

  static unsigned long low_start_time = 0;
  static bool port_1_falling_edge = false;
  static bool port_2_falling_edge = false;

  // utilized for a sample lick. we only move on from a lick once both valve close time AND 
  // lick finish time have been marked.
  bool accept_licks = (PING & (1 << 2)) != 0;
  static bool handling_lick = false;

  // Read current port state as booleans
  if((millis() - last_poll) > 5){
    // update prev state for next loop
    port_1_prev_state = port_1_state;
    port_2_prev_state = port_2_state;

    port_1_state = (PINB & (1 << PINB0)) != 0;
    port_2_state = (PINB & (1 << PINB2)) != 0;

    last_poll = millis();

  }


  if (accept_licks && (!handling_lick)){
    // reject licks if that start before 90 seconds after last lick has ended.
    if(millis() - last_lick_end> 90){
      if (port_1_state && !port_1_prev_state) {
        // only increment once per touch
        handling_lick = true;
      }

      if (port_2_state && !port_2_prev_state) {
        handling_lick = true;
      }
    }
  }else if(handling_lick){
    // ——— Port 1: rising‐edge detection ———
    if (!(port_1_state) && port_1_prev_state) {
      low_start_time = millis();
      port_1_falling_edge = true;

    }
    // ——— Port 2: same thing ———
    else if (!(port_2_state) && port_2_prev_state) {
      low_start_time = millis();
      port_2_falling_edge = true;
    }

    if(port_1_falling_edge && !port_1_state){
      if(millis() - low_start_time > 2){
        if (port_1_val >= PIN_MAX){
          port_1_val = 0;
        }else{                       
          port_1_val++;
          Serial.println(port_1_val);
        }

        handling_lick = false;
        last_lick_end= millis();
        port_1_falling_edge = false;

        display_binary_port_1(port_1_val);

      }

    }
    if(port_2_falling_edge && !port_2_state){
      if(millis() - low_start_time > 2){
        if (port_2_val >= PIN_MAX){
          port_2_val = 0;
        }else{                       
          port_2_val++;
          Serial.println(port_2_val);
        }

        handling_lick = false;
        last_lick_end= millis();
        port_2_falling_edge = false;

        display_binary_port_2(port_2_val);

      }
    }

  }}


