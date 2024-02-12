"""Bridge Mode Example Script
When sending a Bridge Mode Signal the receiving stones will only listen to 
Signals coming from a Bridge. Other Senders like the Remote are Ignored. This Script
puts all receiving devices into Bridge mode for 10 seconds and sends a Signal after
5 Seconds 
"""

import asyncio

from gravitraxconnect import gravitrax_bridge as gb
from gravitraxconnect import gravitrax_constants


async def main():
    """Start the bridge Mode and send a testsignal
    """
    try:
        bridge = gb.Bridge()
        gb.logger.disabled = False
        gb.log_print("Searching for Bridge")
        await bridge.connect()
        await bridge.start_bridge_mode()
        await asyncio.sleep(5)
        await bridge.send_signal(gravitrax_constants.STATUS_STARTER, gravitrax_constants.COLOR_RED)
        await asyncio.sleep(5)
        await bridge.stop_bridge_mode()
        await bridge.disconnect()
    except asyncio.CancelledError:
        return


if __name__ == "__main__":
    asyncio.run(main())
    gb.log_print("Press Enter to close")
    input()
    gb.log_print("Program finished")
