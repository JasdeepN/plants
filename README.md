# Plant Controller

# WIP only work on this when im bored. dont @ me.

## Materials
- Raspberry Pi (3/4b)
- 5v Power Supply for Pi
- 5v Power Supply for Pumps
- ADC1115 16bit i2c ADC
- BME680
- CCS811
- ?x ESP32-C6 (depends on how far i go with this) + USC-C Power
- 5v Relay (4 ports)
- 4x 5v Water Pumps
- 4x Soil Moisture Sensors (tested with v1.2)
- some way to connect everything (breadboard, circutboard, wires, etc)
- reservoir (5gal bucket works till plants get bigger)
- 3D printed enclosures (ill upload these to thingverse if i finish it lol)

## Software reqs
- python3
- i2c enabled on pi
- gpio enabled on pi
- mysql(vTBD)

## What it doos
Records environment data every 60 seconds to a mysql database, when soil moisture readings hit threshold triggers relay for associated pump through GPIO.
Currently uses wires to connect i2c devices back to the pi's bus, plan is to have esp32s deployed close to where the sensors are mounted and have them stream data back over MQTT; So signal degredation over long distances wire runs isnt and issue.

## GPIO Pins Used
...TODO

## TODO
- Add visualizations of recorded data (grafana?)
- [Finish ESP32-C6 integration](https://github.com/JasdeepN/esp32-remote.git)
    - figure out how im getting 5v USB-C to where they will be mounted 
- VPD? calculation is easy but without control over exhaust system is hard to tune environment
- Light Control
- Exhaust System Control 
    - Need an ESP32 to handle this (get instructions from pi over MQTT and trigger a relay)
    - 2 relays (intake/exhaust outside)
    - check temp/humidty of air coming in from outside in intake fan
- Nutirent Mixing (dont know about this)
    - Pump to mix in reservoir
    - peristaltic pump to dose out liquid nutirents (kinda like dosing the reef tank)
    - TDS Meter (easy enough, but only gives a total ppm of nutes)
    - pH Meter (already did this once)
    - water level sensor (float style)
- Database Schema needs to be updated with new data as features get completed 
