"""Offline assessment of a physically recorded Muse S Athena source archive."""
from __future__ import annotations

import json
import math
from pathlib import Path

from eeg_athenalyze.archive import load_recording


def assess_archive(source: Path, report: Path) -> dict[str, object]:
    """Assess time continuity and values; not a certificate of physical accuracy."""
    recording = load_recording(source)
    if recording.metadata.get("data_status") != "measured":
        raise ValueError("Hardware validation requires a measured recording, not synthetic EEG")
    if recording.metadata.get("device_model") != "Muse S Athena":
        raise ValueError("Not a Muse S Athena recording")
    if report.exists():
        raise FileExistsError(f"Report already exists: {report}")
    from statistics import median

    times = recording.timestamps_seconds
    fs = recording.sample_rate_hz
    differences = [b - a for a, b in zip(times, times[1:])]
    duration = times[-1] - times[0] if len(times) >= 2 else 0.0
    expected_intervals = len(times) - 1
    gap_threshold = 1.5 / fs
    gap_count = sum(d > gap_threshold for d in differences)
    median_interval = median(differences) if differences else None
    observed_rate = 1.0 / median_interval if median_interval else None
    channel_ranges = {
        name: {
            "minimum_uv": min(row[index] for row in recording.samples_uv),
            "maximum_uv": max(row[index] for row in recording.samples_uv),
        }
        for index, name in enumerate(recording.channel_names)
    } if recording.samples_uv else {}
    checks = {
        "four_channels": len(recording.channel_names) == 4,
        "has_samples": len(recording.samples_uv) > 1,
        "timestamp_monotonic": all(d > 0 and math.isfinite(d) for d in differences),
        "no_detected_long_intervals": gap_count == 0,
        "hardware_reference_verified": bool(recording.metadata.get("electrode_reference_verified")),
        "physical_timing_verified": bool(recording.metadata.get("timing_verified")),
    }
    outcome = {
        "status": "REQUIRES_PHYSICAL_REVIEW",
        "source_archive": source.name,
        "recording_id": recording.recording_id,
        "channel_names": list(recording.channel_names),
        "sample_count": len(times),
        "sampling_rate_nominal_hz": fs,
        "median_observed_rate_hz": observed_rate,
        "recording_elapsed_seconds": duration,
        "gap_threshold_seconds": gap_threshold,
        "suspected_long_intervals": gap_count,
        "largest_interval_seconds": max(differences) if differences else None,
        "channel_ranges_uv": channel_ranges,
        "checks": checks,
        "notes": [
            "No BLE packet sequence or ground-truth hardware clock is verified.",
            "No detected gaps does not prove that packets were never lost.",
            "Requires review of electrode reference, placement, source clock and firmware.",
        ],
    }
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps(outcome, ensure_ascii=False, indent=2), encoding="utf-8")
    return outcome
