# BlueMuse Athena framing cross-check (2026-10-16)

Inspected actual upstream `kowalej/BlueMuse` implementation:
- `BlueMuse.App/Athena/AthenaPacketParser.cs`: **primary header 14 bytes** (length at byte 0, `uint16 little-endian` packet index at bytes 1–2, tag at byte 9, block index at byte 10), then known tag payload, followed by zero or more **5-byte subpacket headers** and corresponding data. Multiple primary frames can be concatenated into one notification.
- Known payload lengths: EEG `0x11`/`0x12` 28 bytes; optics `0x34` 30 bytes, `0x35`/`0x36` 40 bytes; IMU `0x47` 36 bytes; `0x53` 24 bytes (unknown purpose); battery `0x98` 20 bytes and `0x88` variable length. The combined package identifier in BlueMuse is `(packetIndex << 8) | blockIndex`.
- `BlueMuse.App/Athena/AthenaDecoders.cs` and `Tests/BlueMuse.Athena.Tests/Program.cs` independently support **sample-major, LSB-first, 14-bit** EEG packing and `1450/16383` µV code conversion. Our candidate reference module supports both denominators; 16383 matches this BlueMuse implementation. This is code-level corroboration, **not physical proof**.

Implemented a strict **offline** frame parser in `src/eeg_athenalyze/athena_notification_parser.py`, and fixtures in `tests/test_athena_notification_parser.py`. Unlike BlueMuse's permissive malformed-frame handling, the offline parser raises `ValueError` and does not quietly accept truncation. It deliberately does not compute confirmed packet loss, infer sample-clock timestamps, or connect to BLE.

Outstanding: independently pin BrainFlow source SHA and compare framing and command paths; establish whether packet and block indices are continuous for each tag/preset and support meaningful loss inference; capture local raw notifications with hardware authorization; no real EEG data committed.

Links: https://github.com/kowalej/BlueMuse/blob/master/BlueMuse.App/Athena/AthenaPacketParser.cs ; https://github.com/kowalej/BlueMuse/blob/master/BlueMuse.App/Athena/AthenaDecoders.cs ; issues #47 #48 #49 #53.