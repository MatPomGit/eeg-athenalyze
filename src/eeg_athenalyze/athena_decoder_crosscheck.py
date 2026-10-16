"""Independent bit-by-bit oracle matching upstream BlueMuse's ExtractLsbBits.

Separate algorithm from Python production candidate's int.from_bytes decoder.
For source-level comparison only, not manufacturer/device validation.
"""
from __future__ import annotations

from eeg_athenalyze.athena_notification_parser import parse_notification
from eeg_athenalyze.athena_packet_reference import decode_eeg_tag_payload, codes_to_uv


def extract_bits_oracle(data: bytes, bit_start: int, width: int) -> int:
    if bit_start < 0 or not 0 <= width <= 32 or bit_start + width > len(data) * 8:
        raise ValueError("Invalid bit field")
    number = 0
    for i in range(width):
        offset = bit_start + i
        number |= ((data[offset >> 3] >> (offset & 7)) & 1) << i
    return number


def decode_eeg_oracle(tag: int, data: bytes) -> tuple[tuple[int, ...], ...]:
    layouts = {0x11: (4, 4), 0x12: (8, 2)}
    if tag not in layouts:
        raise ValueError("Unsupported EEG TAG")
    channel_count, sample_count = layouts[tag]
    if len(data) != 28:
        raise ValueError("Expected 28 EEG bytes")
    return tuple(tuple(extract_bits_oracle(data, 14 * (t * channel_count + c), 14)
                       for c in range(channel_count))
                 for t in range(sample_count))


def verify_notification_eeg(notification: bytes) -> dict[str, object]:
    """Reject mismatching decoders; return counts only, never participant values."""
    packets = parse_notification(notification)
    eeg_packets = 0
    checked_codes = 0
    for packet in packets:
        if packet.tag not in (0x11, 0x12):
            continue
        left = decode_eeg_tag_payload(packet.tag, packet.payload)
        right = decode_eeg_oracle(packet.tag, packet.payload)
        if left != right:
            raise ValueError("Independent bitwise decoder mismatch")
        if tuple(codes_to_uv(row, denominator=16383) for row in left) != tuple(
            codes_to_uv(row, denominator=16383) for row in right
        ):
            raise ValueError("EEG scale mismatch")
        eeg_packets += 1
        checked_codes += sum(map(len, left))
    return {
        "source_comparison": "BlueMuse-derived bitwise algorithm vs Python integer algorithm",
        "eeg_tag_count": eeg_packets,
        "checked_14bit_codes": checked_codes,
        "independent_algorithm_agreement": True,
        "hardware_validated": False,
        "physical_timing_verified": False,
    }
