"""Offline derivatives tests, including source immutability."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from eeg_athenalyze.archive import save_recording
from eeg_athenalyze.derivatives import export_alpha_derivatives
from eeg_athenalyze.experiments.eyes_open_closed import (
    EyesOpenClosedConfig, run_eyes_open_closed,
)
from eeg_athenalyze.recording import SyntheticConfig


class DerivativesTests(unittest.TestCase):
    def test_alpha_table_and_source_immutability(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = run_eyes_open_closed(root, config=EyesOpenClosedConfig(
                stabilization_seconds=0.5, eyes_open_seconds=4,
                break_seconds=0.5, eyes_closed_seconds=4,
                participant_id="sub001", session_id="01",
                synthetic=SyntheticConfig(seed=10, sample_rate_hz=128),
            ))
            before = result.archive_path.read_bytes()
            bids = root / "bids"
            bids.mkdir()
            (bids / "dataset_description.json").write_text(
                '{"BIDSVersion":"1.10.0","Name":"Synthetic test"}'
            )
            derivative = export_alpha_derivatives(result.archive_path, bids)
            self.assertTrue(derivative.is_file())
            self.assertTrue(derivative.with_suffix(".json").is_file())
            metadata = json.loads(derivative.with_suffix(".json").read_text())
            self.assertEqual(metadata["DataStatus"], "simulated")
            self.assertEqual(result.archive_path.read_bytes(), before)
            with self.assertRaises(FileExistsError):
                export_alpha_derivatives(result.archive_path, bids)

    def test_rejects_dataset_without_description(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                export_alpha_derivatives(Path(tmp) / "missing.eegz", Path(tmp))
