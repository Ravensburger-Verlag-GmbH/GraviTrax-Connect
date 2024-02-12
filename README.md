[![de](https://img.shields.io/badge/Installationsanleitung-deutsch-red.svg)](./README.de.md)

# GraviTrax Connect Python Library

This Python library is used to communicate with a GraviTrax Bluetooth Connect stone, a BLE device that is capable of controlling Gravitrax POWER RF stones. This library imports the [bleak BLE-Library](https://github.com/hbldh/bleak) and should be compatible with all platforms it supports.

- [Gravitrax Connect Python Library](#gravitrax-connect-python-library)
- [Features](#features)
- [Manual installation](#manual-installation)
  - [Installing python](#installing-python)
  - [Installing GraviTrax connect library](#installing-gravitrax-connect-library)
  - [Example programs](#example-programs)
- [Dependencies](#dependencies)
  - [Windows](#windows)
  - [Linux / Raspberry Pi](#linux--raspberry-pi)
  - [Python packages](#python-packages)
- [Usage](#usage)

# Features
The library supports the following features:

- [Receiving signals](GraviTrax%20Connect%20Python%20Library/docs/How%20to%20use%20the%20GravitraxConnect%20Library.md#notifications) ( [Example](GraviTrax%20Connect%20Python%20Library/examples/example_notification.py) ) from supported Gravitrax Power stones. The library detects the status and color of the signal, as well as the type of stone that sends the signal. It's possible to define a custom callback function that is executed when a signal is received. 
- [Sending Signals](GraviTrax%20Connect%20Python%20Library/docs/How%20to%20use%20the%20GravitraxConnect%20Library.md#sending-signals) to Gravitrax Power Stones. 
    - Send signals to specific stone types, for example, to all green switches.
    - Send signals to all stones that have a certain color. ( [Example](GraviTrax%20Connect%20Python%20Library/examples/example_signals.py) )
    - Send signals as a specific Stone
    - Send signals as a reaction to a received signal. ( [Example](GraviTrax%20Connect%20Python%20Library/examples/example_signal_repeater.py) )
    - Send arbitrary bytes of data ( [Example](GraviTrax%20Connect%20Python%20Library/examples/example_send_bytes.py) )
- [Read out information](GraviTrax%20Connect%20Python%20Library/docs/How%20to%20use%20the%20GravitraxConnect%20Library.md#getting-information-about-the-bridge) ( [Example](GraviTrax%20Connect%20Python%20Library/examples/example_bridge_infos.py) ) about the Bridge ( Battery Level, Firmware Version, etc. )
- [Bridge only mode](GraviTrax%20Connect%20Python%20Library/docs/How%20to%20use%20the%20GravitraxConnect%20Library.md#bridge-mode): Stones in this mode will ignore all signals that are not from a bridge
- Display [logging](GraviTrax%20Connect%20Python%20Library/docs/How%20to%20use%20the%20GravitraxConnect%20Library.md#logging) information about ongoing operations.

A more detailed overview of the features this library supports can be found in [How to use the Gravitrax Connect Library](GraviTrax%20Connect%20Python%20Library/docs/How%20to%20use%20the%20GravitraxConnect%20Library.md), and working examples using this library in the [examples](GraviTrax%20Connect%20Python%20Library/examples/) folder.

# Manual installation 
## Installing Python

Please use Python version 3.1 or newer. Otherwis,e not all functions will work properly. There are several ways to install it:

### Using python.org
You can find the latest version at https://www.python.org/downloads/. During installation, check the “Add Python to Path” box.

### Using Microsoft Store

Alternatively, you can install it using the Microsoft Store. [Here is the latest version](https://www.microsoft.com/store/productId/9NRWMJP3717K). 

Check if the installation was successful by using the command line center with the following commands:

```shell
python -V 
```
and 
```shell
pip -V
```
It should print the installed version number.

## Installing GraviTrax Connect library

1. Download the code as a zip file.

2. Navigate to the download directory, unpack the "GraviTrax-Connect-main.zip" zip file and move it to the desired target folder.

3. Navigate to the library folder and copy the path. It could look like this: "C:\Users\Username\Downloads\GraviTrax-Connect-main\GraviTrax-Connect-Python-Library".

4. Open the Windows command prompt.

5. Install the library using the following command:

```shell
pip install <copied path>
```

Alternatively, you can use these two commands:

```shell
cd <copied path>
```
to navigate to the folder including the pyproject.toml. For installing, use this command afterward:
```shell
pip install . 
```
Check if installation was successful by typing:
```shell
pip list
``` 
You should see the gravitraxconnect library as well as the bleak BLE library listed.
If it didn’t work, try again by using the following command. You need an internet connection.
```
pip install bleak
```

## example programs
the library folder contains a folder "examples". Here you can find scripts showing basic functions.

More complex applications can be found in the folder "Applications".
To use the example applications, you will need to install some more libraries. Therefore, navigate with the command line center to corresponding directory and use the following command:
```shell
pip install -r .\requirements.txt
``` 
- Gravitrax_CLI: command line tool to send and receive signals
- Gravitrax_GUI: GUI to send and receive signals
- Gravitrax_gpio: a script implementing the GPIO-Pins from a Raspberry Pi
- Timer: a script measuring the time between start and finish of a marble

# Dependencies

## Windows
- Windows 10 1709 (October 17, 2017) or newer
- python 3.10 or newer

## Linux / Raspberry Pi
- BlueZ 5.43 or newer(Tested with 5.55-3.1+rpt2)
- python 3.10 or newer

## Python packages
|Package|Tested with Version|installation command*|Link|
|---|---|---|---|
|bleak|0.19.5|pip3 install bleak|[pypi.org](https://pypi.org/project/bleak/)|


The dependencies should be downloaded automatically during the installation of gravitraxconnect.    

# Usage

A detailed explanation of how to use this library can be found in the [How to use the GravitraxConnect Library](GraviTrax%20Connect%20Python%20Library/docs/How%20to%20use%20the%20GravitraxConnect%20Library.md) File.
