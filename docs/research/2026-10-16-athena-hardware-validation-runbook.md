# Muse S Athena hardware qualification runbook (M03)

Status: preparation only. No physical device measurements have been performed under this change. Related issues: #40, #44, #47, #48, #49, #53.

## Controls and prerequisites

- Update local Windows 11 checkout and virtual environment. Install free optional Bleak locally. Record Bluetooth adapter and driver version, firmware, Python/BrainFlow/Bleak versions, preset and low-latency flag in a local worksheet.
- Keep every real EEG and raw BLE notification JSONL under ignored data/local/. Never upload personal signals, MAC/device address or credentials.
- Run exactly ONE BLE owner at a time: terminate BrainFlow, BlueMuse, OpenMuse, Muse apps and previous Bleak connections before each new run.
- Never auto-install certificates, change firmware, or claim physical or BIDS validation without device evidence.

## Sequential 60-second validation

1. Inspect GATT, recording exact presence of FE8D, control characteristic, and notify property for 0013 and 0014. A non-notifiable 0014 characteristic alone is not proof of a defect.
2. Run a short passive subscription, without device write commands. Treat zero callbacks as no callbacks, not absence of sensor data.
3. Exit/disconnect passive session. Run opt-in raw BLE capture with preset p21 and default latency; preserve partial data on errors.
4. Exit/disconnect Bleak completely. Run a *separate* 60-second BrainFlow recording with matching preset and latency, retaining partial journal if it fails.
5. Repeat serially for other allowlisted presets p1035 and p1041 only after verifying that the firmware supports the commands. Record repetitions and session environment. Do not subtract counts from different runs to infer dropped packets.

## Commands (Windows PowerShell)

```powershell
.\.venv\Scripts\python.exe tools\diagnose_muse_gatt.py --name MuseS-C87B
.\.venv\Scripts\python.exe -m eeg_athenalyze.ble_raw_collector --name MuseS-C87B --duration 15 --output data\local\ble-passive-run01.jsonl
.\.venv\Scripts\python.exe -m eeg_athenalyze.ble_raw_collector --name MuseS-C87B --duration 60 --start-stream --preset p21 --output data\local\ble-p21-run01.jsonl
.\.venv\Scripts\python.exe -m eeg_athenalyze record --device muse-athena --duration 60 --preset p21 --no-low-latency --output data\local\brainflow-p21-run01.eegz
```

## Local analysis after completed runs

```powershell
.\.venv\Scripts\python.exe -m eeg_athenalyze.ble_notification_qc --input data\local\ble-p21-run01.jsonl --report data\local\ble-p21-run01-qc.json
.\.venv\Scripts\python.exe -m eeg_athenalyze.athena_receive_event_qc --input data\local\ble-p21-run01.jsonl --report data\local\ble-p21-run01-events.json --gap-threshold 0.2
.\.venv\Scripts\python.exe -m eeg_athenalyze.backend_comparison --ble data\local\ble-p21-run01.jsonl --eegz data\local\brainflow-p21-run01.eegz --report data\local\p21-independent-comparison.json
```

The final comparison is possible only when BrainFlow produced a complete EEGZ archive; a partial acquisition must NOT be passed off as complete. The 0.2-second threshold is diagnostic, not physical proof.

## Attribution and classification

| Observation | What can be concluded | What remains unknown |
|---|---|---|
| Discovery unsuccessful | Discovery stage did not locate target | Firmware defect or radio loss |
| FE8D/control present but no notify on 0014 | Characteristic does not advertise notify | 0013 EEG failure |
| GATT write fails | Observed initiation stage failed | Root cause without OS trace |
| Zero BLE callbacks | Host callback received none | Whether headband sent data |
| Invalid frames | Raw capture does not match decoder's expected framing | RF packet loss |
| Raw EEG tags present; later BrainFlow buffer empty in separate run | Independent backend runs had different outcomes | Same-packet decoding loss |
| Host gap and counter jump | Both software observations occurred | Physical loss count |
| BrainFlow duplicate timestamps | Source software timestamp issue possible | Headset clock defect |
| Partial journal on disconnect | Session did not complete | Clinical signal quality |

## Issue update evidence (metadata only)

Provide run number, date, system/driver and software versions, firmware if shareable, preset, latency, duration requested/actual, GATT notify capabilities, BLE callback/frame/TAG and EEG sample counts, timestamp duplicate counts, events and error phase. Never upload source bytes, actual EEG or personal identifiers. Human device access and approval are needed to perform the experiment. Physical signal timing, electrode mapping and 50 Hz origin stay blocked until validated.