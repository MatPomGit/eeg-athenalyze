"""Mock BLE tests, with no physical hardware access."""
import asyncio
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from eeg_athenalyze.ble_raw_collector import (
    collect, frame_control_command, CONTROL_UUID,
)
from eeg_athenalyze.ble_notification_qc import SENSOR_SUFFIXES


class Scanner:
    @staticmethod
    async def discover(timeout):
        return [SimpleNamespace(name="MuseS-TEST")]


class Client:
    def __init__(self, device, timeout):
        self.is_connected = True
        self.services = [SimpleNamespace(characteristics=[
            SimpleNamespace(uuid=SENSOR_SUFFIXES[0], properties=["notify"]),
            SimpleNamespace(uuid=SENSOR_SUFFIXES[1], properties=["read"]),
            SimpleNamespace(uuid=CONTROL_UUID, properties=["write"]),
        ])]
        self.commands = []
        self.stopped = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, *unused):
        self.is_connected = False

    async def start_notify(self, uuid, callback):
        self.callback = callback
        callback(SimpleNamespace(uuid=uuid), bytes([42]) + bytes(2) + bytes(6)
                 + bytes([0x11, 0]) + bytes(3) + bytes(28))

    async def stop_notify(self, uuid):
        self.stopped.append(uuid)

    async def write_gatt_char(self, uuid, data, response):
        self.commands.append(data)


class QuietClient(Client):
    async def start_notify(self, uuid, callback):
        self.callback = callback


class RawCollectorTests(unittest.TestCase):
    def test_control_command_allowlist(self):
        self.assertEqual(frame_control_command("dc001"), b"\x06dc001\n")
        with self.assertRaises(ValueError):
            frame_control_command("p9999")

    def test_capture_and_qc_compatible(self):
        from eeg_athenalyze.ble_notification_qc import summarize_notification_journal
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "raw.jsonl"
            result = asyncio.run(collect(output, name="MuseS-TEST", duration=0.001,
                                         bleak_client=Client, bleak_scanner=Scanner,
                                         start_stream=True, preset="p21"))
            self.assertEqual(result["notification_count"], 1)
            self.assertEqual(result["notifiable_characteristics"], [SENSOR_SUFFIXES[0]])
            report = summarize_notification_journal(output)
            self.assertEqual(report["parsed_notification_count"], 1)
            rows = output.read_text().splitlines()
            self.assertEqual(len(rows), 1)
            self.assertIn("receive_monotonic_seconds", json.loads(rows[0]))
            with self.assertRaises(FileExistsError):
                asyncio.run(collect(output, name="MuseS-TEST", duration=0.001,
                                    bleak_client=Client, bleak_scanner=Scanner))

    def test_zero_notifications_preserves_empty_raw_file(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "empty.jsonl"
            with self.assertRaisesRegex(RuntimeError, "No BLE notifications"):
                asyncio.run(collect(output, name="MuseS-TEST", duration=0.001,
                                    bleak_client=QuietClient, bleak_scanner=Scanner))
            self.assertTrue(output.exists())
            self.assertEqual(output.stat().st_size, 0)

    def test_invalid_parameters_fail_before_io(self):
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder) / "raw.jsonl"
            for overrides in ({"duration": 0}, {"preset": "p999"}, {"name": ""}):
                with self.subTest(overrides=overrides), self.assertRaises(ValueError):
                    asyncio.run(collect(p, name="MuseS-TEST", duration=1,
                                        bleak_client=Client, bleak_scanner=Scanner,
                                        **overrides))
            self.assertFalse(p.exists())


if __name__ == "__main__":
    unittest.main()
