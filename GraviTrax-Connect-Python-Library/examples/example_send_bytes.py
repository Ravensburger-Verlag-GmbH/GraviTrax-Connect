"""Gravitrax Example Script:Sending Bytes
With this script it´s possible to send bytes of data to the Bridge. 
In order for the Bridge to recognize the data as a signal the following format 
needs to be used.
Byte 0 = 19 -> header
Byte 1 = a valid stonetype -> stone
Byte 2 = a valid status -> status
Byte 3 = 0 - 255 -> Reserved
Byte 4 = 0 - 255 -> Message ID
Byte 5 = (Byte1 + Byte2 + Byte3 + Byte4 + Byte5)%256 -> Checksum 
Byte 6 = a valid color value -> Red=1, Green=2, Blue=3

example: 
Send a Red signal to All Stones as a Sound Stone: data = bytes([19,7,0,0,0,0,1])
"""

import asyncio

from gravitraxconnect import gravitrax_bridge as gb


async def main():
    """Send signal bytes to the bridge"""
    bridge = gb.Bridge()
    gb.logger.disabled = False
    try:
        await bridge.connect()
        for i in range(13):
            data = gb.add_checksum(bytes([19, 8, 0, 0, i, 0, 1]))
            gb.log_print(f"Sending {i}: {data}", bridge=bridge)
            await bridge.send_bytes(data)
            await asyncio.sleep(0.2)
    except asyncio.CancelledError:
        return


if __name__ == "__main__":
    asyncio.run(main())
    gb.log_print("Program finished")
