#define INPUT_BIT_SIDE1 PH5
#define INPUT_BIT_SIDE2 PH6
#define OUTPUT_BIT_SIDE1 PB4
#define OUTPUT_BIT_SIDE2 PB5

unsigned long start_time, end_time; // Variables to store start and end time of licks
unsigned long program_start;
unsigned long current_time; 

volatile bool side_1_pin_state, side_2_pin_state;
volatile bool side_1_previous_state = 1; 
volatile bool side_2_previous_state = 1; 
unsigned int side_1_licks = 0; // Variable to store number of licks detected
unsigned int side_2_licks = 0;

String side; 

void setup() {
  Serial.begin(115200); // Start the serial communication
  // Set up Timer 4 for 1 microsecond interval
  pinMode(10, OUTPUT); // Sets pin 10 as an output pin
  pinMode(11, OUTPUT); // Sets pin 11 as an output pin
  cli(); // Disable global interrupts
  TCCR4A = 0; // Set entire TCCR4A register to 0
  TCCR4B = 0; // Set entire TCCR4B register to 0
  TCNT4 = 0; // Initialize counter value to 0
  OCR4A = 15; // Set compare match register for 1us intervals
  TCCR4B |= (1 << WGM42); // Turn on CTC mode
  TCCR4B |= (1 << CS40); // Set prescaler to 1 (no prescaling)
  TIMSK4 |= (1 << OCIE4A); // Enable timer compare interrupt
  sei(); // Enable global interrupts
  program_start = millis();
}

ISR(TIMER4_COMPA_vect) {
  side_1_pin_state = (PINH & (1 << INPUT_BIT_SIDE1));
  side_2_pin_state = (PINH & (1 << INPUT_BIT_SIDE2));
}

void loop() {
  check_serial_command();
  
  detect_licks("One", side_1_pin_state, side_1_previous_state, side_1_licks, OUTPUT_BIT_SIDE1);
  detect_licks("Two", side_2_pin_state, side_2_previous_state, side_2_licks, OUTPUT_BIT_SIDE2);
}

void check_serial_command() {
  if (Serial.available() > 0) 
  {
    String command = Serial.readStringUntil('\n');
    command.trim(); // Remove any leading/trailing whitespace
    if (command == "reset") 
    {
      asm volatile ("jmp 0"); // Jump to the start of the program
    }
    else if (command == "WHO_ARE_YOU") 
    {
      Serial.println("LASER");
    }
  }
}


void detect_licks(String side, volatile bool& current_state, volatile bool& previous_state, unsigned int& licks, byte output_bit) {
    if (current_state == 0 && previous_state == 1) {
        start_time = millis();
        PINB |= (1 << output_bit);
        previous_state = 0;
    } 
    if (current_state == 1 && previous_state == 0) {
        end_time = millis();
        PINB &= ~(1 << output_bit);
        licks++;
        send_lick_details(licks, start_time, end_time, side);
        previous_state = 1;
    }
}

void send_lick_details(unsigned int licks, unsigned long start_time, unsigned long end_time, String side)
 {
    Serial.print("Stimulus ");
    Serial.print(side);
    Serial.print(" Lick:");
    Serial.println(licks);
    Serial.print("Lick time:");
    Serial.println(end_time - start_time);
    current_time = end_time - program_start;
    Serial.print("Stamp:");
    Serial.println(current_time / 1000.0);
    Serial.println();
}
