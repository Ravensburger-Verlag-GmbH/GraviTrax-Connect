"""Repeat signals using the Notification callback 
When sending signals with a stonetype different than gv.STONE_BRIDGE this signal
is received again as a Notification. This script uses this to repeat received signal
until the bridge is disconnected or the program closed.
"""

import asyncio

from gravitraxconnect import gravitrax_bridge as gb
from gravitraxconnect import gravitrax_constants


finished = asyncio.Event()


def disconnect_callback(bridge: gb.Bridge, **kwargs):
    """Callback for disconnects"""
    finished.set()


async def notification_callback(bridge: gb.Bridge, **signal):
    """Repeat any incoming Signal after 200ms"""
    try:
        if signal.get("Header") == gravitrax_constants.MSG_DEFAULT_HEADER:
            status = signal.get("Status")
            color = signal.get("Color")
            stone = signal.get("Stone")
            await asyncio.sleep(0.2)
            gb.log_print(f"Sending Status {status}, Color {color}, Stone {stone}")
            await bridge.send_signal(status, color, stone=stone, resends=12)
    except asyncio.CancelledError:
        finished.set()
        return


async def main():
    """Connect to the bridge and enable the Notifications"""
    bridge = gb.Bridge()
    try:
        gb.logger.disabled = False
        gb.log_set_level("INFO")
        gb.log_print("Searching for Bridge")
        if await bridge.connect(dc_callback=disconnect_callback):
            await bridge.notification_enable(notification_callback)
            gb.log_print("Received Signals are repeated", bridge=bridge)
            await finished.wait()
    except asyncio.CancelledError:
        return


if __name__ == "__main__":
    asyncio.run(main())
    gb.log_print("Program finished.")
