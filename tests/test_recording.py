import math
import unittest

from eeg_athenalyze.recording import SyntheticConfig, generate_synthetic_recording


class SyntheticRecordingTests(unittest.TestCase):
    def test_generation_is_repeatable_for_same_seed(self):
        config = SyntheticConfig(
            sample_rate_hz=128,
            seed=42,
            line_noise_amplitude_uv=0,
            blink_rate_hz=0,
            muscle_burst_rate_hz=0,
        )
        first = generate_synthetic_recording(1, config=config)
        second = generate_synthetic_recording(1, config=config)

        self.assertEqual(first.samples_uv, second.samples_uv)
        self.assertEqual(first.timestamps_seconds, second.timestamps_seconds)
        self.assertEqual(first.channel_names, ("TP9", "AF7", "AF8", "TP10"))
        self.assertEqual(first.metadata["data_status"], "simulated")
        self.assertEqual(len(first.samples_uv), 128)
        self.assertTrue(
            all(math.isfinite(value) for row in first.samples_uv for value in row)
        )

    def test_alpha_reactivity_increases_closed_condition_amplitude(self):
        config = SyntheticConfig(
            sample_rate_hz=128,
            seed=7,
            oscillations_uv=(),
            alpha_amplitude_uv=10,
            line_noise_amplitude_uv=0,
            noise_amplitude_uv=0,
            blink_rate_hz=0,
            muscle_burst_rate_hz=0,
        )
        eyes_open = generate_synthetic_recording(
            2, config=config, condition="eyes_open"
        )
        eyes_closed = generate_synthetic_recording(
            2,
            config=config,
            condition="eyes_closed",
        )

        open_rms = _rms(eyes_open.samples_uv, channel=0)
        closed_rms = _rms(eyes_closed.samples_uv, channel=0)
        self.assertAlmostEqual(closed_rms / open_rms, 2.0, places=10)

    def test_rejects_duration_shorter_than_one_sample(self):
        with self.assertRaises(ValueError):
            generate_synthetic_recording(
                0.001, config=SyntheticConfig(sample_rate_hz=128)
            )


def _rms(samples, channel):
    return math.sqrt(sum(row[channel] ** 2 for row in samples) / len(samples))


if __name__ == "__main__":
    unittest.main()
