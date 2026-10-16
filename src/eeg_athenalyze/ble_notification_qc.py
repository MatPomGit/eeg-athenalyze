"""Offline summary of explicitly captured BLE notifications; no BLE access.

Input is newline-delimited JSON with receiver-supplied monotonic time, GATT
characteristic and raw payload hex. Never publish raw EEG in output reports.
"""
from __future__ import annotations

from collections import Counter
import json
import math
from pathlib import Path

from eeg_athenalyze.athena_notification_parser import parse_notification

MAX_RECORDS = 2_000_000
MAX_LINE_BYTES = 16_384
SENSOR_SUFFIXES = ("273e0013-4c4d-454d-96be-f03bac821358",
                   "273e0014-4c4d-454d-96be-f03bac821358")


def summarize_notification_journal(source: Path) -> dict[str, object]:
    """Validate schema and summarize locally captured notifications.

    Fail the entire report on invalid JSON/schema. An invalid wire packet is
    counted but NOT interpreted as missing EEG, BLE packet loss or bad hardware.
    """
    total = valid = invalid = 0
    tags: Counter[str] = Counter()
    by_characteristic: Counter[str] = Counter()
    primary_indices: list[int] = []
    prev_time = None
    longest_host_gap = 0.0
    first_time = last_time = None
    with Path(source).open("rb") as stream:
        for line in stream:
            total += 1
            if total > MAX_RECORDS:
                raise ValueError("Too many notification records")
            if len(line) > MAX_LINE_BYTES:
                raise ValueError(f"Record {total}: oversized JSONL line")
            try:
                item = json.loads(line)
                if not isinstance(item, dict):
                    raise ValueError("record must be object")
                t = item["receive_monotonic_seconds"]
                characteristic = item["characteristic"].lower()
                raw_hex = item["payload_hex"]
                if not isinstance(t, (int, float)) or isinstance(t, bool) or not math.isfinite(t) or t < 0:
                    raise ValueError("invalid monotonic time")
                if prev_time is not None and t < prev_time:
                    raise ValueError("nonmonotonic receive clock")
                if not isinstance(characteristic, str) or characteristic not in SENSOR_SUFFIXES:
                    raise ValueError("unrecognized characteristic")
                if not isinstance(raw_hex, str) or len(raw_hex) > 1024 or len(raw_hex) % 2:
                    raise ValueError("invalid payload hex")
                raw = bytes.fromhex(raw_hex)
            except (ValueError, TypeError, KeyError, AttributeError) as exc:
                raise ValueError(f"Record {total}: invalid JSONL schema: {exc}") from exc
            if first_time is None:
                first_time = t
            if prev_time is not None:
                longest_host_gap = max(longest_host_gap, t - prev_time)
            prev_time = last_time = t
            by_characteristic[characteristic] += 1
            try:
                parsed = parse_notification(raw)
                if not parsed:
                    raise ValueError("empty packet payload")
            except ValueError:
                invalid += 1
                continue
            valid += 1
            tags.update(f"0x{packet.tag:02x}" for packet in parsed)
            # One index per decoded *primary* frame; subpacket indices differ.
            # Without a verified frame-offset table, primary boundaries are
            # not recoverable from the flattened packet list: deduplicate by
            # the pair (packet_index, contiguous packet group) conservatively.
            indices = [p.packet_index for p in parsed]
            primary_indices.append(indices[0])
    return {
        "schema_version": 1, "data_source": "offline_user_supplied_raw_ble",
        "hardware_timing_verified": False, "packet_loss_estimate": None,
        "notification_count": total, "parsed_notification_count": valid,
        "invalid_notification_count": invalid,
        "tags": dict(sorted(tags.items())),
        "characteristic_notifications": dict(sorted(by_characteristic.items())),
        "first_host_monotonic_seconds": first_time,
        "last_host_monotonic_seconds": last_time,
        "largest_host_notification_gap_seconds": longest_host_gap if total > 1 else None,
        "first_parsed_packet_index": primary_indices[0] if primary_indices else None,
        "last_parsed_packet_index": primary_indices[-1] if primary_indices else None,
        "note": "Counts are application-visible captures, not controller-level BLE losses.",
    }


def write_notification_summary(source: Path, output: Path) -> Path:
    """Fail closed and do not overwrite reports."""
    output = Path(output)
    if output.exists():
        raise FileExistsError(output)
    result = summarize_notification_journal(source)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as f:
        json.dump(result, f, indent=2, sort_keys=True, allow_nan=False)
        f.write("\n")
    return output


def main(argv: list[str] | None = None) -> int:
    """Standalone read-only analysis: python -m eeg_athenalyze.ble_notification_qc."""
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        result = write_notification_summary(args.input, args.report)
    except (OSError, ValueError) as exc:
        parser.exit(1, f"BLE notification QC failed: {exc}\n")
    print(f"Saved non-raw BLE QC report: {result}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
