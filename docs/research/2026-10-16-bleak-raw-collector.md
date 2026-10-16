# M03: opt-in Muse S Athena raw BLE notification collector

Implementation of the autonomous software portion of #48/#49/#44. **The physical headset has not been tested with this collector.** This module captures only application-visible BLE notifications; it cannot independently measure radio-layer packet losses or certify a hardware sample clock.

## Setup and consent

A Muse S Athena must be physically available. Close BrainFlow, OpenMuse, BlueMuse, the official Muse app and any other BLE owner. Install the free optional dependency in your local environment:

```powershell
.\.venv\Scripts\python.exe -m pip install bleak
```

No pairing settings, Windows root certificates, paid services or device firmware are changed automatically.

## Mode A: passive subscription (no device commands)

```powershell
.\.venv\Scripts\python.exe -m eeg_athenalyze.ble_raw_collector --name MuseS-C87B --duration 60 --output data\local\athena-raw-passive-01.jsonl
```

This attempts discovery and subscribes to *actually notifiable* Athena data characteristics `273e0013` and/or `273e0014`. Passive subscription can yield **zero** samples when the firmware requires explicit streaming commands. In that case an empty local file is retained and the command reports failure, not success.

## Mode B: explicit fixed start/stop sequence

```powershell
.\.venv\Scripts\python.exe -m eeg_athenalyze.ble_raw_collector --name MuseS-C87B --duration 60 --start-stream --preset p21 --output data\local\athena-raw-p21-01.jsonl
```

With explicit `--start-stream`, only a vetted, fixed command allowlist is sent: `v6`, `s`, `h`, selected `p21`/`p1035`/`p1041`, `s`, two `dc001` and optionally `L1` with `--low-latency`. Stop attempts `h` when the BLE session is still connected. **These are commands sourced from public BrainFlow descriptions; successful operation is not guaranteed for the user's firmware.** No unvalidated arbitrary GATT commands are permitted.

Each received callback is written immediately as NDJSON with `receive_monotonic_seconds`, `characteristic` and `payload_hex`. This captures raw human EEG or other sensor data; files reside under ignored `data/local/` and must **not** be committed or shared without explicit privacy authorization. Existing output paths are never overwritten. Errors retain any partial journal for diagnosis.

After a capture, analyze without altering raw bytes:

```powershell
.\.venv\Scripts\python.exe -m eeg_athenalyze.ble_notification_qc --input data\local\athena-raw-p21-01.jsonl --report data\local\athena-raw-p21-01-qc.json
```

The QC report contains counts and host clock intervals, no payload bytes. **Do not interpret zero notifications as zero device samples or clock calibration.** Physical work requires operator approval and on-device GATT logging; these tests only validate the software behavior with mock clients.

## Follow-up

- Verify exact start/stop sequence and GATT write response semantics against installed BrainFlow and actual firmware (#49, #53).
- Capture a physical run with one BLE owner at a time, preserve its raw JSONL locally and generate an anonymized QC report (#48).
- Compare full packet indices including multiple primary frames per BLE notification, and distinguish callback receipt from decode/buffer stages (#44).
- Never promote a software-only test to validated EEG-BIDS export.
