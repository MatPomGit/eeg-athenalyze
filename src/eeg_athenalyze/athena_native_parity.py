"""Offline contract for comparing pinned native Athena EEG decoder outputs.

Input/output JSON contains synthetic codes only. This module cannot run or
certify native BlueMuse/BrainFlow binaries on its own.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from eeg_athenalyze.athena_packet_reference import codes_to_uv, decode_eeg_tag_payload


def fixture_manifest():
    """Generate deterministic synthetic vectors with immutable digest fields."""
    patterns = {
        "rails": (0, 1, 8191, 8192, 8193, 16382, 16383, 42) * 2,
        "channels": tuple(t * 100 + c for t in range(4) for c in range(4)),
        "alternating": (0, 16383) * 8,
    }
    from eeg_athenalyze.athena_packet_reference import encode_lsb_14bit
    vectors = []
    for name, codes in patterns.items():
        payload = encode_lsb_14bit(codes)
        for tag in (0x11, 0x12):
            channels = 4 if tag == 0x11 else 8
            matrix = [list(codes[i:i + channels]) for i in range(0, 16, channels)]
            vectors.append({
                "id": f"{name}-{tag:02x}",
                "tag": tag,
                "payload_hex": payload.hex(),
                "payload_sha256": hashlib.sha256(payload).hexdigest(),
                "expected_codes": matrix,
                "expected_uv": [list(codes_to_uv(row)) for row in matrix],
            })
    return {"schema_version": 1, "origin": "synthetic-only", "scale_uv": "1450/16383",
            "vectors": vectors}


def validate_native_result(manifest, actual, *, tolerance_uv=1e-8):
    """Compare native decoder output, fail closed on IDs, shape and provenance."""
    if actual.get("schema_version") != 1:
        raise ValueError("Invalid native result schema_version")
    if actual.get("decoder") not in ("BlueMuse", "BrainFlow"):
        raise ValueError("Unknown native decoder")
    if not isinstance(actual.get("source_commit"), str) or len(actual["source_commit"]) != 40 or any(
            c not in "0123456789abcdefABCDEF" for c in actual["source_commit"]):
        raise ValueError("Pinned 40-hex-character source_commit required")
    results = actual.get("vectors")
    if not isinstance(results, list):
        raise ValueError("Missing vector results")
    expected = {v["id"]: v for v in manifest["vectors"]}
    seen = set()
    errors = []
    for entry in results:
        if not isinstance(entry, dict):
            raise ValueError("Invalid vector result")
        key = entry.get("id")
        if key not in expected or key in seen:
            raise ValueError("Unknown or repeated vector ID")
        seen.add(key)
        ref = expected[key]
        if entry.get("payload_sha256") != ref["payload_sha256"]:
            errors.append(f"{key}: payload digest differs")
        if entry.get("codes") != ref["expected_codes"]:
            errors.append(f"{key}: exact integer codes differ")
        actual_uv, expected_uv = entry.get("uv"), ref["expected_uv"]
        if not isinstance(actual_uv, list) or len(actual_uv) != len(expected_uv):
            errors.append(f"{key}: amplitude shape differs")
            continue
        for row, ref_row in zip(actual_uv, expected_uv):
            if not isinstance(row, list) or len(row) != len(ref_row):
                errors.append(f"{key}: amplitude row shape differs")
                break
            import math
            if any(not isinstance(x, (int, float)) or not math.isfinite(x)
                   or abs(x - y) > tolerance_uv for x, y in zip(row, ref_row)):
                errors.append(f"{key}: amplitude values differ")
                break
    if seen != set(expected):
        errors.append("Missing vector IDs: " + ", ".join(sorted(set(expected) - seen)))
    return {"passed": not errors, "errors": errors, "decoder": actual["decoder"],
            "source_commit": actual["source_commit"], "hardware_validated": False}


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, help="Optional pre-exported fixture JSON")
    parser.add_argument("--native-output", type=Path, help="Native JSON results to compare")
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8")) if args.manifest else fixture_manifest()
    if not args.native_output:
        print(json.dumps(manifest, indent=2))
        return
    actual = json.loads(args.native_output.read_text(encoding="utf-8"))
    report = validate_native_result(manifest, actual)
    print(json.dumps(report, indent=2))
    if not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
