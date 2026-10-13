# EEGZ command-line visualization

Install the optional plot dependency in your Windows project venv: `.\.venv\Scripts\python.exe -m pip install -e ".[muse,plot]"`.

Use `python -m eeg_athenalyze plot --session data/local/athena-60s.eegz` to display all EEG channels in microvolts. Add `--output data/local/athena-60s-plot.png` to save a PNG (SVG/PDF supported). Use `--session data/local/eo-repeat.eegz.partial.jsonl` to view samples in an incomplete acquisition journal without converting it into a finalized recording.

The default x-axis represents sample index divided by nominal sampling rate. It does **not** assert a verified hardware clock. Use `--time-axis source` to inspect original source timestamps, including duplicates. Use `--max-points 8000` to cap plotted points without modifying original data. Viewing EEG does not require EO/EC experiment event metadata. Never treat a short disconnected journal as a valid experimental trial.
