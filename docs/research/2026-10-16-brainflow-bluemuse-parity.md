# Native BrainFlow vs BlueMuse: Muse Athena source comparison (2026-10-16)

## Examined upstream implementation

- BrainFlow `src/board_controller/muse/muse_athena.cpp`, `src/board_controller/muse/inc/muse_athena_constants.h` on upstream master at inspection date.
- BlueMuse `BlueMuse.App/Athena/AthenaPacketParser.cs`, `AthenaDecoders.cs`, and its Athena tests.

### Confirmed software-level parity
- Both parsers use primary packet length at byte 0, uint16 little-endian index at bytes 1–2, TAG at byte 9, block index at byte 10, primary header of 14 bytes, and 5-byte subpacket header.
- Both compute composite package number `(packet_index << 8) | block_index`.
- EEG `0x11` and `0x12` are decoded as contiguous 14-bit LSB-first, sample-major data. Both use an offset midpoint **8192** and scale `1450/16383` microvolts per code. This corrects the candidate reference module's previous **16384** default; that alternative is retained only for explicit sensitivity comparisons.
- Both specify accelerometer `0.00006103515625`, gyro `-0.007476806640625` and battery `1/512` scaling in current source.

### Timestamp implementation finding

BrainFlow native `MuseAthena::get_sample_timestamp(last_timestamp, current_timestamp, sample_index, n_samples, sampling_rate)` contains the following branches:

1. If rate/count invalid, return current host timestamp.
2. For first package with last_timestamp <=0, distribute sample times *backward* from current host timestamp at the nominal sample period.
3. If `current_timestamp <= last_timestamp`, **return identical current host timestamp for every sample in the packet**, causing repeated timestamps without proof of radio packet loss.
4. Otherwise try nominal forward spacing from last host packet; if that exceeds current timestamp, interpolate `(current-last)/n_samples`.

An exact Python *offline model* of these branches and deterministic tests were added to `athena_packet_reference.py`. This is a sufficient software explanation for **some** duplicate timestamps, but there is still no packet-level evidence establishing what percentage of the observed 74% duplicates arose from this branch. Nor does it prove hardware timing or make spectral interpretations reliable.

### Tests completed and still required

- Offline: reference 14-bit code boundaries, interleaving hypothesis matching observed BlueMuse and BrainFlow source, scaling denominator parity, host timestamp edge cases (first packet, repeat, short and long host intervals).
- Pending: produce frozen raw notification byte fixtures from genuinely **independent decoder golden data**, trace native callback arrival times, and record packet sequence indices to distinguish host jitter from loss. Python test against a Python-generated payload is not itself independent binary corroboration.
- Physical: BrainFlow Windows vs Android / OpenMuse / BlueMuse on the same Athena; cannot be executed in CI. Incomplete BLE sessions still remain rejected and journaled.

**Safety:** raw source values and timestamps are untouched. No assumptions about physical clock, physiological EEG validity or hardware-verified BIDS export changed.

Linked: #47, #48, #53, #38.
