const byte inputBit = PB4;        // PB4 or pin 10 is the bit that detects a switch to low to increment number of licks       
      byte ledBit   = PB7;        
int        intPort  = 26;
unsigned long startTime, endTime; // variables to store start and endtime of licks

volatile bool pinState;
volatile bool previousState = 1; 
int licks = 0;                    // variable to store number of licks detected

void setup() {
  Serial.begin(9600);             // Start the serial communication
  pinMode(intPort, OUTPUT);
  DDRB |= (1 << DDB7);            // Set pin 7 in the Port B register (pin 13) as output, we want to output the value of this pin to the LED.
  PORTB |= (0 << ledBit);         // 

  // Set up Timer 4 for 1 microsecond interval
  cli();                          // Disable global interrupts
  TCCR4A = 0;                     // Set entire TCCR4A register to 0
  TCCR4B = 0;                     // Set entire TCCR4B register to 0
  TCNT4 = 0;                      // Initialize counter value to 0
  OCR4A = 15;                     // Set compare match register for 1us intervals (16MHz/1us = 16, minus 1 for zero indexing)
  TCCR4B |= (1 << WGM42);         // Turn on CTC mode
  TCCR4B |= (1 << CS40);          // Set prescaler to 1 (no prescaling)
  TIMSK4 |= (1 << OCIE4A);        // Enable timer compare interrupt
  sei();                          // Enable global


}

ISR(TIMER4_COMPA_vect) {
  // Read inputPin using direct port manipulation
  pinState = (PINB & (1 << inputBit)) ;    // to know whether or not we have a signal from our photosensor, we AND the value of pinB (0001 0000 if 5V applied), with the value of
                                           // 0001 0000. If photosensor sees light, it will send 5v or a 1 to pin 10, giving us a 1 out of the expression, otherwise we get 0. 
}

void loop() {
  if (pinState == 0 && previousState == 1) {
    startTime = millis();
    PORTB |= (1 << ledBit);
    previousState = 0;
  } 
  if (pinState == 1 && previousState == 0) {
    endTime = millis();
    PORTB &= ~(1 << ledBit);
    licks++;

    String myString = "Current Licks: " + String(licks);
    Serial.print("\nlick time:");
    Serial.println(endTime - startTime);
    Serial.print("\n" + myString);

    previousState = 1;
  }
}


