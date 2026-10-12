# Muse S Athena: real EEG acquisition (M03 development)

This is a **physical hardware** command, not the synthetic demo. It requires Muse S Athena, Bluetooth on Windows 11 and BrainFlow installed in the isolated project environment.

```powershell
.\.venv\Scripts\python.exe -m pip install ".[muse]"
.\.venv\Scripts\python.exe -m eeg_athenalyze devices check --device muse-athena
.\.venv\Scripts\python.exe -m eeg_athenalyze record --device muse-athena --duration 30 --output data\local\physical-session.eegz
```

You can optionally specify `--serial-number` or `--mac-address` if device discovery requires it. Do not put these identifiers in committed config or public issue logs. The command refuses to replace an existing archive.

The adapter reads actual default-preset EEG and BrainFlow source timestamps, saves channel data as microvolts and checks timestamp monotonicity. It cannot claim a particular hardware reference or precise sampling-time accuracy until the physical Muse is tested. **Do not export these measured sessions as BIDS using the synthetic-only exporter.**

Recording now appends an fsync-backed `.partial.jsonl` journal next to the requested archive. If acquisition is interrupted, complete journal records remain available for recovery using `eeg_athenalyze.acquisition_journal.recover_journal`; they are not yet automatically converted into a finalized archive. Successful finalization removes the journal. Do not delete journal files after errors.

Known limits: final archive conversion still loads all recorded samples into RAM; partial recovery is a Python API, not yet a one-click action. Long sessions, packet gaps, all auxiliary presets and physical quality checks remain open tasks. Follow [TODO](../../TODO.md) before research deployment.
