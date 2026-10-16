"""Conservative comparison of *separate* Athena BLE and BrainFlow recordings.

This is a metadata-level cross-backend report, not sample alignment,
simultaneous acquisition, packet loss estimation, or physical timing validation.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from eeg_athenalyze.archive import load_recording
from eeg_athenalyze.ble_notification_qc import summarize_notification_journal


def compare_sequential_sources(ble_jsonl: Path, brainflow_eegz: Path) -> dict[str, object]:
    ble = summarize_notification_journal(ble_jsonl)
    eeg = load_recording(brainflow_eegz)
    timestamps = eeg.timestamps_seconds
    duplicates = sum(b == a for a, b in zip(timestamps, timestamps[1:]))
    backwards = sum(b < a for a, b in zip(timestamps, timestamps[1:]))
    sample_count = len(eeg.samples_uv)
    recorded_span = timestamps[-1] - timestamps[0] if len(timestamps) > 1 else None
    ble_host_span = (
        ble["last_host_monotonic_seconds"] - ble["first_host_monotonic_seconds"]
        if ble["first_host_monotonic_seconds"] is not None else None
    )
    metadata = eeg.metadata
    return {
        "schema_version": 1,
        "comparison_mode": "independent_sequential_sessions_not_aligned",
        "data_sources": ["raw_ble_notification_jsonl", "brainflow_eegz"],
        "simulated_or_measured_eeg": metadata.get("data_status", "unknown"),
        "ble": {
            "notification_count": ble["notification_count"],
            "parsed_notification_count": ble["parsed_notification_count"],
            "invalid_notification_count": ble["invalid_notification_count"],
            "primary_frame_count": ble["primary_frame_count"],
            "eeg_tag_count": ble["eeg_tag_count"],
            "nominal_eeg_sample_positions": ble["nominal_eeg_sample_positions"],
            "host_receive_span_seconds": ble_host_span,
            "largest_host_notification_gap_seconds": ble["largest_host_notification_gap_seconds"],
        },
        "brainflow": {
            "sample_count": sample_count,
            "nominal_sampling_rate_hz": eeg.sample_rate_hz,
            "channel_names": list(eeg.channel_names),
            "source_timestamp_span_seconds": recorded_span,
            "duplicate_adjacent_source_timestamps": duplicates,
            "backwards_source_timestamps": backwards,
        },
        "comparison": {
            "direct_sample_equality_tested": False,
            "same_session": False,
            "packet_loss_estimate": None,
            "physical_timing_verified": False,
            "hardware_validated": False,
            "interpretation": "Independent sessions can support diagnostic comparison only; counts and clocks must not be aligned or subtracted to infer BLE packet loss.",
        },
    }


def write_comparison(ble_jsonl: Path, brainflow_eegz: Path, output: Path) -> Path:
    result = compare_sequential_sources(ble_jsonl, brainflow_eegz)
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write("\n")
    return output


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ble", type=Path, required=True)
    parser.add_argument("--eegz", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        result = write_comparison(args.ble, args.eegz, args.report)
    except (OSError, ValueError) as error:
        parser.exit(1, f"Sequential backend comparison failed: {error}\n")
    print(f"Saved independent-session metadata comparison: {result}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
