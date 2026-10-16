# Paired native decoder report gate (issue #47)

Following PR #71, compare **both** pinned native-decoder result reports rather than one self-reported file:

```bash
python -m eeg_athenalyze.athena_native_pair --bluemuse bluemuse-output.json --brainflow brainflow-output.json
```

Use `athena_native_parity.fixture_manifest()` to export the synthetic input set and produce the two outputs **by actually invoking separately compiled native upstream implementations**. Record immutable source commit, compiler, build settings, platform, input TAG and payload SHA-256 in a research run log. The pair validator rejects wrong or repeated decoder identity, incomplete vectors, incorrect code values, mismatched SHA-256 and amplitude differences. Tests use *simulated* reports, hence a passing CI run is not evidence that native code ran. The `source_commit` text is syntactically checked, **not cryptographically attested**; auditors must verify build provenance independently. The paired contract cannot detect two fabricated matching reports.

Physical validation remains blocked: true BLE notification bytes, firmware/preset, channel-to-electrode mapping, timestamp/counter semantics, ADC rails and analogue clipping, EEG-BIDS/physiological reliability. Do not upload human EEG or relax acquisition validity gates.
