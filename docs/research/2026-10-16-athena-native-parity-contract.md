# Athena native decoder parity contract (issue #47)

This module makes **offline cross-implementation comparisons reproducible**; it does not invoke upstream BlueMuse or BrainFlow itself.

1. Export vectors: `python -m eeg_athenalyze.athena_native_parity > athena-fixtures.json`.
2. Pin a **full 40-character commit SHA** for BlueMuse or BrainFlow. Build the real upstream decoder at that revision using approved, cost-free infrastructure.
3. Feed the exact `payload_hex` bytes into the vendor decoder with the correct TAG and its documented EEG payload entry point. Produce `native-output.json` with `schema_version: 1`, `decoder: "BlueMuse"` or `"BrainFlow"`, `source_commit`, and a `vectors` array. For each ID supply `payload_sha256`, 2D integer `codes`, and 2D floating-point `uv`, in sample-major order. Do not silently transpose; record any upstream orientation differences explicitly.
4. Compare: `python -m eeg_athenalyze.athena_native_parity --manifest athena-fixtures.json --native-output native-output.json`. Exit code 1 flags differences. Default absolute tolerance: 1e-8 µV. Record compiler, build flags, upstream URL and pinned SHA with each native run.

The manifest is **synthetic-only** and does not contain participant EEG or a genuine BLE capture. `tests/test_athena_native_parity.py` exercises the comparator using *simulated* outputs only. Passing it **does not prove vendor binary parity**, even when the synthetic self-check says `passed=true`. BlueMuse and BrainFlow must each be run separately; their output must originate from their own compiled code at a recorded immutable source revision.

Pending separately: real Athena raw GATT notification bytes, firmware/preset and channel-to-electrode mapping, packet timing/index semantics, analogue saturation and EEG/BIDS validity. Do not remove the corresponding quality gates or commit personal EEG data.
