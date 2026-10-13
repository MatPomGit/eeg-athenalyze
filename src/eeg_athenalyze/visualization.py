"""Read-only EEG channel visualization for final archives and recovery journals."""
from __future__ import annotations

import json
import math
from pathlib import Path

DEFAULT_CHANNELS = ("TP9", "AF7", "AF8", "TP10")


def read_samples(source: Path):
    """Return names, channels in microvolts, source times, nominal rate."""
    from eeg_athenalyze.archive import load_recording

    source = Path(source)
    if source.name.endswith(".partial.jsonl"):
        names = DEFAULT_CHANNELS
        rows, times = [], []
        with source.open("rb") as stream:
            for index, raw in enumerate(stream, 1):
                if not raw.endswith(b"\n"):
                    break  # Preserve an incomplete final journal line.
                try:
                    item = json.loads(raw)
                    values = [float(v) for v in item["channels_uv"]]
                    t = float(item["timestamp"])
                except (ValueError, TypeError, KeyError) as error:
                    raise ValueError(f"Invalid journal entry at line {index}") from error
                if len(values) != len(names) or not math.isfinite(t) or any(
                    not math.isfinite(v) for v in values
                ):
                    raise ValueError(f"Invalid journal values at line {index}")
                if times and t < times[-1]:
                    raise ValueError(f"Backward timestamp at journal line {index}")
                rows.append(values)
                times.append(t)
        return names, rows, times, 256.0, "partial journal"
    if source.suffix != ".eegz":
        raise ValueError("Expected .eegz or .partial.jsonl file")
    rec = load_recording(source)
    return rec.channel_names, rec.samples_uv, rec.timestamps_seconds, rec.sample_rate_hz, "EEGZ archive"


def plot_signal(source: Path, *, output: Path | None = None,
                time_axis: str = "samples", max_points: int = 8000) -> Path | None:
    """Visualize source values without changing recording or inventing timestamps.

    samples: display nominal sample-index axis; source: raw timestamps, with duplicates.
    """
    if time_axis not in ("samples", "source"):
        raise ValueError("time_axis must be 'samples' or 'source'")
    if max_points < 100:
        raise ValueError("max_points must be at least 100")
    try:
        import matplotlib.pyplot as plt
    except ImportError as error:
        raise RuntimeError("Install visualization extra: python -m pip install -e '.[plot]'") from error

    names, rows, times, sample_rate, kind = read_samples(source)
    if not rows:
        raise ValueError("The recording contains no recoverable samples")
    # Plot only a subset; the full original samples remain untouched on disk.
    step = max(1, math.ceil(len(rows) / max_points))
    indices = list(range(0, len(rows), step))
    if time_axis == "samples":
        x = [i / sample_rate for i in indices]
        xlabel = f"Nominal sample-index time (s; fs={sample_rate:g} Hz, unverified)"
    else:
        x = [times[i] - times[0] for i in indices]
        xlabel = "Source timestamp offset (s; not validated)"
    fig, axes = plt.subplots(len(names), 1, figsize=(14, max(4, 2.1 * len(names))), sharex=True)
    if len(names) == 1:
        axes = [axes]
    try:
        for channel, ax in enumerate(axes):
            y = [rows[i][channel] for i in indices]
            ax.plot(x, y, linewidth=0.55)
            ax.set_ylabel(f"{names[channel]} (µV)")
            ax.grid(alpha=0.25)
        axes[-1].set_xlabel(xlabel)
        fig.suptitle(f"EEG signal | {source.name} | {kind} | {len(rows)} samples")
        fig.tight_layout()
        if output is not None:
            destination = Path(output)
            if destination.exists():
                raise FileExistsError(f"Plot already exists: {destination}")
            if destination.suffix.lower() not in (".png", ".svg", ".pdf"):
                raise ValueError("Use .png, .svg or .pdf plot output")
            destination.parent.mkdir(parents=True, exist_ok=True)
            fig.savefig(destination, dpi=160)
            return destination
        plt.show()
        return None
    finally:
        plt.close(fig)
