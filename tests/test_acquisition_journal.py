"""Crash-recoverable physical EEG journal: deterministic filesystem tests."""
import tempfile
import unittest
from pathlib import Path

from eeg_athenalyze.acquisition_journal import AcquisitionJournal, recover_journal


class ArrayStub:
    def __init__(self, rows):
        self.rows = rows

    def tolist(self):
        return self.rows


class JournalTests(unittest.TestCase):
    def test_recover_complete_rows_after_torn_tail(self):
        with tempfile.TemporaryDirectory() as directory:
            dest = Path(directory) / "session.eegz"
            with AcquisitionJournal(dest, channel_count=2) as writer:
                writer.append(ArrayStub([[1., 2.], [3., 4.]]), ArrayStub([10., 10.004]))
                self.assertEqual(writer.sample_count, 2)
            journal = Path(str(dest) + ".partial.jsonl")
            with journal.open("ab") as handle:
                handle.write(b'{"timestamp":10.008,"chan')
            rows, times = recover_journal(journal, channel_count=2)
            self.assertEqual(rows, [[1., 2.], [3., 4.]])
            self.assertEqual(times, [10., 10.004])
            with self.assertRaises(FileExistsError):
                AcquisitionJournal(dest, channel_count=2)

    def test_duplicate_timestamp_identifies_sample_and_preserves_prior_chunk(self):
        with tempfile.TemporaryDirectory() as directory:
            dest = Path(directory) / "record.eegz"
            with AcquisitionJournal(dest, channel_count=2) as writer:
                writer.append(ArrayStub([[1.0, 2.0]]), ArrayStub([100.0]))
                writer.append(ArrayStub([[3.0, 4.0]]), ArrayStub([100.0]))
            rows, times = recover_journal(Path(str(dest) + ".partial.jsonl"), channel_count=2)
            self.assertEqual(rows, [[1.0, 2.0], [3.0, 4.0]])
            self.assertEqual(times, [100.0, 100.0])

    def test_invalid_chunk_is_not_written(self):
        with tempfile.TemporaryDirectory() as directory:
            dest = Path(directory) / "session.eegz"
            with AcquisitionJournal(dest, channel_count=2) as writer:
                with self.assertRaises(ValueError):
                    writer.append(ArrayStub([[1., 2.]]), ArrayStub([float("nan")]))
            self.assertEqual(recover_journal(Path(str(dest) + ".partial.jsonl"), channel_count=2), ([], []))
