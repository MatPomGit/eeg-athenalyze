"""External OpenMuse invocation is isolated and non-destructive."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from eeg_athenalyze.openmuse_external import capture_openmuse, find_openmuse


class OpenMuseExternalTests(unittest.TestCase):
    def test_find_runs_upstream_discovery_without_shell(self):
        with patch("eeg_athenalyze.openmuse_external.shutil.which", return_value="OpenMuse.exe"):
            with patch("eeg_athenalyze.openmuse_external.subprocess.run") as execute:
                execute.return_value.returncode = 0
                self.assertEqual(find_openmuse(), 0)
                execute.assert_called_once_with(["OpenMuse.exe", "find"], check=False)

    def test_raw_capture_requires_nonempty_output(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "raw.txt"
            def create_raw(args, check):
                self.assertEqual(args[1:4], ["record", "--address", "selected-device"])
                self.assertEqual(args[-2:], ["--outfile", str(path)])
                path.write_bytes(b"raw demo packet fixture")
                return type("Result", (), {"returncode": 0})()
            with patch("eeg_athenalyze.openmuse_external.shutil.which", return_value="OpenMuse.exe"):
                with patch("eeg_athenalyze.openmuse_external.subprocess.run", side_effect=create_raw):
                    self.assertEqual(capture_openmuse("selected-device", path), path)
            self.assertEqual(path.read_bytes(), b"raw demo packet fixture")
            with self.assertRaises(FileExistsError):
                capture_openmuse("selected-device", path)

    def test_invalid_address_and_duration(self):
        with self.assertRaises(ValueError):
            capture_openmuse("", Path("raw.txt"))
        with self.assertRaises(ValueError):
            capture_openmuse("known", Path("raw.txt"), duration=0)

    def test_success_without_file_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "raw.txt"
            with patch("eeg_athenalyze.openmuse_external.shutil.which", return_value="OpenMuse.exe"):
                with patch("eeg_athenalyze.openmuse_external.subprocess.run") as execute:
                    execute.return_value.returncode = 0
                    with self.assertRaisesRegex(RuntimeError, "nonempty"):
                        capture_openmuse("known", path)
