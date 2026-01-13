# dexcom-ledmatrix
LEDMatrix display for dexcom

Parts:
16x32 LED Matrix
Adafruit Matrix Portal M4

Instructions:
Follow setup guide here: https://learn.adafruit.com/adafruit-matrixportal-m4/overview
Once the device is connected to your computer, copy the contents of code.py and settings.toml in this repository to your Matrix Portal M4 device. Modify settings.toml to match your WiFi SSID & password, and your Dexcom username and password. Modify the region if not in the US, set your high and low thresholds, and the interval it should switch between the latest glucose value with arrow, and the graph of the last 32 values.
