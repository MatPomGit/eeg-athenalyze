"""Require two distinct, pinned decoder reports for offline Athena parity.

Reports remain user-supplied evidence: this code does NOT attest to binary
execution, authenticity, BLE device provenance, or clinical EEG quality.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from eeg_athenalyze.athena_native_parity import fixture_manifest, validate_native_result


def compare_paired_reports(manifest: dict, bluemuse: dict, brainflow: dict,
                           *, tolerance_uv: float = 1e-8) -> dict:
    if (isinstance(tolerance_uv, bool) or not isinstance(tolerance_uv, (int, float))
            or not math.isfinite(tolerance_uv) or tolerance_uv < 0):
        raise ValueError("Tolerance must be finite and nonnegative")
    if bluemuse.get("decoder") != "BlueMuse" or brainflow.get("decoder") != "BrainFlow":
        raise ValueError("Two ordered reports from distinct decoders are required")
    left = validate_native_result(manifest, bluemuse, tolerance_uv=tolerance_uv)
    right = validate_native_result(manifest, brainflow, tolerance_uv=tolerance_uv)
    # validate_native_result verifies complete manifest coverage, unique IDs,
    # matching hashes and sample-major codes, not proof of how outputs arose.
    differences = []
    b_rows = {v["id"]: v for v in bluemuse["vectors"]}
    f_rows = {v["id"]: v for v in brainflow["vectors"]}
    if left["passed"] and right["passed"]:
        for key in sorted(b_rows):
            a, b = b_rows[key], f_rows[key]
            if a["codes"] != b["codes"]:
                differences.append(key + ": native report integer mismatch")
            for row_a, row_b in zip(a["uv"], b["uv"]):
                if any(abs(x - y) > tolerance_uv for x, y in zip(row_a, row_b)):
                    differences.append(key + ": native report amplitude mismatch")
                    break
    return {
        "passed": left["passed"] and right["passed"] and not differences,
        "BlueMuse": left, "BrainFlow": right,
        "cross_report_differences": differences,
        "native_execution_attested": False,
        "hardware_validated": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bluemuse", required=True, type=Path)
    parser.add_argument("--brainflow", required=True, type=Path)
    parser.add_argument("--manifest", type=Path)
    args = parser.parse_args()
    manifest = (json.loads(args.manifest.read_text(encoding="utf-8"))
                if args.manifest else fixture_manifest())
    result = compare_paired_reports(
        manifest,
        json.loads(args.bluemuse.read_text(encoding="utf-8")),
        json.loads(args.brainflow.read_text(encoding="utf-8")))
    print(json.dumps(result, indent=2))
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
