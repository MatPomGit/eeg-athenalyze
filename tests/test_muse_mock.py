"""Mocked physical acquisition lifecycle tests (no BLE device required)."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from eeg_athenalyze.archive import load_recording
from eeg_athenalyze.muse_athena import AthenaSettings, record_athena


class FakeParams:
    serial_number = ""
    mac_address = ""
    other_info = ""


class FakeBoard:
    instances = []

    def __init__(self, board_id, params):
        self.params = params
        self.prepared = False
        self.running = False
        self.stopped = False
        self.released = False
        self.reads = 0
        self.instances.append(self)

    def prepare_session(self):
        self.prepared = True

    def start_stream(self):
        self.running = True

    def get_board_data(self):
        import numpy as np

        self.reads += 1
        if self.reads > 1:
            return np.empty((5, 0))
        return np.asarray([
            [1.0, 2.0, 3.0, 4.0],
            [5.0, 6.0, 7.0, 8.0],
            [9.0, 10.0, 11.0, 12.0],
            [13.0, 14.0, 15.0, 16.0],
            [1000.0, 1000.00390625, 1000.0078125, 1000.01171875],
        ])

    def stop_stream(self):
        self.stopped = True

    def release_session(self):
        self.released = True


class AthenaMockIntegration(unittest.TestCase):
    def test_record_and_cleanup(self):
        try:
            import numpy
        except ImportError:
            self.skipTest("numpy is optional outside the Muse extra")
        FakeBoard.instances.clear()
        info = {
            "eeg_indices": [0, 1, 2, 3],
            "timestamp_channel": 4,
            "sampling_rate_hz": 256,
        }
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "real.eegz"
            with (
                patch("eeg_athenalyze.muse_athena._api", return_value=(FakeBoard, FakeParams, 99)),
                patch("eeg_athenalyze.muse_athena.device_info", return_value=info),
            ):
                path = record_athena(output, AthenaSettings(duration_seconds=0.06))
            self.assertEqual(path, output)
            self.assertTrue(FakeBoard.instances[0].stopped)
            self.assertTrue(FakeBoard.instances[0].released)
            saved = load_recording(path)
            self.assertEqual(saved.metadata["data_status"], "measured")
            self.assertEqual(saved.metadata["timing_verified"], False)
            self.assertEqual(len(saved.samples_uv), 4)
            self.assertEqual(saved.samples_uv[0], (1.0, 5.0, 9.0, 13.0))
            self.assertEqual(saved.metadata["suspected_timestamp_gaps"], 0)
            with (
                patch("eeg_athenalyze.muse_athena._api", return_value=(FakeBoard, FakeParams, 99)),
                patch("eeg_athenalyze.muse_athena.device_info", return_value=info),
            ):
                with self.assertRaises(FileExistsError):
                    record_athena(output, AthenaSettings(duration_seconds=0.06))
            self.assertEqual(path.read_bytes(), output.read_bytes())
