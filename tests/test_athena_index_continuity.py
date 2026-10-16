"""Synthetic fixture tests for independent per-characteristic index evidence."""
import json
import tempfile
import unittest
from pathlib import Path

from eeg_athenalyze.athena_index_continuity import summarize_index_continuity
from eeg_athenalyze.ble_notification_qc import SENSOR_SUFFIXES

def frame(index: int) -> bytes:
    return bytes([42]) + index.to_bytes(2, "little") + bytes(6) + bytes([0x11, 0]) + bytes(3) + bytes(28)

class PacketContinuityTests(unittest.TestCase):
    def test_wrap_repeats_jumps_and_separate_characteristics(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "synthetic.jsonl"
            records = []
            for uuid, indexes in (
                (SENSOR_SUFFIXES[0], (65534, 65535, 0, 0, 3)),
                (SENSOR_SUFFIXES[1], (8, 9)),
            ):
                for index in indexes:
                    records.append({"characteristic": uuid, "payload_hex": frame(index).hex()})
            source.write_text("\n".join(map(json.dumps, records)) + "\n")
            result = summarize_index_continuity(source)
            primary = result["streams"][SENSOR_SUFFIXES[0]]
            secondary = result["streams"][SENSOR_SUFFIXES[1]]
            self.assertEqual(primary["primary_frames"], 5)
            self.assertEqual(primary["successive_index_transitions"], 2)
            self.assertEqual(primary["repeated_index_transitions"], 1)
            self.assertEqual(primary["jump_candidate_transitions"], 1)
            self.assertEqual(secondary["primary_frames"], 2)
            self.assertEqual(secondary["jump_candidate_transitions"], 0)
            self.assertIsNone(result["bluetooth_packet_loss_count"])
            self.assertFalse(result["counter_semantics_verified_on_device"])

    def test_multiple_primaries_one_callback(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "synthetic.jsonl"
            source.write_text(json.dumps({"characteristic": SENSOR_SUFFIXES[0],
                                          "payload_hex": (frame(20) + frame(21)).hex()}) + "\n")
            result = summarize_index_continuity(source)["streams"][SENSOR_SUFFIXES[0]]
            self.assertEqual(result["primary_frames"], 2)
            self.assertEqual(result["successive_index_transitions"], 1)

    def test_malformed_notification_not_treated_as_missing_radio_packet(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "synthetic.jsonl"
            source.write_text(json.dumps({"characteristic": SENSOR_SUFFIXES[0],
                                          "payload_hex": "01"}) + "\n")
            result = summarize_index_continuity(source)
            self.assertEqual(result["invalid_notifications"], 1)
            self.assertIsNone(result["bluetooth_packet_loss_count"])
