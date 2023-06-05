"""Gravitrax Reaction Game: 
A command line Reaction game that uses gravitrax power stones.
Needed Stones:
- 2 Levers
- 1 Starter
- 2 Trigger
- 2 Finishes
- 3 Switches

The game generates a sequence of colors. The player can use Switches 
to direct the automatically released marbles through the correct 
Finishes and Triggers.
"""

# pylint: disable=global-statement
# pylint: disable=global-variable-not-assigned
# pylint: disable=invalid-name

import asyncio
import random
import colorama

from termcolor import colored
from pynput.keyboard import Listener, Key
from gravitraxconnect import gravitrax_bridge as gb
from gravitraxconnect import gravitrax_constants as gv

try:
    import winsound

    playsound = True
except ImportError:
    print("Module Winsounds not found. No sounds are played")
    playsound = False

b = gb.Bridge()
colors = ["red", "green", "blue"]
loop = None
listener = None

# Game state
difficulty = 0
score = 0
sequence = []
fin_count = 0
finished = None
disconnected = False


async def shutdown():
    """Shutdown the main Thread of the Script"""
    finished.set()


def disconnect_callback(bridge: gb.Bridge, **kwargs):
    """Callback for disconnects"""
    if kwargs.get("user_disconnected"):
        finished.set()


async def notification_callback(bridge: gb.Bridge, **signal):
    """callback for received Signals"""
    global score, colors, fin_count, playsound
    stonetype = signal.get("Stone")
    color = signal.get("Color")
    if stonetype == gv.STONE_TRIGGER or stonetype == gv.STONE_FINISH:
        if len(sequence) == 0:  # Do nothing when no game is played
            return
        if color != gv.COLOR_BLUE:  # When a marble finishes
            fin_count += 1
            if difficulty == 1:
                # Release the next marble
                await bridge.send_signal(gv.STATUS_STARTER, gv.COLOR_RED)
            if color == sequence[0]:
                score += 1
        if color != sequence[0]:
            score -= 1
            print(f"Wrong! Next Colors: ", end="")
            if playsound:
                winsound.PlaySound(
                    "WQ.FX.Wrong.wav", winsound.SND_ASYNC | winsound.SND_ALIAS
                )
        else:
            print("Correct! Next Colors: ", end="")
            if playsound:
                winsound.PlaySound(
                    "WQ.FX.GameStart.wav", winsound.SND_ASYNC | winsound.SND_ALIAS
                )

        sequence.pop(0)
        if fin_count < 7:
            for _,color in enumerate(sequence):
                print(
                    colored(f"{colors[color-1]} ", colors[color - 1]),
                    end="",
                )
                if color != 3:
                    break
            print()
        else:  # All Marbles used
            print()
            print(f"All Marbles used: {score} Points scored")
            print("Press Level Button to play again")


def on_press(key):
    """ Evaluation of Button presses"""
    global b, finished, difficulty, listener, loop
    if difficulty == 1:
        status = gv.STATUS_ALL
    else:
        status = gv.STATUS_SWITCH
    if key == Key.f1:
        asyncio.run_coroutine_threadsafe(b.send_signal(status, gv.COLOR_RED), loop)
    elif key == Key.f2:
        asyncio.run_coroutine_threadsafe(b.send_signal(status, gv.COLOR_GREEN), loop)
    elif key == Key.f3:
        asyncio.run_coroutine_threadsafe(b.send_signal(status, gv.COLOR_BLUE), loop)
    elif key == Key.f4:
        difficulty = 0
        level()
    elif key == Key.f5:
        difficulty = 1
        level()
    elif key == Key.f6:
        difficulty = 2
        level()
    elif key == Key.f7:
        if difficulty == 0:
            asyncio.run_coroutine_threadsafe(release_timed(10), loop)
        else:
            asyncio.run_coroutine_threadsafe(
                b.send_signal(gv.STATUS_STARTER, gv.COLOR_RED), loop
            )
    elif key == Key.esc:
        gb.log_print(f"Stop Signal received: Closing Program")
        asyncio.run_coroutine_threadsafe(
            b.disconnect(timeout=15, dc_callback_on_timeout=True), loop
        )
        listener.stop()


def level():
    """Start new level and generate random color sequence"""
    global score, fin_count
    sequence.clear()
    score = 0
    fin_count = 0
    print("Level started. Press F7 ro release the first marble")
    print("The Color sequence is:")
    for _ in range(7):
        color = random.randrange(1, 4)
        sequence.append(color)
        if sequence[-1] == 3:
            sequence.append(random.randrange(1, 4))
            if sequence[-1] == 3:
                sequence.append(random.randrange(1, 3))
    for color in sequence:
        print(colored(f"{colors[color-1]} ", colors[color - 1]), end="")
    print()


async def release_timed(delay):
    """Release 7 marbles with a timegap inbetween"""
    try:
        for _ in range(7):
            await b.send_signal(gv.STATUS_STARTER, gv.COLOR_RED)
            await asyncio.sleep(delay)
    except asyncio.CancelledError:
        return

async def main():
    """Start the keyboard listener and connect to the bridge"""
    global finished, loop, listener
    loop = asyncio.get_running_loop()
    try:
        finished = asyncio.Event()
    except TypeError:
        gb.log_print("Please update to python 3.10 or newer to use this program")
        return
    listener = Listener(on_press=on_press)
    colorama.init()

    gb.logger.disabled = False
    gb.log_print(f"Searching for Bridge")
    try:
        if await b.connect(try_reconnect=True, dc_callback=disconnect_callback):
            await b.start_bridge_mode()
            await b.notification_enable(notification_callback)
            gb.log_print("Start Level with F4=hard, F5=very hard, F6=impossible")
            listener.start()
        else:
            gb.log_print(f"Could not find Bridge to connect to")

        await finished.wait()
    except asyncio.CancelledError:
        return


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    gb.log_print("Program finished")
