import tempfile
import unittest
from pathlib import Path

from eeg_athenalyze.archive import save_recording
from eeg_athenalyze.recording import generate_synthetic_recording
from eeg_athenalyze.hardware_validation import assess_archive


class HardwareValidationTests(unittest.TestCase):
    def test_reject_synthetic_archive(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = save_recording(generate_synthetic_recording(1), root / "demo.eegz")
            with self.assertRaisesRegex(ValueError, "measured"):
                assess_archive(source, root / "qc.json")
            self.assertFalse((root / "qc.json").exists())
