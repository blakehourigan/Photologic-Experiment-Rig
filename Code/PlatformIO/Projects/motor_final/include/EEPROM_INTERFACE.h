// EEPROM_INTERFACE.h
#ifndef EEPROM_INTERFACE_H
#define EEPROM_INTERFACE_H

#include <EEPROM.h>
#include "Arduino.h"

class EEPROM_INTERFACE {
public:
    EEPROM_INTERFACE();
    bool check_EEPROM_initialized();
    void mark_EEPROM_initialized();
    void markEEPROMUninitialized();
    void write_values_to_EEPROM(unsigned long int values[], int start_address, int num_values);
    void read_values_from_EEPROM(unsigned long int values[], int start_address, int num_values, bool print = false);
    void read_single_value_from_EEPROM(unsigned long int &value, int start_address, int index, bool print = false);
    void print_EEPROM_values();
    const int DATA_START_ADDRESS = 1; // Start after the flag
    const int SIDE_TWO_DURATIONS_ADDRESS = DATA_START_ADDRESS + MAX_NUM_VALVES_PER_SIDE * sizeof(long int); // Adjust as necessary



private:
    const int FLAG_ADDRESS_EEPROM = 0;
    const byte EEPROM_INITIALIZED_FLAG = 1;
    const int MAX_NUM_VALVES_PER_SIDE = 8;
};

#endif
