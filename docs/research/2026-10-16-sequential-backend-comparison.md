# M03: independent-session BLE versus BrainFlow evidence comparison

Related: #44, #48, #49, #53. This is a **software-only** comparison of separate, not synchronized sessions.

## Usage (Windows PowerShell)

After explicitly acquiring data from the actual headset through *one* BLE client at a time, use a previously completed `.eegz` BrainFlow recording and an independently captured raw BLE notification journal:

```powershell
.\.venv\Scripts\python.exe -m eeg_athenalyze.backend_comparison --ble data\local\athena-raw-p21-01.jsonl --eegz data\local\athena-p21-test01.eegz --report data\local\athena-independent-backend-comparison01.json
```

Inputs must exist. The module validates the original EEGZ archive checksum through `load_recording` and parses the BLE journal using the existing strict frame QC. It produces an exclusive-create JSON report and refuses to overwrite existing reports.

## Outputs and limits

- Raw BLE: notification, valid/invalid frame, EEG TAG and primary frame counts, nominal EEG time positions, host callback span and greatest callback gap.
- BrainFlow: channel labels, number of returned EEG samples, nominal sample frequency, source timestamp span and duplicate/backward timestamp counts.
- The report does **not** include raw BLE bytes, EEG values, source file names, participant identifiers or inferred firmware version.
- `same_session=false`, `direct_sample_equality_tested=false`, `packet_loss_estimate=null`, `physical_timing_verified=false` and `hardware_validated=false` are explicit. A ratio of BLE EEG positions to BrainFlow samples across sessions must **not** be interpreted as packet loss, BLE throughput or decoder efficiency.
- Actual sample-by-sample comparison requires a *single exact notification fixture* passed through two independently verified decoders, rather than two competing live BLE clients.

## Next steps

Audit exact channel mapping and code scales with source-pinned independent fixtures (#47, #53), perform authorized serial 3×60 s trials on the physical Athena (#40, #50), preserve version/preset/lifecycle evidence, and compare the resulting anonymized reports (#44, #48). Keep research EEG/BIDS validation blocked until physical measurement is verified.
