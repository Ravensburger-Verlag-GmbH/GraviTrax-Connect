"""Gravitrax Example Script: 
This script uses the GPIO Pins of a Raspberry Pi. For every Color(R,G,B)
there is a Input as well as an output pin.  
If a input pin is set to high a signal with the corresponding color
is send. The output pins are set to the last send or received signal.
"""

import asyncio
import sys

from gravitraxconnect import gravitrax_bridge as gb
from gravitraxconnect import gravitrax_constants as gv

# pylint: disable=global-statement
# pylint: disable=global-variable-not-assigned
# pylint: disable=invalid-name

try:
    import RPi.GPIO as GPIO
except ImportError:
    sys.exit("Program finished: Module RPi.GPIO not found")

b = gb.Bridge()
loop = None
name = gv.BRIDGE_NAME
notif_counter = 0


# Output Pins
pin_out_red = 22
pin_out_green = 27
pin_out_blue = 17

# Input Pins
pin_in_red = 13
pin_in_green = 6
pin_in_blue = 5


def disconnect_callback(bridge: gb.Bridge, **kwargs):
    """Callback for disconnects"""
    gb.log_print("Bridge was disconnected", bridge=bridge)


def setOutput(color):
    """Sets one of the 3 outputs to high the others to low.

    Args:
        - color: int value for red(1), green(2) or blue(3)
    """
    for i, channel in enumerate([pin_out_red, pin_out_green, pin_out_blue]):
        if i + 1 == color:
            GPIO.output(channel, True)
        else:
            GPIO.output(channel, False)


def gpio_callback(channel):
    """Executed when one of the input pins is connected to ground.
    Args:
        - channel: Number of the detected pin
    """
    global loop
    try:
        color = [pin_in_red, pin_in_green, pin_in_blue].index(channel) + 1
        setOutput(color)
    except ValueError:
        return

    asyncio.run_coroutine_threadsafe(
        b.send_signal(gv.STATUS_ALL, color, stone=gv.STONE_BRIDGE), loop
    )


async def notification_callback(bridge: gb.Bridge, **signal):
    """Callback function for received Notifications

    When a signal is received the output is set to the color
    of the received signal.

    """
    global notif_counter

    def lookup(value, table):
        try:
            return table[value]
        except (IndexError, KeyError):
            return value

    notif_counter += 1
    color_int = signal.get("Color")

    try:
        setOutput([gv.COLOR_RED, gv.COLOR_GREEN, gv.COLOR_BLUE].index(color_int) + 1)
    except ValueError:
        return

    stone = lookup(signal.get("Stone"), gv.DICT_VAL_STONE)
    color = lookup(color_int, gv.LOOKUP_COLOR)
    gb.log_print(
        f"{color:5} detected ",
        f"from Stone {stone:10}",
        f"( {notif_counter} Notifications received )",
        bridge=bridge,
    )

async def main():
    """Enable GPIo Pins and attach """
    global loop
    loop = asyncio.get_running_loop()
    gb.logger.disabled = False

    GPIO.setmode(GPIO.BCM)

    # Output Pins
    GPIO.setup(pin_out_red, GPIO.OUT)
    GPIO.setup(pin_out_green, GPIO.OUT)
    GPIO.setup(pin_out_blue, GPIO.OUT)

    # Input Pins
    GPIO.setup(pin_in_red, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(pin_in_green, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(pin_in_blue, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    # Set Callback for input Pins
    GPIO.add_event_detect(
        pin_in_red, GPIO.FALLING, callback=gpio_callback, bouncetime=150
    )
    GPIO.add_event_detect(
        pin_in_green, GPIO.FALLING, callback=gpio_callback, bouncetime=150
    )
    GPIO.add_event_detect(
        pin_in_blue, GPIO.FALLING, callback=gpio_callback, bouncetime=150
    )

    gb.log_print(f"Looking for connection: {name}")
    try:
        if await b.connect(name, dc_callback=disconnect_callback, try_reconnect=True):
            await b.notification_enable(notification_callback)
        else:
            gb.log_print(f"Could not connect to Device with Name: {name}")
            return

        await asyncio.Event().wait()
    except asyncio.CancelledError:
        return


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    finally:
        GPIO.cleanup()

    gb.log_print("Program finished")
    