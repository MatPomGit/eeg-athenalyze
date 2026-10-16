# Athena EEG cross-decoder offline audit

Issue #47 / #53. Implements independent **algorithmic** comparison between (1) the `int.from_bytes` LSB-first packed-14-bit decoding in `athena_packet_reference.py` and (2) a byte-by-byte bit-field extractor transcribed from the algorithmic approach of `kowalej/BlueMuse/BlueMuse.App/Athena/AthenaDecoders.cs`.

Tests verify known byte fields 0xA5 and 0x01FF, extreme 14-bit EEG codes, both 0x11 (4×4) and 0x12 (8×2) layouts, and seeded randomized buffers, as well as malformed inputs.

Both software algorithms agree on **synthetic bytes**. These are not two separately executed vendor decoders; shared packet-format assumptions could still be wrong. Real device data, independent native BrainFlow execution, physical channel mapping and clock verification remain blocked. The cross-check outputs **counts only**, no participant EEG, and does not change production acquisition or BIDS validity.

Sources: https://github.com/kowalej/BlueMuse/blob/master/BlueMuse.App/Athena/AthenaDecoders.cs and https://github.com/brainflow-dev/brainflow/blob/master/src/board_controller/muse/muse_athena.cpp .
