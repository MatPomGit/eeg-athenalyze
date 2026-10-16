"""Strict offline Athena notification parser based on BlueMuse 3.1 framing.

No BLE access, no hardware clock or loss inference. Reject malformed messages
rather than silently accepting partial sensor payloads.
Upstream: kowalej/BlueMuse, AthenaPacketParser.cs (2026-10-16).
"""
from __future__ import annotations

from dataclasses import dataclass

PRIMARY_HEADER_SIZE = 14
SUB_HEADER_SIZE = 5
FIXED_LENGTHS = {
    0x11: 28, 0x12: 28, 0x34: 30, 0x35: 40,
    0x36: 40, 0x47: 36, 0x53: 24, 0x98: 20,
}
VARIABLE_LENGTH_TAG = 0x88


@dataclass(frozen=True)
class TaggedPacket:
    tag: int
    packet_index: int
    block_index: int
    payload: bytes

    @property
    def package_number(self) -> int:
        """Upstream composite identifier, not certified loss/clock counter."""
        return (self.packet_index << 8) | self.block_index


def _size_for(tag: int, available: int) -> int:
    if tag == VARIABLE_LENGTH_TAG:
        if available < 2:
            raise ValueError("Truncated variable battery payload")
        return available
    if tag not in FIXED_LENGTHS:
        raise ValueError(f"Unknown Athena tag 0x{tag:02x}; cannot recover framing")
    n = FIXED_LENGTHS[tag]
    if n > available:
        raise ValueError(f"Truncated Athena tag 0x{tag:02x} payload")
    return n


def parse_notification(notification: bytes) -> tuple[TaggedPacket, ...]:
    """Parse complete concatenated primary frames and tagged subframes.

    Only parse *already captured* notification bytes. Never fabricate clocks or
    silently replace malformed data; caller may quarantine failed frames.
    """
    if not isinstance(notification, bytes):
        raise TypeError("Notification must be bytes")
    frames = []
    offset = 0
    while offset < len(notification):
        remaining = len(notification) - offset
        if remaining < PRIMARY_HEADER_SIZE:
            raise ValueError("Truncated primary header")
        length = notification[offset]
        if length < PRIMARY_HEADER_SIZE or length > remaining:
            raise ValueError("Invalid primary frame length")
        end = offset + length
        index = int.from_bytes(notification[offset + 1:offset + 3], "little")
        tag = notification[offset + 9]
        block = notification[offset + 10]
        pos = offset + PRIMARY_HEADER_SIZE
        data_length = _size_for(tag, end - pos)
        frames.append(TaggedPacket(tag, index, block, notification[pos:pos + data_length]))
        pos += data_length
        while pos < end:
            if end - pos < SUB_HEADER_SIZE:
                raise ValueError("Truncated subpacket header")
            subtag, subblock = notification[pos], notification[pos + 1]
            pos += SUB_HEADER_SIZE
            n = _size_for(subtag, end - pos)
            frames.append(TaggedPacket(subtag, index, subblock, notification[pos:pos + n]))
            pos += n
        offset = end
    return tuple(frames)
