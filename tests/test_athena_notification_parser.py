"""Protocol framing fixtures derived from BlueMuse AthenaPacketParser.cs."""
import unittest

from eeg_athenalyze.athena_notification_parser import parse_notification


def primary(tag, payload, *, index=700, block=3, sub=b""):
    n = 14 + len(payload) + len(sub)
    assert n <= 255
    return bytes([n]) + index.to_bytes(2, "little") + bytes(6) + bytes([tag, block]) + bytes(3) + payload + sub


def subpacket(tag, payload, block=2):
    return bytes([tag, block, 0, 0, 0]) + payload


class AthenaFramingTests(unittest.TestCase):
    def test_primary_plus_imu_subpacket_and_counters(self):
        eeg, imu = bytes(range(28)), bytes(range(36))
        packet = parse_notification(primary(0x11, eeg, sub=subpacket(0x47, imu)))
        self.assertEqual(len(packet), 2)
        self.assertEqual((packet[0].tag, packet[0].packet_index, packet[0].block_index),
                         (0x11, 700, 3))
        self.assertEqual(packet[0].package_number, (700 << 8) | 3)
        self.assertEqual(packet[0].payload, eeg)
        self.assertEqual((packet[1].tag, packet[1].block_index, packet[1].payload), (0x47, 2, imu))

    def test_two_concatenated_frames(self):
        raw = primary(0x47, bytes(36), index=1) + primary(0x12, bytes(28), index=2)
        self.assertEqual([(x.tag, x.packet_index) for x in parse_notification(raw)],
                         [(0x47, 1), (0x12, 2)])

    def test_all_fixed_tags(self):
        for tag, size in {0x11:28,0x12:28,0x34:30,0x35:40,0x36:40,
                          0x47:36,0x53:24,0x98:20}.items():
            with self.subTest(tag=tag):
                self.assertEqual(parse_notification(primary(tag, bytes(size)))[0].payload, bytes(size))

    def test_variable_battery_uses_remainder(self):
        self.assertEqual(parse_notification(primary(0x88, b"\x00\x63\x00\x00"))[0].payload,
                         b"\x00\x63\x00\x00")

    def test_bad_lengths_and_unknowns_fail_closed(self):
        cases = [bytes(5), bytes([3]) + bytes(30),
                 bytes([100]) + bytes(20),
                 primary(0x77, bytes(4)),
                 primary(0x11, bytes(27)),
                 primary(0x11, bytes(28), sub=b"\x12\x00"),
                 primary(0x11, bytes(28), sub=subpacket(0x77, bytes(4))),
                 primary(0x88, bytes(1))]
        for raw in cases:
            with self.subTest(size=len(raw),raw=raw[:15]):
                with self.assertRaises(ValueError):
                    parse_notification(raw)

    def test_empty_is_no_data(self):
        self.assertEqual(parse_notification(b""), ())


if __name__ == "__main__":
    unittest.main()
