"""Read out information from multiple Bridges
This Script connects to all available Bridges and prints out the Battery Level
as well as the hardware and Firmware Version.
"""

import asyncio

from gravitraxconnect import gravitrax_bridge as gb

finished = asyncio.Event()


async def main():
    """Connect to all available Bridges and read out information     
    """
    try:
        bridges = [gb.Bridge()]
        gb.logger.disabled = False
        index = 0

        gb.log_print("Searching for Bridge")

        while await bridges[index].connect(timeout=10, try_reconnect=False):
            gb.log_print("Searching for more Bridges")
            new_bridge = gb.Bridge()
            bridges.append(new_bridge)
            index += 1

        bridges.pop()
        gb.log_print(f"{len(bridges)} Bridges found")

        for bridge in bridges:
            gb.log_print(await bridge.request_battery_string(), bridge=bridge)

            # Getting the Firmware and Hardware Version from the Member variables
            # that are set after connecting to the bridge
            gb.log_print(f"Firmware: {bridge.firmware} Hardware: {bridge.hardware}")
            # Requesting the current Firmware/ Hardware Version from the Bridge
            if (await bridge.request_bridge_info())[0] >= 14:
                gb.log_print("Firmware 14 or newer is used")

            await bridge.disconnect()

        gb.log_print("Press Enter to close")
        input()
    except asyncio.CancelledError:
        return


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass

    gb.log_print("Program finished")
