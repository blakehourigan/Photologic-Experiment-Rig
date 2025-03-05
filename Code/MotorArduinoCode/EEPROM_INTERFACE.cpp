// EEPROM_INTERFACE.cpp
#include "EEPROM_INTERFACE.h"

EEPROM_INTERFACE::EEPROM_INTERFACE() {
  // Constructor
}

bool EEPROM_INTERFACE::check_EEPROM_initialized() {
  byte flag;
  EEPROM.get(FLAG_ADDRESS_EEPROM, flag);
  return (flag == EEPROM_INITIALIZED_FLAG);
}

void EEPROM_INTERFACE::mark_EEPROM_initialized() {
  EEPROM.update(FLAG_ADDRESS_EEPROM, EEPROM_INITIALIZED_FLAG);
}

void EEPROM_INTERFACE::markEEPROMUninitialized() {
  EEPROM.update(FLAG_ADDRESS_EEPROM, 0);
}

void EEPROM_INTERFACE::write_values_to_EEPROM(unsigned long int values[],
                                              int start_address,
                                              int num_values) {
  for (int i = 0; i < num_values; i++) {
    EEPROM.put(start_address + i * sizeof(long int), values[i]);
  }
}

void EEPROM_INTERFACE::read_values_from_EEPROM(unsigned long int values[],
                                               int start_address,
                                               int num_values, bool print) {
  for (int i = 0; i < num_values; i++) {
    EEPROM.get(start_address + i * sizeof(long int), values[i]);
    if (print) {
      Serial.println(values[i]);
    }
  }
}

void EEPROM_INTERFACE::read_single_value_from_EEPROM(unsigned long int &value,
                                                     int start_address,
                                                     int index, bool print) {
  int address = start_address + index * sizeof(unsigned long int);
  EEPROM.get(address, value);
  if (print) {
    Serial.println(value);
  }
}

void EEPROM_INTERFACE::print_EEPROM_values() {
  unsigned long int value;
  for (int side = 0; side < 2; side++) {
    Serial.print("Side ");
    Serial.print(side + 1);
    Serial.println(" Values:");
    for (int j = 0; j < 8; j++) {
      int addressOffset = (side * 8 + j) * sizeof(unsigned long int);
      EEPROM.get(DATA_START_ADDRESS + addressOffset, value);
      Serial.println(value);
    }
  }
}
