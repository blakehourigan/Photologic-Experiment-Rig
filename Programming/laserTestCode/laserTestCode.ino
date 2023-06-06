const byte inputPort = PINB;
const byte inputBit = PB4;
byte ledPort = PINB;
byte ledBit = PB7;

volatile bool pinState;
int licks = 0;                    // variable to store number of licks detected

void setup() {
  Serial.begin(9600);             // Start the serial communication
  // Set up Timer 4 for 1 microsecond interval
  cli(); // Disable global interrupts
  TCCR4A = 0; // Set entire TCCR4A register to 0
  TCCR4B = 0; // Set entire TCCR4B register to 0
  TCNT4 = 0; // Initialize counter value to 0
  OCR4A = 15; // Set compare match register for 1us intervals (16MHz/1us = 16, minus 1 for zero indexing)
  TCCR4B |= (1 << WGM42); // Turn on CTC mode
  TCCR4B |= (1 << CS40); // Set prescaler to 1 (no prescaling)
  TIMSK4 |= (1 << OCIE4A); // Enable timer compare interrupt
  sei(); // Enable global interrupts


}

ISR(TIMER4_COMPA_vect) {
  // Read inputPin using direct port manipulation
  pinState = (inputPort & (1 << inputBit)) >> inputBit;
}

void loop() {
  unsigned long currentMillis = millis(); // Get the current time

  // Check if it's time to read the pin state
  //if (currentMillis - previousMillis >= interval) {
    // Save the current time as the last time the pin state was checked



    // Check if the pin is LOW
    if (pinState == 0) {
      ledPort = (1 << PB7);
      licks++;                             // increment number of licks
    } 
    if (pinState == 1) {
      ledPort = ~(1 << PB7);

    }
  String myString = "Current Licks: " + String(licks);
  Serial.print("\n" + myString);
  }

//}
