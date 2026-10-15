# Timestamp-aware EO/EC analysis: verification specification

Related: #21, #22, #28.

## Current behavior and defect

`compare_resting_alpha` in `src/eeg_athenalyze/analysis/spectral.py` converts event onset and duration to sample indices by rounding elapsed seconds multiplied by nominal sample rate. This is valid for uniformly sampled synthetic data but is not a reliable selection method for measured recordings with duplicated timestamps, gaps or drift.

## Proposed contract

1. Keep the existing sample-index selection for explicitly simulated uniformly sampled archives, preserving current results.
2. For measured archives, interpret event bounds as half-open intervals `[onset_seconds, onset_seconds + duration_seconds)` in the same clock domain as `timestamps_seconds`. Select samples by timestamp, not nominal sample index.
3. Validate finite onset and duration, timestamp array length, nondecreasing timestamps, and clock origin. Reject incompatible clock domains rather than silently shifting events.
4. Detect duplicate timestamps and intersample gaps; report counts and durations. Do not apply Welch to a segment that crosses a discontinuity. Split into contiguous runs and aggregate PSD with explicit segment weighting; fail with a clear quality-control error if insufficient usable data remain.
5. Make gap tolerance configurable relative to expected sample period, document its units and provide a deterministic default. Do not infer that duplicate timestamps imply independent time samples.
6. For adjacent frequency bands use half-open intervals `[low, high)` except an explicitly documented terminal Nyquist edge. Preserve or version existing alpha-band behavior deliberately; never change numerical semantics without regression tests.

## Implemented minimum spectral-resolution gate

For measured event segments, the analyser only accepts contiguous runs of
at least `ceil(sample_rate_hz * max(1.0, 1.0 / band_width_hz))` samples
(minimum eight). This guarantees an unpadded time-window resolution no worse
than 1 Hz and no worse than the requested band width; zero-padding does not
satisfy the minimum duration. Runs shorter than the threshold are discarded,
and an event with no qualifying runs raises `ValueError` rather than
returning a misleading zero. Simulated uniform-clock archives retain their
legacy sample-index behavior. Usable measured runs are aggregated by actual
contributing Welch-window counts (not by their raw sample counts).

The default `max_gap_factor=1.5` allows consecutive timestamps separated
by at most 1.5 nominal sample periods. Duplicate timestamps and longer gaps
split runs. The coverage convention ends one nominal sample period after the
final measured timestamp.

## Regression test matrix

- Uniform 256 Hz synthetic EO/EC fixture: backward-compatible values.
- Measured timestamps with a fixed offset: correct event sample selection.
- Clock drift, jitter and duplicate timestamps: no index-based misalignment.
- Missing packet and long gap inside a condition: Welch windows never span the gap.
- Gap leaves fewer than eight samples, or leaves runs too short to resolve 8–13 Hz: explicit error, not plausible-looking alpha power.
- Empty event, negative duration, nonfinite timestamps, out-of-range event, mismatched array lengths: explicit errors.
- Two adjacent bands sharing a boundary: no double-counted edge bin.
- Windows and Ubuntu CI: same deterministic results; alpha regressions use explicit tolerances (0.02 and 0.04 µV²).

## Acceptance evidence

Store tests in `tests/`, implementation under `src/eeg_athenalyze/`, and document the QC policy in `docs/`. Capture command, commit SHA, test outcome and remaining limitations in #22. Real Muse validation remains a separate hardware gate and must not be claimed on the basis of simulated fixtures.
