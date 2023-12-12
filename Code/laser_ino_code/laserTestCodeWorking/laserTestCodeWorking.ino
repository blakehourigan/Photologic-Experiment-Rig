#define INPUT_BIT_SIDE1 PH5
#define INPUT_BIT_SIDE2 PH6
#define OUTPUT_BIT_SIDE1 PB4
#define OUTPUT_BIT_SIDE2 PB5

unsigned long startTime, endTime; // Variables to store start and end time of licks
unsigned long programStart;
unsigned long currentTime; 

volatile bool PinStateSide1, PinStateSide2;
volatile bool previousStateSide1 = 1; 
volatile bool previousStateSide2 = 1; 
unsigned int licksSideOne = 0; // Variable to store number of licks detected
unsigned int licksSideTwo = 0;

void setup() {
  Serial.begin(9600); // Start the serial communication
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
  programStart = millis();
}

ISR(TIMER4_COMPA_vect) {
  PinStateSide1 = (PINH & (1 << INPUT_BIT_SIDE1));
  PinStateSide2 = (PINH & (1 << INPUT_BIT_SIDE2));
}

void loop() {
  checkSerialCommand();
  
  detectLick(PinStateSide1, previousStateSide1, licksSideOne, OUTPUT_BIT_SIDE1);
  detectLick(PinStateSide2, previousStateSide2, licksSideTwo, OUTPUT_BIT_SIDE2);
}

void checkSerialCommand() {
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim(); // Remove any leading/trailing whitespace
    if (command == "reset") {
      asm volatile ("jmp 0"); // Jump to the start of the program
    }
  }
}

void detectLick(bool& currentState, bool& previousState, unsigned int& licks, byte outputBit) {
    if (currentState == 0 && previousState == 1) {
        startTime = millis();
        PINB |= (1 << outputBit);
        previousState = 0;
    } 
    if (currentState == 1 && previousState == 0) {
        endTime = millis();
        PINB &= ~(1 << outputBit);
        licks++;
        printLickDetails(licks, startTime, endTime);
        previousState = 1;
    }
}

void printLickDetails(unsigned int licks, unsigned long startTime, unsigned long endTime) {
    Serial.print("Stimulus Lick:");
    Serial.println(licks);
    Serial.print("Lick time:");
    Serial.println(endTime - startTime);
    currentTime = endTime - programStart;
    Serial.print("Stamp:");
    Serial.println(currentTime / 1000.0);
    Serial.println();
}
