"""Bridge ID Example Script
Bridges can be grouped together by assigning IDs to them. 
In this Example all connected Bridges get split into two Groups. 
The group with id=0 prints an output when receiving red and green signals.
The group with id=1 prints an output when receiving a blue signal
"""

import asyncio

from gravitraxconnect import gravitrax_bridge as gb
from gravitraxconnect import gravitrax_constants


async def notification_callback(bridge: gb.Bridge, **signal):
    """Callback for Received Notifications

    Different colors are displayed depending on the id of the receiving bridge 
    """
    stone = signal.get("Stone")
    color = signal.get("Color")

    try:
        color_lookup = gravitrax_constants.LOOKUP_COLOR[color]
    except IndexError:
        color_lookup = color

    try:
        stone_lookup = gravitrax_constants.DICT_VAL_STONE[stone]
    except KeyError:
        stone_lookup = stone

    if (bridge.id == 0 and color != gravitrax_constants.COLOR_BLUE) or (
        bridge.id == 1 and color == gravitrax_constants.COLOR_BLUE
    ):
        gb.log_print(
            f"{color_lookup:5} detected from", f"Stone {stone_lookup:10}", bridge=bridge
        )


async def main():
    """Connect to all available bridges and split them in 2 groups
    """
    try:
        b_list = [gb.Bridge()]
        index = 0
        gb.log_set_level("DEBUG")
        gb.logger.disabled = False
        gb.log_print("Searching for Bridges")
        # Connect to all available Bridges

        while await b_list[index].connect(timeout=15):
            new_bridge = gb.Bridge()
            b_list.append(new_bridge)
            index += 1

        if len(b_list) > 0:
            b_list.pop()  # Removing the last element that could not connect

        for bridge in b_list:
            bridge.id = b_list.index(bridge) % 2  # Bridges get 2 Different IDs
            await bridge.notification_enable(notification_callback)

        await asyncio.sleep(10.0)

        for bridge in b_list:
            await bridge.notification_disable()
            await bridge.disconnect()
    except asyncio.CancelledError:
        return


if __name__ == "__main__":
    asyncio.run(main())
    gb.log_print("Program finished")
