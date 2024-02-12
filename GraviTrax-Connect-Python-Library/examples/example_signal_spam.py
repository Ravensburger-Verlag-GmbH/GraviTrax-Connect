"""Gravitrax Example Script:Sending Signals
This Script sends out 7 Signals in all three colors to Startes.
In order to send a Signal multiple times the send_periodic() function can be used.
In this example a red signal for Switches is send 10 times with a delay of 1 second 
between each send.
"""

import asyncio

from gravitraxconnect import gravitrax_bridge as gb
from gravitraxconnect import gravitrax_constants


async def main():
    """ Repeatedly send signals in different colors
    """
    gb.logger.disabled = False
    gb.log_print("Searching for Bridge")
    bridge = gb.Bridge()
    try:
        if await bridge.connect():
            for _ in range(7):
                if not await bridge.send_signal(
                    gravitrax_constants.STATUS_STARTER, gravitrax_constants.COLOR_RED
                ):
                    break
                if not await bridge.send_signal(
                    gravitrax_constants.STATUS_STARTER, gravitrax_constants.COLOR_GREEN
                ):
                    break
                if not await bridge.send_signal(
                    gravitrax_constants.STATUS_STARTER, gravitrax_constants.COLOR_BLUE
                ):
                    break
            await asyncio.sleep(1)
            await bridge.send_periodic(
                gravitrax_constants.STATUS_SWITCH,
                gravitrax_constants.COLOR_RED,
                10,
                gap=1,
                resends=12,
                resend_gap=0,
            )
            await bridge.disconnect()
    except asyncio.CancelledError:
        return


if __name__ == "__main__":
    asyncio.run(main())
    gb.log_print("Program finished")
