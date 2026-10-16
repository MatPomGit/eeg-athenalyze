"""Frozen, synthetic Athena EEG golden bytes. No hardware or participant data.

Hex vectors are literals, not assembled by the decoder under test. Each vector
asserts an independently specified 14-bit code sequence and sample-major layout.
See docs/research/2026-10-16-athena-frozen-fixtures.md.
"""
import unittest

from eeg_athenalyze.athena_packet_reference import (
    decode_eeg_tag_payload, decode_lsb_14bit, codes_to_uv,
)
from eeg_athenalyze.athena_decoder_crosscheck import (
    decode_eeg_oracle, verify_notification_eeg,
)
from eeg_athenalyze.athena_notification_parser import parse_notification


GOLDEN = {
    "rails": (
        "004000f0ff018001a0ffffffab00004000f0ff018001a0ffffffab00",
        (0, 1, 8191, 8192, 8193, 16382, 16383, 42) * 2,
    ),
    "sample_major": (
        "640032c0124006654032d0124406668032e012480667c032f0124c06",
        (100, 200, 300, 400, 101, 201, 301, 401,
         102, 202, 302, 402, 103, 203, 303, 403),
    ),
    "reversed_logical_channels": (
        "90014b800c900191414b900c940192814ba00c980193c14bb00c9c01",
        (400, 300, 200, 100, 401, 301, 201, 101,
         402, 302, 202, 102, 403, 303, 203, 103),
    ),
    "alternating_rails": (
        "00c0ff0f00fcff00c0ff0f00fcff00c0ff0f00fcff00c0ff0f00fcff",
        (0, 16383) * 8,
    ),
}


def primary(tag, payload, index=65535):
    length = 14 + len(payload)
    if length > 255:
        raise ValueError("Frame length overflow")
    return (bytes([length]) + index.to_bytes(2, "little") + bytes(6)
            + bytes([tag, 0]) + bytes(3) + payload)


class FrozenAthenaGoldenTests(unittest.TestCase):
    def test_fixed_raw_bytes_and_both_algorithms(self):
        for name, (hex_payload, codes) in GOLDEN.items():
            payload = bytes.fromhex(hex_payload)
            self.assertEqual(len(payload), 28)
            with self.subTest(name=name):
                self.assertEqual(decode_lsb_14bit(payload, sample_count=16), codes)
                for tag, channels, samples in ((0x11, 4, 4), (0x12, 8, 2)):
                    expected = tuple(tuple(codes[t * channels:(t + 1) * channels])
                                     for t in range(samples))
                    self.assertEqual(decode_eeg_tag_payload(tag, payload), expected)
                    self.assertEqual(decode_eeg_oracle(tag, payload), expected)
                    report = verify_notification_eeg(primary(tag, payload))
                    self.assertEqual(report["checked_14bit_codes"], 16)
                    self.assertFalse(report["hardware_validated"])

    def test_scale_rails_and_midpoint(self):
        result = codes_to_uv((0, 1, 8191, 8192, 8193, 16382, 16383))
        self.assertEqual(result[3], 0.0)
        for code, uv in zip((0, 1, 8191, 8192, 8193, 16382, 16383), result):
            self.assertAlmostEqual(uv, (code - 8192) * 1450 / 16383)
        self.assertLess(result[0], -725)
        self.assertLess(result[-1], 725)

    def test_unknown_tags_and_truncated_or_oversized_frames_fail_closed(self):
        payload = bytes.fromhex(GOLDEN["rails"][0])
        good = primary(0x11, payload)
        malformed = (
            primary(0x77, payload),  # unknown primary TAG
            good[:-1],  # truncated primary packet
            good + b"\x00",  # trailing undersized header
            bytes([255]) + good[1:],  # advertised length overflow
            good[:14] + payload + bytes([0x77, 0, 0, 0, 0]),  # unannounced trailing bytes
            primary(0x11, payload) + primary(0x12, payload)[:-1],
        )
        for raw in malformed:
            with self.subTest(raw=raw.hex()[:40]):
                with self.assertRaises(ValueError):
                    parse_notification(raw)

    def test_subpacket_unknown_and_truncated(self):
        payload = bytes.fromhex(GOLDEN["sample_major"][0])
        prefix = primary(0x11, payload)
        # Recompute the length field to explicitly include trailing subframes.
        for sub in (bytes([0x77, 0, 0, 0, 0]) + bytes(3),
                    bytes([0x12, 0, 0, 0, 0]) + bytes(27),
                    bytes([0x12, 0])):
            framed = bytes([len(prefix) + len(sub)]) + prefix[1:] + sub
            with self.subTest(sub=sub.hex()[:20]):
                with self.assertRaises(ValueError):
                    parse_notification(framed)

    def test_16_bit_index_wrap_does_not_claim_packet_loss(self):
        payload = bytes.fromhex(GOLDEN["rails"][0])
        seq = primary(0x11, payload, 65535) + primary(0x12, payload, 0)
        packets = parse_notification(seq)
        self.assertEqual(tuple(p.packet_index for p in packets), (65535, 0))
        self.assertEqual(tuple(p.tag for p in packets), (0x11, 0x12))


if __name__ == "__main__":
    unittest.main()
