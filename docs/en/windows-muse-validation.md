# Windows 11 Muse S Athena hardware validation

This is an **on-device test procedure**, not evidence of successful physical acquisition.

Install core venv and the optional Muse extra. Use `python -m eeg_athenalyze devices check --device muse-athena` to inspect the BrainFlow layout (this does not establish Bluetooth connectivity). With the charged headband fitted and competing Muse applications closed, run:

```powershell
.\.venv\Scripts\python.exe -m eeg_athenalyze record --device muse-athena --duration 30 --output data\local\athena-30s.eegz
.\.venv\Scripts\python.exe -m eeg_athenalyze devices assess --session data\local\athena-30s.eegz --report data\local\athena-30s-qc.json
```

Repeat with a fresh filename and a five-minute recording. Review per-channel ranges, observed timestamp spacing, apparent gaps, and contact/artifact behavior. Record the Windows and BrainFlow versions, board ID, channel mapping, Muse firmware if available, and connectivity observations privately.

Pass criteria: successful recordings, non-overwritten source archives, investigated timestamp anomalies, documented verified channel units/reference and reproducible results. A lack of detected long intervals **does not prove absence of packet loss**. Timing precision and BLE behavior require physical validation and must not be inferred from mocked CI tests.
