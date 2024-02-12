# How to use the Gravitrax Connect Library

This Library uses the `asyncio` framework to allow the asynchronous execution of functions. 
Because most methods of the `gravitrax_bridge.Bridge` class are [asyncio coroutines](https://docs.python.org/3/library/asyncio-task.html#coroutines) they need to be started inside an asynchronous function itself.
This is achieved by putting the keyword `async` in font of the main function and running it with `asyncio.run()` afterwards. 

```python
import asyncio

async def main():
    # Add your Code here

if __name__ == "__main__":
    asyncio.run(main())
```
All async methods from gravitraxconnect need to be prefixed with the keyword `await`. 
More information about asyncio can be found in [the asyncio documentation](https://docs.python.org/3/library/asyncio.html). 
A basic program that simply connects to a bridge looks as follows: 

```python
import asyncio
from gravitraxconnect import gravitrax_bridge as gb

bridge = gb.Bridge()

async def main():
    await bridge.connect()

if __name__ == "__main__":
    asyncio.run(main())
```
The gravitrax_constants module can be imported to provide access to frequently used data like Statuscodes, Stonetypes and Color Values. 
Although optional, it's still recommended to use it as it future proofs your programs against potential changes and improves readability.

# Table of Content
- [How to use the Gravitrax Connect Library](#how-to-use-the-gravitrax-connect-library)
- [Table of Content](#table-of-content)
- [Connecting and disconnecting from a Bridge](#connecting-and-disconnecting-from-a-bridge)
  - [connect()](#connect)
  - [is\_connected()](#is_connected)
  - [disconnect()](#disconnect)
  - [Handling Disconnects](#handling-disconnects)
- [Sending Signals](#sending-signals)
  - [send\_signal()](#send_signal)
  - [send\_periodic()](#send_periodic)
  - [send\_bytes()](#send_bytes)
- [Bridge Mode](#bridge-mode)
  - [start\_bridge\_mode()](#start_bridge_mode)
  - [stop\_bridge\_mode()](#stop_bridge_mode)
- [Notifications](#notifications)
  - [notification\_enable()](#notification_enable)
  - [notification\_disable()](#notification_disable)
- [Getting Information about the Bridge](#getting-information-about-the-bridge)
  - [Battery Level](#battery-level)
    - [request\_battery()](#request_battery)
    - [request\_battery\_string()](#request_battery_string)
  - [request\_bridge\_info()](#request_bridge_info)
  - [get\_address()](#get_address)
  - [get\_name()](#get_name)
  - [print\_services()](#print_services)
- [Logging](#logging)
  - [log\_print()](#log_print)
  - [log\_set\_level()](#log_set_level)
- [Additional Utility methods](#additional-utility-methods)
  - [scan\_bridges()](#scan_bridges)
  - [calc\_checksum()](#calc_checksum)
  - [add\_checksum()](#add_checksum)



# Connecting and disconnecting from a Bridge

## connect()

| Argument              | Description                                                                       | Default value                   |
| --------------------- | --------------------------------------------------------------------------------- | ------------------------------- |
| name_or_addr          | The identifier(name or MAC-Address) for the Bridge.                               | gravitrax_constants.BRIDGE_NAME |
| by_name               | Specifies whether name_or_addr is a name(True) or MAC-Address(False)              | True                            |
| timeout               | Maximum allowed Time in seconds for the scan or the connect process               | 25                              |
| dc_callback           | Callback function that is executed when the bridge is disconnected.               | None                            |
| try_reconnect         | Specifies if there should be an attempt to reconnect after the connection is lost | False                           |
| restart_notifications | Specifies if the Notifications should be enabled after a reconnect                | True                            |

| Return Value | Type    | Description                          |
| ------------ | ------- | ------------------------------------ |
| True         | boolean | Successfully connected to the Bridge |
| False        | boolean | Failed to connect to a bridge        |

The [connect()](#connect) method is used to find a Bridge and connect to it. The default behavior is to look for a Bluetooth device with
the name "GravitraxConnect"(can be found in the gravitrax_constants file). When multiple bridges are available, 
the connection will be established with the first one found. It's is possible to change
the name by adjusting the `name_or_addr` argument. This doesn't really make sense as of now because every Bridge uses the name
"GravitraxConnect". 

It's also possible to connect to a specific Bridge by its MAC-Address. In order to do that the `by_name` argument needs to be set to False
and `name_or_addr` must contain the MAC-Address in this format "FF:FF:FF:FF:FF:FF".  

Both connect methods return a boolean value representing whether the connection attempt
was successful. 

```python
    # Connect by MAC-Address
    if not await b.connect(name_or_addr="FF:FF:FF:FF:FF:FF",by_name=False, timeout=10):
        # Connect by Name
        if not await b.connect():
            sys.exit("Could not find a bridge to connect to")
    
    print("Connected to {} ({})".format(b.get_name(), b.get_address()))
```
## is_connected()

| Return Value | Type    | Description                 |
| ------------ | ------- | --------------------------- |
| True         | boolean | Active connection to bridge |
| False        | boolean | Not connected to the bridge |

Returns True if there is an active connection to the bridge.

```python
    while await b.is_connected():
        print("Still connected")
```

## disconnect()
| Argument               | Description                                                                                                                                               | Default value |
| ---------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------- |
| timeout                | Maximum allowed time before the method returns false. The bridge may still disconnect                                                                     | 20            |
| dc_callback_on_timeout | If set to True the [disconnect callback function](#handling-disconnects) is called if the disconnect takes longer than specified in the timeout parameter | False         |
| _user                  | Used to enable/disable the tracking if a disconnect was made intentional by the user or not.                                                              | True          |

| Return Value | Type    | Description                    |
| ------------ | ------- | ------------------------------ |
| True         | boolean | Disconnect was successful      |
| False        | boolean | Disconnect failed or timed out |

The connection to a bridge can be closed by calling `disconnect()`. 
If the bridge is not disconnected after the timeout period, the method returns False. It's also possible to call the [disconnect callback](#handling-disconnects) in this case by setting `dc_callback_on_timeout` to True.
The connection will be closed eventually even if a timeout occurs.

```python
    await b.disconnect(timeout=15, dc_callback_on_timeout=True)
```

## Handling Disconnects
It's possible to specify a custom callback function that is executed when the Bridge is disconnected. The callback has to accept the following Arguments: 
- bridge: the Object of the Bridge that was disconnected 
- **kwargs: 

| Argument          | Description                                                                                                                               | typical values |
| ----------------- | ----------------------------------------------------------------------------------------------------------------------------------------- | -------------- |
| user_disconnected | Indicates if the disconnect was intentional(i.e. [disconnect()](#disconnect()) was called ) or not.                                       | True/False     |
| by_timeout        | If the disconnect callback was called because of a timeout(of [disconnect()](#disconnect()) ) or because the bridge actually disconnected | True/False     |

The callback function can be passed to [connect()](#connect). 
Alternatively, the member variable 'dc_callback' can be accessed directly.
If the `try_reconnect` member variable is set to `True` the callback will try to reestablish an interrupted connection. 
After a successful reconnect the notifications are reenabled by default. This can be changed by setting `restart_notifications` to `False` 

```python
def disconnect_callback(bridge: gb.Bridge, **kwargs):
    if kwargs.get('by_timeout'):
        print(f"({bridge.get_address()}) Disconnect timed out")
    elif kwargs.get('user_disconnected'):
        print(f"({bridge.get_address()}) User Disconnected from Bridge!")
    else:
        print(f"({bridge.get_address()}) Connection to Bridge was interrupted")

def main():
    # Passing the callback as a Argument
    await b.connect(dc_callback=disconnect_callback, try_reconnect = True, restart_notifications = False)
    # Or set directly to the variable
    b.dc_callback = disconnect_callback
```

# Sending Signals
The Library implements multiple ways to send data to the bridge. [send_signal()](#send_signal) can be used to send signals to any receiver Stones (Lever, Starter, Switch, etc.). To send arbitrary data, the [send_bytes](#send_bytes) method can be used. [send_periodic()](#send_periodic) can be used to send multiple signals in a fixed time interval.

## send_signal()

| Argument      | Description                                                                                                                      | Default value                                       |
| ------------- | -------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------- |
| status        | Specifies which Blocks should react to the signal                                                                                |                                                     |
| color_channel | The color value of the signal                                                                                                    |                                                     |
| resends       | How often a Signal is transmitted                                                                                                | 12                                                  |
| resend_gap    | How long the added delay(in seconds) after every transmission(including resends) is                                              | 0                                                   |
| uuid          | The uuid of the Bridge to send the Signals. Should not be changed unless future updates to the Bridge change the uuid for writes | Default value specified in gravitrax_constants file |
| header        | The header of the send signal. Should not be changed unless there are changes to the communications protocol in the future       | Default value specified in gravitrax_constants file |
| stone         | Specifies the Stonetype of the send signal.                                                                                      | Defaults to the value of the Bridge Stone(5)        |
| random_id     | Boolean specifying if the the message_id value should be chosen randomly or incremented with each signal                         | False                                               |
| error_event   | A asyncio.Event that is set when a error happens during the send operation                                                       | None                                                |

The method [send_signal()](#send_signal) is used to send a Signal that is understood by Receiver Stones. The Arguments resend and resend_gap are used to prevent package loss at the cost of a higher delay between transmissions. 
The argument `error_event` can be used to specify a `asyncio.Event` that is set when an error happens during the send process. An example how this can be used can be found in the [send_periodic()](#send_periodic) Method. 

```python
    if await b.send_signal(gv.STATUS_ALL, gv.COLOR_RED, stone=gv.STONE_REMOTE):
        print("Send red Signal")
```

## send_periodic()

| Argument        | Description                                                                         | Default value                                |
| --------------- | ----------------------------------------------------------------------------------- | -------------------------------------------- |
| status          | Specifies which Stones should react to the signal                                   |                                              |
| color_channel   | The color value of the signal                                                       |                                              |
| count           | The amount of signals to send                                                       |                                              |
| gap             | The time in seconds between every transmission                                      | 0                                            |
| resends         | How often a Signal is transmitted                                                   | 12                                           |
| resend_gap      | How long the added delay(in seconds) after every transmission(including resends) is | 0                                            |
| stone           | Specifies the Stonetype of the send signal.                                         | Defaults to the value of the Bridge Stone(5) |
| stop_on_failure | Specifies if the function should stop if a send fails                               | True                                         |

Sends multiple Signals with a fixed time in between.  

```python
    await b.send_periodic(gv.STATUS_ALL, gv.COLOR_RED, count=20, gap=2, stone=gv.STONE_REMOTE):
    print("Sending 20 red Signals")
```

## send_bytes()

| Argument    | Description                                                                                                                      | Default value                                       |
| ----------- | -------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------- |
| data        | The bytes to send to the bridge                                                                                                  |                                                     |
| resends     | How often a Signal is transmitted                                                                                                | 1                                                   |
| resend_gap  | How long the added delay(in seconds) after every transmission(including resends) is                                              | 0                                                   |
| uuid        | The uuid of the Bridge to send the Signals. Should not be changed unless future updates to the Bridge change the uuid for writes | Default value specified in gravitrax_constants file |
| error_event | A asyncio.Event that is set when a error happens during the send operation                                                       | None                                                |

The [send_bytes()]() method can be used to send arbitrary data to the bridge. Doing this usually doesn't make sense because the Bridge only reacts to specific Signals. 
In order to send a correct Signal [send_signal()](#send_signal) is used.  The argument `error_event` can be used to specify a `asyncio.Event` which is set when an error occurs. 
This is used by [send_periodic()](#send_periodic) to stop if an error happens.

```python
    if await b.send_bytes(bytes([1,2,3])):
        print("Send 1,2,3")
```

# Bridge Mode
By using [start_bridge_mode()](#start_bridge_mode) a signal is sent that puts all receiving Stones in a mode where they only accept signals with the Stonetype set to Bridge. To return to normal operation, [stop_bridge_mode()](#stop_bridge_mode) is used. 

## start_bridge_mode()
Send a signal that puts all receiving Stones into Bridge Mode, where all signals not from a Bridge are ignored.

```python
    if await b.start_bridge_mode():
        print("Change to Bridge mode Requested")
```
## stop_bridge_mode()
Send a signal that puts all receiving stones into the normal operation Mode.
```python
    if await b.stop_bridge_mode():
        print("Change to Normal mode Requested")
```

# Notifications

## notification_enable()
| Argument | Description                                                                                                      | Default value                                       |
| -------- | ---------------------------------------------------------------------------------------------------------------- | --------------------------------------------------- |
| callback | A callback function that is executed when a Notification is received                                             |                                                     |
| uuid     | The uuid for Notifications. Should not be changed unless future updates to the Bridge change the uuid for writes | Default value specified in gravitrax_constants file |

| Return Value | Type    | Description                           |
| ------------ | ------- | ------------------------------------- |
| True         | boolean | Enabling Notifications was successful |
| False        | boolean | Enabling Notifications failed         |

Enables Notifications for the Bridge. A Callback function that is executed when a notification is received needs to be specified. 

```python

    async def notification_callback(bridge: gb.Bridge, **signal):
        # add your code here

    if await b.notification_enable(notification_callback):
        print("Notifications enabled")
```
The Arguments for the callback need to be like in the example above. Relevant information about the signal can be accessed from the keyword arguments.

```python

    async def notification_callback(bridge: gb.Bridge, **signal):
        status = signal.get('Status')  
        stone = signal.get('Stone')
        color = signal.get('Color')

    if await b.notification_enable(notification_callback):
        print("Notifications enabled")
```

The following keyword arguments are passed to the callback and can be accessed like above:
| Argument | Description                                                                                     | typical values                        |
| -------- | ----------------------------------------------------------------------------------------------- | ------------------------------------- |
| Header   | The header value. Always set to 19                                                              | 19                                    |
| Stone    | The Type of Stone the Message was send from.                                                    | 1-11                                  |
| Status   | Used to transmit additional Information                                                         | 0-255                                 |
| Reserved | Currently not used. Usually a random value                                                      | 0-255                                 |
| Id       | Id to differentiate consecutive Signals                                                         | 0-255                                 |
| Checksum | the checksum of the Signal                                                                      | 0-255                                 |
| Color    | The Color Channel of the Signal                                                                 | 1,2,3                                 |
| Data     | The raw notification data  | bytearray containing the Data |

A simple program that prints out useful information about a received Notification looks as follows:

```python
async def notification_callback(bridge: gb.Bridge,**signal):
    if signal.get("Header") :
         print(f"New Notification: Stone={signal.get('Stone')}, Color={signal.get('Color')}")
    else:
        print(f"Received Data: {signal.get('Data')}")
       
    
async def main():
    b = gb.Bridge()
    await b.connect()
    await b.notification_enable(notification_callback)
    await asyncio.sleep(15.0)
    await b.notification_disable()

if __name__ == "__main__":
    asyncio.run(main())
```

## notification_disable()
| Argument | Description                                                                                                      | Default value                                       |
| -------- | ---------------------------------------------------------------------------------------------------------------- | --------------------------------------------------- |
| uuid     | The uuid for Notifications. Should not be changed unless future updates to the Bridge change the uuid for writes | Default value specified in gravitrax_constants file |

| Return Value | Type    | Description                            |
| ------------ | ------- | -------------------------------------- |
| True         | boolean | Disabling Notifications was successful |
| False        | boolean | Disabling Notifications failed         |

Disables Notifications for the bridge

```python
        await b.notification_disable()
        print("Notifications disabled")
```

# Getting Information about the Bridge

## Battery Level
The Library implements two ways to get the current battery level of the bridge.
[request_battery()](#request_battery) returns an float value from 2 to 3.1 that represents the approximate
Voltage of the batteries. These values can be interpreted as follows:
| value | Voltage   | Battery String          |
| ----- | --------- | ----------------------- |
| 2     | <2V       | Battery is empty.       |
| 2.5   | 2V - 2,5V | Battery level is low    |
| 2.9   | 2,5V - 3V | Battery level is medium |
| 3     | 3V        | Battery level is high   |
| 3.1   | 3V+       | Battery is full         |

If [request_battery_string()](#request_battery_string) is used, the Strings in the above table are returned instead of voltage values.

### request_battery()
| Return Value | Type  | Description                 |
| ------------ | ----- | --------------------------- |
| 2-3.1        | float | The approx. Battery Voltage |

Returns the approximate battery Voltage

```python
    print(f"Battery level: {await b.request_battery()} V")
```

### request_battery_string()
| Return Value   | Type | Description                          |
| -------------- | ---- | ------------------------------------ |
| Battery String | str  | String for the current battery level |

Returns the approximate Battery level in form of a descriptive String

```python
    print(await b.request_battery_string())  
```

## request_bridge_info()
| Return Value | Type  | Description                                    |
| ------------ | ----- | ---------------------------------------------- |
| (int,int)    | tuple | Tuple containing Firmware and Hardware version |

The Software and Hardware Version of a connected bridge can be read by using the [request_bridge_info()](#request_bridge_info) method. It returns a Tuple containing 2 int values. The first value 
is the current Firmware Version, the second one the Hardware Version. When [request_bridge_info()](#request_bridge_info) is called the Member Variables firmware and hardware are set to the received values.
After successfully [connecting](#connecting-and-disconnecting-from-a-bridge) to a Bridge [request_bridge_infos()](#request_bridge_info) is called automatically so it's usually easier to use the member variables instead of [request_bridge_infos()](#request_battery).

```python
    info = await b.request_bridge_info()
    print(f"Firmware: {info[0]} \n Hardware: {info[1]}")  
    # Output: 
    # Firmware: 16
    # Hardware: 1
    print(f"Firmware: {b.firmware} \n Hardware: {b.hardware}") 
    # Output: 
    # Firmware: 16 
    # Hardware: 1
```

## get_address()
| Return Value   | Type | Description                                               |
| -------------- | ---- | --------------------------------------------------------- |
| address String | str  | The address of the bridge in the format FF:FF:FF:FF:FF:FF |

Returns the MAC-Address of the currently or last connected Bridge.

```python
    print(await b.get_address())  
    # Output: FF:FF:FF:FF:FF:FF
```

## get_name()
| Return Value | Type | Description            |
| ------------ | ---- | ---------------------- |
| name String  | str  | The name of the bridge |

Returns the Device Name of the currently or last connected Bridge.

```python
    print(await b.get_name())  
    # Output: GravitraxConnect
```

## print_services()
Prints out the GATT services of the bridge.

```python
    await b.print_services()
```

# Logging

This library uses a logger from the `logging` module to display status messages.
The logger is disabled by default, but can be enabled like so:

```python
    
async def main():
    gravitrax_bridge.logger.disabled = False
    b = gravitrax_bridge.Bridge()
    await b.connect()
    # Output:
    # (FF:FF:FF:FF:FF:FF) Connected to bridge (MTU:512)
    
if __name__ == "__main__":
    asyncio.run(main())
```
To print your own status messages with this logger, the `log_print()` function can be used.
The `log_set_level()` function can be used to set the level of the logger without importing the logging module in your script.

## log_print()

| Argument | Description                                                                          | Default value |
| -------- | ------------------------------------------------------------------------------------ | ------------- |
| *text    | Arguments to be printed                                                              |               |
| bridge   | bridge object. When passed the address of the bridge is added to the printed message | None          |
| level    | logging level for the message                                                        | 'INFO'        |

Prints out the Arguments using the formatting of the log messages used in the library.

```python
    gravitrax_bridge.log_print(f"A simple log print")
    # Output: 15:42:12.833 - INFO: A simple log print

    gravitrax_bridge.log_print(f"Passing ", 3, " Arguments")
    # Output: 15:42:12.833 - INFO: Passing 3 Arguments
    
    gravitrax_bridge.log_print(f"Connected!",bridge=b)
    # Output: 15:42:16.082 - INFO: (FF:FF:FF:FF:FF:FF) Connected to Bridge!
    
    gravitrax_bridge.log_print(f"Connected!",bridge=b, level='DEBUG')
    #Output: 15:42:16.082 - DEBUG: (FF:FF:FF:FF:FF:FF) Connected to Bridge!
    
```
## log_set_level()
| Argument | Description              | Default value |
| -------- | ------------------------ | ------------- |
| level    | logging level to be used | 'INFO'        |

Sets the logging level of the logger to the one specified. 

```python
    gravitrax_bridge.log_set_level('NOTSET')  # All Messages are printed
    gravitrax_bridge.log_set_level('DEBUG')   # DEBUG, INFO, WARNING, ERROR and CRITICAL Messages are printed
    gravitrax_bridge.log_set_level('INFO')    # INFO, WARNING, ERROR and CRITICAL Messages are printed
    gravitrax_bridge.log_set_level('WARNING') # WARNING, ERROR and CRITICAL Messages are printed
    gravitrax_bridge.log_set_level('ERROR')   # ERROR and CRITICAL Messages are printed
    gravitrax_bridge.log_set_level('CRITICAL')# CRITICAL Messages are printed
```

# Additional Utility methods

## scan_bridges()
| Argument    | Description                                                                 | Default value                   |
| ----------- | --------------------------------------------------------------------------- | ------------------------------- |
| name        | name to filter the scan results with. All other names are discarded         | gravitrax_constants.BRIDGE_NAME |
| timeout     | The duration of the scan                                                    | 10                              |
| do_print    | If set to True the discovered device is printed as soon as it is discovered | False                           |
| stop_on_hit | If set to True the scan is stopped as soon as one device is found           | False                           |

| Return Value       | Type | Description                                                                           |
| ------------------ | ---- | ------------------------------------------------------------------------------------- |
| [String,String,..] | List | A List containing the MAC-Addresses of all discovered devices with the specified name |

Scan for Bluetooth devices with the specified name. By default the standard name for Gravitrax Power Bridges is used. A List containing all MAC-Addresses of the found Bluetooth devices is returned.

## calc_checksum()
| Argument     | Description                                                                                                   | Default value |
| ------------ | ------------------------------------------------------------------------------------------------------------- | ------------- |
| data         | the data bytes to calculate the checksum from                                                                 |               |
| for_received | Specifies whether the calculation should be done for Signals received(True) from or send(False) to the bridge | False         |

| Return Value | Type | Description                                        |
| ------------ | ---- | -------------------------------------------------- |
| int          | int  | the calculated checksum for the passed signal data |

Returns the checksum for a 7-Byte Signal. The calculation for send and received Signals is slightly different. By default the calculation is 
for a send signal. To calculate the checksum for a received Signal `for_received` needs to be set to True.

```python
    print(b.calc_checksum(bytes([1,1,1,1,1,0,3])))
    # output:
    # 5
    print(b.calc_checksum(bytes([1,1,1,1,1,0,3]),for_received=True))
    # output:
    # 7
```

## add_checksum()
| Argument     | Description                                                                                                   | Default value |
| ------------ | ------------------------------------------------------------------------------------------------------------- | ------------- |
| data         | the data bytes to calculate the checksum from                                                                 |               |
| for_received | Specifies whether the calculation should be done for Signals received(True) from or send(False) to the bridge | False         |

| Return Value                                | Type  | Description                                                    |
| ------------------------------------------- | ----- | -------------------------------------------------------------- |
| bytes([byte,byte,byte,byte,byte,byte,byte]) | bytes | the data bytes passed as argument with the calculated checksum |

Returns the bytes for a signal with the content of the checksum field substituted for the correct checksum.

```python
    print(b.add_checksum(bytes([1,1,1,1,1,0,1])))
    # output:
    # b'\x01\x01\x01\x01\x01\x05\x01'
```


