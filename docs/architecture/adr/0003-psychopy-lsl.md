# ADR-0003: Optional PsychoPy engine and LSL-based coordination

- Date: 2026-10-12
- Status: Accepted
- Scope: experiment engine and clocks

## Context
Neuropsychology studies require controlled stimuli and reaction-time records, while EEG acquisition must remain usable without a task engine. Bluetooth arrival latency is not equivalent to source-clock time.

## Decision
Use PsychoPy Builder `.psyexp` templates for editable teaching tasks and PsychoPy Python API for dynamic paradigms. Run stimuli and EEG acquisition as separated components with explicit session coordination. Use LSL marker/EEG streams where supported, optional XDF persistence, clock-correction metadata and offline alignment. Prefer frame-aligned callbacks for stimulus marker emission. Preserve planned/software-observed/physically validated onset as distinct concepts. EO/EC remains independent of PsychoPy.

## Consequences
Requires extra runtime, clock-domain contracts and timing QA. LSL cannot reverse unknown Muse BLE delay. ERP and other event-locked research require a measured timing-validation protocol (e.g., photodiode) before timing claims.

## Alternatives
Embed PsychoPy into acquisition: dependency and failure coupling. Manual trial timestamps: insufficient for event-locked studies. LSL-only recordings without native archive: unacceptable loss of original evidence.

## Verification
Synthetic marker alignment; later a physical timing characterization on the Windows 11 + Muse device combination.
