"""
This script can be used to test if the library functions  work on 
the used System. A Gravitrax Connect Bridge needs to be running while 
doing the tests.
"""

import time
import asyncio
import re

from gravitraxconnect import gravitrax_bridge as gb


async def wait_for_disconnect(bridge: gb.Bridge, timeout=30):
    """Wait for a disconnect to conclude"""

    async def wait():
        while await bridge.is_connected():
            await asyncio.sleep(0.5)

    try:
        await asyncio.wait_for(wait(), timeout=timeout)
    except TimeoutError:
        return False
    return True


async def test_scan():
    """Test for the scan_bridges() function"""
    test = "test_scan"
    gb.log_print(f"--- Starting {test}")
    timeout = 10
    start = time.time()
    try:
        assert (
            len(
                await gb.scan_bridges(
                    name="not_a_Gravitrax_Bridge_123", timeout=timeout
                )
            )
            == 0
        ), "address list not empty"
        duration = time.time() - start
        assert duration >= timeout - 1, "Scan timeout to fast"
        assert duration <= timeout + 1, "Scan timeout to slow"
        assert (
            len(await gb.scan_bridges(name="GravitraxConnect", timeout=timeout)) != 0
        ), "Bridge not detected"

        gb.log_print(f"--- {test} passed")
        return True
    except AssertionError as exc:
        gb.log_print(f"xxx {test} failed: {str(exc)}")
        return False


async def test_connect_disconnect():
    """Test connecting and disconnecting from a bridge"""
    test = "test_connect_disconnect"
    gb.log_print(f"--- Starting {test}")
    bridge = gb.Bridge()
    try:
        assert await bridge.connect("GravitraxConnect"), "connect failed"

        assert await bridge.is_connected(), "not connected (name)"
        address = bridge.get_address()
        assert await bridge.disconnect(), "disconnect failed"
        assert await bridge.connect(address, by_name=False), "connect failed"
        assert await bridge.is_connected(), "not connected (addr)"
        address = bridge.get_address()
        assert await bridge.disconnect(), "disconnect failed"
        assert await wait_for_disconnect(bridge), "Disconnect timed out"
        gb.log_print(f"--- {test} passed")

        return True
    except AssertionError as exc:
        gb.log_print(f"xxx {test} failed: {str(exc)}")
        return False
    finally:
        if await bridge.is_connected():
            await bridge.disconnect()
            await wait_for_disconnect(bridge)


async def test_disconnect_timeout():
    """Test if timeout for the disconnect method and
    the dc_callback_on_timeout Parameter are functional.
    """
    test = "test_disconnect_timeout"
    gb.log_print(f"--- Starting {test}")
    called = 0
    bridge = gb.Bridge()

    def callback(bridge: gb.Bridge, **kwargs):
        nonlocal called
        try:
            assert kwargs.get("user_disconnected"), "user_disconnected not set"
            if called == 0:
                assert kwargs.get("by_timeout"), "disconnected before timeout"
        except AssertionError as exc:
            gb.log_print(f"xxx {test} failed: {str(exc)}", bridge=bridge)
        finally:
            called += 1

    try:
        assert await bridge.connect(
            "GravitraxConnect", dc_callback=callback
        ), "connect failed"

        assert not await bridge.disconnect(
            timeout=0, dc_callback_on_timeout=True
        ), "Disconnected before timeout"
        assert await wait_for_disconnect(bridge), "Disconnect timed out"
        assert called > 0, f"Disconnect callback was not called"
        assert (
            called == 2
        ), f"disconnect callback called {called} \
times instead of 2(after Timeout and after disconnect )"
        gb.log_print(f"--- {test} passed")
        return True
    except AssertionError as exc:
        gb.log_print(f"xxx {test} failed: {str(exc)}")
        return False
    finally:
        if await bridge.is_connected():
            await bridge.disconnect()
            await wait_for_disconnect(bridge)


async def test_double_connect():
    """Test how the Library handles tries to connect to a Bridge
    multiple times
    """
    test = "test_double_connect"
    gb.log_print(f"--- Starting {test}")
    bridge = gb.Bridge()
    bridge2 = gb.Bridge()
    try:
        assert await bridge.connect("GravitraxConnect"), "connect failed"

        assert await bridge.is_connected(), "connect failed"
        address = bridge.get_address()

        assert not await bridge2.connect(
            address, by_name=False, timeout=20
        ), "Connected to Bridge twice"

        assert await bridge.is_connected(), "1st Bridge was disconnected"

        assert not await bridge2.is_connected(), "2nd Bridge is connected"
        gb.log_print(f"--- {test} passed")
        return True
    except AssertionError as exc:
        gb.log_print(f"xxx {test} failed: {str(exc)}")
        return False
    finally:
        if await bridge.is_connected():
            await bridge.disconnect()
            await wait_for_disconnect(bridge)


async def test_connect_timeout():
    """Test if the timeout for an connection attempt works correctly"""
    test = "test_connect_timeout"
    gb.log_print(f"--- Starting {test}")
    bridge = gb.Bridge()
    timeout = 10
    start = time.time()
    try:
        assert not await bridge.connect(
            "not_a_Gravitrax_Bridge_123", timeout=timeout
        ), "Device found and connected"

        duration = time.time() - start
        assert duration >= timeout - 1, "Timeout to fast"
        assert duration <= timeout + 1, "Timeout to slow"
        gb.log_print(f"--- {test} passed")
        return True
    except AssertionError as exc:
        gb.log_print(f"xxx {test} failed: {str(exc)}")
        return False


async def test_disconnect_callback():
    """Test if the disconnect callback is called after a bridge
    disconnected
    """
    test = "test_disconnect_callback"
    gb.log_print(f"--- Starting {test}")
    called = False
    bridge = gb.Bridge()

    def callback(bridge: gb.Bridge, **kwargs):
        nonlocal called
        called = True
        try:
            assert kwargs.get(
                "user_disconnected"
            ), "Disconnected before disconnect call"
            assert not kwargs.get("by_timeout"), "Disconnected timed out"
        except AssertionError as exc:
            gb.log_print(f"xxx {test} failed: {str(exc)}", bridge=bridge)

    try:
        assert await bridge.connect(
            "GravitraxConnect", dc_callback=callback
        ), "connect failed"

        assert await bridge.disconnect(), "disconnect failed"
        assert await wait_for_disconnect(bridge), "Disconnect timed out"
        assert called, f"Disconnect callback was not called"
        gb.log_print(f"--- {test} passed")
        return True
    except AssertionError as exc:
        gb.log_print(f"xxx {test} failed: {str(exc)}")
        return False
    finally:
        if await bridge.is_connected():
            await bridge.disconnect()
            await wait_for_disconnect(bridge)


async def test_reconnect():
    """Test for reconnection after an unintentional disconnect"""
    lock = asyncio.Lock()
    called = False

    async def callback(bridge: gb.Bridge, **signal):
        nonlocal called, lock
        await lock.acquire()
        called = True
        lock.release()

    test = "test_reconnect"
    gb.log_print(f"--- Starting {test}")
    bridge = gb.Bridge()

    try:
        assert await bridge.connect(
            "GravitraxConnect", try_reconnect=True, restart_notifications=True
        ), "connect failed"
        bridge.noti_callback = callback
        assert await bridge.is_connected(), "not connected"
        assert await bridge.disconnect(_user=False), "disconnect failed"
        start = time.time()
        while await bridge.is_connected():
            await asyncio.sleep(0.1)
            if time.time() - start > 20:
                raise AssertionError("Bridge not disconnected after 20 seconds")
        start = time.time()
        while not await bridge.is_connected():
            await asyncio.sleep(1)
            if time.time() - start > 20:
                raise AssertionError("Bridge not reconnected after 20 seconds")
        start = time.time()
        while True:
            await lock.acquire()
            if called:
                break
            lock.release()
            await bridge.send_signal(0, 1, stone=5)
            await asyncio.sleep(1)
            if time.time() - start > 20:
                raise AssertionError(
                    "No signal received after restarting Notifications"
                )
        gb.log_print(f"--- {test} passed")
        return True
    except AssertionError as exc:
        gb.log_print(f"xxx {test} failed: {str(exc)}")
        return False
    finally:
        if await bridge.is_connected():
            await bridge.disconnect()
            await wait_for_disconnect(bridge)


async def test_notifications():
    """Test if notifications are received and if the received data
    is correct.
    """
    test = "test_notifications"
    gb.log_print(f"--- Starting {test}")
    called = False

    async def callback(bridge: gb.Bridge, **signal):
        nonlocal called
        try:
            assert signal.get("Header") == 19, "Header incorrect"
            assert signal.get("Status") == 0, "Status incorrect"
            assert signal.get("Stone") == 5, "Stonetype incorrect"
            assert signal.get("Color") == 1, "Color incorrect"
        except AssertionError as exc:
            gb.log_print(f"xxx {test} failed: {str(exc)}")
        called = True

    bridge = gb.Bridge()
    try:
        assert await bridge.connect("GravitraxConnect"), "connect failed"

        assert await bridge.notification_enable(
            callback
        ), "enabling Notifications failed"

        # Sending Signal as Remote.Should be received again
        await bridge.send_signal(0, 1, stone=5)
        await asyncio.sleep(0.5)
        assert called, "Callback was not called"
        assert await bridge.notification_disable(), "disabling Notifications failed"

        called = False
        # Sending Signal as Remote.Should be received again
        await bridge.send_signal(0, 1, stone=5)
        await asyncio.sleep(0.5)
        assert not called, "Callback was called after Notif. disabled"
        gb.log_print(f"--- {test} passed")
        return True
    except AssertionError as exc:
        gb.log_print(f"xxx {test} failed: {str(exc)}")
        return False
    finally:
        if await bridge.is_connected():
            await bridge.disconnect()
            await wait_for_disconnect(bridge)


async def test_send(count=100, resends=12, resend_gap=0):
    """Test if signals are send correctly. By default multiple Signals
    are send and it is tested how many signals are received again.
    """
    test = "test_send"
    gb.log_print(f"--- Starting {test}")
    gb.log_print(locals())
    called = False
    received = 0
    last_signal = None
    signals = []

    async def callback(bridge: gb.Bridge, **signal):
        nonlocal called, received, last_signal
        signals.append((signal.get("Id"), signal.get("Data")))
        try:
            assert signal.get("Header") == 19, "Header incorrect"
            assert signal.get("Status") == 3, "Status incorrect"
            assert signal.get("Stone") == 5, "Stonetype incorrect"
            assert signal.get("Color") == 1, "Color incorrect"
        except AssertionError as exc:
            gb.log_print(f"xxx {test} failed: {str(exc)}")
        received += 1
        called = True
        last_signal = time.time()

    bridge = gb.Bridge()
    try:
        assert await bridge.connect("GravitraxConnect"), "connect failed"

        assert await bridge.notification_enable(
            callback
        ), "enabling Notifications failed"

        for _ in range(count):
            await bridge.send_signal(
                3, 1, resends=resends, resend_gap=resend_gap, stone=5
            )  # Sending Signal as Remote.Should be received again
        while True:
            await asyncio.sleep(2)
            if last_signal and time.time() - last_signal > 2:
                break
        assert called, "Callback was not called"
        assert received == count, f"received {received}/{count} packages"
        gb.log_print(f"--- {test} passed")
        return True
    except AssertionError as exc:
        for signal in signals:
            print(f"{signal[0]}: {signal[1]}")
        gb.log_print(f"xxx {test} failed: {str(exc)}")
        return False
    finally:
        if await bridge.is_connected():
            await bridge.notification_disable()
            await bridge.disconnect()
            await wait_for_disconnect(bridge)


async def test_send_bytes(count=100, resends=12, resend_gap=0):
    """Test if bytes are send correctly. By default multiple Signals
    are send and it is tested how many signals are received again.
    """
    test = "test_send_bytes"
    gb.log_print(f"--- Starting {test}")
    gb.log_print(locals())
    called = False
    received = 0
    failed = False
    last_signal = None

    async def callback(bridge: gb.Bridge, **signal):
        nonlocal called, received, failed, last_signal
        try:
            assert signal.get("Header") == 19, "Header incorrect"
            assert signal.get("Stone") == 5, "Stone incorrect"
            assert signal.get("Status") == 0, "Status incorrect"
            assert signal.get("Reserved") == 0, "Reserved incorrect"
            assert signal.get("Id") in range(0, 256), "Id incorrect"
            assert signal.get("Checksum") in range(0, 256), "Checksum incorrect"
            assert signal.get("Color") == 1, "Color incorrect"

        except AssertionError as exc:
            gb.log_print(f"xxx {test} failed: {str(exc)}")
            failed = True

        received += 1
        called = True
        last_signal = time.time()

    bridge = gb.Bridge()
    try:
        assert await bridge.connect("GravitraxConnect"), "connect failed"

        assert await bridge.notification_enable(
            callback
        ), "enabling Notifications failed"

        for i in range(count):
            data = gb.add_checksum(bytes([19, 5, 0, 0, i, 0, 1]))
            await bridge.send_bytes(data, resends=resends, resend_gap=resend_gap)
        while True:
            await asyncio.sleep(2)
            if last_signal and time.time() - last_signal > 2:
                break
        await asyncio.sleep(0.5)
        assert called, f"Callback was not called"
        assert received == count, f"received {received}/{count} packages"
        gb.log_print(f"--- {test} passed")
        return not failed
    except AssertionError as exc:
        gb.log_print(f"xxx {test} failed: {str(exc)}")
        return False
    finally:
        if await bridge.is_connected():
            await bridge.notification_disable()
            await bridge.disconnect()
            await wait_for_disconnect(bridge)


async def test_signal_roundtrip_time(
    count, threshold=0.25, resends=1, resend_gap=0, signal_gap=0
):
    """Test the time for a signal to be send and received again.

    Send(PC) Bluetooth
    -> Send(Bridge) RF
    -> Receive(Bridge) RF
    -> Send(Bridge) Bluetooth
    -> Receive(PC) Bluetooth
    """
    test = "test_signal_roundtrip_time"
    gb.log_print(f"--- Starting {test}")
    gb.log_print(locals())
    send_signal_times = []
    received_signal_times = []

    async def callback(bridge: gb.Bridge, **signal):
        nonlocal received_signal_times
        received_signal_times.append(time.time())

    async def send():
        nonlocal signal_gap

        send_signal_times.append(time.time())
        await bridge.send_signal(
            0, 1, resends=resends, resend_gap=resend_gap, stone=5
        )  # Sending Signal as Remote.Should be received again
        if signal_gap:
            await asyncio.sleep(signal_gap)

    rtt_list = []
    bridge = gb.Bridge()
    try:
        assert await bridge.connect("GravitraxConnect"), "connect failed"
        assert await bridge.notification_enable(
            callback
        ), "enabling Notifications failed"

        for _ in range(count):
            await send()

        while True:
            await asyncio.sleep(2)
            if time.time() - received_signal_times[-1] > 5 + signal_gap:
                break
        assert (
            len(send_signal_times) == count
        ), f"Incorrect amount of send signals {len(send_signal_times)} / {count}"
        assert len(received_signal_times) == len(send_signal_times), (
            f"Incorrect amount of received signals "
            f"{len(received_signal_times)} / {len(send_signal_times)}"
        )

        rtt_sum = 0

        for i in range(count):
            rtt = received_signal_times[i] - send_signal_times[i]
            rtt_list.append(rtt)
            rtt_sum += rtt
        to_slow = []
        for i, rtt in enumerate(rtt_list):
            if rtt > threshold:
                to_slow.append(i)

        assert (
            len(to_slow) == 0
        ), f"Roundtriptime for {len(to_slow)} signals({to_slow}) over threshold({threshold}s)"

        gb.log_print(f"Average RTT {rtt_sum/count} seconds", level="INFO")
        gb.log_print(f"--- {test} passed")
        return True
    except AssertionError as exc:
        gb.log_print(f"RTT-Times:", rtt_list)
        gb.log_print(f"xxx {test} failed: {str(exc)}")
        return False
    finally:
        if await bridge.is_connected():
            await bridge.notification_disable()
            await bridge.disconnect()
            await wait_for_disconnect(bridge)


async def test_add_checksum():
    """Test if the checksum calculation is correct"""
    test = "test_add_checksum"
    gb.log_print(f"--- Starting {test}")
    checksum_index = -2
    try:
        data = bytes([19, 5, 0, 0, 0, 0, 1])
        assert (gb.add_checksum(data))[
            checksum_index
        ] == 24, "19,5,0,0,0,0,1 Checksum wrong"
        data = bytes([19, 5, 0, 0, 0, 0, 2])

        assert (gb.add_checksum(data))[
            checksum_index
        ] == 24, "19,5,0,0,0,0,2 Checksum wrong"
        data = bytes([19, 5, 0, 0, 0, 0, 3])

        assert (gb.add_checksum(data))[
            checksum_index
        ] == 24, "19,5,0,0,0,0,3 Checksum wrong"
        data = bytes([19, 5, 10, 10, 10, 0, 1])

        assert (gb.add_checksum(data))[
            checksum_index
        ] == 54, "19,5,10,10,10,0,1 Checksum wrong"
        data = bytes([19, 5, 10, 10, 10, 5, 1])

        assert (gb.add_checksum(data))[
            checksum_index
        ] == 54, "19,5,7,2,3,5,1 Checksum wrong"
        data = bytes([255, 255, 255, 255, 3, 0, 1])

        assert (gb.add_checksum(data))[
            checksum_index
        ] == 255, "255,255,255,255,3,0,1 Checksum wrong"
        data = bytes([255, 255, 255, 255, 4, 0, 1])

        assert (gb.add_checksum(data))[
            checksum_index
        ] == 0, "255,255,255,255,4,0,1 Checksum wrong"
        data = bytes([1, 2, 3])

        assert (gb.add_checksum(data)) is None, "1,2,3 Checksum not None"
        data = bytes([1, 2, 3, 4, 5, 6, 7, 8])

        assert (gb.add_checksum(data)) is None, "1,2,3,4,5,6,7,8 Checksum not None"

        gb.log_print(f"--- {test} passed")
        return True
    except AssertionError as exc:
        gb.log_print(f"xxx {test} failed: {str(exc)}")
        return False


async def test_send_periodic(gap=2, resends=12, resend_gap=0, count=20, tolerance=0.2):
    """Test if signals are lost and if the time gap between signals
    is withing the specified tolerance

    """
    test = "test_send_periodic"
    gb.log_print(f"--- Starting {test}")
    gb.log_print(locals())
    called = False
    failed_counter = 0
    received = 0
    last_received = 0

    async def callback(bridge: gb.Bridge, **signal):
        nonlocal called, received, last_received, tolerance, failed_counter
        gap_measured = time.time() - last_received

        try:
            if received != 0:
                assert (
                    gap_measured < gap + tolerance
                ), f"Signal {received} slow: gap={gap_measured} s"

                assert (
                    gap_measured >= gap - tolerance
                ), f"Signal {received} fast: gap={gap_measured} s"

        except AssertionError as exc:
            gb.log_print(str(exc))
            failed_counter += 1

        received += 1
        called = True
        last_received = time.time()

    bridge = gb.Bridge()
    try:
        assert await bridge.connect(
            "GravitraxConnect", timeout=20
        ), f"{test}: connect failed"

        assert await bridge.notification_enable(
            callback
        ), f"{test}: enabling Notifications failed"

        await bridge.send_periodic(
            0, 1, stone=5, count=count, gap=gap, resend_gap=resend_gap, resends=resends
        )
        while True:
            await asyncio.sleep(2)
            if time.time() - last_received > 5 + gap:
                break

        assert called, f"{test}: Callback was not called"
        assert received == count, f"received {received}/{count} packages"

        assert (
            failed_counter == 0
        ), f"Gap for {failed_counter}/{count} not in {tolerance}s tolerance"
        gb.log_print(f"--- {test} passed")

        return True
    except AssertionError as exc:
        gb.log_print(f"xxx {test} failed: {str(exc)}")
        return False
    finally:
        if await bridge.is_connected():
            await bridge.notification_disable()
            await bridge.disconnect()
            await wait_for_disconnect(bridge)


async def test_bridge_info():
    """Test if reading out the Firmware and Hardware version works
    correctly
    """
    test = "test_bridge_info"
    gb.log_print(f"--- Starting {test}")
    bridge = gb.Bridge()
    try:
        assert await bridge.connect("GravitraxConnect"), "connect failed"
        info = await bridge.request_bridge_info()
        assert info is not None, "No info received"
        assert int(info[0]) > 12, "Wrong Firmware Version detected"
        assert int(info[1]) >= 1, "Wrong hardware version detected"
        assert await bridge.disconnect(), "disconnect failed"

        assert await wait_for_disconnect(bridge), "Disconnect timed out"
        gb.log_print(f"--- {test} passed")

    except AssertionError as exc:
        gb.log_print(f"xxx {test} failed: {str(exc)}")
        return False
    finally:
        if await bridge.is_connected():
            await bridge.disconnect()
            await wait_for_disconnect(bridge)


async def test_request_battery():
    """Test if reading out the battery level works correctly"""
    test = "test_request_battery"
    gb.log_print(f"--- Starting {test}")
    bridge = gb.Bridge()
    try:
        assert await bridge.connect("GravitraxConnect"), "connect failed"

        level = await bridge.request_battery()
        assert level is not None, "Reading battery level failed"
        assert level >= 2 and level <= 3.1, "battery level outside known range"

        assert await bridge.disconnect(), "disconnect failed"
        assert await wait_for_disconnect(bridge), "Disconnect timed out"
        gb.log_print(f"--- {test} passed")
    except AssertionError as exc:
        gb.log_print(f"xxx {test} failed: {str(exc)}")
        return False
    finally:
        if await bridge.is_connected():
            await bridge.disconnect()
            await wait_for_disconnect(bridge)


async def test_get_address():
    """test if reading out the address of the bridge works correctly"""
    test = "test_get_address"
    gb.log_print(f"--- Starting {test}")
    bridge = gb.Bridge()
    try:
        assert await bridge.connect("GravitraxConnect"), "connect failed"

        address = bridge.get_address()
        assert address is not None, "No address received"
        assert re.match(
            "([0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}", address
        ), "wrong address format"

        assert await bridge.disconnect(), "disconnect failed"
        assert await wait_for_disconnect(bridge), "Disconnect timed out"
        gb.log_print(f"--- {test} passed")
    except AssertionError as exc:
        gb.log_print(f"xxx {test} failed: {str(exc)}")
        return False
    finally:
        if await bridge.is_connected():
            await bridge.disconnect()
            await wait_for_disconnect(bridge)


async def test_get_name(name="GravitraxConnect"):
    """Test if reading out the name of the bridge works correctly"""
    test = "test_get_name"
    gb.log_print(f"--- Starting {test}")
    gb.log_print(locals())
    bridge = gb.Bridge()
    try:
        assert await bridge.connect(name), "connect failed"
        assert bridge.get_name() == name, "wrong name received"
        assert await bridge.disconnect(), "disconnect failed"
        assert await wait_for_disconnect(bridge), "Disconnect timed out"
        gb.log_print(f"--- {test} passed")
    except AssertionError as exc:
        gb.log_print(f"xxx {test} failed: {str(exc)}")
        return False
    finally:
        if await bridge.is_connected():
            await bridge.disconnect()
            await wait_for_disconnect(bridge)


async def main():
    """Run all testcases for the gravitraxconnect library"""
    # Additional logging output
    gb.logger.disabled = False
    gb.log_set_level("INFO")
    try:
        # test cases
        
        await test_scan()
        await test_connect_disconnect()
        await test_disconnect_timeout()
        await test_double_connect()
        await test_connect_timeout()
        await test_disconnect_callback()
        await test_reconnect()
        await test_notifications()
        await test_send(count=100, resends=10, resend_gap=0)
        await test_send(count=100, resends=10, resend_gap=0.01)
        await test_send_bytes(count=100, resends=12, resend_gap=0)
        await test_send_bytes(count=100, resends=12, resend_gap=0.01)
        await test_signal_roundtrip_time(
            count=30, threshold=0.25, resends=5, resend_gap=0.01, signal_gap=0
        )
        await test_signal_roundtrip_time(
            count=30, threshold=0.25, resends=12, resend_gap=0.01, signal_gap=0
        )
        await test_signal_roundtrip_time(
            count=30, threshold=0.25, resends=5, resend_gap=0.1, signal_gap=1
        )
        await test_signal_roundtrip_time(
            count=30, threshold=0.25, resends=12, resend_gap=0.1, signal_gap=1
        )
        await test_send_periodic()
        await test_add_checksum()
        await test_bridge_info()
        await test_request_battery()
        await test_get_address()
        await test_get_name()
        
    except asyncio.CancelledError:
        return


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        gb.log_print("Program finished")
