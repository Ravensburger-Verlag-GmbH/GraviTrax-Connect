"""gravitrax_bridge.py: Connect and interact with a GravitraxConnect Bridge

This is the main file of the gravitraxconnect Library. It contains the Bridge Class
which is used for everything related to the communication with a GravitraxConnect 
Bridge, as well as some extra utility functions. The logger used in this Library can 
be accessed with gravitrax_bridge.logger. 

Bridge Class:
    Member Variables:
    - client: BleakClient object used for the connection
    - name: Name of the last connected Bridge
    - firmware: The firmware version
    - hardware: The hardware version
    - id: int value for grouping Bridges
    - dc_callback: Callback function for disconnects
    - try_reconnect: Try to reconnect after disconnect(Bool)   
    - restart_notifications: Restart Notifications after reconnect(Bool)
    - noti_callback: Callback function for Notifications

    Methods:
    - connect(): Connect to a Bridge by name or MAC-Address
    - is_connected(): Return if there is a active connection
    - disconnect(): Disconnect the Bridge
    - notification_enable(): Enable Notifications
    - notification_disable(): Disable Notifications
    - send_bytes(): Send Data-Bytes
    - send_signal(): Send a Gravitrax Signal
    - send_periodic(): Send Signals in a fixed interval
    - start_bridge_mode(): Start Bridge exclusive Mode
    - stop_bridge_mode(): Stop Bridge exclusive Mode
    - request_bridge_info(): Read Firmware and Hardware Version
    - request_battery(): Return the approx. Voltage of the batteries
    - request_battery_string(): Return a descriptive String of the battery level
    - get_address(): Return the MAC-Address of the Bridge
    - get_name(): Return the Name of the Bridge.
    - print_services(): print all gatt-services

Utility Functions:
    - scan_bridges: Make a Bluetooth scan for available Devices
    - calc_checksum: Calculate the checksum for a Signal
    - add_checksum: add the checksum to a signal
    - log_print: print with the logger
    - log_set_level: Set the logging level of the logger

"""

import random
import re
import logging
import platform
import asyncio

from bleak import BleakScanner, BleakClient
from bleak.exc import BleakError, BleakDeviceNotFoundError
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData
from bleak.backends.characteristic import BleakGATTCharacteristic

from gravitraxconnect import gravitrax_constants


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
stream_handler = logging.StreamHandler()
stream_handler.name = f"{__name__}_stream_handler"
stream_handler.setFormatter(
    logging.Formatter(
        "%(asctime)s.%(msecs)03d - %(levelname)s: %(message)s", "%H:%M:%S"
    )
)
stream_handler.setLevel(logging.INFO)
logger.addHandler(stream_handler)
logger.disabled = True


class Bridge:
    def __init__(self):
        self.client = None  # BleakClient Object used for the Connection
        self.name = None  # Name of the connected Bridge
        self.firmware = None  # Firmware Version of the Bridge
        self.hardware = None  # Hardware Version of the Bridge
        self.id = 0  # Can be used to group multiple bridges
        self.dc_callback = None  # Callback function for bridge disconnect
        self.try_reconnect = False  # Reconnect after connection loss
        self.restart_notifications = True  # Restart Notifications after reconnect
        self.noti_callback = None  # Callback function for Notifications
        # Lock for exclusive access to __last_notification
        self.__noti_lock = asyncio.Lock()
        self.__send_lock = asyncio.Lock()  # Lock for exclusive access to __next_send_id
        self.__address = None  # MAC-Address of the connected Bridge
        self.__next_send_id = 0  # Message-ID for the next send signal.
        self.__user_disconnected = False  # If the user called disconnect()
        self.__last_notifications = []

    async def connect(
        self,
        name_or_addr: str = gravitrax_constants.BRIDGE_NAME,
        by_name=True,
        timeout: float = 25,
        dc_callback=None,
        try_reconnect: bool = False,
        restart_notifications: bool = True,
    ) -> bool:
        """Connect to a Bridge.

        Establishes the Connection with a Bridge. it is possible to either connect by
        the Name of the device or the MAC-Address.

        Args:
            - name_or_addr: The identifier of the bridge. The name when by_name is True
            else the MAC-Address.
            - by_name: Whether the name or MAC-Address should be used to identify the device
            to connect to.
            - timeout: The time in seconds the Scanner tries to find a device
            before the search is stopped. Also applies to the attempt to establish
            the connection.
            - dc_callback: Callback Function that is called when the bridge disconnects.
            - try_reconnect: Sets the try_reconnect member variable.
            - restart_notifications: Sets the restart_notifications member variable.

        Returns: Boolean
            - True: Successfully connected to the Bridge.
            - False: Failed to connect to Bridge.
        """
        self.try_reconnect = try_reconnect
        self.restart_notifications = restart_notifications
        if dc_callback and not callable(dc_callback):
            raise TypeError("dc_callback is not callable")
        if not isinstance(name_or_addr, str):
            raise TypeError("addr needs to be a string")
        if not isinstance(timeout, (int, float)):
            raise TypeError("timeout needs to be int or float")
        self.dc_callback = dc_callback

        device = None
        if by_name:
            device = await BleakScanner.find_device_by_filter(
                lambda d, ad: d.name and d.name.lower() == name_or_addr.lower(), timeout
            )
        else:
            device = await BleakScanner.find_device_by_address(name_or_addr, timeout)

        if not isinstance(device, BLEDevice):
            log_print("No Bridge found to connect to", level="WARNING")
            return False

        self.client = BleakClient(
            device, disconnected_callback=self.__disconnect_callback
        )
        log_print(f"Connecting to {device.name}:{device.address}", level="DEBUG")
        try:
            await self.client.connect(timeout=timeout)
        except TimeoutError:
            log_print(
                f"Failed to connect to {device.address} after {timeout} seconds",
                level="WARNING",
            )
            return
        except (BleakDeviceNotFoundError, asyncio.CancelledError):
            return False

        self.__user_disconnected = False
        self.name = device.name
        self.__address = device.address
        if platform.system() == "Linux":
            await self.client._backend._acquire_mtu()
        log_print(
            "Connected to bridge",
            f"(MTU:{self.client.mtu_size})",
            bridge=self,
            level="INFO",
        )
        await self.request_bridge_info()
        return True

    async def is_connected(self) -> bool:
        """Return whether the bridge is connected.

        Returns: Boolean
            - False: When the Bridge is not connected.
            - True: When the Bridge is connected.
        """
        try:
            return self.client.is_connected
        except AttributeError:
            return False

    async def disconnect(
        self,
        timeout: float = 20,
        dc_callback_on_timeout: bool = False,
        _user: bool = True,
    ) -> bool:
        """Terminate the connection to the bridge.
        Closes the Connection to the Bridge.

        Args:
            - timeout: The time in seconds the function waits for the disconnect to finish.
            - dc_callback_on_timeout: Whether the disconnect callback should be called when
            a timeout occurs.
            - _user: Used to enable/disable the tracking if a disconnect was
            made intentional by the user or not.

        Returns: Boolean
            - True: Successfully disconnected from the Bridge.
            - False: The Disconnect timed out, no bridge was connected or an error occurred while
            disconnecting.

        """
        if not isinstance(self.client, BleakClient):
            log_print(
                "Disconnecting:",
                f"BleakClient Object was not initialized. Please connect to a bridge first.",
                bridge=self,
                level="ERROR",
            )
            # The disconnect callback is also executed here to prevent Skripts don't get stuck if
            # they use it to close
            try:
                if self.dc_callback:
                    self.dc_callback(self, user_disconnected=True, by_timeout=False)
            except TypeError as exc:
                log_print(
                    f"Disconnecting: Failed to call Disconnect Callback ({str(exc)})",
                    level="ERROR",
                )
            return False
        if _user:
            self.__user_disconnected = True
        try:
            log_print("Disconnecting", bridge=self, level="DEBUG")
            await asyncio.wait_for(
                asyncio.shield(self.client.disconnect()), timeout=timeout
            )
        except TimeoutError:
            log_print(
                f"Disconnect is taking longer than {timeout} seconds",
                bridge=self,
                level="WARNING",
            )
            try:
                if dc_callback_on_timeout and self.dc_callback:
                    self.dc_callback(self, user_disconnected=True, by_timeout=True)
            except TypeError as exc:
                log_print(
                    f"Disconnecting: Failed to call Disconnect Callback ({str(exc)})",
                    level="ERROR",
                )
            return False
        return True

    def __disconnect_callback(self, client: BleakClient) -> bool:
        """Handle the disconnect of the bridge

        This function is called when the bridge is disconnected
        If the disconnect wasn't requested by the user an try_reconnect
        is set to True the __reconnect() method is called.
        When a custom disconnect callback is defined(while connecting or
        using the dc_callback variable) it is executed here.

        Args:
            - client: A BleakClient from the bleak Library. Used to get
            the MAC address of the disconnected bridge

        """
        log_print(
            "Bridge disconnected",
            f" (Disconnected by user: {self.__user_disconnected})",
            bridge=self,
        )
        try:
            if self.dc_callback:
                self.dc_callback(
                    self, user_disconnected=self.__user_disconnected, by_timeout=False
                )
        except TypeError as exc:
            log_print(
                f"Disconnect Callback: Failed to call Disconnect Callback ({str(exc)})",
                level="ERROR",
            )
        if (not self.__user_disconnected) and self.try_reconnect:
            log_print("Trying to reconnect", bridge=self)
            asyncio.get_running_loop().create_task(self.__reconnect(client.address))

    async def __reconnect(self, address: str) -> None:
        """Reconnect to the bridge after a disconnect.

        This function is called when the connection to the Bridge is interrupted and
        the member variable try_reconnect is set to True. If restart_notifications
        is set to True the Notifications are restarted after a successful reconnect.
        If the reconnect fails the dc_callback is called.

        Args:
            - address: MAC address of the disconnected bridge.
        """
        try:
            await asyncio.wait_for(
                self.connect(address, by_name=False, try_reconnect=True), timeout=15
            )
        except TimeoutError:
            log_print(
                "Could not reconnect to Bridge: Reconnect timed out",
                bridge=self,
                level="WARNING",
            )
            try:
                if self.dc_callback:
                    self.dc_callback(self, user_disconnected=False, by_timeout=True)
            except TypeError as exc:
                log_print(
                    f"Disconnect Callback: Failed to call Disconnect Callback ({str(exc)})",
                    level="ERROR",
                )
            return
        log_print("Reconnected to Bridge", bridge=self)
        if self.restart_notifications and self.noti_callback:
            await self.notification_enable(self.noti_callback)

    async def notification_enable(
        self, callback, uuid: str = gravitrax_constants.UUID_NOTIF
    ) -> bool:
        """Enable Notifications from the bridge.

        Args:
            - callback: A function to be called when a Notification is
            received.
            - uuid: The uuid to receive Notifications from. Defaults to
            Standard value from gravitrax_constants.py. Needs to be a string.

        Returns:
            - True: Successfully enabled the notifications.
            - False: Enabling the notifications failed.

        """
        if not isinstance(uuid, str):
            raise TypeError(
                "Disabling Notifications failed: The uuid {uuid} is not a string"
            )
        if not callable(callback):
            raise TypeError("callback is not callable")
        try:
            await self.client.start_notify(uuid, self.__notification_handler)
        except AttributeError:
            log_print(
                "Enabling Notifications failed:",
                f"BleakClient Object was not initialized. Please connect to a bridge first.",
                bridge=self,
                level="ERROR",
            )
            return False
        except BleakError as exc:
            log_print(
                f"Enabling Notifications failed: {str(exc)}",
                bridge=self,
                level="ERROR",
            )
            return False

        log_print("Notifications Enabled", bridge=self, level="INFO")
        self.noti_callback = callback
        return True

    async def notification_disable(
        self, uuid: str = gravitrax_constants.UUID_NOTIF
    ) -> None:
        """Disable Notifications from the bridge

        Args:
            - uuid: The uuid to stop receive Notifications from. Defaults to
            Standard value from gravitrax_constants. Needs to be a string.

        Returns:
            - True: Successfully disabled the notifications.
            - False: Disabling the Notifications failed.
        """
        if not isinstance(uuid, str):
            raise TypeError(
                "Disabling Notifications failed: The uuid {uuid} is not a string"
            )

        try:
            await self.client.stop_notify(uuid)
        except AttributeError:
            log_print(
                "Disabling Notifications failed:",
                f"BleakClient Object was not initialized. Please connect to a bridge first.",
                bridge=self,
                level="ERROR",
            )
            return False
        except BleakError as exc:
            log_print(
                f"Disabling Notifications failed: {str(exc)}",
                bridge=self,
                level="ERROR",
            )
            return False
        log_print("Notifications disabled", bridge=self, level="INFO")
        return True

    async def __notification_handler(
        self, characteristic: BleakGATTCharacteristic, data: bytearray
    ) -> None:
        """Handle received Notifications

        This Method is called when the bridge receives a Notification.
        The Notification Data is searched for messages that conform to the
        Gravitrax Signal Protocol.For every found message the user specified notification callback
        is executed. If the Notification Data does not contain any valid messages only the raw data
        is passed to the callback. When a valid Message is the same as the last one received
        or the checksum is incorrect it's discarded.

        Args:
            - characteristic: A BleakGATTCharacteristic from the Bleak
            Library
            - data: Bytearray containing the Data of the Notification
        """
        message = " ".join("{:02x}".format(x) for x in data)
        # Check if data conforms to Gravitrax Signal Protocol

        recv_signals = [
            match.group() for match in re.finditer(r"13(\s[0-9a-fA-F]{2}){6}", message)
        ]

        if len(recv_signals) == 0:
            await self.noti_callback(
                self,
                Header=None,
                Stone=None,
                Status=None,
                Reserved=None,
                Id=None,
                Checksum=None,
                Color=None,
                Data=data,
            )
            return

        await self.__noti_lock.acquire()
        try:

            for recv_signal in recv_signals:

                # Check if the same Signal was already received
                if recv_signal in self.__last_notifications:
                    continue
                self.__last_notifications.append(recv_signal)
                while len(self.__last_notifications) > 12:
                    self.__last_notifications.pop(0)

                signal = [
                    int(recv_signal[0:2], base=16),  # 0.Header
                    int(recv_signal[3:5], base=16),  # 1.Stonetype
                    int(recv_signal[6:8], base=16),  # 2.Status
                    int(recv_signal[9:11], base=16),  # 3.Reserved
                    int(recv_signal[12:14], base=16),  # 4.Message ID
                    int(recv_signal[15:17], base=16),  # 5.Checksum
                    int(recv_signal[18:20], base=16),  # 6.Color
                ]

                if signal[5] != calc_checksum(signal, for_received=True):
                    log_print(
                        "Incoming Notification was discarded because the Checksum was incorrect",
                        level="DEBUG",
                    )

                try:
                    await self.noti_callback(
                        self,
                        Header=signal[0],
                        Stone=signal[1],
                        Status=signal[2],
                        Reserved=signal[3],
                        Id=signal[4],
                        Checksum=signal[5],
                        Color=signal[6],
                        Data=data,
                    )
                except TypeError as exc:
                    log_print(
                        f"Failed to call notification callback: {str(exc)}",
                        bridge=self,
                        level="ERROR",
                    )
        finally:
            self.__noti_lock.release()

    async def send_bytes(
        self,
        data: bytes,
        resends: int = 1,
        resend_gap: float = 0,
        uuid: str = gravitrax_constants.UUID_WRITE,
        error_event: asyncio.Event = None,
    ) -> None:
        """Send arbitrary Bytes of data to the Bridge.

        Args:
            - data: The bytes of data to send
            - resends: How often a signal with the same data should be resend.
            Setting a higher value here helps to decrease package loss at
            the cost of reduced throughput when sending multiple Signals.
            - resend_gap: How much big of a timegap(in seconds) should be
            between there every package send.
            - uuid: The uuid of the Bridge to send the Signals. Should not be
            changed unless future updates to the Bridge change the uuid for writes
            - error_event: A asyncio.Event that is set when a error happens
            during the send operation
        """
        try:
            # Sending a Message multiple times reduces the odds for package
            # loss to occur. If the Bridge receives an identical message
            # more then once in a span of 12 non-identical Messages it is discarded.
            for _ in range(resends):
                await self.client.write_gatt_char(uuid, data)
                await asyncio.sleep(resend_gap)
        except (TypeError, BleakError) as exc:
            if isinstance(error_event, asyncio.Event):
                error_event.set()
            log_print(
                "Error sending Data:",
                f"({type(exc).__name__}) {str(exc)}",
                bridge=self,
                level="ERROR",
            )
        except AttributeError:
            if isinstance(error_event, asyncio.Event):
                error_event.set()
            log_print(
                "Error sending Data:",
                f"BleakClient Object was not initialized. Please connect to a bridge first.",
                bridge=self,
                level="ERROR",
            )

    async def send_signal(
        self,
        status: int,
        color_channel: int,
        resends: int = 12,
        resend_gap: float = 0,
        random_id: bool = False,
        uuid: str = gravitrax_constants.UUID_WRITE,
        header: int = gravitrax_constants.MSG_DEFAULT_HEADER,
        stone: int = gravitrax_constants.STONE_BRIDGE,
        error_event: asyncio.Event = None,
    ) -> None:
        """Send a Signal to a Bridge

        Args:
            - status: int value specifying which Blocks should react to the
            signal. Allowed Values can be found in the gravitrax_variables
            file
            - color: int value specifying what color the signal should have.
            Only Blocks set to this colors will trigger when receiving the
            signal
            - resends: How often a signal with the same data should be resend.
            Setting a higher value here helps to decrease package loss at
            the cost of reduced throughput when sending multiple Signals.
            - resend_gap: Additional delay in seconds between every resend of
            a signal
            - random_id: Boolean specifying if the the message_id value should
            be chosen randomly or incremented with each signal
            - uuid: The uuid of the Bridge to send the Signals. Should not
            be changed unless future updates to the Bridge change the uuid
            for writes
            - header: The header of the send signal. Should not be changed
            unless there are changes to the communications protocol in the
            future
            - stone: Specifies the Stonetype of the send signal. Defaults to
            the value of the Bridge Stone.
            - error_event: A asyncio.Event that is set when a error happens
            during the send operation

        Instance variables:

            - __next_send_id (set, read): The message id for the next send signal if
            random_id is set to false
        """
        reserved = random.randrange(0, 255)
        await self.__send_lock.acquire()
        if random_id:
            message_id = random.randrange(0, 255)
        else:
            message_id = self.__next_send_id
        self.__next_send_id = (self.__next_send_id + 1) % 256
        self.__send_lock.release()
        checksum = (header + stone + status + reserved + message_id) % 256
        await self.send_bytes(
            bytes(
                [header, stone, status, reserved, message_id, checksum, color_channel]
            ),
            uuid=uuid,
            resends=resends,
            resend_gap=resend_gap,
            error_event=error_event,
        )

    async def send_periodic(
        self,
        status: int,
        color_channel: int,
        count: int,
        gap: float = 0,
        resends: int = 12,
        resend_gap: float = 0,
        stone: int = gravitrax_constants.STONE_BRIDGE,
        stop_on_failure: bool = True,
    ) -> None:
        """Send multiple Signals with a time gap in between.

        Args:
            - status: int value specifying which Blocks should react to the
            signal. Allowed Values can be found in the gravitrax_variables
            file
            - color: int value specifying what color the signal should have.
            Only Stones set to this colors will trigger when receiving the
            signal
            - gap: Delay in Seconds between sending signals . Defaults to 0
            - resends: How often a signal with the same data should be resend.
              Setting a higher value here helps to decrease package loss at
              the cost of reduced throughput when sending multiple Signals.
            - resend_gap: Additional delay in seconds between every resend of
            a signal
            - stop_on_failure: Specifies whether the function should continue
            to run if there was an error during one send operation(usually
            because the used bridge was disconnected)
        """
        error_event = asyncio.Event()
        for i in range(count):
            # Handling of a failed Transmission
            if stop_on_failure and error_event.is_set():
                return

            if gap > 0 and i > 0:
                await asyncio.sleep(gap)
            await self.send_signal(
                status,
                color_channel,
                resends=resends,
                resend_gap=resend_gap,
                stone=stone,
                error_event=error_event,
            )

    async def start_bridge_mode(self) -> None:
        """Put Gravitrax Power stones in Bridge Only mode

        Send a signal with the Lock Status to the Gravitrax Bridge.
        All Gravitrax Power stones that receive this signal will switch to
        the Bridge only mode. In this mode only signals from
        Gravitrax Bridges are accepted.
        """
        await self.send_signal(
            gravitrax_constants.STATUS_LOCK, gravitrax_constants.COLOR_RED
        )
        log_print("Bridge Mode enabled", bridge=self, level="INFO")

    async def stop_bridge_mode(self) -> None:
        """Put Gravitrax Power stones in Normal mode
        Sends signal with the Unlock Status over the Gravitrax Bridge.
        All Gravitrax Power stones that receive this signal will switch out
        of the Bridge only mode.
        """
        await self.send_signal(
            gravitrax_constants.STATUS_UNLOCK, gravitrax_constants.COLOR_RED
        )
        log_print("Bridge Mode disabled", bridge=self, level="INFO")

    async def __read_chraceristic(
        self, characteristic: str, error_prefix: str
    ) -> (bytearray | None):
        """A wrapper for BleakClient.read_gatt_char() with additional Error handling

        Arg:
            - characteristic: uuid of the characteristic to read
            - error_prefix: string printed before error messages

        Instance Variables:
            - client (read): The BleakClient object used for the connection to
            the Bridge
        """
        try:
            return await self.client.read_gatt_char(characteristic)
        except AttributeError:
            log_print(
                error_prefix,
                f"BleakClient Object was not initialized. Please connect to a bridge first.",
                bridge=self,
                level="ERROR",
            )
            return None
        except BleakError as exc:
            err_text = str(exc)
            if re.match(r"Characteristic [\-\w]* was not found!", err_text):
                err_text = "Characteristic not found. Make sure the bridge is connected"

            log_print(
                f"{error_prefix} ({type(exc).__name__})",
                err_text,
                bridge=self,
                level="ERROR",
            )
            return None

    async def request_bridge_info(self) -> tuple | None:
        """Read Firmware and Hardware Version of Gravitrax Bridges

        returns:
            - Tuple containing the firmware version and hardware version as
            int values
            - None: Retrieving the Information failed

        """
        if not (
            data := await self.__read_chraceristic(
                gravitrax_constants.UUID_WRITE, "Error Requesting Bridge Information: "
            )
        ):
            return None

        try:
            self.firmware = int(data[1])
            self.hardware = int(data[2])
        except IndexError:
            log_print(
                "Error Requesting Bridge Information: ",
                f"(IndexError) Received Data: {data}",
                bridge=self,
                level="ERROR",
            )
            return None
        log_print(
            f"Firmware Version: {self.firmware}",
            f" Hardware Version: {self.hardware}",
            bridge=self,
            level="INFO",
        )
        return (self.firmware, self.hardware)

    async def request_battery(self) -> int | None:
        """Read out the Battery Level from the Bridge

        Returns:
            - approximate Battery Voltage (2->3.1)
            - None: When the Battery Level could not be read
        """
        if not (
            data := await self.__read_chraceristic(
                gravitrax_constants.UUID_BATTERY,
                "Error Requesting Battery Information: ",
            )
        ):
            return None

        log_print(
            "Battery Request: Bridge returned ",
            data,
            bridge=self,
            level="DEBUG",
        )
        try:
            return gravitrax_constants.DICT_BATTERYVALUES[data[0]]
        except (KeyError, IndexError):
            return None

    async def request_battery_string(self) -> str | None:
        """Get descriptive string of Battery Level

        Returns:
            - String describing the Battery Level
            - None: When the Battery Level could not be read
        """
        try:
            return gravitrax_constants.DICT_BATTERYSTRINGS[await self.request_battery()]
        except (KeyError, TypeError) as exc:
            log_print(
                "Error requesting Battery",
                f"({type(exc).__name__}) {str(exc)}",
                bridge=self,
                level="ERROR",
            )
            return None

    def get_address(self) -> str | None:
        """Returns the MAC-Address of the connected Bridge

        Returns: String
            - MAC-Address of Bridge
            - None: When the address wasn't stored during the connection process

        Instance variables:
            - __address (read): the address of the Bridge.
        """
        return self.__address

    def get_name(self) -> str | None:
        """Returns the Name of the connected Bridge

        Returns: String
            - MAC-Address of Bridge
            - None: When address wasn't stored during the connection process

        Instance variables:
            - name (read): the name of the Bridge.
        """
        return self.name

    async def print_services(self) -> None:
        """Prints out the Services of the Bridge"""
        log_print("Services of the Bridge", level="INFO")
        for service in self.client.services:
            print(service)
            for char in service.characteristics:
                print(f"  {char}")
                for desc in char.descriptors:
                    print(f"    {desc}")
            print()


async def scan_bridges(
    name: str = gravitrax_constants.BRIDGE_NAME,
    timeout: float = 10.0,
    do_print: bool = False,
    stop_on_hit: bool = False,
) -> None:
    """Scan for Bluetooth LE Devices.
    The MAC addresses(as String) of all found Bridges are returned
    after the timeout is reached. When do_print is enabled found
    devices are printed out immediately after they are discovered.

    Args:
        name: Discovered devices are filtered by this name. Use "" to scan for all names
        - timeout: The duration of the scan
        - do_print: print out the bridge address as soon as the device
        is discovered
        - stop_on_hit: Specifies whether the scan should stop after a
        device was found

    Returns:
        - address_list: list containing MAC address Strings of all
        discovered Bridges. When no Devices are found the empty List
        is returned

    Raises:
        ValueError: Invalid value for timeout. Use a int or float value
    """
    try:
        timeout = float(timeout)
    except ValueError as exc:
        raise ValueError(
            "Invalid Timeout for scan_bridges(). Use float,int,...."
        ) from exc

    address_list = []
    log_prev_state = logger.disabled
    logger.disabled = not do_print

    def discover_callback(device: BLEDevice, advertisement_data: AdvertisementData):
        if (device.name == name or name == "") and not device.address in address_list:
            address_list.append(device.address)
            if do_print:
                log_print(advertisement_data.local_name, ":", device.address)

            if stop_on_hit:
                return address_list

    scanner = BleakScanner(discover_callback, "")
    await scanner.start()
    await asyncio.sleep(int(timeout))
    await scanner.stop()
    logger.disabled = log_prev_state
    return address_list


def calc_checksum(data: bytes, for_received: bool = False) -> int | None:
    """
    Calculates the Checksum for a 7-Byte Message

    Args:
        - data: The 7-Byte Message
        - for_received: If the checksum is for send or received Signals

    returns:
        - int: The Calculated Checksum
        - None: When the length of the data is not 7 Bytes
    """
    if len(data) != 7:
        return None
    checksum = (data[0] + data[1] + data[2] + data[3] + data[4]) % 256
    if for_received:
        checksum = (checksum + data[6] - 1) % 256
    return checksum


def add_checksum(data: bytes, for_received: bool = False) -> bytes | None:
    """Adds the Checksum to a 7-Byte Message.

    Args:
        - data: The 7-Byte Message
        - for_received: If the checksum is for send or received Signals

    Returns:
        - bytes: The Message with the calculated checksum
        - None: When the length of the data is not 7 Bytes
    """
    if len(data) != 7:
        return None
    return bytes(
        [
            data[0],
            data[1],
            data[2],
            data[3],
            data[4],
            calc_checksum(data, for_received),
            data[6],
        ]
    )


def log_print(*text, bridge: Bridge = None, level: (str | int) = "INFO") -> None:
    """Print something with the logger

    Args:
        *text: values to be printed
        bridge: Bridge object. Used to print the address in front of logging messages
        level: The logging level for the message.
    """
    msg = ""
    for t in text:
        msg = msg + str(t)

    if isinstance(level, str):
        try:
            level = getattr(logging, level)
        except AttributeError:
            logger.error(f"Logging Level {level} not supported. Message:({msg})")
    try:
        if bridge and (addr := bridge.get_address()):
            logger.log(level, f"({addr}) {msg}")
        else:
            logger.log(level, msg)
    except TypeError:
        logger.error(f"Wrong Type for Logging level: {type(level)}. Message:({msg})")


def log_set_level(level: (str | int) = "DEBUG") -> None:
    """Set the level of the Logger.

    Args:
        level (str | int): the logging level to be used
    """
    try:
        logger.setLevel(level)
        for handler in logger.handlers:
            if handler.name == f"{__name__}_stream_handler":
                handler.setLevel(level)
    except (TypeError, ValueError):
        log_print(f"Logging level can´t be set to {level} ", level="ERROR")
