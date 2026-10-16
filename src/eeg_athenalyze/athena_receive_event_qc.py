"""Offline event classification from host receive gaps and Athena frame counters.

Event labels are software observations, never certified RF loss or device faults.
"""
from __future__ import annotations

from collections import Counter
import json
import math
from pathlib import Path

from eeg_athenalyze.athena_notification_parser import parse_notification
from eeg_athenalyze.ble_notification_qc import SENSOR_SUFFIXES, MAX_LINE_BYTES, MAX_RECORDS


def summarize_receive_events(source: Path, *, gap_threshold_seconds: float = 0.2) -> dict[str, object]:
    if not math.isfinite(gap_threshold_seconds) or gap_threshold_seconds <= 0:
        raise ValueError("Gap threshold must be finite and positive")
    previous: dict[str, tuple[float, int]] = {}
    counts: Counter[str] = Counter()
    by_stream: dict[str, Counter[str]] = {uuid: Counter() for uuid in SENSOR_SUFFIXES}
    first_timestamp = None
    last_timestamp = None
    observed = 0
    with Path(source).open("rb") as stream:
        for lineno, line in enumerate(stream, 1):
            if lineno > MAX_RECORDS or len(line) > MAX_LINE_BYTES:
                raise ValueError("Capture exceeds supported limits")
            try:
                item = json.loads(line)
                if not isinstance(item, dict):
                    raise ValueError("Expected object")
                uuid = item["characteristic"]
                t = item["receive_monotonic_seconds"]
                raw = bytes.fromhex(item["payload_hex"])
                if not isinstance(uuid, str) or uuid.lower() not in by_stream:
                    raise ValueError("Unknown characteristic")
                uuid = uuid.lower()
                if isinstance(t, bool) or not isinstance(t, (int, float)) or not math.isfinite(t) or t < 0:
                    raise ValueError("Invalid receive time")
                if last_timestamp is not None and t < last_timestamp:
                    raise ValueError("Nonmonotonic host receipt time")
            except (KeyError, TypeError, ValueError, AttributeError) as exc:
                raise ValueError(f"Invalid notification record {lineno}: {exc}") from exc
            observed += 1
            first_timestamp = t if first_timestamp is None else first_timestamp
            last_timestamp = t
            try:
                decoded = parse_notification(raw)
                if not decoded:
                    raise ValueError("Empty notification")
            except ValueError:
                counts["malformed_notification"] += 1
                by_stream[uuid]["malformed_notification"] += 1
                continue
            primary = []
            offset = 0
            while offset < len(raw):
                primary.append(int.from_bytes(raw[offset + 1:offset + 3], "little"))
                offset += raw[offset]
            if not primary:
                raise ValueError("Parsed notification contains no primary frames")
            for i, index in enumerate(primary):
                previous_frame = previous.get(uuid)
                # Within a single callback, frames have the same host receipt time:
                # do not label this as an interarrival gap.
                if previous_frame is not None:
                    prev_t, prev_index = previous_frame
                    delta = (index - prev_index) & 0xFFFF
                    gap = i == 0 and t - prev_t > gap_threshold_seconds
                    if delta == 0:
                        label = "repeated_index"
                    elif delta > 1:
                        label = "index_jump_candidate"
                    else:
                        label = "successive_index"
                    counts[label] += 1
                    by_stream[uuid][label] += 1
                    if gap:
                        counts["host_receive_gap"] += 1
                        by_stream[uuid]["host_receive_gap"] += 1
                        if delta > 1:
                            counts["host_gap_with_index_jump"] += 1
                            by_stream[uuid]["host_gap_with_index_jump"] += 1
                previous[uuid] = (t, index)
    return {
        "status": "offline_observations_only",
        "schema_version": 1,
        "notification_count": observed,
        "host_gap_threshold_seconds": gap_threshold_seconds,
        "event_counts": dict(sorted(counts.items())),
        "events_by_characteristic": {key: dict(sorted(value.items())) for key, value in by_stream.items()},
        "first_receive_monotonic_seconds": first_timestamp,
        "last_receive_monotonic_seconds": last_timestamp,
        "packet_loss_estimate": None,
        "device_clock_validated": False,
        "physical_ble_validated": False,
    }


def main(argv: list[str] | None = None) -> int:
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--gap-threshold", type=float, default=0.2)
    args = parser.parse_args(argv)
    try:
        result = summarize_receive_events(args.input, gap_threshold_seconds=args.gap_threshold)
        args.report.parent.mkdir(parents=True, exist_ok=True)
        with args.report.open("x", encoding="utf-8") as output:
            json.dump(result, output, sort_keys=True, indent=2, allow_nan=False)
            output.write("\n")
    except (OSError, ValueError) as exc:
        parser.exit(1, f"Receive event QC failed: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
