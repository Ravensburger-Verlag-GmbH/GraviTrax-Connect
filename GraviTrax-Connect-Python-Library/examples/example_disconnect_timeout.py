"""Gravitrax Example Script: Disconnect Timeout
When calling disconnect() the dc_callback_on_timeout parameter can be
set to trigger the disconnect callback when the disconnect 
attempt times out. This can be used to ensure that a script
that is supposed to shut down if the bridge is disconnected
doesn't run forever even if the disconnect fails.
If the disconnect times out it still continues to run. The timeout
is just a way to call the disconnect callback early if the disconnect 
takes to long. As a result if the disconnect times out but finishes afterwards 
the disconnect callback is called twice.
"""

import asyncio

from gravitraxconnect import gravitrax_bridge as gb


finished = asyncio.Event()


def disconnect_callback(bridge: gb.Bridge, **kwargs):
    """Callback for disconnects"""
    try:
        if kwargs.get("by_timeout"):
            gb.log_print("Disconnect timed out", bridge=bridge)
        elif kwargs.get("user_disconnected"):
            gb.log_print("Disconnect by user!", bridge=bridge)
        else:
            gb.log_print("Connection to Bridge was interrupted", bridge=bridge)
    finally:
        finished.set()


async def main():
    """Connect to a bridge and wait for the timeout of the disconnect"""
    gb.logger.disabled = False
    gb.log_print("Searching for Bridge")
    bridge = gb.Bridge()
    try:
        if not await bridge.connect(dc_callback=disconnect_callback):
            return

        await asyncio.sleep(5)
        if await bridge.is_connected():
            await bridge.disconnect(timeout=2, dc_callback_on_timeout=True)
        while await bridge.is_connected():
            gb.log_print("Waiting")
            await asyncio.sleep(0.5)
        await finished.wait()
    except asyncio.CancelledError:
        return


if __name__ == "__main__":
    asyncio.run(main())
    gb.log_print("Program finished")
