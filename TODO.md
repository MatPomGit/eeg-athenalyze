# EEG Neurolyze: implementation TODO

Statuses: [x] implemented in main, [ ] planned or pending verification; see [roadmap](docs/architecture/ROADMAP.md). A merged implementation is not evidence of physical validation.

## M01 Core
- [x] Deterministic synthetic EEG and EO/EC session.
- [x] SHA-256-protected native .eegz archive and HTML analysis report.
- [x] Local Windows venv and synthetic demonstration launchers.

## M02 EEG-BIDS
- [x] Synthetic-only BrainVision export using MNE-BIDS and read-back check.
- [x] Official BIDS validator command and CI integration.
- [x] Custom alpha-power derivatives and provenance.
- [ ] Review BIDS derivatives standard schema and optional metadata completeness for scientific sharing.

## M03 Muse S Athena
- [x] Implement guarded native BrainFlow connection, start/stop, buffer collection, four-channel mapping and immutable archive (new PR).
- [x] Expose device diagnostics and physical recording CLI (new PR).
- [x] Provide minimal mock tests, Windows launcher and bilingual acquisition guide (new PR).
- [ ] Test actual Muse S Athena hardware under Windows 11; record BrainFlow version, firmware and BLE connection parameters.
- [ ] Confirm runtime board identifier spelling, sampling rate, electrode mapping, reference and units.
- [ ] Quantify BLE dropouts, source-clock discontinuities, packet-count agreement and sustained recording stability.
- [ ] Support per-preset archival for IMU and raw optical streams without mixing them into scalp EEG.
- [x] Append-only fsync-backed acquisition journal and recoverable complete rows, with journal removed only after successful archive finalization (new PR).
- [ ] Implement streamed final archive conversion to bound memory for very long sessions, automated recovery CLI and crash-injection tests. Journal recovery currently reads all complete samples into memory.
- [ ] Implement gap-aware measured-data conversion and validation for BIDS; currently BIDS intentionally accepts synthetic source only.
- [ ] Validate real EO/EC session quality and complete experiment timing; do not claim hardware readiness before this gate.

- [x] Add offline physical archive assessment CLI and Windows 11 hardware validation protocol (implementation only; validation still pending).

## M04 PsychoPy / LSL
- [ ] Isolated PsychoPy venv, Builder and Python API experiments.
- [ ] EEG/marker streams and clock-domain metadata; validate timing against external ground truth.

## M05–M07
- [ ] Stroop and N-back with behavioral data and BIDS events.
- [ ] Six bilingual laboratory tutorials, MkDocs and Pages.
- [ ] Validated ERP/BCI/online visualization modules.

## Safety and release gates
- [ ] Required Windows/Linux CI checks green on final PR head.
- [ ] Physical recording never silently substitutes synthetic data.
- [ ] Ensure no participant data or device credentials are committed to Git.
- [ ] Preserve existing CLI name `eeg-athenalyze` until ADR-0006 migration.
