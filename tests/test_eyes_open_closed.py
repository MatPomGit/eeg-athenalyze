import tempfile
import unittest
from pathlib import Path

from eeg_athenalyze.analysis.spectral import compare_resting_alpha
from eeg_athenalyze.archive import load_recording
from eeg_athenalyze.cli import main
from eeg_athenalyze.experiments.eyes_open_closed import (
    EyesOpenClosedConfig,
    run_eyes_open_closed,
)
from eeg_athenalyze.recording import SyntheticConfig


class EyesOpenClosedTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.output = Path(self.temporary_directory.name)
        self.config = EyesOpenClosedConfig(
            stabilization_seconds=0.5,
            eyes_open_seconds=4,
            break_seconds=0.5,
            eyes_closed_seconds=4,
            participant_id="sub001",
            session_id="session01",
            synthetic=SyntheticConfig(
                sample_rate_hz=128,
                seed=10,
                oscillations_uv=(),
                alpha_amplitude_uv=10,
                line_noise_amplitude_uv=0,
                noise_amplitude_uv=0,
                blink_rate_hz=0,
                muscle_burst_rate_hz=0,
            ),
        )

    def test_synthetic_session_archives_events_analysis_and_report(self):
        result = run_eyes_open_closed(self.output, config=self.config)
        restored = load_recording(result.archive_path)
        comparison = compare_resting_alpha(restored)

        self.assertEqual(restored.metadata["data_status"], "simulated")
        self.assertEqual(
            [event["condition"] for event in restored.metadata["events"]],
            ["stabilization", "eyes_open", "break", "eyes_closed"],
        )
        for channel in restored.channel_names:
            self.assertAlmostEqual(
                comparison.eyes_closed_uv2[channel]
                / comparison.eyes_open_uv2[channel],
                4.0,
                places=6,
            )
        report = result.report_path.read_text(encoding="utf-8")
        self.assertIn("Simulated EEG", report)
        self.assertIn("Alpha-band power", report)

    def test_existing_archive_is_not_overwritten(self):
        first = run_eyes_open_closed(self.output, config=self.config)
        original = first.archive_path.read_bytes()

        with self.assertRaises(FileExistsError):
            run_eyes_open_closed(self.output, config=self.config)
        self.assertEqual(first.archive_path.read_bytes(), original)

    def test_cli_runs_and_analyzes_offline_session(self):
        self.assertEqual(
            main(
                [
                    "experiment",
                    "run",
                    "eyes-open-closed",
                    "--output",
                    str(self.output),
                    "--participant",
                    "sub002",
                    "--session",
                    "session02",
                    "--sample-rate",
                    "128",
                    "--duration-scale",
                    "0.03",
                ]
            ),
            0,
        )
        archive_path = self.output / "sub002_ses-session02_task-rest.eegz"
        analysis_path = self.output / "offline.html"
        self.assertEqual(
            main(
                [
                    "analyze",
                    "--session",
                    str(archive_path),
                    "--output",
                    str(analysis_path),
                ]
            ),
            0,
        )
        self.assertTrue(analysis_path.is_file())


if __name__ == "__main__":
    unittest.main()
