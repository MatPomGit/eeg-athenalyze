"""M03 tests without Bluetooth hardware or BrainFlow installation."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from eeg_athenalyze.muse_athena import AthenaSettings, record_athena


class AthenaTests(unittest.TestCase):
    def test_invalid_duration(self):
        with self.assertRaises(ValueError):
            AthenaSettings(duration_seconds=-1)

    def test_driver_absence_is_explicit(self):
        with patch("eeg_athenalyze.muse_athena._api", side_effect=RuntimeError("no board")):
            with tempfile.TemporaryDirectory() as tmp:
                destination = Path(tmp) / "physical.eegz"
                with self.assertRaisesRegex(RuntimeError, "no board"):
                    record_athena(destination, AthenaSettings(duration_seconds=0.1))
                self.assertFalse(destination.exists())
