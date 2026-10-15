import math
import unittest
from dataclasses import replace

from eeg_athenalyze.analysis.spectral import band_power, welch_psd, compare_resting_alpha
from eeg_athenalyze.recording import Recording


class SpectralAnalysisTests(unittest.TestCase):
    def test_welch_psd_recovers_known_sinusoid_power(self):
        sample_rate = 128
        samples = tuple(
            10.0 * math.sin(2 * math.pi * 10 * index / sample_rate)
            for index in range(4 * sample_rate)
        )

        spectrum = welch_psd(samples, sample_rate)

        self.assertAlmostEqual(band_power(spectrum, 8, 13), 50.0, delta=2.0)

    def test_measured_events_use_timestamp_clock(self):
        rate = 64
        times = tuple(10 + i / rate for i in range(256))
        samples = tuple(
            ((1.0 if i < 128 else 2.0) * math.sin(2 * math.pi * 10 * i / rate),)
            for i in range(256)
        )
        rec = Recording("test", rate, ("Cz",), samples, times, {
            "data_status": "measured",
            "events": [
                {"condition": "eyes_open", "onset_seconds": 10, "duration_seconds": 2},
                {"condition": "eyes_closed", "onset_seconds": 12, "duration_seconds": 2},
            ],
        })
        result = compare_resting_alpha(rec)
        self.assertAlmostEqual(result.eyes_open_uv2["Cz"], 0.5, delta=0.02)
        self.assertAlmostEqual(result.eyes_closed_uv2["Cz"], 2.0, delta=0.02)

    def test_measured_long_gap_rejects_short_runs(self):
        rate = 64
        times = tuple([i / rate for i in range(7)] + [1 + i / rate for i in range(7)])
        rec = Recording("gap", rate, ("Cz",), tuple((1.0,) for _ in times), times, {
            "data_status": "measured",
            "events": [
                {"condition": "eyes_open", "onset_seconds": 0, "duration_seconds": 2},
                {"condition": "eyes_closed", "onset_seconds": 0, "duration_seconds": 2},
            ],
        })
        with self.assertRaisesRegex(ValueError, "insufficient contiguous"):
            compare_resting_alpha(rec)

    def test_rejects_invalid_sampling_rate(self):
        with self.assertRaises(ValueError):
            welch_psd([0.0] * 16, 0)


if __name__ == "__main__":
    unittest.main()
