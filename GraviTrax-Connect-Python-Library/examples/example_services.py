"""Example Script for the print_services function.
This Script connects to all available Bridges and prints out the Battery Level
as well as the services offered by the bridge.
"""

import asyncio

from gravitraxconnect import gravitrax_bridge as gb


async def main():
    """Print out the services offered by the available bridges"""
    bridges = [gb.Bridge()]
    gb.logger.disabled = False
    index = 0

    gb.log_print("Searching for Bridge")
    try:
        while await bridges[index].connect(timeout=8):
            gb.log_print("Searching for more Bridges")
            new_bridge = gb.Bridge()
            bridges.append(new_bridge)
            index += 1

        bridges.pop()  # Removing the last element that could not connect
        gb.log_print(f"{len(bridges)} Bridges found")

        for bridge in bridges:
            gb.log_print(await bridge.request_battery_string(), bridge=bridge)
            await bridge.print_services()
            await bridge.disconnect()
    except asyncio.CancelledError:
        return


if __name__ == "__main__":
    asyncio.run(main())
    gb.log_print("Program finished")
