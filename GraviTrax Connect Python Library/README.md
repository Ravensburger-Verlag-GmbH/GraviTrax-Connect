# Gravitrax Connect Python Library

This Python Library is used to communicate with a Gravitrax Bluetooth Connect stone, a BLE Device that is capable of controlling Gravitrax Power stones. This Library imports the [bleak BLE-Library](https://github.com/hbldh/bleak) and should be compatible with all platforms it supports.

- [Gravitrax Connect Python Library](#gravitrax-connect-python-library)
- [Features](#features)
- [Manual installation](#manual-installation)
- [Dependencies](#dependencies)
  - [Windows](#windows)
  - [Linux / Raspberry Pi](#linux--raspberry-pi)
  - [Python packages](#python-packages)
- [Usage](#usage)
- [Licence](#licence)

# Features
The Library supports the following features:

- [Receiving Signals](./docs/How%20to%20use%20the%20GravitraxConnect%20Library.md#notifications) ( [Example](./examples/example_notification.py) ) from supported Gravitrax Power Stones. The Library detects the Status and Color of the Signal, as well as the type of Stone that send the Signal. It's possible to define a custom callback function that is executed when a signal is received. 
- [Sending Signals](./docs/How%20to%20use%20the%20GravitraxConnect%20Library.md#sending-signals) to Gravitrax Power Stones. 
    - Send signals to specific stone types, for example to all green Switches.
    - Send signals to all stones that have a certain color. ( [Example](./examples/example_signals.py) )
    - Send Signals as a specific Stone
    - Send signals as a reaction to a received Signal. ( [Example](./examples/example_signal_repeater.py) )
    - Send arbitrary bytes of data ( [Example](./examples/example_send_bytes.py) )
- [Read out Information](./docs/How%20to%20use%20the%20GravitraxConnect%20Library.md#getting-information-about-the-bridge) ( [Example](./examples/example_bridge_infos.py) ) about the Bridge ( Battery Level, Firmware Version, etc. )
- [Bridge only mode](./docs/How%20to%20use%20the%20GravitraxConnect%20Library.md#bridge-mode): Stones in this mode will ignore all signals that are not from a bridge
- Display [logging](./docs/How%20to%20use%20the%20GravitraxConnect%20Library.md#logging) information about ongoing operations.

A more detailed overview of the features this Library supports can be found in [How to use the Gravitrax Connect Library](./docs/How%20to%20use%20the%20GravitraxConnect%20Library.md), and working examples using this Library in the [examples](./examples/) folder.

# Manual installation 

Download the package and unzip it. Navigate to the folder where the pyproject.toml file is located and run the following command:
```bash
    pip install .
```
Sometimes necessary to specify that python3 should be used. In this case, use the Command:
```bash
    pip3 install .
```
This should also install all necessary dependencies. If this is not the case, please install the missing [Dependencies](#python-packages) manually.

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

A detailed explanation on how to use this Library can be found in the [How to use the GravitraxConnect Library](docs/How%20to%20use%20the%20GravitraxConnect%20Library.md) File.

# Licence
MIT License

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
