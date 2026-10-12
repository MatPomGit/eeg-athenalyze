# Muse S Athena: real EEG acquisition (M03 development)

This is a **physical hardware** command, not the synthetic demo. It requires Muse S Athena, Bluetooth on Windows 11 and BrainFlow installed in the isolated project environment.

```powershell
.\.venv\Scripts\python.exe -m pip install ".[muse]"
.\.venv\Scripts\python.exe -m eeg_athenalyze devices check --device muse-athena
.\.venv\Scripts\python.exe -m eeg_athenalyze record --device muse-athena --duration 30 --output data\local\physical-session.eegz
```

You can optionally specify `--serial-number` or `--mac-address` if device discovery requires it. Do not put these identifiers in committed config or public issue logs. The command refuses to replace an existing archive.

The adapter reads actual default-preset EEG and BrainFlow source timestamps, saves channel data as microvolts and checks timestamp monotonicity. It cannot claim a particular hardware reference or precise sampling-time accuracy until the physical Muse is tested. **Do not export these measured sessions as BIDS using the synthetic-only exporter.**

Known limits: collection is in-memory; interrupted runs do not yet preserve their partial samples. Long sessions, packet gaps, all auxiliary presets and physical quality checks remain open tasks. Follow [TODO](../../TODO.md) before research deployment.
