import tempfile
import unittest
import zipfile
from pathlib import Path

from eeg_athenalyze.archive import load_recording, save_recording
from eeg_athenalyze.recording import SyntheticConfig, generate_synthetic_recording


class RecordingArchiveTests(unittest.TestCase):
    def setUp(self):
        self.recording = generate_synthetic_recording(
            0.25,
            config=SyntheticConfig(
                sample_rate_hz=128,
                seed=11,
                blink_rate_hz=0,
                muscle_burst_rate_hz=0,
            ),
        )
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.path = Path(self.temporary_directory.name) / "session.eegz"

    def test_archive_round_trip_preserves_raw_samples_and_metadata(self):
        save_recording(self.recording, self.path)

        self.assertEqual(load_recording(self.path), self.recording)

    def test_saving_never_overwrites_an_existing_recording(self):
        save_recording(self.recording, self.path)
        original_bytes = self.path.read_bytes()
        replacement = generate_synthetic_recording(
            0.5, config=SyntheticConfig(sample_rate_hz=128, seed=12)
        )

        with self.assertRaises(FileExistsError):
            save_recording(replacement, self.path)
        self.assertEqual(self.path.read_bytes(), original_bytes)

    def test_checksum_mismatch_is_rejected(self):
        save_recording(self.recording, self.path)
        tampered_path = Path(self.temporary_directory.name) / "tampered.eegz"
        with zipfile.ZipFile(self.path, mode="r") as source:
            members = {name: source.read(name) for name in source.namelist()}
        members["recording.json"] += b" "
        with zipfile.ZipFile(tampered_path, mode="w") as target:
            for name, content in members.items():
                target.writestr(name, content)

        with self.assertRaisesRegex(ValueError, "checksum mismatch"):
            load_recording(tampered_path)


if __name__ == "__main__":
    unittest.main()
