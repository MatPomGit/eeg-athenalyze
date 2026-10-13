"""Measured timestamp duplicates are preserved, synthetic timelines stay strict."""
import tempfile
import unittest
from pathlib import Path

from eeg_athenalyze.acquisition_journal import AcquisitionJournal, recover_journal
from eeg_athenalyze.archive import save_recording, load_recording
from eeg_athenalyze.recording import Recording


class Matrix:
    def __init__(self, values):
        self.values = values

    def tolist(self):
        return self.values


class DuplicateTimestampTests(unittest.TestCase):
    def test_measured_duplicates_survive_journal_and_archive(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "source.eegz"
            with AcquisitionJournal(source, channel_count=2) as journal:
                journal.append(Matrix([[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]]),
                               Matrix([100.0, 100.0, 100.004]))
            rows, times = recover_journal(Path(str(source) + ".partial.jsonl"), channel_count=2)
            self.assertEqual(times, [100.0, 100.0, 100.004])
            recording = Recording(
                recording_id="measured-test", sample_rate_hz=256,
                channel_names=("TP9", "AF7"),
                samples_uv=tuple(map(tuple, rows)),
                timestamps_seconds=tuple(t - times[0] for t in times),
                metadata={"data_status": "measured", "duplicate_source_timestamps": 1},
            )
            save_recording(recording, source)
            self.assertEqual(load_recording(source).timestamps_seconds, (0., 0., .004))

    def test_synthetic_duplicate_is_not_permitted(self):
        with self.assertRaises(ValueError):
            Recording(
                recording_id="synthetic-test", sample_rate_hz=256,
                channel_names=("TP9",),
                samples_uv=((1.,), (2.,)),
                timestamps_seconds=(0., 0.),
                metadata={"data_status": "simulated"},
            )
