import asyncio
import unittest
from contextlib import suppress
from unittest.mock import AsyncMock, patch

from gravitraxconnect import gravitrax_bridge as gb


class _FakeClientTimeout:
    def __init__(self, *_args, **_kwargs):
        self.mtu_size = 23

    async def connect(self, timeout):
        raise TimeoutError()


class _FakeScanner:
    def __init__(self, *_args, **_kwargs):
        pass

    async def start(self):
        return None

    async def stop(self):
        return None


class _FakeScannerStopOnHit:
    emitted_addresses = []

    def __init__(self, discover_callback, *_args, **_kwargs):
        self._discover_callback = discover_callback
        self._task = None
        self._stopped = False

    async def _emit_devices(self):
        first_device = type(
            "FakeDevice", (), {"name": "GravitraxConnect", "address": "11:22:33"}
        )()
        second_device = type(
            "FakeDevice", (), {"name": "GravitraxConnect", "address": "44:55:66"}
        )()
        fake_advertisement = type("FakeAd", (), {"local_name": "GravitraxConnect"})()

        self._discover_callback(first_device, fake_advertisement)
        _FakeScannerStopOnHit.emitted_addresses.append(first_device.address)

        # Give scan_bridges() a chance to stop the scanner after the first hit.
        await asyncio.sleep(0.05)
        if not self._stopped:
            self._discover_callback(second_device, fake_advertisement)
            _FakeScannerStopOnHit.emitted_addresses.append(second_device.address)

    async def start(self):
        _FakeScannerStopOnHit.emitted_addresses = []
        self._task = asyncio.create_task(self._emit_devices())

    async def stop(self):
        self._stopped = True
        if self._task:
            self._task.cancel()
            with suppress(asyncio.CancelledError):
                await self._task


class UnitTests(unittest.IsolatedAsyncioTestCase):
    async def test_connect_timeout_returns_false(self):
        bridge = gb.Bridge()
        fake_device = type(
            "FakeDevice", (), {"name": "GravitraxConnect", "address": "AA:BB:CC"}
        )()

        with (
            patch.object(gb, "BLEDevice", object),
            patch.object(
                gb.BleakScanner,
                "find_device_by_filter",
                new=AsyncMock(return_value=fake_device),
            ),
            patch.object(gb, "BleakClient", _FakeClientTimeout),
        ):
            result = await bridge.connect("GravitraxConnect")

        self.assertFalse(result)

    async def test_notification_handler_drops_wrong_checksum(self):
        bridge = gb.Bridge()
        received = 0

        async def callback(_bridge, **_signal):
            nonlocal received
            received += 1

        bridge.noti_callback = callback

        # 0x00 is intentionally wrong here so the packet must be discarded.
        bad_signal = bytearray([0x13, 0x01, 0x02, 0x03, 0x04, 0x00, 0x01])
        await bridge._Bridge__notification_handler(None, bad_signal)

        self.assertEqual(received, 0)

    async def test_scan_bridges_uses_float_timeout(self):
        with (
            patch.object(gb, "BleakScanner", _FakeScanner),
            patch.object(gb.asyncio, "sleep", new=AsyncMock()) as sleep_mock,
        ):
            await gb.scan_bridges(timeout=0.75)

        sleep_mock.assert_awaited_once_with(0.75)

    async def test_scan_bridges_stop_on_hit_returns_early(self):
        with patch.object(gb, "BleakScanner", _FakeScannerStopOnHit):
            addresses = await gb.scan_bridges(timeout=5, stop_on_hit=True)

        self.assertEqual(addresses, ["11:22:33"])
        self.assertEqual(_FakeScannerStopOnHit.emitted_addresses, ["11:22:33"])


if __name__ == "__main__":
    unittest.main()
