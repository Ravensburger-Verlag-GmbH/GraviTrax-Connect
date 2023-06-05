# Gravitrax GPIO Application
This script uses the GPIO pins of a Raspberry Pi as an input in order to send Signals
to Gravitrax Power Stones. For each color there is one PIN configured as an Input as
well as one as an output.
# Dependencies
RPi.GPIO >= 0.7.1  [pypi.org](https://pypi.org/project/RPi.GPIO) 

# Usage
The PINS BCM 13(red),6(green) and 5(blue) are used as inputs. If one of the pins is set to high a signal is send. The PINS BCM 22(red),27(green) and 17(blue) are configured as outputs and are set to high whenever a signal is with the respective color is send or received. 



