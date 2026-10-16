"""Deterministic independent algorithm comparison; no physical EEG."""
import random
import unittest
from eeg_athenalyze.athena_decoder_crosscheck import (
    decode_eeg_oracle, extract_bits_oracle, verify_notification_eeg)
from eeg_athenalyze.athena_packet_reference import (
    decode_eeg_tag_payload, encode_lsb_14bit)


def frame(tag, values):
    payload = encode_lsb_14bit(values)
    return (bytes([14 + len(payload)]) + bytes([1, 0]) + bytes(6)
            + bytes([tag, 0]) + bytes(3) + payload)


class DecoderCrosscheckTests(unittest.TestCase):
    def test_known_non_roundtrip_byte_fields(self):
        self.assertEqual(extract_bits_oracle(bytes.fromhex("a500"), 0, 4), 5)
        self.assertEqual(extract_bits_oracle(bytes.fromhex("a500"), 4, 4), 10)
        self.assertEqual(extract_bits_oracle(bytes.fromhex("ff01"), 4, 8), 31)

    def test_boundaries_and_modes(self):
        for tag in (0x11, 0x12):
            raw = [0, 1, 8191, 8192, 8193, 16382, 16383, 42] * 2
            f = frame(tag, raw)
            report = verify_notification_eeg(f)
            self.assertEqual(report["checked_14bit_codes"], 16)
            self.assertTrue(report["independent_algorithm_agreement"])
            self.assertFalse(report["hardware_validated"])

    def test_seeded_randomized_packed_bit_layout(self):
        rng = random.Random(77213)
        for tag in (0x11, 0x12):
            for _ in range(64):
                values = [rng.randrange(16384) for i in range(16)]
                payload = encode_lsb_14bit(values)
                self.assertEqual(decode_eeg_tag_payload(tag, payload),
                                 decode_eeg_oracle(tag, payload))

    def test_corrupt_and_unknown(self):
        with self.assertRaises(ValueError):
            decode_eeg_oracle(0x11, bytes(27))
        with self.assertRaises(ValueError):
            decode_eeg_oracle(0x77, bytes(28))
        with self.assertRaises(ValueError):
            verify_notification_eeg(b"\x7f")


if __name__ == "__main__":
    unittest.main()
