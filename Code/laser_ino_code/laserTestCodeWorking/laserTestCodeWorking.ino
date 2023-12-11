const byte inputBitSide1 = PH5;        // PB4 or pin 10 is the bit that detects a switch to low to increment number of licks       
      byte inputBitSide2 = PH6;
      byte outputBitSide1 = PB4;
      byte outputBitSide2 = PB5;

unsigned long startTime, endTime; // variables to store start and endtime of licks
unsigned long programStart;
unsigned long currentTime; 

volatile bool PinStateSide1,PinStateSide2;
volatile bool previousStateSide1 = 1; 
volatile bool previousStateSide2 = 1; 
int licksSideOne = 0;                    // variable to store number of licks detected
int licksSideTwo = 0;

void setup() {
  Serial.begin(9600);             // Start the serial communication
  // Set up Timer 4 for 1 microsecond interval
  pinMode(10, OUTPUT); // Sets pin 10 as an output pin
  pinMode(11, OUTPUT); // Sets pin 11 as an output pin
  cli();                          // Disable global interrupts
  TCCR4A = 0;                     // Set entire TCCR4A register to 0
  TCCR4B = 0;                     // Set entire TCCR4B register to 0
  TCNT4 = 0;                      // Initialize counter value to 0
  OCR4A = 15;                     // Set compare match register for 1us intervals (16MHz/1us = 16, minus 1 for zero indexing)
  TCCR4B |= (1 << WGM42);         // Turn on CTC mode
  TCCR4B |= (1 << CS40);          // Set prescaler to 1 (no prescaling)
  TIMSK4 |= (1 << OCIE4A);        // Enable timer compare interrupt
  sei();                          // Enable global
  programStart = millis();

}

ISR(TIMER4_COMPA_vect) {
  // Read inputPin using direct port manipulation
  PinStateSide1 = (PINH & (1 << inputBitSide1)) ;    // to know whether or not we have a signal from our photosensor, we AND the value of pinB (0001 0000 if 5V applied), with the value of
                                           // 0001 0000. If photosensor sees light, it will send 5v or a 1 to pin 10, giving us a 1 out of the expression, otherwise we get 0. 
  PinStateSide2 = (PINH & (1 << inputBitSide2)) ; 
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
  
  if (PinStateSide1 == 0 && previousStateSide1 == 1) {
    startTime = millis();
    PINB |= (1 << outputBitSide1);
    previousStateSide1 = 0;
  } 
  if (PinStateSide1 == 1 && previousStateSide1 == 0) {
    endTime = millis();
    PINB &= ~(1 << outputBitSide1);
    licksSideOne++;

    String myString = "Stimulus One Lick:";
    Serial.print(myString + licksSideOne + "\n");
    Serial.print("lick time:");
    Serial.println(endTime - startTime);
    currentTime= endTime - programStart;
    Serial.println("Stamp:" + String(currentTime / 1000.0) );
    Serial.println("\n");
   

    previousStateSide1 = 1;

    
  }

  if (PinStateSide2 == 0 && previousStateSide2 == 1) {
    startTime = millis();
    PINB |= (1 << outputBitSide2);
    previousStateSide2 = 0;
  } 
  if (PinStateSide2 == 1 && previousStateSide2 == 0) {
    endTime = millis();
    PINB &= ~(1 << outputBitSide2);
    licksSideTwo++;

    String myString = "Stimulus Two Lick:";
    Serial.print(myString + licksSideTwo + "\n");
    Serial.print("lick time:");
    Serial.println(endTime - startTime);
    currentTime = endTime - programStart;
    Serial.println("Stamp:" + String(currentTime / 1000.0) );
    Serial.println("\n");
    previousStateSide2 = 1;

    
  }

  
}


