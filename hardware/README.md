# Hardware Documentation
## Components Used
- Arduino UNO
- MFRC522 RFID Module
- Servo Motor
- Buzzer
- RFID Cards/Tags

## Function
The hardware system reads RFID tags using MFRC522, validates UID, and triggers:
- Servo rotation for access granted
- Buzzer alert for access denied

## Communication
Uses SPI protocol between Arduino and RFID module.

Serial communication sends results to Python application.

# NOTE: The Fritzing diagram shows a connection error due to a possible corrupted file imported during project development.
