"""Gravitrax Example Script: Connect to Bridge with the MAC-Address
"""
import asyncio

from gravitraxconnect import gravitrax_bridge as gb

gb.logger.disabled = False


async def main():
    """Connect to a bridge by MAC-Address"""
    addr_list = await gb.scan_bridges(timeout=10)

    if len(addr_list) == 0:
        gb.log_print("No bridge found")
        return
    gb.log_print("Found bridges:")
    print(addr_list)

    addr = addr_list[0]
    gb.log_print(f"Connecting to {addr} by using its MAC-Address")

    bridge = gb.Bridge()

    try:
        await bridge.connect(addr, by_name=False)
        await asyncio.sleep(3)
        await bridge.disconnect()
    except asyncio.CancelledError:
        return


if __name__ == "__main__":
    asyncio.run(main())
    gb.log_print("program finished")
