const byte inputBit0 = PH5;        // PB4 or pin 10 is the bit that detects a switch to low to increment number of licks       
      byte inputBit1 = PH6;

unsigned long startTime, endTime; // variables to store start and endtime of licks
unsigned long programStart;
unsigned long currentTime; 

volatile bool pinState0,pinState1;
volatile bool previousState0 = 1; 
volatile bool previousState1 = 1; 
int licksLeft = 0;                    // variable to store number of licks detected
int licksRight = 0;

void setup() {
  Serial.begin(9600);             // Start the serial communication
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
  programStart = millis();

}

ISR(TIMER4_COMPA_vect) {
  // Read inputPin using direct port manipulation
  pinState0 = (PINH & (1 << inputBit0)) ;    // to know whether or not we have a signal from our photosensor, we AND the value of pinB (0001 0000 if 5V applied), with the value of
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
    previousState0 = 0;
  } 
  if (pinState0 == 1 && previousState0 == 0) {
    endTime = millis();

    licksLeft++;

    String myString = "Left Lick:";
    Serial.print(myString + licksLeft + "\n");
    Serial.print("lick time:");
    Serial.println(endTime - startTime);
    currentTime= endTime - programStart;
    Serial.println(currentTime / 1000.0 );
    Serial.println("\n");
   

    previousState0 = 1;

    
  }

  if (pinState1 == 0 && previousState1 == 1) {
    startTime = millis();

    previousState1 = 0;
  } 
  if (pinState1 == 1 && previousState1 == 0) {
    endTime = millis();
    licksRight++;

    String myString = "Right Lick:";
    Serial.print(myString + licksRight + "\n");
    Serial.print("lick time:");
    Serial.println(endTime - startTime);
    currentTime= endTime - programStart;
    Serial.println(currentTime / 1000.0 );
    Serial.println("\n");
    previousState1 = 1;

    
  }

  
}


