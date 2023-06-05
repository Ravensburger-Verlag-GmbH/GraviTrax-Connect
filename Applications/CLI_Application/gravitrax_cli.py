"""Gravitrax Example Script: Using Keyboard buttons to send signals.
This script binds the sending of signals to Keyboard Buttons. Received 
Notifications are displayed.
The input for the status and stonetype can be done by typing the name of the
intended Stone or the int value. 
"""

import asyncio


from threading import Lock
from concurrent.futures import ThreadPoolExecutor
from pynput.keyboard import Listener, Key
from gravitraxconnect import gravitrax_bridge as gb
from gravitraxconnect import gravitrax_constants as gv

# pylint: disable=global-statement
# pylint: disable=global-variable-not-assigned
# pylint: disable=invalid-name

gravitrax_cli = "\
                                          ><<                                 ><<    ><<       ><< \n\
                                      ><  ><<                              ><<   ><< ><<       ><< \n\
   ><<   >< ><<<   ><<    ><<     ><<   ><>< ><>< ><<<   ><<    ><<   ><< ><<        ><<       ><< \n\
 ><<  ><< ><<    ><<  ><<  ><<   ><< ><<  ><<   ><<    ><<  ><<   >< ><<  ><<        ><<       ><< \n\
><<   ><< ><<   ><<   ><<   ><< ><<  ><<  ><<   ><<   ><<   ><<    ><     ><<        ><<       ><< \n\
 ><<  ><< ><<   ><<   ><<    ><><<   ><<  ><<   ><<   ><<   ><<  ><  ><<   ><<   ><< ><<       ><< \n\
     ><< ><<<     ><< ><<<    ><<    ><<   ><< ><<<     ><< ><<<><<   ><<    ><<<<   ><<<<<<<< ><< \n\
  ><<                                                                                             "

key_info = "\
========================================================\n\
|   Keys:                                              |\n\
|   r,g,b:  Send Red/Green/Blue Signal                 |\n\
|   k:      Send Signals in a fixed interval           |\n\
|   s:      Change the Status value of send signals    |\n\
|   t:      Change the stonetype of send signals       |\n\
|   u:      Send unlock signal                         |\n\
|   l:      Send lock signal                           |\n\
|   Esc:    Disconnect and close the program.          |\n\
|   Ctrl+C: Close the program.                         |\n\
========================================================"

b = gb.Bridge()
input_Lock = Lock()
finished = None
loop = None
listener = None

# Signal Parameter
status = gv.STATUS_ALL
stone = gv.STONE_BRIDGE

notif_counter = 0  # Tracks how many Notifications where received


def print_input_info(name, dictionary: dict):
    """Prints out the key/value pairs of a dictionary.
    Used to provide additional information for user inputs.
    """
    print("=============================================")
    print(f"|{name:20} |{'value':20} |")
    for key, value in dictionary.items():
        print(f"|{key:20} | {value:20}|")
    print("=============================================")


async def asyncinput(prompt="") -> str:
    """input that is run asynchronously"""
    # Flush keyboard buffer before getting input
    try:
        import sys  # pylint: disable=import-outside-toplevel
        import termios  # pylint: disable=import-outside-toplevel

        termios.tcflush(sys.stdin, termios.TCIOFLUSH)
    except ImportError:
        import msvcrt  # pylint: disable=import-outside-toplevel

        while msvcrt.kbhit():
            msvcrt.getch()

    with ThreadPoolExecutor(1, "asyncinput") as executor:
        return (
            await asyncio.get_running_loop().run_in_executor(executor, input, prompt)
        ).rstrip()


def disconnect_callback(bridge: gb.Bridge, **kwargs):
    """Callback function that is executed when the bridge disconnects"""
    if kwargs.get("by_timeout"):
        gb.log_print("Disconnect timed out", bridge=bridge)
        finished.set()
    elif kwargs.get("user_disconnected"):
        gb.log_print("Successfully Disconnected", bridge=bridge)
        finished.set()
    else:
        gb.log_print("Connection to Bridge was interrupted", bridge=bridge)


def sanitize_input(user_input, cast_to=int, unsigned=True):
    """Cast a user input into a positive int value."""
    try:
        user_input = cast_to(user_input)
        if unsigned and user_input < 0:
            raise ValueError("Input of negative number is not allowed")
        return user_input
    except (ValueError, TypeError):
        return None
    except:  # pylint: disable=bare-except
        return None


async def color_input(prompt):
    """User Input for a color value"""
    red_list = ["red", "r", "rot", "1"]
    green_list = [
        "green",
        "g",
        "grün",
        "gruen",
        "2",
    ]
    blue_list = [
        "blue",
        "b",
        "blau",
        "3",
    ]

    user_input = await asyncinput(prompt)
    if user_input.lower() in red_list:
        return gv.COLOR_RED
    elif user_input.lower() in green_list:
        return gv.COLOR_GREEN
    elif user_input.lower() in blue_list:
        return gv.COLOR_BLUE
    return 0


async def stone_input(prompt):
    """User Input for a stone value"""
    global stone, input_Lock
    input_Lock.acquire()
    print_input_info("Stonetype", gv.DICT_STONE)
    user_input = (await asyncinput(prompt)).lower()
    try:
        stone = gv.DICT_STONE[user_input]
    except KeyError:
        if not (stone := sanitize_input(user_input, int)) or stone > 255:
            stone = gv.STONE_BRIDGE
            gb.log_print("Unknown Stonetype Value")
    try:
        gb.log_print(f"Stonetype switched to {gv.DICT_VAL_STONE[stone]}", bridge=b)
    except KeyError:
        gb.log_print(f"Stonetype switched to {stone}", bridge=b)
    finally:
        input_Lock.release()


async def status_input(prompt):
    """User input for a status value"""
    global status, input_Lock
    input_Lock.acquire()
    print_input_info("Status", gv.DICT_STATUS)
    user_input = (await asyncinput(prompt)).upper()
    try:
        status = gv.DICT_STATUS[user_input]
    except KeyError:
        if not (status := sanitize_input(user_input, int)) or status > 255:
            status = gv.STATUS_ALL
            gb.log_print("Unknown Status Value")
    try:
        gb.log_print(
            f"Message Status switched to {gv.DICT_VAL_STATUS[status]}", bridge=b
        )
    except KeyError:
        gb.log_print(f"Message Status switched to {status}", bridge=b)
    finally:
        input_Lock.release()


async def send_signals():
    """Get signal information from the user and sends the specified Signals"""
    global status, stone, input_Lock, finished
    input_Lock.acquire()
    try:
        user_input = await asyncinput("Enter the signal count: ")
        count = sanitize_input(user_input, int)
        if count is None:
            gb.log_print("Unknown input")
            return
        if not (color := await color_input("Enter the color of the signal(r,g,b): ")):
            gb.log_print("Unknown input")
            return
        user_input = await asyncinput("Enter the time in sec between each signal:")
        gap = sanitize_input(user_input, float)
        input_Lock.release()
        gb.log_print("Sending Signals")
        await b.send_periodic(
            status,
            color,
            count=count,
            stone=stone,
            gap=gap,
            resend_gap=0,
            resends=12,
        )
    except asyncio.CancelledError:
        finished.set()
        if input_Lock.locked():
            input_Lock.release()
        return


async def notification_callback(bridge: gb.Bridge, **signal):
    """Callback function that is executed when a notification is received"""

    def lookup(key, table, prefix: str):
        try:
            return table[key]
        except (KeyError, IndexError):
            if prefix:
                return f"{prefix}{key}"
            return key

    global notif_counter
    notif_counter += 1
    if signal.get("Header"):  # Check if Notification was a signal
        sig_status = lookup(signal.get("Status"), gv.DICT_VAL_STATUS, None)
        sig_stone = lookup(signal.get("Stone"), gv.DICT_VAL_STONE, None)
        sig_color = lookup(signal.get("Color"), gv.LOOKUP_COLOR, "Color")

        gb.log_print(
            f"{sig_color:5} detected from Stone",
            f" {sig_stone} with Status {sig_status}",
            f"( {notif_counter} Notifications received )",
            bridge=bridge,
        )
    else:
        gb.log_print(f"New Notification: {signal.get('Data')}", bridge=bridge)


def on_press(key):
    """Handling of keyboard presses"""
    global b, status, finished, stone, listener, loop

    if key == Key.esc:
        asyncio.run_coroutine_threadsafe(
            b.disconnect(timeout=15, dc_callback_on_timeout=True), loop
        )
        listener.stop()
    elif input_Lock.locked():
        return
    try:
        k = key.char
    except:  # pylint: disable=bare-except
        k = key.name
    if k == "r":
        asyncio.run_coroutine_threadsafe(
            b.send_signal(status, gv.COLOR_RED, stone=stone), loop
        )
    elif k == "g":
        asyncio.run_coroutine_threadsafe(
            b.send_signal(status, gv.COLOR_GREEN, stone=stone), loop
        )
    elif k == "b":
        asyncio.run_coroutine_threadsafe(
            b.send_signal(status, gv.COLOR_BLUE, stone=stone), loop
        )

    elif k == "u":
        asyncio.run_coroutine_threadsafe(
            b.send_signal(gv.STATUS_UNLOCK, gv.COLOR_RED), loop
        )
    elif k == "l":
        asyncio.run_coroutine_threadsafe(
            b.send_signal(gv.STATUS_LOCK, gv.COLOR_RED), loop
        )


def on_release(key):
    """handling of keyboard releases"""
    global b, loop
    if input_Lock.locked():
        return
    try:
        k = key.char
    except:  # pylint: disable=bare-except
        k = key.name
    if k == "k":
        asyncio.run_coroutine_threadsafe(send_signals(), loop)
    elif k == "s":
        asyncio.run_coroutine_threadsafe(
            status_input("Enter status (name or value):"), loop
        )
    elif k == "t":
        asyncio.run_coroutine_threadsafe(
            stone_input("Enter stonetype value (name or value):"), loop
        )


async def main():
    """Connect to the bridge and start the input Listener."""
    global loop, listener, finished
    loop = asyncio.get_running_loop()
    try:
        finished = asyncio.Event()
    except TypeError:
        gb.log_print("Please update to python 3.10 or newer to use this program")
        return
    listener = Listener(on_press=on_press, on_release=on_release)
    gb.logger.disabled = False
    print(gravitrax_cli)

    gb.log_print(f"Searching for Bridge")
    try:
        if not await b.connect(
            try_reconnect=True,
            dc_callback=disconnect_callback,
        ):
            return

        gb.log_print(await b.request_battery_string(), bridge=b)
        await b.notification_enable(notification_callback)
        await b.request_bridge_info()
        print(key_info)
        listener.start()
        await finished.wait()
    except asyncio.CancelledError:
        return
    finally:
        listener.stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    print()
    gb.log_print("Program finished")
