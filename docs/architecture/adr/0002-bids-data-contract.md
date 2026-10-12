# ADR-0002: Native immutable archive plus validated EEG-BIDS

- Date: 2026-10-12
- Status: Accepted
- Scope: scientific data and interoperability

## Context
The current checksummed `.eegz` archive is a valid internal container but not an EEG-BIDS format. Lossy interpretation of channels, referencing or timing would undermine scientific reproducibility.

## Decision
Preserve original samples, timestamps and metadata in an immutable checksummed native source (with explicit interruption/quality flags). Export a separate MNE-BIDS EEG dataset using a BIDS-permitted format, initially BrainVision. Use actual channel labels, units, reference and event onsets relative to the recording start; do not invent unknown electrode positions or hardware timestamps. Separate raw BIDS from derivatives with `GeneratedBy` provenance. Invoke the official BIDS Validator and record its version/output. Block compliance claims on errors and test read-back with MNE for samples, metadata and event timing.

## Consequences
There are two independently traceable representations and additional dependencies for export. Conversion tolerances, participant anonymization and unknown metadata require documented handling.

## Alternatives
Native-only storage limits interoperability. BIDS-only acquisition risks destroying original timebase/packet evidence. Merely BIDS-styled folders do not satisfy the standard.

## Verification
Validator + round-trip comparison + corruption tests + explicit source/derivative linkage. Implementation remains pending until corresponding code merges.
