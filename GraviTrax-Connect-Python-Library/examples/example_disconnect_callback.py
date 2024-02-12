"""Gravitrax Example Script: Disconnect Callback
This Script connects to a Gravitrax Bridge for 5 seconds. 
The disconnect callback is executed when the bridge disconnects. 
"""

import asyncio

from gravitraxconnect import gravitrax_bridge as gb

disconnected = asyncio.Event()


def disconnect_callback(bridge: gb.Bridge, **kwargs):
    """Callback for disconnects"""
    if kwargs.get("user_disconnected"):
        gb.log_print("Successfully Disconnected from Bridge!", bridge=bridge)
    else:
        gb.log_print("Connection to Bridge was interrupted", bridge=bridge)
    disconnected.set()


async def main():
    """Connect to to a bridge disconnect it and wait for the disconnect to conclude"""
    gb.logger.disabled = False
    gb.log_print("Searching for Bridge")
    bridge = gb.Bridge()
    try:
        await bridge.connect(dc_callback=disconnect_callback)
        await asyncio.sleep(5)
        if await bridge.is_connected():
            await bridge.disconnect()
        await disconnected.wait()
    except asyncio.CancelledError:
        return


if __name__ == "__main__":
    asyncio.run(main())
    gb.log_print("Program finished")
