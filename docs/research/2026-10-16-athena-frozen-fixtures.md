# Issue #47: frozen synthetic Athena EEG fixtures (2026-10-16)

## Reproducible offline qualification

Test file: `tests/test_athena_frozen_golden.py`. The four **hard-coded**, 28-byte vectors are `rails`, `sample_major`, `reversed_logical_channels` and `alternating_rails`. They cover raw codes 0/1/8191/8192/8193/16382/16383, cross-byte 14-bit packing, four logical EEG channels × four samples (0x11), and eight logical values × two samples (0x12). The numeric comparator uses offset 8192 and **1450/16383 µV**. A reversed logical-channel vector detects accidental channel-order assumptions. It does **not** establish mapping to physical electrodes.

The tests exercise the independently implemented bit-by-bit reference and integer bit-unpacker; neither is a compiled vendor binary. Negative vectors exercise unknown primary and sub-TAGs, truncated notifications and subframes, invalid declared lengths, trailing incomplete primary header, and 16-bit packet-index wrap. The latter is only an index behavior check, **never** a packet-loss measurement. Parsing of a variable-length TAG and unknown TAG recovery remains source-dependent.

## Run

```bash
PYTHONPATH=src python -m unittest discover -s tests -p 'test_athena*frozen*.py' -v
PYTHONPATH=src python -m unittest tests.test_athena_packet_reference tests.test_athena_notification_parser tests.test_athena_decoder_crosscheck tests.test_athena_frozen_golden -v
```

The first command runs this frozen-vector module; the second runs the related reference/framing/cross-check suites. These tests require no device, participant data, BLE scanning, paid service or elevated permissions.

## Validation level and provenance

- **Confirmed by source review (PR #58/#59):** BlueMuse and BrainFlow software implement sample-major 14-bit LSB-first decoding with 1450/16383 scaling. Software parity is not measurement accuracy.
- **Synthetic software regressions:** frozen byte literals, known code sequences and negative cases. Generated/test-design values are not raw bytes from a Muse.
- **Pending independent native parity:** capture outputs of fixed-version native BlueMuse and BrainFlow decoding for *identical fixed byte vectors*, recording exact upstream commit, build, configuration/preset and tolerances. Python/Python checks cannot substitute for this.
- **Blocked until approved real-device measurements:** collect complete timestamped BLE GATT notifications with exact hardware model/firmware, sampling preset and electrode map; compare same bytes to both native decoders; verify sample/channel ordering, counter scopes, clock behavior, code-rail prevalence, dropped/reordered packets and analog saturation separately. Keep raw participant EEG local and consent/ethics-controlled.
- **Blocked for scientific validity:** any claims of physical 14-bit quantization fidelity, ±725 µV analogue clipping, hardware clock accuracy, valid EEG/BIDS quality and physiological spectral interpretation. Software rails do not establish physical clipping.

**Release gate:** do not update production acquisition pathways or relax BIDS/EEG quality gates on the basis of these offline fixtures. Leave issue #47 open for native and physical evidence. Related #38, #42, #44, #48, #53, #64.
