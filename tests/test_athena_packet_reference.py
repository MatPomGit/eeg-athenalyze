"""No-device tests for explicitly unverified Athena payload hypotheses."""
import unittest

from eeg_athenalyze.athena_packet_reference import (
    codes_to_uv, decode_eeg_tag_payload, decode_lsb_14bit,
    encode_lsb_14bit, summarize_packet_indices,
)


class PackedEegReferenceTests(unittest.TestCase):
    def test_golden_code_boundaries(self):
        codes = (0, 1, 8191, 8192, 8193, 16382, 16383)
        self.assertEqual(decode_lsb_14bit(
            encode_lsb_14bit(codes), sample_count=len(codes)), codes)

    def test_expected_four_channel_mode_size(self):
        values = tuple(range(16))
        self.assertEqual(len(encode_lsb_14bit(values)), 28)
        self.assertEqual(decode_eeg_tag_payload(0x11, encode_lsb_14bit(values)),
                         ((0, 1, 2, 3), (4, 5, 6, 7),
                          (8, 9, 10, 11), (12, 13, 14, 15)))

    def test_eight_logical_channels_mode(self):
        values = tuple(range(16))
        self.assertEqual(decode_eeg_tag_payload(0x12, encode_lsb_14bit(values)),
                         (tuple(range(8)), tuple(range(8, 16))))

    def test_reject_partial_unknown_or_padded_data(self):
        payload = encode_lsb_14bit((0,))
        with self.assertRaisesRegex(ValueError, "Expected"):
            decode_lsb_14bit(payload[:-1], sample_count=1)
        with self.assertRaisesRegex(ValueError, "padding"):
            decode_lsb_14bit(bytes([0, 0xc0]), sample_count=1)
        with self.assertRaisesRegex(ValueError, "Unknown"):
            decode_eeg_tag_payload(0xff, bytes(28))
        with self.assertRaises(ValueError):
            encode_lsb_14bit((-1,))
        with self.assertRaises(ValueError):
            encode_lsb_14bit((16384,))

    def test_scale_is_explicit_and_not_a_hardware_claim(self):
        a = codes_to_uv((0, 8192, 16383))
        self.assertEqual(a[0], -725.0)
        self.assertEqual(a[1], 0.0)
        self.assertLess(a[2], 725.0)
        self.assertNotEqual(a[2], codes_to_uv((16383,), denominator=16383)[0])
        with self.assertRaises(ValueError):
            codes_to_uv((8192,), denominator=1)


class PacketIndexTests(unittest.TestCase):
    def test_unknown_modulus_does_not_infer_loss(self):
        result = summarize_packet_indices((254, 255, 0, 1, 1, 3))
        self.assertIsNone(result["index_jump_candidates"])
        self.assertIsNone(result["packet_loss_estimate"])
        self.assertEqual(result["repeated_adjacent_indices"], 1)

    def test_wrapping_indices_are_not_called_packet_losses(self):
        result = summarize_packet_indices((254, 255, 0, 2), modulus=256)
        self.assertEqual(result["index_jump_candidates"], 1)
        self.assertIsNone(result["packet_loss_estimate"])

    def test_invalid_modulus_and_indices_fail_closed(self):
        for sample, modulus in (((256,), 256), ((-1,), 256), ((0,), 1)):
            with self.subTest(sample=sample, modulus=modulus):
                with self.assertRaises(ValueError):
                    summarize_packet_indices(sample, modulus=modulus)


if __name__ == "__main__":
    unittest.main()
