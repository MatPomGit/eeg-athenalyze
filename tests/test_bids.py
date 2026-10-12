"""BIDS export integration tests; optional dependencies required."""
import tempfile
from dataclasses import replace
import unittest
from pathlib import Path

from eeg_athenalyze.archive import save_recording
from eeg_athenalyze.recording import SyntheticConfig, generate_synthetic_recording


class BidsExportTests(unittest.TestCase):
    def test_export_roundtrip(self):
        try:
            import mne_bids  # noqa: F401
            import pybv  # noqa: F401
        except ImportError:
            self.skipTest("Install project with [bids] extra")
        from eeg_athenalyze.bids import export_bids
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            recording = generate_synthetic_recording(
                4, config=SyntheticConfig(seed=4), condition="eyes_closed"
            )
            source = save_recording(recording, root / "original.eegz")
            digest = source.read_bytes()
            destination = export_bids(source, root / "dataset")
            self.assertTrue(list(destination.rglob("*_eeg.vhdr")))
            self.assertEqual(digest, source.read_bytes())
            with self.assertRaises(FileExistsError):
                export_bids(source, destination)

    def test_rejects_nonfinite_event_timing_without_writing_dataset(self):
        try:
            import mne_bids  # noqa: F401
        except ImportError:
            self.skipTest("Install project with [bids] extra")
        from eeg_athenalyze.bids import export_bids
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            recording = generate_synthetic_recording(2)
            damaged = replace(recording, metadata={
                **recording.metadata,
                "events": [{"condition": "eyes_open", "onset_seconds": float("nan"), "duration_seconds": 0.5}],
            })
            # The checksummed archive intentionally rejects non-JSON-safe NaN.
            # Use an invalid but JSON-safe negative duration to exercise export.
            damaged.metadata["events"][0]["onset_seconds"] = 0.0
            damaged.metadata["events"][0]["duration_seconds"] = -0.5
            source = save_recording(damaged, root / "bad.eegz")
            with self.assertRaises(ValueError):
                export_bids(source, root / "invalid")
            self.assertFalse((root / "invalid").exists())

    def test_rejects_invalid_line_frequency(self):
        try:
            import mne_bids  # noqa: F401
        except ImportError:
            self.skipTest("Install project with [bids] extra")
        from eeg_athenalyze.bids import export_bids
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            recording = generate_synthetic_recording(2)
            source = save_recording(recording, root / "original.eegz")
            with self.assertRaises(ValueError):
                export_bids(source, root / "bad", power_line_frequency=float("nan"))
            self.assertFalse((root / "bad").exists())

    def test_missing_validator_fails_closed(self):
        from eeg_athenalyze.bids import validate_bids
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(RuntimeError):
                validate_bids(Path(folder), executable="certainly-not-installed-validator")
