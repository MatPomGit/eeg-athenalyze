# EEG Neurolyze

EEG acquisition, preprocessing, and analysis toolkit for Muse S Athena, Python,
and Windows 11.

## Current status

The initial implementation provides deterministic synthetic EEG generation,
lossless SHA-256-verified native archives, and an EO/EC resting-state synthetic
workflow with Welch alpha-power comparison and an HTML report. Synthetic data is
clearly identified as simulated; physical Muse S Athena acquisition, EEG-BIDS
export, and PsychoPy experiments are not implemented yet.

## Windows 11 one-click tutorial

Run `windows/setup_environment.bat` once, then double-click `windows/run_synthetic_demo.bat`. The scripts use `.venv` and do not install packages globally. The demo creates a new simulated EO/EC archive and HTML report under `data/demo/` (ignored by Git).

Detailed guides: [English](docs/en/quickstart.md) | [Polski](docs/pl/quickstart.md).

These launchers currently run **simulated recordings only**. They do not connect to Muse S Athena or generate BIDS datasets.

## Quick start

Use Python 3.12 in a local virtual environment:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install .
.venv\Scripts\eeg-athenalyze.exe experiment run eyes-open-closed --output data\demo --duration-scale 0.05 --seed 42
```

Omit `--duration-scale` for the specified 30 s stabilization, 120 s eyes-open,
30 s break, and 120 s eyes-closed protocol. The `--duration-scale` option is
useful for quick software demonstrations; it does not change the defaults.
Each archive contains original simulated sample values, elapsed timestamps,
condition events, channel metadata, and a checksum manifest. Existing archives
and reports are never overwritten.

Reanalyze an archived session without reacquiring data:

```powershell
.venv\Scripts\eeg-athenalyze.exe analyze --session data\demo\sub-001_ses-SESSION_task-rest.eegz
```

The analysis reports per-channel 8–13 Hz alpha-band power for eyes-open and
eyes-closed blocks. It is an educational signal summary, not a diagnosis or a
validated BIDS export.

## Development

Run the standard-library tests without hardware or third-party runtime packages:

```powershell
python -m unittest discover -s tests -v
```

All EEG values are simulated in this initial implementation. It has not been
validated with physical hardware and does not claim BIDS compliance.
