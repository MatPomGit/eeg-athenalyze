"""M03 tests without Bluetooth hardware or BrainFlow installation."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from eeg_athenalyze.muse_athena import AthenaSettings, record_athena, validate_sample_coverage


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

class PhysicalCompletenessTests(unittest.TestCase):
    def test_short_disconnect_is_rejected(self):
        with self.assertRaisesRegex(RuntimeError, "Incomplete physical EEG session"):
            validate_sample_coverage(96, 60.0, 256.0)

    def test_full_sixty_second_session_passes(self):
        validate_sample_coverage(15520, 60.0, 256.0)

    def test_short_mock_diagnostic_is_not_rejected(self):
        validate_sample_coverage(4, 0.05, 256.0)

class AthenaPresetTests(unittest.TestCase):
    def test_allowed_presets_and_latency_flags(self):
        from eeg_athenalyze.muse_athena import make_preset_command
        for preset in ("p21", "p1035", "p1041"):
            for enabled in (False, True):
                command = make_preset_command(preset, enabled)
                self.assertEqual(
                    AthenaSettings(preset_command=command).preset_command,
                    command,
                )

    def test_reject_unverified_raw_commands(self):
        from eeg_athenalyze.muse_athena import make_preset_command
        with self.assertRaises(ValueError):
            make_preset_command("p1034;dc001", True)
        with self.assertRaisesRegex(ValueError, "Unsupported"):
            AthenaSettings(preset_command="preset=p21;low_latency=maybe")
