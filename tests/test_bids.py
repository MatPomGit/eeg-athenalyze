"""BIDS export integration tests; optional dependencies required."""
import tempfile
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

    def test_missing_validator_fails_closed(self):
        from eeg_athenalyze.bids import validate_bids
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(RuntimeError):
                validate_bids(Path(folder), executable="certainly-not-installed-validator")
