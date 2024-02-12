"""Connection Check example Script
Running Code in a continuos loop that checks if 
the bridge is still connected
"""
import asyncio
import sys

from gravitraxconnect import gravitrax_bridge as gb


async def main():
    """Connect to the bridge and print for how long it is connected
    """
    bridge = gb.Bridge()
    gb.logger.disabled = False
    try:
        await bridge.connect()

        timer = 0
        while await bridge.is_connected():
            sys.stdout.write(f"\rConnected for {timer} seconds")
            sys.stdout.flush()
            timer += 1
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        return


if __name__ == "__main__":
    asyncio.run(main())
    gb.log_print("Program finished")
