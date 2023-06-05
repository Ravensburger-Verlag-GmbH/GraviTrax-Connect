"""Graphical user Interface for the gravitraxconnect library
A Graphical User Interface Application using the gravitraxconnect 
Python Library.

Features:
- Send Signals and receive Notifications for incoming Signals
- Modify the Signal Parameters like the Stone type or which Stones should 
receive the signal
- Queue multiple Signals
- Implement If/ Then Logic: If Signal X then do Signal a, Signal b, ...... 
- Timer: Measure the time between two Signals
- Loading saved Signal presets from a file. (filename can be passed as an argument)

"""

import time
import asyncio
import json

from datetime import datetime
from collections import namedtuple
from queue import Queue
from threading import Thread, Event

import PySimpleGUI as sg
from gravitraxconnect import gravitrax_bridge as gb
from gravitraxconnect import gravitrax_constants as gv

SignalTuple = namedtuple(
    "SignalTuple",
    ["color", "status", "stone", "count", "resends", "resend_gap", "pause"],
)

TriggerSignal = namedtuple("TriggerSignal", ["color", "status", "stone", "actionlist"])

b = gb.Bridge()  # Gravitrax Bridge Object
loop = None  # Asyncio Event Loop

# Logging for gravitraxconnect library
gb.logger.disabled = False
gb.log_set_level("DEBUG")

# Default Values
try:
    DEFAULT_STATUS = ["ALL", gv.DICT_STATUS["ALL"]]
except KeyError:
    DEFAULT_STATUS = ["0", 0]
try:
    DEFAULT_STONE = ["bridge", gv.DICT_STONE["bridge"]]
except KeyError:
    DEFAULT_STONE = ["6", 6]

DEFAULT_COUNT = 1
DEFAULT_RESENDS = 12
DEFAULT_RESEND_GAP = 0
DEFAULT_PAUSE = 0.1
DEFAULT_PRESET = ""

# Signal Parameter presets
signal_preset_dict = {}


# GUI Configuration
BACKGROUND_COLOR = "#DBDBDB"
BUTTON_COLOR = ("#000000", "#8DBF28")  # Text Color, Background Color
UI_TEXT_COLOR = "#000000"
SCROLLBAR_COLOR = "#8DBF28"
RELIEF = ["raised", "sunken", "flat", "ridge", "groove", "solid"][
    3
]  # The type of border around Frame Elements
QUEUEMODE_COLOR = "#b300ff"
IFMODE_COLOR = "#74798b"
TIMER_COLOR = "#1d92e2"
FONT = "Open Sans"
FONT_H1 = (FONT, 15, "bold")
FONT_H2 = (FONT, 10, "bold")
FONT_TEXT = (FONT, 10, "normal")
FONT_BUTTON = (FONT, 9, "bold")

# PysimpleGUI Elements
window_main = None  # Main Input Window
window_help = None  # Window Containing the Manual
window_log = None  # Window for the Log Output

# Events to ensure correct  startup and shutdown behavior
startup_event = (
    Event()
)  # Prevents the GUI from starting before the asyncio loop is running

finished_event = None

# Timer Mode variables
timer = False
start_signal = None  # Signal that starts a timer
stop_signal = None  # Signal that stops a timer
start_times = []  # Holds the time of detected timer start signals


notif_counter = 0  # Number of received Notifications

# Queue for User Inputs from the GUI. main-Thread -> gui_worker_thread
eventqueue = Queue()

# List that stores the Signals for the If/Then mode. The items in the list
# are TriggerSignal tuples
notilist = []


def read_preset_file(filename):
    """Use the json module to load a preset file into the preset dictionary"""
    global signal_preset_dict
    try:
        signal_preset_dict = dict(json.load(open(filename, "rb")))
    except TypeError:
        print_log("Preset File doesn't have the correct Format")
        return False
    except FileNotFoundError:
        print_log("No presets file found")
        return False
    except:
        return False
    return True


def save_preset_file(filename):
    """Use the json module to save the preset dictionary into a json file"""
    json.dump(
        signal_preset_dict,
        open(filename, "w", encoding="locale"),
    )
    print_log("Presets saved")


def set_buttons(buttons: list, active=True, text=None):
    """Enable,Disable or change the Button text for multiple buttons at once"""
    global window_main
    for button in buttons:
        if not text:
            window_main[button].update(disabled=not active)
            continue
        window_main[button].update(text=text, disabled=not active)


def print_log(text, add_timestamp=True, text_color=None, end=None):
    """Print text in the multiline Element of the logging Window"""
    global window_log
    if window_log is None:
        return

    if add_timestamp:
        current_time = datetime.now()
        hour = str(current_time.hour).zfill(2)
        minute = str(current_time.minute).zfill(2)
        second = str(current_time.second).zfill(2)
        millis = str(current_time.microsecond)[:3]
        window_log["log_window"].print(
            f"{hour:2}:{minute:2}:{second:2}.{millis:3}",
            end=": ",
            font=FONT_TEXT,
            text_color=text_color,
        )

    window_log["log_window"].print(text, font=FONT_H2, text_color=text_color, end=end)


async def connect() -> bool:
    """Connect to a Gravitrax Power Bridge
    After Connecting the Battery level and the Firmware and Hardware Version are
    printed in the log. The Notifications are enabled as well
    """
    global b
    set_buttons(["Connect"], False)
    if await b.connect(
        timeout=60, dc_callback=disconnect_callback, try_reconnect=False
    ):
        await b.notification_enable(notification_callback)
        print_log(f"Connected to {b.get_name()}")
        print_log(f"MAC-Address: {b.get_address()}")
        print_log(f"Firmware Version: {b.firmware} ")
        print_log(f"Hardware Version: {b.hardware}")
        print_log(await b.request_battery_string())
        print_log("", add_timestamp=False)
        set_buttons(["Quit"], text="Disconnect")
        set_buttons(
            ["Red", "Green", "Blue", "Lock", "Unlock", "Queuemode", "IF", "Timer"]
        )
        return True
    else:
        print_log("Could not connect to a Bridge")
        set_buttons(["Connect"])
        return False


def disconnect_callback(bridge: gb.Bridge, **kwargs):
    """Function that is executed when the Bridge is disconnected"""
    if kwargs.get("user_disconnected"):
        print_log("Bridge successfully disconnected")
    else:
        print_log("Connection to Bridge lost")
    set_buttons(["Quit"], text="Quit")
    set_buttons(["Connect"])
    set_buttons(
        ["Red", "Green", "Blue", "Lock", "Unlock", "Queuemode", "IF", "Timer"], False
    )


async def notification_callback(bridge: gb.Bridge, **signal):
    """Handling of received Notifications
    - Incoming Signals are printed in the Log Window
    - If the signal is the start signal for the timer the current time is stored in
    the start_times list
    - If the signal is the stop signal for the timer the time since the first entry
    in the start_times list is printed to the log
    - If the signal was set as the Condition in If-Mode the Queued Signals are send
    """
    global notif_counter, notilist, start_signal, stop_signal, start_times, timer

    def lookup(value, table):
        try:
            return table[value]
        except (IndexError, KeyError):
            return value

    notif_counter += 1

    status = signal.get("Status")
    stone = signal.get("Stone")
    color = signal.get("Color")

    status_name = lookup(status, gv.DICT_VAL_STATUS)
    stone_name = lookup(stone, gv.DICT_VAL_STONE)
    color_name = lookup(color, gv.LOOKUP_COLOR)

    print_log(
        f"{color_name:5} detected from Stone {stone_name} with Status {status_name}"
        f" ( {notif_counter} Notifications received )"
    )

    # If Timer is enabled and the received Signal is a start or stop Signal
    if (
        timer
        and start_signal.status == status
        and start_signal.stone == stone
        and start_signal.color == color
    ):
        start_times.append(time.time())
    elif (
        timer
        and stop_signal.status == status
        and stop_signal.stone == stone
        and stop_signal.color == color
    ):
        if start_times:
            print_log(f"Time between Start and Finish {time.time()-start_times.pop(0)}")

    # If received Signal was set as condition in IF-mode the Queued signals are send
    for item in notilist:
        if item.status == status and item.stone == stone and item.color == color:
            await send(item.actionlist)


async def send(list_queue):
    """Reads the SignalTuple Items from a list or queue and sends them"""
    if isinstance(list_queue, Queue):
        while not list_queue.empty():
            signal = list_queue.get()
            await send_signals(
                signal.status,
                signal.color,
                signal.stone,
                signal.count,
                signal.resends,
                signal.resend_gap,
                signal.pause,
            )
    elif isinstance(list_queue, list):
        for signal in list_queue:
            await send_signals(
                signal.status,
                signal.color,
                signal.stone,
                signal.count,
                signal.resends,
                signal.resend_gap,
                signal.pause,
            )


async def send_signals(status, color_channel, stone, count, resends, resend_gap, pause):
    """Send Signals to the Bridge
    When count is set to 0 the specified pause is awaited.
    """
    if count == 0:
        await asyncio.sleep(pause)
    else:
        await b.send_periodic(
            status,
            color_channel,
            count,
            pause,
            resends=resends,
            resend_gap=resend_gap,
            stone=stone,
        )


def make_help_window() -> sg.Window:
    """Create the Window with the manual for the application"""

    def formatted_print(headline: str, dictionary: dict):
        help_ml.print(headline, justification="c", font=FONT_H1, autoscroll=False)
        for key, val in dictionary.items():
            help_ml.print(key, justification="l", font=FONT_H2, autoscroll=False)
            help_ml.print(val, justification="l", font=FONT_TEXT, autoscroll=False)

    options_dict = {
        "Status": "The Status ID of the Signal usually specifies that only"
        " certain Stones will react to the Signal, but it also is used by Stones"
        " to transmit additional Information. The Starter Stone for example uses a Status"
        " value to signal that a marble was released manually",
        "Stone": "The Stone ID identifies the source of a signal. Receiving Stones might"
        " react differently to Signals depending on this Value. An example for this would"
        " be that Bridge Stones filter out all Signals with the Stone ID set to Bridge,"
        " otherwise the Bridge would detect it's own signals",
        "Count": "The Count option specifies how many Signals should be send. If this Value"
        " is set to 0 no signal is send but the specified Pause duration is awaited",
        "Resends": "How often the same signal should be transmitted. A higher value"
        " decreases the likelihood for package loss to occur. A lower value speeds up"
        " the transmission when sending many Signals",
        "Resend Gap": "Additional wait time in Seconds after every Signal transmission."
        " This can help against package loss, but it's usually best to keep this at 0 and"
        " increase the amount of resends instead",
        "Pause": "Wait time in between every Signal. If the Count for a Signal is set to"
        " 0 the duration is awaited without a signal being send",
        "Preset": "Contains presets for commonly used signal settings. The preset is"
        " applied when clicking it in the dropdown list. Presets can be added with the"
        " Add button ot loaded from a File",
        "Reset": "Reset the Signal Options to the Default values",
        "Save Presets": "Save the current Preset List in a json File.This overwrites the"
        " previous File when an existing file is selected. ",
        "Load Presets": "Load a Preset List from a json File. ",
    }
    signal_dict = {
        "Color Buttons": "During normal operation the Buttons Red(F1), Green(F2) and Blue(F3)"
        " send Signals in the corresponding Color. If one of the special Modes is active the"
        " inputs from the Buttons are used to queue up Signals, set conditions etc.",
        "Lock Buttons": "The Lock Button(F4) sends out a Signal that puts receiving Stones in"
        " Bridge-Only Mode. In this Mode they will only accept Signals where the Stone value"
        " is set to Bridge.The Unlock button(F5) reverses this. The Count parameter is ignored"
        " when using both the Lock and the Unlock Button.",
    }
    mode_dict = {
        "Timer": "The Timer Button(F6) is used to measures the time between 2 Signals. When"
        " the Button is pressed the Signals that start and stop the timer are entered."
        " Whenever a Stop Signal is received after a Start Signal the time in between is"
        " printed in the log. The Timer mode can be stopped by pressing the Cancel Button.",
        "If/Then": "The If/Then Button(F7) allows to implement simple If/Then logic. The"
        " first Signal entered after pressing the Button is used as the IF-Condition. Other"
        " Signals can be queued afterwards. If the Signal that was set as the IF-Condition"
        " is received all Queued up Signals are send. An Example how this can be used is to"
        " set a Red Signal from a Remote as the Condition an Queue up 7 Signals with the"
        " Status STARTER. A single press on the red remote button will empty a full starter"
        " this way.",
        "Queuemode": "The Queuemode Button(F8) starts the Queuemode. In this Mode Signals"
        " are put into a queue instead of being send directly. After pressing the Button the"
        " Buttontext changes to Send. Pressing the button then sends the queued Up Signals.",
    }
    conn_dict = {
        "Connect": "The Connect Button is used to establish a connection to a Bride. The button"
        " is disabled when there is already an active connection to a Bridge.",
        "Disconnect": "Disconnect from the Bridge. If there is no active connection the Button"
        " is used to Close the Application",
    }

    help_ml = sg.Multiline(
        "",
        expand_x=True,
        expand_y=True,
        font=FONT_TEXT,
        background_color="#FFFFFF",
        disabled=True,
        sbar_background_color=SCROLLBAR_COLOR,
        autoscroll=False,
    )

    window = sg.Window(
        "",
        [[help_ml]],
        background_color=BACKGROUND_COLOR,
        element_justification="l",
        resizable=True,
        size=(500, 300),
        finalize=True,
        location=(
            window_main.current_location()[0] + 30,
            window_main.current_location()[1] + 30,
        ),
    )
    formatted_print("Signal Options", options_dict)
    formatted_print("Signal Buttons", signal_dict)
    formatted_print("Mode Buttons", mode_dict)
    formatted_print("Connection Buttons", conn_dict)
    return window


def make_log_window() -> sg.Window:
    """Create the Window with the logging output"""
    global window_main
    main_loc = window_main.current_location()
    min_size = (300, window_main.size[1])

    log_ml = sg.Multiline(
        "",
        size=(40, 8),
        expand_x=True,
        expand_y=True,
        key="log_window",
        autoscroll=True,
        disabled=True,
        sbar_background_color=SCROLLBAR_COLOR,
    )

    # Determine the best location to place the log window
    if (
        main_loc[0] + window_main.size[0] + min_size[0] + 10
        < sg.Window.get_screen_size()[0]
    ):
        loc = (main_loc[0] + window_main.size[0] + 10, main_loc[1])
    else:
        loc = (main_loc[0] + 30, main_loc[1] + 30)

    window = sg.Window(
        "Gravitrax Connect Log Window",
        [[log_ml]],
        background_color=BACKGROUND_COLOR,
        element_justification="l",
        resizable=True,
        finalize=True,
        location=loc,
        disable_close=True,
    )

    window.set_min_size(min_size)
    return window


def run_gui():
    """Reads inputs from the GUI and puts them in the eventqueue for the
    gui_worker_thread. The Closing of windows is handled directly in this
    function and not by the worker thread
    """
    global window_main, window_help, window_log, eventqueue
    while True:
        window, event, values = sg.read_all_windows()
        if event == "Help" and window_help is None:  # Open Help Window
            window_help = make_help_window()
            set_buttons(["Help"], False)
        elif event == sg.WINDOW_CLOSED and window == window_help:  # Close Help Window
            window_help.close()
            window_help = None
            set_buttons(["Help"], True)
        else:  # Other inputs are handled by the gui_worker thread
            eventqueue.put((event, values))
            if event == sg.WINDOW_CLOSED:
                break
            if event == "Quit" and window_main[event].get_text() == "Quit":
                break

    if window_help:
        window_help.close()
    if window_log:
        window_log.close()
    window_main.close()
    gb.log_print("GUI stopped", level="DEBUG")


def read_signal_options(values) -> SignalTuple:
    """Reads the values from the Signal Options Comboboxes and
    returns them as int values. If a Combobox contains an invalid
    value it is reset.
    """
    try:
        status = gv.DICT_STATUS[values["StatusCombo"]]
    except KeyError as exc:
        try:
            status = int(values["StatusCombo"])
            if status not in range(0, 256):
                raise ValueError("Value outside accepted range") from exc
        except ValueError:
            print_log("Status Value outside accepted range. Resetting to default Value")
            status = DEFAULT_STATUS[1]
            window_main["StatusCombo"].update(DEFAULT_STATUS[0])

    # Get stone Value from GUI
    try:
        stone = gv.DICT_STONE[values["StoneCombo"]]
    except KeyError as exc:
        try:
            stone = int(values["StoneCombo"])
            if stone not in range(0, 256):
                raise ValueError("Value outside accepted range") from exc
        except ValueError:
            print_log(
                "Stonetype Value outside accepted range. Resetting to default Value"
            )
            stone = DEFAULT_STONE[1]
            window_main["StoneCombo"].update(DEFAULT_STONE[0])

    # Get count Value from GUI
    try:
        count = int(values["Count"])
        if count < 0:
            raise ValueError
    except ValueError:
        count = DEFAULT_COUNT
        window_main["Count"].update(DEFAULT_COUNT)

    # Get resends Value from GUI
    try:
        resends = int(values["Resends"])
        if resends < 1:
            resends = 1
            window_main["Resends"].update(1)
        if resends > 12:
            resends = 12
            window_main["Resends"].update(12)
    except ValueError:
        resends = DEFAULT_RESENDS
        window_main["Resends"].update(DEFAULT_RESENDS)

    # Get resend_gap Value from GUI
    try:
        resend_gap = float(values["ResendGap"])
    except ValueError:
        resend_gap = DEFAULT_RESEND_GAP
        window_main["ResendGap"].update(DEFAULT_RESEND_GAP)

    # Get pause Value from GUI
    try:
        pause = float(values["Pause"])
    except ValueError:
        pause = DEFAULT_PAUSE
        window_main["Pause"].update(DEFAULT_PAUSE)
    return SignalTuple(None, status, stone, count, resends, resend_gap, pause)


def gui_worker_thread():
    """Thread that gets input events from the eventqueue and does event specific work
    Depending on the input event:
    - UI-Elements are updated
    - Coroutines are scheduled to run in the asyncthread
    - Trigger Signals are added to Notification List used for IF/Then Mode

    """
    global window_main, b, notilist, loop, timer, start_signal, stop_signal
    ifmode = False
    queuemode = False
    signalqueue = Queue()
    if_mode_condition = None  # temp variable for the Trigger Signal in IF-Mode.
    gb.log_print("GUI Worker started", level="DEBUG")
    while True:

        event, values = eventqueue.get()
        # Events are Ignored if the Button etc. is disabled
        if (
            event
            and isinstance(window_main[event], sg.Button)
            and window_main[event].Disabled
        ):
            continue
        elif event == sg.WINDOW_CLOSED:
            break
        elif event == "Quit":  # Disconnecting the Bridge and closing the program
            if window_main[event].get_text() == "Disconnect":
                set_buttons(
                    [
                        "Red",
                        "Green",
                        "Blue",
                        "Lock",
                        "Unlock",
                        "Queuemode",
                        "IF",
                        "Timer",
                    ],
                    False,
                )
                asyncio.run_coroutine_threadsafe(b.disconnect(), loop)
                print_log("Disconnecting")
                set_buttons(["Quit"], text="Quit")
                continue
            break
        elif event == "Connect":  # Connect to a Bridge
            print_log("Searching for Bridge")
            asyncio.run_coroutine_threadsafe(connect(), loop)
            continue
        elif event == "Reset":  # Reset the Signal Options
            window_main["StatusCombo"].update(DEFAULT_STATUS[0])
            window_main["StoneCombo"].update(DEFAULT_STONE[0])
            window_main["Count"].update(DEFAULT_COUNT)
            window_main["Resends"].update(DEFAULT_RESENDS)
            window_main["ResendGap"].update(DEFAULT_RESEND_GAP)
            window_main["Pause"].update(DEFAULT_PAUSE)
            window_main["Preset"].update(DEFAULT_PRESET)
            print_log("Reset Signal Options to default values")
            continue
        elif event == "Preset":  # Apply signal Option preset
            try:
                preset = signal_preset_dict[values["Preset"]]
                signal_item = SignalTuple(*preset)
            except KeyError:
                window_main["Preset"].update(DEFAULT_PRESET)
                continue
            try:
                stone_name = gv.DICT_VAL_STONE[signal_item.stone]
            except KeyError:
                stone_name = signal_item.stone
            try:
                status_name = gv.DICT_VAL_STATUS[signal_item.status]
            except KeyError:
                status_name = signal_item.status
            window_main["StatusCombo"].update(status_name)
            window_main["StoneCombo"].update(stone_name)
            window_main["Count"].update(signal_item.count)
            window_main["Pause"].update(signal_item.pause)
            window_main["Resends"].update(signal_item.resends)
            window_main["ResendGap"].update(signal_item.resend_gap)
            print_log("Preset Applied: " + values["Preset"])
            continue
        elif event == "FileLoad":
            if read_preset_file(values["FileLoad"]):
                window_main["Preset"].update(values=list(signal_preset_dict.keys()))
        elif event == "FileSave":
            save_preset_file(values["FileSave"])
        elif event == "Add":
            sig_opt = read_signal_options(values)
            name = values["Preset"]
            signal_preset_dict[name] = sig_opt
            window_main["Preset"].update(values=list(signal_preset_dict.keys()))
            print_log(f"Added {name} to Presets")
        elif event == "Help":
            pass

        elif event in (
            "Queuemode",
            "key-q",
        ):  # Button to toggle the Queuemode and Send Signals in Queuemode
            if window_main["Queuemode"].get_text() == "Send":
                queuemode = False
                set_buttons(["Queuemode"], text="Queuemode")
                set_buttons(["IF", "Timer"])
                print_log("Sending Queued Signals", text_color=QUEUEMODE_COLOR)
                asyncio.run_coroutine_threadsafe(send(signalqueue), loop)
            elif window_main["Queuemode"].get_text() == "Queuemode":
                queuemode = True
                set_buttons(["Queuemode"], text="Send")
                set_buttons(["IF", "Timer"], False)
                print_log(
                    "Queuemode: Signals are Queued.Send with Send Button",
                    text_color=QUEUEMODE_COLOR,
                )
            continue
        # Button to Start the If Mode where Reactions to Notifications
        # can be set
        elif event in ("IF", "key-i"):
            if window_main["IF"].get_text() == "If/Then":
                ifmode = True
                set_buttons(["IF"], text="DONE")
                set_buttons(
                    ["Pause", "Count", "Resends", "ResendGap", "Queuemode", "Timer"],
                    False,
                )
                print_log(
                    "IF Mode: Enter the Signal you would like to react to",
                    text_color=IFMODE_COLOR,
                )
            elif window_main["IF"].get_text() == "DONE":
                if if_mode_condition:
                    # remove previos occurrences of the Signal
                    for item in reversed(notilist):
                        if (
                            item.status == if_mode_condition.status
                            and item.stone == if_mode_condition.stone
                            and item.color == if_mode_condition.color
                        ):
                            notilist.remove(item)
                    notilist.append(if_mode_condition)
                    if_mode_condition = None
                ifmode = False
                set_buttons(["IF"], text="If/Then")
                set_buttons(
                    ["Pause", "Count", "Resends", "ResendGap", "Queuemode", "Timer"]
                )
                print_log("If-Mode finished", text_color=IFMODE_COLOR)
            continue
        elif event in ("Timer", "key-t"):  # Button to set the timer signals
            if window_main["Timer"].get_text() == "Timer":
                timer = True
                set_buttons(["Timer"], text="Cancel")
                set_buttons(
                    ["Pause", "Count", "Resends", "ResendGap", "Queuemode", "IF"], False
                )
                print_log(
                    "Timer Mode: Enter the Signal that starts the timer",
                    text_color=TIMER_COLOR,
                )
            elif window_main["Timer"].get_text() == "Cancel":
                timer = False
                start_signal = None
                stop_signal = None
                set_buttons(["Timer"], text="Timer")
                set_buttons(
                    ["Pause", "Count", "Resends", "ResendGap", "Queuemode", "IF"]
                )
                print_log("Timer stopped", text_color=TIMER_COLOR)
            continue
        # A Signal Button was pressed
        elif event in (
            "Red",
            "Green",
            "Blue",
            "Lock",
            "Unlock",
        ):
            sig_opt = read_signal_options(values)
            resends = sig_opt.resends
            resend_gap = sig_opt.resend_gap

            if event in ("Red", "Green", "Blue"):  # Signal Button pressed
                color = ["Red", "Green", "Blue"].index(event) + 1
                status = sig_opt.status
                stone = sig_opt.stone
                count = sig_opt.count
                pause = sig_opt.pause

            if event in ("Lock", "Unlock"):  # Lock Button Pressed
                color = 1
                stone = 6
                count = 1
                pause = 0
                if event in ("Lock"):
                    status = 201
                else:
                    status = 200

            # Read names of Color,Status,Stone from Lookup tables for the log window output
            try:
                color_name = gv.LOOKUP_COLOR[color]
            except IndexError:
                color_name = f"Color {color}"
            try:
                stone_name = gv.DICT_VAL_STONE[stone]
            except KeyError:
                stone_name = f"Stone {stone}"
            try:
                status_name = gv.DICT_VAL_STATUS[status]
            except KeyError:
                status_name = f"{status}"

            if color_name in ["red", "green", "blue"]:
                sig_log_color = color_name
            else:
                sig_log_color = None

            # Send or store the pressed signal
            if queuemode:
                signalqueue.put(
                    SignalTuple(
                        color=color,
                        status=status,
                        stone=stone,
                        count=count,
                        resends=resends,
                        resend_gap=resend_gap,
                        pause=pause,
                    )
                )

                print_log(
                    f"Added to Queue: {count} x", text_color=QUEUEMODE_COLOR, end=" "
                )
                print_log(
                    f"{color_name}",
                    add_timestamp=False,
                    text_color=sig_log_color,
                    end=" ",
                )
                print_log(
                    f"as {stone_name} (Status: {status_name}, Pause: {pause}s)",
                    add_timestamp=False,
                    text_color=QUEUEMODE_COLOR,
                )

            elif ifmode and if_mode_condition:
                if_mode_condition.actionlist.append(
                    SignalTuple(
                        color=color,
                        status=status,
                        stone=stone,
                        count=count,
                        resends=resends,
                        resend_gap=resend_gap,
                        pause=pause,
                    )
                )
                print_log(f"Added to THEN: {count} x", text_color=IFMODE_COLOR, end=" ")
                print_log(
                    f"{color_name}",
                    add_timestamp=False,
                    text_color=sig_log_color,
                    end=" ",
                )
                print_log(
                    f"as {stone_name} (Status: {status_name}, Pause: {pause}s)",
                    add_timestamp=False,
                    text_color=IFMODE_COLOR,
                )

            elif ifmode:
                if_mode_condition = TriggerSignal(
                    color=color,
                    status=status,
                    stone=stone,
                    actionlist=[],
                )
                print_log(f"Condition Set: Color", text_color=IFMODE_COLOR, end=" ")
                print_log(
                    f"{color_name}",
                    add_timestamp=False,
                    text_color=sig_log_color,
                    end=" ",
                )
                print_log(
                    f"from {stone_name} with Status {status_name}.",
                    add_timestamp=False,
                    text_color=IFMODE_COLOR,
                )
                print_log(
                    "Queue Signals now. Press Done when finished",
                    text_color=IFMODE_COLOR,
                )
                set_buttons(["Count", "Pause", "Resends", "ResendGap"])
            elif timer and not start_signal:
                start_signal = TriggerSignal(
                    color=color, status=status, stone=stone, actionlist=None
                )
                print_log(f"Timer Start Signal: ", text_color=TIMER_COLOR, end=" ")
                print_log(
                    f"{color_name}",
                    add_timestamp=False,
                    text_color=sig_log_color,
                    end=" ",
                )
                print_log(
                    f"from {stone_name} with Status {status_name}.",
                    add_timestamp=False,
                    text_color=TIMER_COLOR,
                )
                print_log("What signal should stop the timer?", text_color=TIMER_COLOR)
            elif timer and not stop_signal:
                stop_signal = TriggerSignal(
                    color=color, status=status, stone=stone, actionlist=None
                )

                print_log(f"Timer Stop Signal: ", text_color=TIMER_COLOR, end=" ")
                print_log(
                    f"{color_name}",
                    add_timestamp=False,
                    text_color=sig_log_color,
                    end=" ",
                )
                print_log(
                    f"from {stone_name} with Status {status_name}.",
                    add_timestamp=False,
                    text_color=TIMER_COLOR,
                )
                set_buttons(
                    ["Pause", "Count", "Resends", "ResendGap", "Queuemode", "IF"]
                )
            else:
                print_log(
                    f"{count} x Sending {color_name} as {stone_name} "
                    f"(Status: {status_name}, Pause: {pause}s)",
                    text_color=sig_log_color,
                )

                asyncio.run_coroutine_threadsafe(
                    send_signals(
                        status, color, stone, count, resends, resend_gap, pause
                    ),
                    loop,
                )
        else:
            gb.log_print(f"Unhandled Event: {event}", level="WARNING")
    asyncio.run_coroutine_threadsafe(shutdown(), loop)
    gb.log_print("GUI Worker stopped", level="DEBUG")


async def shutdown():
    """Coroutine that can be scheduled from other threads to close the asyncthread"""
    finished_event.set()


async def asyncthread():
    """Thread that runs an asyncio Event Loop
    This thread is used to run asyncio coroutines scheduled from other Threads.
    In this application it's exclusively used for the Bluetooth communication with the bridge
    """
    global loop, finished_event
    loop = asyncio.get_running_loop()
    try:
        finished_event = asyncio.Event()
    except TypeError:
        # To use with older versions add the deprecated loop parameter to the Event
        # not all functions of gravitraxconnect work with older
        gb.log_print("Please install Python 3.10 or newer to use this program")
        return
    startup_event.set()
    await finished_event.wait()
    gb.log_print("Async Thread closed", level="DEBUG")


def main():
    """
    The Main thread is used to:
    1) Load the Configuration for the UI-Elements
    2) Load the Layout for the main window
    3) Map Keyboard buttons to the GUI-Buttons
    4) Start the Log Window
    5) Read the inputs from the GUI and put them in the eventqueue for the gui_worker_thread
    """
    global window_main, window_help, window_log, signal_preset_dict, loop

    # Configuration of the PySimpleGUI Elements
    headline = sg.Text(
        "Gravitrax Connect",
        background_color=BACKGROUND_COLOR,
        text_color=UI_TEXT_COLOR,
        font=FONT_H1,
    )

    button_help = sg.Button(
        "Help",
        size=(7, 1),
        disabled=False,
        button_color=BUTTON_COLOR,
        font=FONT_BUTTON,
        # Tooltips are disabled for now as they cause issues with the detection
        # of button presses (https://github.com/PySimpleGUI/PySimpleGUI/issues/5036)
        # tooltip="Display a manual how to use the application",
    )

    ## Signal Buttons
    button_red = sg.Button(
        "Red",
        button_color="red",
        size=(7, 1),
        disabled=True,
        font=FONT_BUTTON,
        # Tooltips are disabled for now as they cause issues with the detection
        # of button presses (https://github.com/PySimpleGUI/PySimpleGUI/issues/5036)
        # tooltip="Send a Red Signal with the set parameters",
    )
    button_green = sg.Button(
        "Green",
        button_color="green",
        size=(7, 1),
        disabled=True,
        font=FONT_BUTTON,
        # Tooltips are disabled for now as they cause issues with the detection
        # of button presses (https://github.com/PySimpleGUI/PySimpleGUI/issues/5036)
        # tooltip="Send a Green Signal with the set parameters",
    )
    button_blue = sg.Button(
        "Blue",
        button_color="blue",
        size=(7, 1),
        disabled=True,
        font=FONT_BUTTON,
        # Tooltips are disabled for now as they cause issues with the detection
        # of button presses (https://github.com/PySimpleGUI/PySimpleGUI/issues/5036)
        # tooltip="Send a Blue Signal with the set parameters",
    )
    button_lock = sg.Button(
        "Lock",
        size=(7, 1),
        disabled=True,
        button_color=BUTTON_COLOR,
        font=FONT_BUTTON,
        # Tooltips are disabled for now as they cause issues with the detection
        # of button presses (https://github.com/PySimpleGUI/PySimpleGUI/issues/5036)
        # tooltip="Send a Signal that makes receiving stones ignore signals not from a Bridge",
    )
    button_unlock = sg.Button(
        "Unlock",
        size=(7, 1),
        disabled=True,
        button_color=BUTTON_COLOR,
        font=FONT_BUTTON,
        # Tooltips are disabled for now as they cause issues with the detection
        # of button presses (https://github.com/PySimpleGUI/PySimpleGUI/issues/5036)
        # tooltip="Send a Signal that makes receiving stones accept all Signals",
    )
    signal_buttons = sg.Frame(
        "Signal Buttons",
        title_color=UI_TEXT_COLOR,
        title_location="n",
        relief=RELIEF,
        font=FONT_H2,
        border_width=1,
        background_color=BACKGROUND_COLOR,
        expand_x=True,
        element_justification="center",
        layout=[[button_lock, button_red, button_green, button_blue, button_unlock]],
    )

    ## Mode Buttons
    button_timer = sg.Button(
        "Timer",
        size=(10, 1),
        disabled=True,
        expand_x=True,
        button_color=BUTTON_COLOR,
        font=FONT_BUTTON,
        # Tooltips are disabled for now as they cause issues with the detection
        # of button presses (https://github.com/PySimpleGUI/PySimpleGUI/issues/5036)
        # tooltip="Measure time between 2 Signals",
    )

    button_if = sg.Button(
        key="IF",
        button_text="If/Then",
        size=(10, 1),
        disabled=True,
        expand_x=True,
        button_color=BUTTON_COLOR,
        font=FONT_BUTTON,
        # Tooltips are disabled for now as they cause issues with the detection
        # of button presses (https://github.com/PySimpleGUI/PySimpleGUI/issues/5036)
        # tooltip="Configure Signals that are send when a specific Signal is received",
    )
    button_queue = sg.Button(
        "Queuemode",
        size=(10, 1),
        disabled=True,
        expand_x=True,
        button_color=BUTTON_COLOR,
        font=FONT_BUTTON,
        # Tooltips are disabled for now as they cause issues with the detection
        # of button presses (https://github.com/PySimpleGUI/PySimpleGUI/issues/5036)
        # tooltip="Queue Signals",
    )

    mode_buttons = sg.Frame(
        "Mode Buttons",
        title_location="n",
        relief=RELIEF,
        font=FONT_H2,
        border_width=1,
        layout=[[button_timer, button_if, button_queue]],
        title_color=UI_TEXT_COLOR,
        expand_x=True,
        background_color=BACKGROUND_COLOR,
    )

    ## Connection Buttons
    button_connect = sg.Button(
        "Connect",
        size=(10, 1),
        disabled=False,
        expand_x=True,
        focus=True,
        button_color=BUTTON_COLOR,
        font=FONT_BUTTON,
        # Tooltips are disabled for now as they cause issues with the detection
        # of button presses (https://github.com/PySimpleGUI/PySimpleGUI/issues/5036)
        # tooltip="Connect to a Bridge",
    )
    button_quit = sg.Button(
        "Quit",
        size=(10, 1),
        expand_x=True,
        button_color=BUTTON_COLOR,
        font=FONT_BUTTON,
        # Tooltips are disabled for now as they cause issues with the detection
        # of button presses (https://github.com/PySimpleGUI/PySimpleGUI/issues/5036)
        # tooltip="Exit the program or disconnect the Bridge",
    )
    connection_buttons = sg.Frame(
        "Connection Buttons",
        title_location="n",
        relief=RELIEF,
        font=FONT_H2,
        border_width=1,
        layout=[[button_connect, button_quit]],
        title_color=UI_TEXT_COLOR,
        expand_x=True,
        background_color=BACKGROUND_COLOR,
    )

    ## signal options
    combo_status = [
        sg.Text(
            text="Status:",
            size=(10, 1),
            background_color=BACKGROUND_COLOR,
            text_color=UI_TEXT_COLOR,
        ),
        sg.Combo(
            key="StatusCombo",
            default_value=DEFAULT_STATUS[0],
            values=list(gv.DICT_STATUS.keys()),
            size=(25, 1),
            # Tooltips are disabled for now as they cause issues with the detection
            # of button presses (https://github.com/PySimpleGUI/PySimpleGUI/issues/5036)
            # tooltip="The value the Status-ID field of the Signal is set to(usually "
            # "\nwhich stonetype should accept the signal)",
            expand_x=True,
        ),
    ]
    combo_stone = [
        sg.Text(
            text="Stone:",
            size=(10, 1),
            background_color=BACKGROUND_COLOR,
            text_color=UI_TEXT_COLOR,
        ),
        sg.Combo(
            key="StoneCombo",
            default_value=DEFAULT_STONE[0],
            values=list(gv.DICT_STONE.keys()),
            # Tooltips are disabled for now as they cause issues with the detection
            # of button presses (https://github.com/PySimpleGUI/PySimpleGUI/issues/5036)
            # tooltip="The value the Stonetype-ID field of the Signal is set to(Stone "
            # "\nfrom which the signal originates)",
            expand_x=True,
        ),
    ]
    combo_count = [
        sg.Text(
            text="Count:",
            size=(10, 1),
            background_color=BACKGROUND_COLOR,
            text_color=UI_TEXT_COLOR,
        ),
        sg.Combo(
            key="Count",
            default_value=DEFAULT_COUNT,
            values=[0, 1, 2, 3, 5, 7, 10, 20, 50, 100, 500, 1000],
            # Tooltips are disabled for now as they cause issues with the detection
            # of button presses (https://github.com/PySimpleGUI/PySimpleGUI/issues/5036)
            # tooltip="How often the Signal should be send",
            expand_x=True,
        ),
    ]
    combo_resends = [
        sg.Text(
            text="Resends:",
            size=(10, 1),
            background_color=BACKGROUND_COLOR,
            text_color=UI_TEXT_COLOR,
        ),
        sg.Combo(
            key="Resends",
            default_value=DEFAULT_RESENDS,
            values=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
            # Tooltips are disabled for now as they cause issues with the detection
            # of button presses (https://github.com/PySimpleGUI/PySimpleGUI/issues/5036)
            # tooltip="How often the same signal should be retransmitted.",
            expand_x=True,
        ),
    ]
    combo_resend_gap = [
        sg.Text(
            text="Resend Gap:",
            size=(10, 1),
            background_color=BACKGROUND_COLOR,
            text_color=UI_TEXT_COLOR,
        ),
        sg.Combo(
            key="ResendGap",
            default_value=DEFAULT_RESEND_GAP,
            values=[0, 0.01, 0.02, 0.03, 0.05, 0.1, 1],
            # Tooltips are disabled for now as they cause issues with the detection
            # of button presses (https://github.com/PySimpleGUI/PySimpleGUI/issues/5036)
            # tooltip="Wait time in Seconds after every resend.",
            expand_x=True,
        ),
    ]
    combo_pause = [
        sg.Text(
            text="Pause:",
            size=(10, 1),
            background_color=BACKGROUND_COLOR,
            text_color=UI_TEXT_COLOR,
        ),
        sg.Combo(
            key="Pause",
            default_value=DEFAULT_PAUSE,
            values=[0.1, 0.2, 0.3, 0.4, 0.5, 1, 2, 5, 10, 20, 30],
            expand_x=True,
            # Tooltips are disabled for now as they cause issues with the detection
            # of button presses (https://github.com/PySimpleGUI/PySimpleGUI/issues/5036)
            # tooltip="Wait time in Seconds that can be added after a Signal \nin Queuemode",
        ),
    ]

    combo_presets = [
        sg.Text(
            text="Presets:",
            size=(10, 1),
            background_color=BACKGROUND_COLOR,
            text_color=UI_TEXT_COLOR,
        ),
        sg.Combo(
            key="Preset",
            default_value=DEFAULT_PRESET,
            values=list(signal_preset_dict.keys()),
            expand_x=True,
            enable_events=True
            # Tooltips are disabled for now as they cause issues with the detection
            #  of button presses (https://github.com/PySimpleGUI/PySimpleGUI/issues/5036)
            # tooltip="Wait time in Seconds that can be added after a Signal \nin Queuemode",
        ),
    ]

    button_reset = sg.Button(
        "Reset",
        disabled=False,
        button_color=BUTTON_COLOR,
        font=FONT_BUTTON,
        expand_x=True,
        # pad=((5,5),(10,10)),
    )

    button_preset_add = sg.Button(
        "Add",
        disabled=False,
        button_color=BUTTON_COLOR,
        font=FONT_BUTTON,
        expand_x=True,
        # pad=((5,5),(10,10)),
    )

    # Dummy Inputs that get passed the filename of the filebrowsers that follow
    # and trigger an event. The name of the file is in the values for the event
    file_load = sg.Input(key="FileLoad", visible=False, enable_events=True)
    file_save = sg.Input(key="FileSave", visible=False, enable_events=True)

    button_preset_load = sg.FileBrowse(
        target="FileLoad",
        button_text="Load Presets",
        key="LoadPreset",
        disabled=False,
        button_color=BUTTON_COLOR,
        font=FONT_BUTTON,
        # pad=((5,5),(10,10)),
        file_types=[("ALL Files", ".json")],
    )

    button_preset_save = sg.SaveAs(
        target="FileSave",
        button_text="Save Presets",
        key="SavePreset",
        # pad=((5,5),(10,10)),
        disabled=False,
        button_color=BUTTON_COLOR,
        font=FONT_BUTTON,
        file_types=[("ALL Files", ".json")],
    )

    signal_options = sg.Frame(
        "Signal Options",
        title_color=UI_TEXT_COLOR,
        title_location="n",
        relief=RELIEF,
        font=FONT_H2,
        border_width=1,
        background_color=BACKGROUND_COLOR,
        element_justification="c",
        expand_x=True,
        layout=[
            combo_status,
            combo_stone,
            combo_count,
            combo_resends,
            combo_resend_gap,
            combo_pause,
            combo_presets,
            [sg.HorizontalSeparator()],
            [
                file_save,
                file_load,
                button_reset,
                button_preset_add,
                button_preset_save,
                button_preset_load,
            ],
        ],
    )

    layout = [
        [
            sg.Column(
                layout=[[headline]],
                justification="l",
                expand_x=True,
                background_color=BACKGROUND_COLOR,
            ),
            sg.Column(
                layout=[[button_help]],
                justification="r",
                background_color=BACKGROUND_COLOR,
            ),
        ],
        [signal_options],
        [signal_buttons],
        [mode_buttons],
        [connection_buttons],
    ]

    window_main = sg.Window(
        "Gravitrax Connect",
        layout,
        background_color=BACKGROUND_COLOR,
        font=FONT_TEXT,
        element_justification="l",
        resizable=False,
        finalize=True,
        sbar_background_color=SCROLLBAR_COLOR,
        # location =(0,0),
    )

    # Mapping of Keyboard buttons to GUI-Buttons
    window_main.bind("<F1>", "Red")
    window_main.bind("<F2>", "Green")
    window_main.bind("<F3>", "Blue")
    window_main.bind("<F4>", "Lock")
    window_main.bind("<F5>", "Unlock")
    window_main.bind("<F6>", "Timer")
    window_main.bind("<F7>", "IF")
    window_main.bind("<F8>", "Queuemode")

    # Seperate resizable Window for the Log Output
    window_log = make_log_window()
    window_main.force_focus()
    gb.log_print("Waiting for asyncio Loop to start", level="DEBUG")
    startup_event.wait()
    gb.log_print("Asyncio Loop started.", level="DEBUG")
    asyncio.run_coroutine_threadsafe(connect(), loop)
    print_log("Trying to connect to Gravitrax Connect")
    run_gui()


if __name__ == "__main__":
    # Thread to run Asyncio corutines for bluetooth communication
    Thread(target=asyncio.run, args=[asyncthread()]).start()
    # Thread to work off the queued commands from the GUI
    Thread(target=gui_worker_thread).start()
    main()  # initialize and run the GUI
