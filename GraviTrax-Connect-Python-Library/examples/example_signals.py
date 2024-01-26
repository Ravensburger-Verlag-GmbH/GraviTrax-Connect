"""Example Script for sending Signals
This Script sends Signals with Different Colors over the Bridge.The resends parameter 
specifies how often a package is resend. 
A lower value can lead to package loss. The resends_gap parameter 
specifies how long the artificial delay behind every transmission is. Usually this 
value can be set to 0 if the resends value is sufficiently high.
The default values are set to values that are moste likely to work on most Systems. 
It´s also possible to adjust which stones are targeted by changing the status value. 
The Status values for available Gravitrax Power stones can be found in the 
gravitrax_constants file.
"""

import asyncio

from gravitraxconnect import gravitrax_bridge as gb
from gravitraxconnect import gravitrax_constants


async def main():
    """Send a Signal Sequence of red, green and blue signals
    """
    bridge = gb.Bridge()
    gb.logger.disabled = False
    try:
        if await bridge.connect():
            for _ in range(3):
                gb.log_print("Send RED", bridge=bridge)
                await bridge.send_signal(
                    gravitrax_constants.STATUS_ALL,
                    gravitrax_constants.COLOR_RED,
                    resends=12,
                )
                await asyncio.sleep(3)
                gb.log_print("Send GREEN and BLUE", bridge=bridge)
                await bridge.send_signal(
                    gravitrax_constants.STATUS_ALL,
                    gravitrax_constants.COLOR_GREEN,
                    resends=12,
                )
                await bridge.send_signal(
                    gravitrax_constants.STATUS_ALL,
                    gravitrax_constants.COLOR_BLUE,
                    resends=12,
                    resend_gap=0,
                )
                await asyncio.sleep(3)

            await bridge.disconnect()
    except asyncio.CancelledError:
        return


if __name__ == "__main__":
    asyncio.run(main())
    gb.log_print("Program finished")
