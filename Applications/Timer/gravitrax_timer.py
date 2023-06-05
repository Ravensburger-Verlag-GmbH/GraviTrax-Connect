"""Gravitrax Example Script: 
Using a Thread to receive Keyboard inputs while using the Gravitrax Library . 
- Send Signal with Keyboard inputs
- React to Notifications in different ways depending on the stonetype and color
"""

import asyncio
import time

from pynput.keyboard import Listener, Key
from gravitraxconnect import gravitrax_bridge as gb
from gravitraxconnect import gravitrax_constants as gv


# pylint: disable=global-statement
# pylint: disable=global-variable-not-assigned
# pylint: disable=invalid-name

b = gb.Bridge()
loop = None
listener = None

START_COLOR = gv.COLOR_BLUE
FIN_COLOR = gv.COLOR_GREEN

start_times = []
disconnected = False
finished = None


def disconnect_callback(bridge: gb.Bridge, **kwargs):
    """Callback for disconnects"""
    if kwargs.get("user_disconnected"):
        finished.set()


async def notification_callback(bridge: gb.Bridge, **signal):
    """callback for incomming Signals"""
    global FIN_COLOR, START_COLOR, start_times
    if signal.get("Header"):  # Check if Notification was a signal
        status = signal.get("Status")
        stone = signal.get("Stone")
        color = signal.get("Color")
        if color == START_COLOR or status == gv.STATUS_STARTER_PRESS:
            start_times.append(time.time())
        if stone == gv.STONE_FINISH and color == FIN_COLOR:
            if start_times:
                gb.log_print(
                    f"Time between Start and Finish {time.time()-start_times.pop(0)}"
                )


def on_press(key):
    """Evaluation of Keypresses"""
    global b, START_COLOR, disconnected
    if key == Key.f1:
        asyncio.run_coroutine_threadsafe(
            b.send_signal(gv.STATUS_STARTER, START_COLOR, stone=gv.STONE_REMOTE), loop
        )
    if key == Key.esc:
        gb.log_print(f"Stop Signal received: Disconnecting Bridge", bridge=b)
        asyncio.run_coroutine_threadsafe(b.disconnect(), loop)
        listener.stop()


async def main():
    """Connect to the Bridge and start the keyboard input listener"""
    global finished, loop, listener
    loop = asyncio.get_running_loop()
    try:
        finished = asyncio.Event()
    except TypeError:
        gb.log_print("Please update to python 3.10 or newer to use this program")
        return
    listener = Listener(on_press=on_press)
    gb.logger.disabled = False
    gb.log_print(f"Searching for Bridge")
    if await b.connect(try_reconnect=True, dc_callback=disconnect_callback):
        gb.log_print(await b.request_battery_string(), bridge=b)
        await b.notification_enable(notification_callback)
        listener.start()
    else:
        gb.log_print(f"Could find Bridge to connect to")
    await finished.wait()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        gb.log_print("Program finished")
