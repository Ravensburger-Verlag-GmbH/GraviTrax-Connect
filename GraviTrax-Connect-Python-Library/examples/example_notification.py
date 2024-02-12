"""Gravitrax Example Script: Handling Notifications
This Script connects to a Bridge and displays inforation about 
received Notifications as well as the count of all notifications
received at runtime. All protocol fields of the received signal 
can be accessed as Keyword Arguments. The program closes after
10 Notifications are received.
"""

import asyncio

from gravitraxconnect import gravitrax_bridge as gb
from gravitraxconnect import gravitrax_constants

counter = 0
finished = asyncio.Event()
disconnected = asyncio.Event()


def disconnect_callback(bridge: gb.Bridge, **kwargs):
    """Callback function for disconnects"""
    disconnected.set()


async def notification_callback(bridge: gb.Bridge, **signal):
    """Callback function for incoming Signals

    This callback is executed when a Notification i.e a Signal is received.
    After 10 Signals the finished event is set which closes the program.
    """
    global counter

    def lookup(key, table, prefix):
        try:
            return table[key]
        except (IndexError, KeyError):
            if prefix:
                return f"{prefix}{key}"
            return key

    counter += 1
    # Received Data doesn't fits the communication protocol
    if not (data := signal.get("Header")):
        gb.log_print(f"Received Notification: {data}", bridge=bridge)
    # Received Data does fits the communication protocol
    else:
        # Access relevant Signal information
        # Other kwargs that can be accessed are:
        # Header, Reserved, id and Checksum
        stone = lookup(signal.get("Stone"), gravitrax_constants.DICT_VAL_STONE, None)
        color = lookup(signal.get("Color"), gravitrax_constants.LOOKUP_COLOR, None)
        status = lookup(
            signal.get("Status"), gravitrax_constants.DICT_VAL_STATUS, "Color"
        )

        # Printing information about the received signal
        gb.log_print(
            f"{color} detected from Stone {stone} with Status {status}",
            f"( {counter} Notifications received )",
            bridge=bridge,
        )
    if counter >= 10:
        finished.set()


async def main():
    """Recieve Notifications from the Bridge"""
    bridge = gb.Bridge()
    gb.logger.disabled = False
    gb.log_set_level("INFO")
    gb.log_print("Searching for Bridge")
    try:
        if await bridge.connect(dc_callback=disconnect_callback):
            await bridge.notification_enable(notification_callback)
            await finished.wait()
            await bridge.notification_disable()
            gb.log_print(f"Received {counter} Notifications", bridge=bridge)
            await bridge.disconnect()
            await disconnected.wait()
    except asyncio.CancelledError:
        return


if __name__ == "__main__":
    asyncio.run(main())
    gb.log_print("Program finished")
