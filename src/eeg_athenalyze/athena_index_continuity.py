"""Conservative offline Athena primary-counter continuity evidence.

Packet index is a 16-bit sequence *candidate*. Without firmware-confirmed
increment semantics, discontinuities are not radio packet-loss measurements.
"""
from __future__ import annotations
from collections import Counter
from pathlib import Path
import json
from eeg_athenalyze.athena_notification_parser import parse_notification

def summarize_index_continuity(source: Path) -> dict[str, object]:
    from eeg_athenalyze.ble_notification_qc import SENSOR_SUFFIXES
    grouped: dict[str, list[int]] = {uuid: [] for uuid in SENSOR_SUFFIXES}
    invalid = 0
    with Path(source).open(encoding="utf-8") as stream:
        for row in stream:
            item = json.loads(row)
            uuid = item["characteristic"].lower()
            if uuid not in grouped:
                raise ValueError("Unexpected GATT characteristic")
            raw = bytes.fromhex(item["payload_hex"])
            try:
                parse_notification(raw)
            except ValueError:
                invalid += 1
                continue
            offset = 0
            while offset < len(raw):
                size = raw[offset]
                grouped[uuid].append(int.from_bytes(raw[offset + 1:offset + 3], "little"))
                offset += size
    result = {}
    for uuid, indices in grouped.items():
        deltas = [((b - a) & 0xFFFF) for a, b in zip(indices, indices[1:])]
        result[uuid] = {
            "primary_frames": len(indices),
            "repeated_index_transitions": deltas.count(0),
            "successive_index_transitions": deltas.count(1),
            "jump_candidate_transitions": sum(d > 1 for d in deltas),
            "forward_modulo_65536_delta_histogram": dict(sorted(Counter(map(str, deltas)).items())),
            "first_index": indices[0] if indices else None,
            "last_index": indices[-1] if indices else None,
        }
    return {
        "status": "offline_counter_evidence_only",
        "invalid_notifications": invalid,
        "streams": result,
        "counter_semantics_verified_on_device": False,
        "bluetooth_packet_loss_count": None,
        "physical_clock_verified": False,
    }
