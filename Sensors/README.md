# Sensors
The part of the project containing the required hardware schematics and code.

## Materials
Materials used:
- NodeMcu Lua ESP8266 WIFI Board
- DHT22 Digital Humidity & Temperature Sensor
- Breadboard
- Jumpers

## Setup
1. Install XAMPP
2. Install Arduino IDE
3. Download required libraries for the project (DHT-sensor-library, Adafruit Unified Sensor), the required boards (ESP8266) and setup the IDE for the ESP8266
4. Place the php files inside the htdocs folder in the xampp folder
5. Configure your php code to fit your database
6. Configure your ESP8266 code to fit the wifi, path of the php files
7. Setup your breadboard according to the schematic (Coming soon)
8. Upload the ESP8266 code to the microcontroller (Make sure the cable connecting D0 and RST is not connected during the programming phase of your device)
9. Power up your ESP8266 and use
