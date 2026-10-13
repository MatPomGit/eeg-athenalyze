import tempfile
import unittest
from pathlib import Path

from eeg_athenalyze.archive import save_recording
from eeg_athenalyze.recording import Recording, generate_synthetic_recording
from eeg_athenalyze.hardware_validation import assess_archive


class HardwareValidationTests(unittest.TestCase):
    def test_reject_synthetic_archive(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = save_recording(generate_synthetic_recording(1), root / "demo.eegz")
            with self.assertRaisesRegex(ValueError, "measured"):
                assess_archive(source, root / "qc.json")
            self.assertFalse((root / "qc.json").exists())

    def test_repeated_timestamps_and_high_amplitude_channel(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            measured = Recording(
                recording_id="qc-test",
                sample_rate_hz=256.0,
                channel_names=("TP9", "AF7", "AF8", "TP10"),
                samples_uv=((724.9, 10.0, -11.0, -725.0),
                            (724.9, 12.0, -9.0, -725.0),
                            (0.0, 15.0, -8.0, 0.0)),
                timestamps_seconds=(0.0, 0.0, 0.004),
                metadata={"data_status": "measured", "device_model": "Muse S Athena"},
            )
            archive = save_recording(measured, root / "measured.eegz")
            report = assess_archive(archive, root / "qc.json")
            self.assertEqual(report["duplicate_timestamp_intervals"], 1)
            self.assertEqual(report["backward_timestamp_intervals"], 0)
            self.assertIsNone(report["median_observed_rate_hz"])
            self.assertAlmostEqual(report["channel_ranges_uv"]["TP9"]["fraction_abs_above_700_uv"], 2 / 3)
            self.assertFalse(report["checks"]["timestamp_monotonic"])
            self.assertTrue(report["checks"]["timestamp_nondecreasing"])
