# M02: offline alpha-power derivatives

After exporting and validating a synthetic EEG-BIDS dataset, run:

```powershell
.\.venv\Scripts\python.exe -m eeg_athenalyze bids derivatives --session data\demo\RECORDING.eegz --dataset data\bids\ds-demo
```

Creates a versioned, non-overwriting *custom* per-channel alpha-power TSV and JSON metadata in `derivatives/eeg-neurolyze/`, with source archive SHA-256 and processing provenance. The original `.eegz` remains unchanged.

This feature does **not** establish standardized BIDS support for alpha-power tables or guarantee the custom derivative will pass every BIDS derivative schema rule. Run the official validator separately. Real Muse recording reference, physical timing and verified preprocessing are not yet implemented.
