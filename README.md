# EEG Athenalyze

EEG acquisition, preprocessing, and analysis toolkit for Muse S Athena, Python,
and Windows 11.

## Current status

The initial implementation provides a deterministic synthetic EEG generator and
a lossless, SHA-256-verified native recording archive. Synthetic data is clearly
identified as simulated; physical Muse S Athena acquisition, EEG-BIDS export,
preprocessing, and experiments are not implemented yet.

## Quick start

Use Python 3.12 in a local virtual environment:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install .
.venv\Scripts\eeg-athenalyze.exe synthetic-record --output data\demo.eegz --duration 10 --seed 42
```

The `synthetic-record` command refuses to overwrite an existing archive. Each
archive contains the original simulated sample values, elapsed timestamps,
channel metadata, and a checksum manifest.

## Development

Run the standard-library tests without hardware or third-party runtime packages:

```powershell
python -m unittest discover -s tests -v
```

All EEG values are simulated in this initial implementation. It has not been
validated with physical hardware and does not claim BIDS compliance.
