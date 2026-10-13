# EEGZ command-line visualization

Install the optional plot dependency in your Windows project venv: `.\.venv\Scripts\python.exe -m pip install -e ".[muse,plot]"`.

Use `python -m eeg_athenalyze plot --session data/local/athena-60s.eegz` to display all EEG channels in microvolts. Add `--output data/local/athena-60s-plot.png` to save a PNG (SVG/PDF supported). Use `--session data/local/eo-repeat.eegz.partial.jsonl` to view samples in an incomplete acquisition journal without converting it into a finalized recording.

The default x-axis represents sample index divided by nominal sampling rate. It does **not** assert a verified hardware clock. Use `--time-axis source` to inspect original source timestamps, including duplicates. Use `--max-points 8000` to cap plotted points without modifying original data. Viewing EEG does not require EO/EC experiment event metadata. Never treat a short disconnected journal as a valid experimental trial.

## Interactive trace and spectral views

The Matplotlib toolbar provides zoom/pan and an amplitude scale slider controls the trace y-axis in microvolts. Choose a nominal sample-index interval using `--start` and `--duration`. Select `--view trace|psd|spectrogram|all` and optionally a channel via `--channel AF7`. A multichannel spectrogram uses the first displayed channel; select a channel explicitly when needed.

```powershell
.\.venv\Scripts\python.exe -m eeg_athenalyze plot --session data\local\athena-60s.eegz --view all --channel AF7 --start 5 --duration 20
.\.venv\Scripts\python.exe -m eeg_athenalyze plot --session data\local\athena-60s.eegz --view psd --channel AF8 --output data\local\af8-psd.png
```

Spectral frequencies use the **nominal** sampling rate, not verified physical timestamps. Interpret cautiously when packet timing, repeated timestamps, or amplitude clipping are present. The plot command never edits the raw source archive.
