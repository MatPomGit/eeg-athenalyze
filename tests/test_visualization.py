"""Read-only EEGZ plot command regression tests."""
import tempfile
import unittest
from pathlib import Path

from eeg_athenalyze.archive import save_recording
from eeg_athenalyze.recording import Recording
from eeg_athenalyze.visualization import read_samples


class VisualizationTests(unittest.TestCase):
    def test_archive_readback_for_plot(self):
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "test.eegz"
            recording = Recording(
                recording_id="test", sample_rate_hz=256,
                channel_names=("TP9", "AF7"),
                samples_uv=((1., 2.), (3., 4.)),
                timestamps_seconds=(0., 0.),
                metadata={"data_status": "measured"},
            )
            save_recording(recording, destination)
            channels, samples, timestamps, sampling_rate, label = read_samples(destination)
            self.assertEqual(channels, ("TP9", "AF7"))
            self.assertEqual(len(samples), 2)
            self.assertEqual(timestamps, (0., 0.))
            self.assertEqual(sampling_rate, 256)
            self.assertEqual(label, "EEGZ archive")

    def test_partial_journal_readback(self):
        with tempfile.TemporaryDirectory() as directory:
            journal = Path(directory) / "trial.eegz.partial.jsonl"
            journal.write_text(
                '{"timestamp":12.0,"channels_uv":[1,2,3,4]}\n'
                '{"timestamp":12.0,"channels_uv":[5,6,7,8]}\n'
                '{"timestamp":',
                encoding="utf-8",
            )
            channels, samples, times, _, label = read_samples(journal)
            self.assertEqual(channels, ("TP9", "AF7", "AF8", "TP10"))
            self.assertEqual(len(samples), 2)
            self.assertEqual(times, [12., 12.])
            self.assertEqual(label, "partial journal")
