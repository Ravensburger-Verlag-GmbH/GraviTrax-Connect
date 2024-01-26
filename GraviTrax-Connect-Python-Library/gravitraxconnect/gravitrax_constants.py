"""Constant values used for the gravitraxconnect library
    This file contains parameters for the Bluetooth Communication and 
    other constant values. It is recommended to use these values 
    in your programs for improved readability and maintainability.
"""

# Default Name of Bridge
BRIDGE_NAME = "GravitraxConnect"

# UUIDs to communicate with the Bridge
UUID_WRITE = "0000ff02-0000-1000-8000-00805f9b34fb"
UUID_BATTERY = "00002a19-0000-1000-8000-00805f9b34fb"
UUID_NAME = "00002a00-0000-1000-8000-00805f9b34fb"
UUID_NOTIF = "0000ff03-0000-1000-8000-00805f9b34fb"

# Handles to Communicate with the Bridge
HANDLE_WRITE = "0xc"
HANDLE_BATTERY = "0x6"
HANDLE_NOT_CONFIG = "0xf"

# Default protocol fields for Messages
MSG_DEFAULT_HEADER = 19
MSG_DEFAULT_TYPE = 6

# Color Values for Messages
COLOR_RED = 1
COLOR_GREEN = 2
COLOR_BLUE = 3

LOOKUP_COLOR = ["reserved0", "red", "green", "blue"]

# Status values for Messages
STATUS_ALL = 0
STATUS_STARTER = 1
STATUS_SWITCH = 2
STATUS_BRIDGE = 3
STATUS_SOUND = 4
STATUS_LEVER = 6
STATUS_UNLOCK = 200
STATUS_LOCK = 201
STATUS_STARTER_PRESS = 202

DICT_STATUS = {
    "ALL": STATUS_ALL,
    "STARTER": STATUS_STARTER,
    "SWITCH": STATUS_SWITCH,
    "BRIDGE": STATUS_BRIDGE,
    "SOUND": STATUS_SOUND,
    "LEVER": STATUS_LEVER,
    "UNLOCK": STATUS_UNLOCK,
    "LOCK": STATUS_LOCK,
    "STARTER_PRESS": STATUS_STARTER_PRESS,
}

DICT_VAL_STATUS = {
    STATUS_ALL: "ALL",
    STATUS_STARTER: "STARTER",
    STATUS_SWITCH: "SWITCH",
    STATUS_BRIDGE: "BRIDGE",
    STATUS_SOUND: "SOUND",
    STATUS_LEVER: "LEVER",
    STATUS_UNLOCK: "UNLOCK",
    STATUS_LOCK: "LOCK",
    STATUS_STARTER_PRESS: "STARTER_PRESS",
}

# Stone values for Messages
STONE_TRIGGER = 1
STONE_FINISH = 2
STONE_STARTER = 4
STONE_CONTROLLER = 5
STONE_BRIDGE = 6

DICT_STONE = {
    "trigger": STONE_TRIGGER,
    "finish": STONE_FINISH,
    "starter": STONE_STARTER,
    "controller": STONE_CONTROLLER,
    "bridge": STONE_BRIDGE,
}

DICT_VAL_STONE = {
    STONE_TRIGGER: "trigger",
    STONE_FINISH: "finish",
    STONE_STARTER: "starter",
    STONE_CONTROLLER: "controller",
    STONE_BRIDGE: "bridge",
}

LOOKUP_BATTERYSTRINGS = [
    "Battery is empty.",
    "Battery level is low",
    "Battery level is medium",
    "Battery level is high",
    "Battery is full",
]
LOOKUP_BATTERYVALUES = [64, 96, 128, 160, 100]  # <2V  # 2V-2.5V  # 2.5V-3V  # 3V  # 3V+

DICT_BATTERYVALUES = {
    64:2,
    96:2.5,
    128:2.9,
    160:3,
    100:3.1,
}

DICT_BATTERYSTRINGS = {
    2:"Battery is empty.",
    2.5:"Battery level is low",
    2.9:"Battery level is medium",
    3:"Battery level is high",
    3.1:"Battery is full",
}
