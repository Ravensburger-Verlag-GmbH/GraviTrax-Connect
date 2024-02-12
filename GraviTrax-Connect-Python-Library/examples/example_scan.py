"""Example Script for using the scan_bridges function



"""

import asyncio

from gravitraxconnect import gravitrax_bridge as gb


b = gb.Bridge()


async def main():
    """Scan for Bridges / BLE-Devices in multiple ways"""
    try:
        # Scan for available Bridges. Stop when a Bridge is found
        await gb.scan_bridges(timeout=10, do_print=True, stop_on_hit=True)
        gb.log_print("Found Bridge")
        # Scan for available Bridges.
        await gb.scan_bridges(timeout=10, do_print=True)
        # Scan for all Bluetooth Devices
        await gb.scan_bridges(name="", timeout=10, do_print=True)
    except asyncio.CancelledError:
        return


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    gb.log_print("Program finished")
