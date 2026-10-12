import math
import unittest

from eeg_athenalyze.analysis.spectral import band_power, welch_psd


class SpectralAnalysisTests(unittest.TestCase):
    def test_welch_psd_recovers_known_sinusoid_power(self):
        sample_rate = 128
        samples = tuple(
            10.0 * math.sin(2 * math.pi * 10 * index / sample_rate)
            for index in range(4 * sample_rate)
        )

        spectrum = welch_psd(samples, sample_rate)

        self.assertAlmostEqual(band_power(spectrum, 8, 13), 50.0, delta=2.0)

    def test_rejects_invalid_sampling_rate(self):
        with self.assertRaises(ValueError):
            welch_psd([0.0] * 16, 0)


if __name__ == "__main__":
    unittest.main()
