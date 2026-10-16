"""Exhaustive, hardware-free 14-bit code-domain and channel-permutation tests.

Every possible raw 14-bit code is checked at each logical slot over a series
of payloads. No device, EEG subject data or proprietary binary is used.
"""
import unittest

from eeg_athenalyze.athena_packet_reference import (
    decode_eeg_tag_payload, decode_lsb_14bit, encode_lsb_14bit, codes_to_uv,
)
from eeg_athenalyze.athena_decoder_crosscheck import decode_eeg_oracle


class ExhaustiveAthenaCodeDomainTests(unittest.TestCase):
    def test_all_16384_codes_at_each_of_16_positions(self):
        # Each cycle has 16 different known codes, and each code is rotated
        # through all 16 logical positions; total: 262144 observed code-slots.
        for base in range(0, 16384, 16):
            codes = tuple(range(base, base + 16))
            for shift in range(16):
                rotated = codes[shift:] + codes[:shift]
                payload = encode_lsb_14bit(rotated)
                self.assertEqual(decode_lsb_14bit(payload, sample_count=16),
                                 rotated, (base, shift))
                # Test both parsers on representative rotations to keep CI fast,
                # and use the independent oracle for every 14-bit code.
                if shift == 0:
                    for tag, channels, samples in ((0x11, 4, 4), (0x12, 8, 2)):
                        expected = tuple(
                            rotated[t*channels:(t+1)*channels]
                            for t in range(samples))
                        self.assertEqual(decode_eeg_oracle(tag, payload), expected)
                        self.assertEqual(decode_eeg_tag_payload(tag, payload), expected)

    def test_distinct_channel_values_catch_permutations(self):
        values = tuple(t * 1000 + c * 17 for t in range(4) for c in range(4))
        payload = encode_lsb_14bit(values)
        expected = tuple(
            tuple(t * 1000 + c * 17 for c in range(4)) for t in range(4))
        decoded = decode_eeg_tag_payload(0x11, payload)
        self.assertEqual(decoded, expected)
        for left, right in ((0, 1), (0, 3), (1, 2)):
            swapped = list(decoded[0])
            swapped[left], swapped[right] = swapped[right], swapped[left]
            self.assertNotEqual(tuple(swapped), expected[0])

    def test_scale_monotonicity_and_exact_code_endpoints(self):
        codes = tuple(range(16384))
        uv = codes_to_uv(codes)
        self.assertEqual(len(uv), 16384)
        self.assertEqual(uv[8192], 0.0)
        self.assertAlmostEqual(uv[0], -8192 * 1450 / 16383)
        self.assertAlmostEqual(uv[-1], 8191 * 1450 / 16383)
        self.assertTrue(all(a < b for a, b in zip(uv, uv[1:])))

    def test_invalid_raw_codes_rejected_without_wraparound(self):
        for invalid in (-32768, -1, 16384, 65535):
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    encode_lsb_14bit((invalid,))
                with self.assertRaises(ValueError):
                    codes_to_uv((invalid,))


if __name__ == "__main__":
    unittest.main()
