# M03: accounting for multiple primary frames per BLE notification

Date: 2026-10-16. Issue #48 and #44, software-only.

Previously the offline BLE QC tool returned the first `packet_index` per notification, omitting later primary frames when one callback carried concatenated frames. It also did not distinguish TAG subpackets from primary frames or nominal sample positions.

The updated tool strictly parses the full notification first; only valid input is used for accounting. It advances over **every** outer primary frame by its leading length byte (the framing already independently validated in `parse_notification`), reads the little-endian 16-bit index at offsets 1–2, separately counts tagged EEG blocks `0x11` (4 time positions) and `0x12` (2 time positions), and reports:
- `primary_frame_count` and `primary_frames_by_characteristic`
- `eeg_tag_count`
- `nominal_eeg_sample_positions` (time positions described by tags, not physical acquisition count)
- `adjacent_repeated_primary_indices`
- first/last parsed primary indices across the entire journal

Regressions cover one notification with two outer frames, an EEG subpacket, duplicate indices, and malformed frames. Raw bytes are not emitted in the report. **All packet-loss and hardware clock certification metrics remain unknown/null.** Further tasks: demonstrate packet counter continuity on real device, correlate with BrainFlow decoded sample counts under comparable controlled sequential sessions (not simultaneous BLE clients), and classify a real disconnect with local raw capture.

Related: #38, #44, #47, #48, #49. Source: BlueMuse framing audit in `docs/research/2026-10-16-bluemuse-framing-audit.md`.
