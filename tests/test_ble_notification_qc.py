"""Offline BLE notifications diagnostic without physical hardware."""
import json
import tempfile
import unittest
from pathlib import Path

from eeg_athenalyze.ble_notification_qc import (
    SENSOR_SUFFIXES, summarize_notification_journal, write_notification_summary,
)


def frame(tag=0x11, index=7):
    payload = bytes(28)
    return (bytes([14 + len(payload)]) + index.to_bytes(2, "little")
            + bytes(6) + bytes([tag, 0]) + bytes(3) + payload).hex()


class NotificationQCTests(unittest.TestCase):
    def record(self, t, raw=None):
        return {"receive_monotonic_seconds": t, "characteristic": SENSOR_SUFFIXES[0],
                "payload_hex": frame() if raw is None else raw}

    def test_repeated_notification_is_not_claimed_as_packet_loss(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "raw.jsonl"
            rows = [self.record(1), self.record(1.01), self.record(3, "ff")]
            source.write_text("".join(json.dumps(x) + "\n" for x in rows), encoding="utf-8")
            report = summarize_notification_journal(source)
            self.assertEqual(report["notification_count"], 3)
            self.assertEqual(report["parsed_notification_count"], 2)
            self.assertEqual(report["invalid_notification_count"], 1)
            self.assertEqual(report["tags"], {"0x11": 2})
            self.assertEqual(report["primary_frame_count"], 2)
            self.assertEqual(report["nominal_eeg_sample_positions"], 8)
            self.assertEqual(report["adjacent_repeated_primary_indices"], 1)
            self.assertIsNone(report["packet_loss_estimate"])
            self.assertAlmostEqual(report["largest_host_notification_gap_seconds"], 1.99)
            output = Path(folder) / "summary.json"
            write_notification_summary(source, output)
            self.assertNotIn("payload_hex", output.read_text())
            with self.assertRaises(FileExistsError):
                write_notification_summary(source, output)

    def test_schema_rejects_invalid_clocks_or_characteristics(self):
        bad = [self.record(-1), self.record(float("nan")),
               {**self.record(0), "characteristic": "unknown"},
               {**self.record(0), "payload_hex": "0"},
               {**self.record(0), "payload_hex": "gg"}]
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "bad.jsonl"
            for row in bad:
                with self.subTest(row=row):
                    source.write_text(json.dumps(row) + "\n")
                    with self.assertRaises(ValueError):
                        summarize_notification_journal(source)
            source.write_text(json.dumps(self.record(2)) + "\n" +
                              json.dumps(self.record(1)) + "\n")
            with self.assertRaisesRegex(ValueError, "nonmonotonic"):
                summarize_notification_journal(source)

    def test_empty_capture_is_unverified_not_successful_stream(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "empty.jsonl"
            source.write_text("")
            r = summarize_notification_journal(source)
            self.assertEqual(r["notification_count"], 0)
            self.assertIsNone(r["first_host_monotonic_seconds"])


if __name__ == "__main__":
    unittest.main()

class MultiplePrimaryFrameTests(unittest.TestCase):
    def test_concatenated_frames_and_subpacket_not_double_counted(self):
        import json
        from eeg_athenalyze.ble_notification_qc import SENSOR_SUFFIXES
        # One notification, two primaries; first has a tagged EEG subpacket.
        first_payload = bytes(28) + bytes([0x11, 4, 0, 0, 0]) + bytes(28)
        def make(index, payload):
            size = 14 + len(payload)
            return (bytes([size]) + index.to_bytes(2, "little")
                    + bytes(6) + bytes([0x11, 3]) + bytes(3) + payload)
        raw = make(5, first_payload) + make(6, bytes(28))
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "multi.jsonl"
            source.write_text(json.dumps({
                "receive_monotonic_seconds": 1.0,
                "characteristic": SENSOR_SUFFIXES[0],
                "payload_hex": raw.hex(),
            }) + "\n")
            report = summarize_notification_journal(source)
            self.assertEqual(report["notification_count"], 1)
            self.assertEqual(report["primary_frame_count"], 2)
            self.assertEqual(report["eeg_tag_count"], 3)
            self.assertEqual(report["nominal_eeg_sample_positions"], 12)
            self.assertEqual(report["first_parsed_packet_index"], 5)
            self.assertEqual(report["last_parsed_packet_index"], 6)
            self.assertIsNone(report["packet_loss_estimate"])
