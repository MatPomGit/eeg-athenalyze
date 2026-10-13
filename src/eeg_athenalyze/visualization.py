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


def inspect_signal(
    source: Path, *, output: Path | None = None, view: str = "all",
    channel: str | None = None, start: float = 0.0,
    duration: float | None = None, scale_uv: float | None = None,
    max_points: int = 8000,
) -> Path | None:
    """Interactive trace, PSD and spectrogram using a *nominal* sample clock.

    Source timestamps and amplitudes are never modified or inferred to be validated.
    """
    if view not in ("trace", "psd", "spectrogram", "all"):
        raise ValueError("Unsupported view")
    if not math.isfinite(start) or start < 0:
        raise ValueError("start must be non-negative")
    if duration is not None and (not math.isfinite(duration) or duration <= 0):
        raise ValueError("duration must be positive and finite")
    if scale_uv is not None and (not math.isfinite(scale_uv) or scale_uv <= 0):
        raise ValueError("scale_uv must be positive and finite")
    if max_points < 100:
        raise ValueError("max_points must be at least 100")
    try:
        import numpy as np
        import matplotlib.pyplot as plt
        from matplotlib.widgets import Slider
    except ImportError as error:
        raise RuntimeError("Install plotting dependencies: python -m pip install -e '.[plot]'") from error

    names, rows, _, fs, kind = read_samples(source)
    if channel and channel not in names:
        raise ValueError(f"Unknown channel: {channel}. Available: {', '.join(names)}")
    if not rows:
        raise ValueError("Recording has no samples")
    first = int(start * fs)
    stop = min(len(rows), int((start + duration) * fs)) if duration else len(rows)
    if first >= len(rows) or stop <= first:
        raise ValueError("Selected interval contains no samples")
    selected_names = (channel,) if channel else names
    selected_indices = [names.index(name) for name in selected_names]
    values = np.asarray(rows[first:stop], dtype=float)[:, selected_indices]
    if view in ("psd", "spectrogram", "all") and len(values) < 16:
        raise ValueError("At least 16 samples are needed for spectral views")
    modes = ("trace", "psd", "spectrogram") if view == "all" else (view,)
    fig, axes = plt.subplots(len(modes), 1, figsize=(13, 3.2 * len(modes) + 1.5),
                             squeeze=False)
    fig.subplots_adjust(bottom=0.16 if output is None else 0.1, hspace=0.55)
    axes = axes[:, 0]
    nominal_t = (np.arange(len(values)) + first) / fs
    nfft = min(len(values), max(16, int(fs * 2)))
    for mode, ax in zip(modes, axes):
        if mode == "trace":
            step = max(1, math.ceil(len(values) / max_points))
            t = nominal_t[::step]
            for col, label in enumerate(selected_names):
                ax.plot(t, values[::step, col], lw=0.65, label=label)
            if scale_uv is not None:
                ax.set_ylim(-scale_uv, scale_uv)
            ax.set_ylabel("Amplitude (µV)")
            ax.set_xlabel("Nominal sample-index time (s)")
            ax.legend(loc="upper right")
            ax.grid(alpha=0.25)
        elif mode == "psd":
            for col, label in enumerate(selected_names):
                ax.psd(values[:, col], NFFT=nfft, Fs=fs,
                       noverlap=nfft // 2, label=label)
            ax.set_xlim(0, min(60, fs / 2))
            ax.set_xlabel("Frequency (Hz)")
            ax.set_ylabel("PSD (dB/Hz, ref. 1 µV²/Hz)")
            ax.legend(loc="upper right")
            ax.grid(alpha=0.25)
        else:
            chosen = 0
            pxx, freq, bins, raster = ax.specgram(
                values[:, chosen], NFFT=nfft, Fs=fs,
                noverlap=nfft // 2, xextent=(nominal_t[0], nominal_t[-1]),
                cmap="viridis",
            )
            ax.set_ylim(0, min(45, fs / 2))
            ax.set_ylabel("Frequency (Hz)")
            ax.set_xlabel("Nominal sample-index time (s)")
            ax.set_title(f"Spectrogram: {selected_names[chosen]}")
            fig.colorbar(raster, ax=ax, label="PSD (dB)")
    fig.suptitle(f"{Path(source).name} | {kind} | fs={fs:g} Hz (nominal; timing unverified)")
    if output is not None:
        output = Path(output)
        if output.exists():
            raise FileExistsError(f"Plot already exists: {output}")
        if output.suffix.lower() not in (".png", ".svg", ".pdf"):
            raise ValueError("Output must be PNG, SVG or PDF")
        output.parent.mkdir(parents=True, exist_ok=True)
        try:
            fig.savefig(output, dpi=160)
        finally:
            plt.close(fig)
        return output

    # Standard Matplotlib toolbar provides zoom/pan. This slider adjusts
    # amplitude scaling of a trace without touching samples or the archive.
    if "trace" in modes:
        trace_ax = axes[modes.index("trace")]
        slider_ax = fig.add_axes((0.18, 0.04, 0.66, 0.025))
        peak = max(1.0, float(np.nanmax(np.abs(values))))
        slider = Slider(slider_ax, "Scale (µV)", 1.0, max(2.0, peak * 2),
                        valinit=scale_uv or peak * 1.1)
        def update_scale(value):
            trace_ax.set_ylim(-value, value)
            fig.canvas.draw_idle()
        slider.on_changed(update_scale)
        fig._eeg_scale_slider = slider  # retain widget for GUI lifetime
    try:
        plt.show()
    finally:
        plt.close(fig)
    return None
