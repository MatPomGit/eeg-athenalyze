# M03: host callback gaps and primary packet-index events

Software-only addition for issues #44, #48 and #49. Reads existing locally captured Athena raw BLE JSONL (no connection) and classifies events **per characteristic**, avoiding false discontinuities when 0013 and 0014 interleave.

Events: `successive_index`, `repeated_index`, `index_jump_candidate`, `host_receive_gap`, `host_gap_with_index_jump`, and `malformed_notification`. The configurable gap threshold defaults to **0.2 seconds**, a diagnostic choice rather than a validated physical limit. Only intervals between distinct callbacks can be host gaps; concatenated primary frames in one callback are not host-gap events. Modulo 65536 is a software counter hypothesis.

```powershell
.\.venv\Scripts\python.exe -m eeg_athenalyze.athena_receive_event_qc --input data\local\athena-raw-p21-01.jsonl --report data\local\athena-receive-events-01.json --gap-threshold 0.2
```

The output contains aggregate event counts, first/last host receipt time and explicit `packet_loss_estimate: null`. Raw sample bytes are neither emitted nor committed. These events do **not** establish link-layer BLE loss, device clock correctness, channel validity, or a BrainFlow bug.

Covered offline tests: host gap coincident with counter jump, frame concatenation in a single notification, separate GATT streams, malformed notifications, and monotonic-time validation. Physical trials are required to explain the user's BLE disconnects and non-monotonic BrainFlow software timestamps. Related docs: `2026-10-16-athena-index-continuity.md`, `2026-10-16-bleak-raw-collector.md`.
