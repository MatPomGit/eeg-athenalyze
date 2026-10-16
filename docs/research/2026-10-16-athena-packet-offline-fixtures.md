# M03 offline Muse Athena packet reference tests

This package adds **candidate decoding fixtures**, not a manufacturer-certified Athena protocol implementation. It does not connect to BLE or parse complete GATT notifications.

## What is implemented
- `athena_packet_reference.decode_lsb_14bit`: strict 14-bit little-endian bitstream unpacker; rejects incorrect payload byte lengths and nonzero padding bits.
- `encode_lsb_14bit`: synthetic fixture generation without EEG participant data.
- `decode_eeg_tag_payload`: assumed 0x11 4×4 and 0x12 8×2 logical sample matrices, with **sample-major** ordering as a *hypothesis*. Neither actual subpacket offsets nor physical channel mapping are verified.
- `codes_to_uv`: explicitly selectable 16384 or 16383 denominator; values near ±725 µV require comparison against raw-code count distribution before assuming analog clipping.
- `summarize_packet_indices`: repeated indices and candidate discontinuities under an *explicitly configured* modulus. **packet_loss_estimate is always null**, because a missing index does not establish a missed BLE notification until packet counter scope is verified.

## Next validation gates
1. Pin upstream BlueMuse, BrainFlow, Amused-Py versions and extract their independent decoding reference byte vectors; compare not only round-trips between encoder and decoder in this module but known incoming raw notification bytes.
2. Parse complete packet framing, TAG boundaries, channel order and counters with source-cited offsets, then test truncated/unknown TAG, counter wrap, gaps, and multi-TAG packets.
3. Independently capture actual Muse S Athena notifications for this specific device, by human-assisted experiment only. Preserve raw bytes, receipt timestamps and firmware/version metadata locally; do not publish human EEG.
4. Compare decoded signal to BrainFlow/BlueMuse for identical raw packet bytes; distinguish ADC rails from reference/contact artefact and source timestamp duplication.
5. Only after physical validation consider production acquisition integration. **Do not lift EEG-BIDS hardware validity gates** as part of these tests.

Related: #47, #48, #49, #53; [protocol evidence review](2026-10-16-muse-athena-packet-protocol.md).

## Example standalone offline command

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_athena_packet_reference -v
```
