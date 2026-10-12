# EEG Neurolyze

![EEG Neurolyze logo](src/eeg_athenalyze/assets/neurolyze-logo.svg)

EEG acquisition, preprocessing, and analysis toolkit for Muse S Athena, Python,
and Windows 11.

## Architecture and roadmap

- [Full project concept and system architecture](docs/architecture/PROJECT-CONCEPT.md)
- [Architecture Decision Records](docs/architecture/adr/README.md)
- [Implementation roadmap and verification gates](docs/architecture/ROADMAP.md)
- [Agent development rules](AGENTS.md)

The public project is **EEG Neurolyze**; the existing installed Python package and CLI still use the legacy `eeg_athenalyze` / `eeg-athenalyze` names pending a compatibility-managed migration.

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

## EEG-BIDS export (M02 preview)

Install optional requirements in the isolated environment:

```powershell
.\.venv\Scripts\python.exe -m pip install ".[bids]"
.\.venv\Scripts\python.exe -m eeg_athenalyze bids export --session "data\demo\RECORDING.eegz" --dataset "data\bids\ds-demo"
.\.venv\Scripts\python.exe -m eeg_athenalyze bids validate --dataset "data\bids\ds-demo"
```

Replace RECORDING with the generated archive filename. See [English instructions](docs/en/bids.md) and [instrukcja po polsku](docs/pl/bids.md). The exporter currently accepts **synthetic, uniformly sampled recordings only**. BIDS compliance is reported only after official validation; real hardware support and BIDS derivatives remain pending.

## Real Muse S Athena acquisition (M03 development)

Use the isolated Python environment and install the optional BrainFlow adapter:

```powershell
.\.venv\Scripts\python.exe -m pip install ".[muse]"
.\.venv\Scripts\python.exe -m eeg_athenalyze devices check --device muse-athena
.\.venv\Scripts\python.exe -m eeg_athenalyze record --device muse-athena --duration 30 --output data\local\physical-session.eegz
```

This is a **physical recording path**, never a simulated fallback. The code has not yet been tested with an actual Muse S Athena; do not use it for research data until the hardware validation checklist passes. See [English guide](docs/en/muse-athena.md), [polska instrukcja](docs/pl/muse-athena.md), and [TODO](TODO.md).

## Development

Run the standard-library tests without hardware or third-party runtime packages:

```powershell
python -m unittest discover -s tests -v
```

All EEG values are simulated in this initial implementation. It has not been
validated with physical hardware and does not claim BIDS compliance.
