# Athena notification journal QC (offline, M03)

Partial autonomous work on issues #48, #49 and #44. This tool **does not connect to BLE**; it inspects captures produced by a future explicitly authorized/raw-notification collector. A BrainFlow `.eegz` file or `.partial.jsonl` acquisition journal is **not** this format, because neither contains native BLE notification bytes.

## Strict input contract

Each NDJSON line must be one object:

```json
{"receive_monotonic_seconds":1.25,"characteristic":"273e0013-4c4d-454d-96be-f03bac821358","payload_hex":"<actual-hex-bytes>"}
```

Use real hex bytes in local files only; never publish participant EEG. `receive_monotonic_seconds` is the host callback arrival time in seconds, not a calibrated headset clock. Supported characteristics are `273e0013-...` and `273e0014-...`. Invalid schema or nonmonotonic time fails closed; corrupt but syntactically valid frames count as invalid wire packets.

## Usage

```powershell
.\.venv\Scripts\python.exe -m eeg_athenalyze.ble_notification_qc --input data\local\athena-notify-01.jsonl --report data\local\athena-notify-01-qc.json
```

Never reuse a report filename; report creation refuses overwrite.

The output contains only notification and TAG counts, valid/invalid-frame counts, first/last receiver timestamps, maximum host inter-arrival interval, and first/last parsed packet index. No raw bytes, decoded samples, hardware-validity flag, source-personal identifiers or simulated BLE-loss estimates are emitted. All conclusions are **application-visible only**: missed radio notifications before the callback, device packet counter continuity, firmware clocks, GATT disconnect causes and BrainFlow buffer losses remain undetermined.

## Acceptance and blockers

- Mock CI tests cover malformed records, lengths, invalid host time, non-overwrite and lack of raw EEG in JSON report.
- No claim of physical Athena testing or success and no adjustment to research/BIDS validation gates.
- Future device-assisted task: add a safe, opt-in Bleak collector in a separate process; preserve all incoming raw notification bytes in a local ignored path, confirm GATT characteristics and permission before starting. Do not have two BLE owners simultaneously.
- Future improvements: carry primary-frame indices *individually*, not only first per notification; correlate parser decoder, BrainFlow buffering and physical-device disconnections with strongly separated error causes.

Sources: `athena_notification_parser.py`, prior BrainFlow/BlueMuse audit `docs/research/2026-10-16-brainflow-bluemuse-parity.md`.
