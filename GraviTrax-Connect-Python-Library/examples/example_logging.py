"""Example script how to use the Logger of the gravitraxconnect library.

The gravitraxconnect library uses Logger for status Messages.
log_print can be used to make prints using this Logger
"""

import asyncio

from gravitraxconnect import gravitrax_bridge as gb

bridge = gb.Bridge()


async def main():
    """Enable the logger and print some Messages with it"""
    # Enabling the logger
    gb.logger.disabled = False
    # printing with the logger
    gb.log_print(f"A simple log print")
    # Passing multiple Arguments
    gb.log_print(f"Passing ", 3, " Arguments")
    try:
        if await bridge.connect():
            # Passing the Bridge to print the address
            gb.log_print(f"<--- This is the MAC-address of the Bridge", bridge=bridge)
        else:
            gb.log_print(f"Could not connect to Bridge")
    except asyncio.CancelledError:
        return

    # Log levels
    gb.log_set_level("DEBUG")
    gb.log_print("This is printed", level="DEBUG")
    gb.log_set_level("ERROR")
    gb.log_print("This is not", level="DEBUG")
    gb.log_print("But this is", level="ERROR")
    gb.log_set_level("DEBUG")
    await bridge.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
    gb.log_print("Program finished")
