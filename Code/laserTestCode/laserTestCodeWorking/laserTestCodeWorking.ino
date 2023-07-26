const byte inputBit0 = PB4;        // PB4 or pin 10 is the bit that detects a switch to low to increment number of licks       
      byte ledBit0   = PB5;
      byte inputBit1 = PH5;
      byte ledBit1   = PH6;    

unsigned long startTime, endTime; // variables to store start and endtime of licks

volatile bool pinState0,pinState1;
volatile bool previousState0 = 1; 
volatile bool previousState1 = 1; 
int licksLeft = 0;                    // variable to store number of licks detected
int licksRight = 0;

void setup() {
  Serial.begin(9600);             // Start the serial communication
  DDRB |= (1 << DDB5);            // Set pin 7 in the Port B register (pin 13) as output, we want to output the value of this pin to the LED.
  PORTB |= (0 << ledBit0);         // 

  DDRH |= (1 << DDH6);            // Set pin 7 in the Port H register (pin 13) as output, we want to output the value of this pin to the LED.
  PORTH |= (0 << ledBit1);         // 

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
  pinState0 = (PINB & (1 << inputBit0)) ;    // to know whether or not we have a signal from our photosensor, we AND the value of pinB (0001 0000 if 5V applied), with the value of
                                           // 0001 0000. If photosensor sees light, it will send 5v or a 1 to pin 10, giving us a 1 out of the expression, otherwise we get 0. 
  pinState1 = (PINH & (1 << inputBit1)) ; 
}

void loop() 
{
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim();  // Remove any leading/trailing whitespace
 if (command == "reset") {
      asm volatile ("jmp 0");  // Jump to the start of the program
    }
  }
  
  if (pinState0 == 0 && previousState0 == 1) {
    startTime = millis();
    PORTB |= (1 << ledBit0);
    previousState0 = 0;
  } 
  if (pinState0 == 1 && previousState0 == 0) {
    endTime = millis();
    PORTB &= ~(1 << ledBit0);
    licksLeft++;

    String myString = "Left Lick\n";
    Serial.print("\nlick time:");
    Serial.println(endTime - startTime);
    Serial.print("\n" + myString);

    previousState0 = 1;

    
  }

  if (pinState1 == 0 && previousState1 == 1) {
    startTime = millis();
    PORTH |= (1 << ledBit1);
    previousState1 = 0;
  } 
  if (pinState1 == 1 && previousState1 == 0) {
    endTime = millis();
    PORTH &= ~(1 << ledBit1);
    licksRight++;

    String myString = "Right Lick";
    Serial.print("\nlick time:");
    Serial.println(endTime - startTime);
    Serial.print("\n" + myString);

    previousState1 = 1;

    
  }

  
}


