"""Append-only recovery journal for in-progress physical EEG sessions.

Journal files are not BIDS and cannot be mistaken for finalized .eegz archives.
"""
from __future__ import annotations

import json
import math
import os
from pathlib import Path

_JOURNAL_SUFFIX = ".partial.jsonl"


class AcquisitionJournal:
    """Write each acquired chunk durably with explicit timestamps and channels."""

    def __init__(self, destination: Path, *, channel_count: int) -> None:
        if channel_count <= 0:
            raise ValueError("channel_count must be positive")
        self.path = Path(str(destination) + _JOURNAL_SUFFIX)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._handle = self.path.open("x", encoding="utf-8", newline="\n")
        self.channel_count = channel_count
        self.sample_count = 0
        self._last_timestamp = -math.inf

    def append(self, eeg: object, timestamps: object) -> None:
        """Persist a sample-major chunk. Never synthesize or correct timing."""
        rows = eeg.tolist()
        times = timestamps.tolist()
        if len(rows) != len(times):
            raise ValueError("EEG and timestamp counts differ")
        payload = []
        last = self._last_timestamp
        for offset, (row, value) in enumerate(zip(rows, times)):
            t = float(value)
            sample_index = self.sample_count + offset
            if len(row) != self.channel_count:
                raise ValueError(
                    f"EEG channel count mismatch at sample {sample_index}: "
                    f"expected {self.channel_count}, received {len(row)}"
                )
            if not math.isfinite(t):
                raise ValueError(
                    f"Nonfinite BrainFlow source timestamp at sample {sample_index}: {t!r}"
                )
            if t < last:
                raise ValueError(
                    f"Decreasing BrainFlow source timestamp at sample {sample_index}: "
                    f"current={t:.9f}, previous={last:.9f}, delta={t-last:.9f} s. "
                    "Samples cannot be silently sorted, dropped or retimed."
                )
            if not all(math.isfinite(float(item)) for item in row):
                raise ValueError(f"Nonfinite EEG measurement at sample {sample_index}")
            payload.append({"timestamp": t, "channels_uv": [float(v) for v in row]})
            last = t
        if not payload:
            return
        # Commit the complete validated chunk; lines up to the last newline
        # remain readable after a crash, even if the final line was torn.
        self._handle.write("".join(json.dumps(item, allow_nan=False) + "\n" for item in payload))
        self._handle.flush()
        os.fsync(self._handle.fileno())
        self._last_timestamp = last
        self.sample_count += len(payload)

    def close(self) -> None:
        if not self._handle.closed:
            self._handle.close()

    def __enter__(self) -> AcquisitionJournal:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()


def recover_journal(path: Path, *, channel_count: int) -> tuple[list[list[float]], list[float]]:
    """Read complete validated lines, ignoring only a torn trailing line."""
    samples: list[list[float]] = []
    times: list[float] = []
    with Path(path).open("rb") as handle:
        data = handle.read()
    lines = data.split(b"\n")
    # An un-terminated final record is incomplete and cannot be trusted.
    if lines and lines[-1]:
        lines.pop()
    for number, line in enumerate(lines, start=1):
        if not line:
            continue
        try:
            item = json.loads(line)
            row, timestamp = item["channels_uv"], float(item["timestamp"])
            if (
                len(row) != channel_count
                or not math.isfinite(timestamp)
                or (times and timestamp < times[-1])
                or any(not math.isfinite(float(v)) for v in row)
            ):
                raise ValueError("Invalid journal sample")
        except (ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
            raise ValueError(f"Corrupted journal at line {number}") from exc
        samples.append([float(v) for v in row])
        times.append(timestamp)
    return samples, times
