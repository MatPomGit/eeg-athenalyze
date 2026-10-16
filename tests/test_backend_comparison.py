"""Mock-independent sequential BLE/BrainFlow comparison; no human data."""
import json
import tempfile
import unittest
from pathlib import Path

from eeg_athenalyze.archive import save_recording
from eeg_athenalyze.backend_comparison import compare_sequential_sources, write_comparison
from eeg_athenalyze.ble_notification_qc import SENSOR_SUFFIXES
from eeg_athenalyze.recording import Recording


class SequentialBackendTests(unittest.TestCase):
    def make_inputs(self, root):
        payload = bytes([42]) + bytes(2) + bytes(6) + bytes([0x11, 0]) + bytes(3) + bytes(28)
        ble = root / "ble.jsonl"
        ble.write_text(json.dumps({
            "receive_monotonic_seconds": 4.0,
            "characteristic": SENSOR_SUFFIXES[0],
            "payload_hex": payload.hex(),
        }) + "\n")
        eegz = root / "bf.eegz"
        save_recording(Recording(
            recording_id="synthetic",
            sample_rate_hz=256.0,
            channel_names=("TP9", "AF7", "AF8", "TP10"),
            samples_uv=((0.0, 0.0, 0.0, 0.0), (1.0, 2.0, 3.0, 4.0)),
            timestamps_seconds=(1.0, 1.0),
            metadata={"data_status": "measured", "hardware_validated": False},
        ), eegz)
        return ble, eegz

    def test_different_sessions_no_false_loss_or_clock(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            ble, eegz = self.make_inputs(root)
            report = compare_sequential_sources(ble, eegz)
            self.assertEqual(report["ble"]["primary_frame_count"], 1)
            self.assertEqual(report["ble"]["nominal_eeg_sample_positions"], 4)
            self.assertEqual(report["brainflow"]["sample_count"], 2)
            self.assertEqual(report["brainflow"]["duplicate_adjacent_source_timestamps"], 1)
            self.assertIsNone(report["comparison"]["packet_loss_estimate"])
            self.assertFalse(report["comparison"]["same_session"])
            self.assertFalse(report["comparison"]["physical_timing_verified"])
            output = root / "comparison.json"
            write_comparison(ble, eegz, output)
            self.assertNotIn("payload_hex", output.read_text())
            self.assertNotIn("samples_uv", output.read_text())
            with self.assertRaises(FileExistsError):
                write_comparison(ble, eegz, output)

    def test_missing_input_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaises(OSError):
                compare_sequential_sources(root / "missing.jsonl", root / "missing.eegz")


if __name__ == "__main__":
    unittest.main()
