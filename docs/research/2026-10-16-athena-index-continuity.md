# Muse Athena packet-index continuity: offline diagnostic

This is a software-only diagnostic for issue #48. The 16-bit little-endian primary-frame index is evaluated separately for the two GATT characteristic UUIDs, to prevent cross-stream interleaving from creating false discontinuities. Each BLE callback may contain multiple primary frames. For known-framed notifications, the program reads every primary index, computes successive modulo-65536 transitions and reports repeats, sequential increments, and jump candidates.

**Crucial qualification:** neither a repeated index nor a jump proves BLE packet loss, because the index's increment and multiplexing semantics have not been physically certified. `bluetooth_packet_loss_count` remains null, and `counter_semantics_verified_on_device` remains false. Invalid parsed notifications are counted separately. Only offline JSONL input compatible with the raw Bleak collector is accepted; no device commands are sent.

Automated synthetic fixtures cover wrap 65535→0, repeated values, non-unit jumps, independent GATT streams, and two primary frames in one notification.

Next: couple this evidence with host receive gaps and validated firmware/packet counter behavior in a physically recorded session. Keep source data local and do not attribute dropouts to BrainFlow without native driver traces.

Implementation: `src/eeg_athenalyze/athena_index_continuity.py`, `tests/test_athena_index_continuity.py`. Related issues: #48, #49, #44.
